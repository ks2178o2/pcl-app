from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
import json
import time
import random
import asyncio
from middleware.auth import get_current_user, require_org_admin
from services.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

logger = logging.getLogger(__name__)

# Rate limiting: cap concurrent analysis requests (default: 3)
MAX_CONCURRENT_ANALYSES = int(os.getenv('MAX_CONCURRENT_ANALYSES', '3'))
_analysis_semaphore: Optional[asyncio.Semaphore] = None

def get_analysis_semaphore() -> asyncio.Semaphore:
    """Get or create the analysis semaphore (lazy initialization)"""
    global _analysis_semaphore
    if _analysis_semaphore is None:
        _analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)
    return _analysis_semaphore

# Retry configuration
MAX_RETRIES = int(os.getenv('ANALYSIS_MAX_RETRIES', '3'))
BASE_RETRY_DELAY = float(os.getenv('ANALYSIS_BASE_RETRY_DELAY', '1.0'))  # seconds
MAX_RETRY_DELAY = float(os.getenv('ANALYSIS_MAX_RETRY_DELAY', '30.0'))  # seconds


class AnalyzePayload(BaseModel):
    prompt: str
    provider: Optional[str] = None  # Optional override, but org settings take precedence


def _calculate_retry_delay(attempt: int) -> float:
    """Calculate exponential backoff with jitter"""
    # Exponential: base * 2^attempt
    delay = BASE_RETRY_DELAY * (2 ** attempt)
    # Cap at max delay
    delay = min(delay, MAX_RETRY_DELAY)
    # Add jitter: ±25% random variation
    jitter = delay * 0.25 * (random.random() * 2 - 1)  # -0.25 to +0.25
    final_delay = delay + jitter
    # Ensure non-negative
    return max(0.1, final_delay)


def _retry_with_backoff(func, *args, **kwargs):
    """Retry a function call with exponential backoff + jitter"""
    import requests
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            last_error = e
            # Check HTTP status code
            is_rate_limit = e.response.status_code == 429
            error_str = str(e)
            
            # Also check error message for rate limit indicators
            if not is_rate_limit:
                is_rate_limit = '429' in error_str or 'Too Many Requests' in error_str or 'rate limit' in error_str.lower()
            
            # Don't retry on non-rate-limit errors after first attempt
            if not is_rate_limit and attempt > 0:
                logger.debug(f"Non-rate-limit error on attempt {attempt + 1}, not retrying: {e}")
                raise e
            
            # If this is the last attempt, raise
            if attempt == MAX_RETRIES - 1:
                logger.warning(f"Max retries ({MAX_RETRIES}) reached for {func.__name__}")
                raise last_error
            
            # Calculate delay and wait
            delay = _calculate_retry_delay(attempt)
            logger.info(f"Retry attempt {attempt + 1}/{MAX_RETRIES} after {delay:.2f}s delay for {func.__name__}: {e}")
            time.sleep(delay)
        except Exception as e:
            last_error = e
            error_str = str(e)
            # Check if it's a rate limit error (429) in error message
            is_rate_limit = '429' in error_str or 'Too Many Requests' in error_str or 'rate limit' in error_str.lower()
            
            # Don't retry on non-rate-limit errors after first attempt
            if not is_rate_limit and attempt > 0:
                logger.debug(f"Non-rate-limit error on attempt {attempt + 1}, not retrying: {e}")
                raise e
            
            # If this is the last attempt, raise
            if attempt == MAX_RETRIES - 1:
                logger.warning(f"Max retries ({MAX_RETRIES}) reached for {func.__name__}")
                raise last_error
            
            # Calculate delay and wait
            delay = _calculate_retry_delay(attempt)
            logger.info(f"Retry attempt {attempt + 1}/{MAX_RETRIES} after {delay:.2f}s delay for {func.__name__}: {e}")
            time.sleep(delay)
    
    # Should never reach here, but just in case
    raise last_error


def _get_org_analysis_settings(supabase, user_id: str) -> tuple[List[str], List[str]]:
    """Fetch provider order and enabled providers from analysis_settings.
    Falls back to env defaults if table missing or row absent.
    Returns (provider_order, enabled_providers)
    """
    env_available = os.getenv('ANALYSIS_AVAILABLE_PROVIDERS', 'openai,gemini')
    available = [p.strip() for p in env_available.split(',') if p.strip()]
    env_default = os.getenv('ANALYSIS_PROVIDER_ORDER', ','.join(available))
    default_order = [p.strip() for p in env_default.split(',') if p.strip()]

    try:
        # Lookup org from profiles (tolerant: take newest row if multiples exist)
        prof = (
            supabase
            .table('profiles')
            .select('organization_id, created_at')
            .eq('user_id', user_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        # supabase-py returns list under .data for non-single queries
        prof_row = (prof.data[0] if isinstance(prof.data, list) and prof.data else prof.data) if prof else None
        org_id = prof_row.get('organization_id') if prof_row else None
        if not org_id:
            return (default_order, available)

        # Try to fetch org-specific settings (tolerant)
        try:
            st = (
                supabase
                .from_('analysis_settings')
                .select('provider_order, enabled_providers, created_at')
                .eq('organization_id', org_id)
                .order('created_at', desc=True)
                .limit(1)
                .execute()
            )
            st_row = (st.data[0] if isinstance(st.data, list) and st.data else st.data) if st else None
            if st_row:
                order = st_row.get('provider_order') or default_order
                enabled = st_row.get('enabled_providers') or None
                # Normalize
                if isinstance(order, str):
                    order = [p.strip() for p in order.split(',') if p.strip()]
                if isinstance(enabled, str):
                    enabled = [p.strip() for p in enabled.split(',') if p.strip()]
                # Filter enabled by available
                if enabled:
                    order = [p for p in order if p in enabled and p in available]
                else:
                    order = [p for p in order if p in available]
                return (order or default_order, enabled or available)
        except Exception as e:
            logger.debug(f"No org analysis settings found: {e}")
            # Table might not exist yet, fall through to defaults

    except Exception as e:
        logger.warning(f"Error fetching analysis settings: {e}")

    return (default_order, available)


def _analyze_with_openai(text: str) -> str:
    """Analyze text using OpenAI API with retry logic"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not set")

    import requests
    
    def _make_openai_request():
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes healthcare consultation transcripts and extracts insights for healthcare consumer psychology and sales optimization."},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    
    return _retry_with_backoff(_make_openai_request)


def _analyze_with_gemini(text: str) -> str:
    """Analyze text using Google Gemini API with retry logic"""
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        raise ValueError("GOOGLE_API_KEY not set")

    import requests
    
    def _make_gemini_request():
        # Use Gemini 2.0 Flash Experimental API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={google_key}"
        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [{
                "parts": [{"text": text}]
            }],
            "generationConfig": {
                "temperature": 0.2,
            }
        }
        resp = requests.post(url, json=body, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Extract text from Gemini response
        if "candidates" in data and len(data["candidates"]) > 0:
            content = data["candidates"][0].get("content", {})
            parts = content.get("parts", [])
            if parts and len(parts) > 0:
                return parts[0].get("text", "").strip()
        raise ValueError("Unexpected Gemini response format")
    
    return _retry_with_backoff(_make_gemini_request)


@router.post("/analyze", response_model=dict)
async def analyze(payload: AnalyzePayload, current_user: dict = Depends(get_current_user)):
    """Analyze transcript text via org-configured providers (primary/backup).
    Falls back to heuristic summary if all providers fail.
    Rate-limited to prevent 429 errors.
    """
    text = payload.prompt or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty prompt")

    # Rate limiting: acquire semaphore (caps concurrent analyses)
    async with get_analysis_semaphore():
        logger.debug(f"Analysis request acquired semaphore ({MAX_CONCURRENT_ANALYSES} max concurrent)")
        
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        
        # Get org-specific provider order
        provider_order, enabled_providers = _get_org_analysis_settings(supabase, user_id)
        
        # Allow override via payload.provider, but still respect enabled list
        if payload.provider and payload.provider in enabled_providers:
            provider_order = [payload.provider] + [p for p in provider_order if p != payload.provider]

        # Try each provider in order
        last_error = None
        for provider in provider_order:
            try:
                logger.info(f"Attempting analysis with {provider}")
                if provider == "openai":
                    # Run blocking LLM call in thread pool to avoid blocking event loop
                    content = await asyncio.to_thread(_analyze_with_openai, text)
                    return {"analysis": content, "provider": "openai"}
                elif provider == "gemini":
                    # Run blocking LLM call in thread pool to avoid blocking event loop
                    content = await asyncio.to_thread(_analyze_with_gemini, text)
                    return {"analysis": content, "provider": "gemini"}
            except Exception as e:
                logger.error(f"{provider} analysis failed: {e}")
                last_error = e
                # Continue to next provider

        # Heuristic fallback if all providers failed
        logger.warning(f"All analysis providers failed, using heuristic. Last error: {last_error}")
        summary = text.strip()
        if len(summary) > 1200:
            summary = summary[:1200] + "..."
        analysis = f"Summary: {summary}\n\nKey points:\n- Potential interest detected if keywords like 'price', 'timeline' present.\n- Objections and next steps should be confirmed on follow-up."
        return {"analysis": analysis, "provider": "heuristic"}


class AnalysisSettingsPayload(BaseModel):
    provider_order: Optional[List[str]] = None
    enabled_providers: Optional[List[str]] = None


@router.get('/settings', response_model=dict)
async def get_analysis_settings(user=Depends(require_org_admin)):
    """Get analysis provider settings for current user's organization (admin only)"""
    supabase = get_supabase_client()
    try:
        # Tolerant: newest profile row for this user
        prof = (
            supabase
            .table('profiles')
            .select('organization_id, created_at')
            .eq('user_id', user['user_id'])
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        prof_row = (prof.data[0] if isinstance(prof.data, list) and prof.data else prof.data) if prof else None
        org_id = prof_row.get('organization_id') if prof_row else None
        if not org_id:
            raise HTTPException(status_code=400, detail='No organization context')

        st = (
            supabase
            .from_('analysis_settings')
            .select('provider_order, enabled_providers, created_at')
            .eq('organization_id', org_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        st_row = (st.data[0] if isinstance(st.data, list) and st.data else st.data) if st else None
        return st_row or {}
    except Exception:
        return {}


@router.put('/settings', response_model=dict)
async def update_analysis_settings(payload: AnalysisSettingsPayload, user=Depends(require_org_admin)):
    """Update analysis provider settings for current user's organization (admin only)"""
    supabase = get_supabase_client()
    # Get system allowed list for validation
    _, sys_allowed = _get_org_analysis_settings(supabase, user['user_id'])
    allowed_set = set(sys_allowed) if sys_allowed else set(os.getenv('ANALYSIS_AVAILABLE_PROVIDERS', 'openai,gemini').split(','))

    try:
        # Lookup org id
        prof = (
            supabase
            .table('profiles')
            .select('organization_id, created_at')
            .eq('user_id', user['user_id'])
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        prof_row = (prof.data[0] if isinstance(prof.data, list) and prof.data else prof.data) if prof else None
        org_id = prof_row.get('organization_id') if prof_row else None
        if not org_id:
            raise HTTPException(status_code=400, detail='No organization context')

        record = {'organization_id': org_id}
        if payload.provider_order is not None:
            po = [p.strip() for p in payload.provider_order if p and p.strip()]
            po = [p for p in po if p in allowed_set][:3]  # Limit to 3 providers
            record['provider_order'] = po
        if payload.enabled_providers is not None:
            en = [p.strip() for p in payload.enabled_providers if p and p.strip()]
            en = [p for p in en if p in allowed_set]
            record['enabled_providers'] = en
        if len(record) == 1:
            raise HTTPException(status_code=400, detail='No fields to update')

        supabase.from_('analysis_settings').upsert(record).execute()
        return {'success': True, **record}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Analysis settings update failed: {e}')
        raise HTTPException(status_code=500, detail='Failed to update analysis settings')


