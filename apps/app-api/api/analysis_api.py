from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import os
import logging
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

logger = logging.getLogger(__name__)


class AnalyzePayload(BaseModel):
    prompt: str


@router.post("/analyze", response_model=dict)
async def analyze(payload: AnalyzePayload, current_user: dict = Depends(get_current_user)):
    """Analyze transcript text via provider (OpenAI if available), return { analysis }.
    Falls back to a simple heuristic summary if no provider key is set.
    """
    text = payload.prompt or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty prompt")

    openai_key = os.getenv("OPENAI_API_KEY")

    # Try OpenAI if available
    if openai_key:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            }
            # Use gpt-4o-mini or gpt-3.5-turbo compatible endpoint
            body = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes sales call transcripts and extracts insights succinctly."},
                    {"role": "user", "content": f"Summarize this sales call and extract key insights, objections, next steps.\n\n{text}"},
                ],
                "temperature": 0.2,
            }
            resp = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return {"analysis": content}
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            # Fall through to heuristic

    # Heuristic fallback
    # Simple extraction of key sentences
    summary = text.strip()
    if len(summary) > 1200:
        summary = summary[:1200] + "..."
    analysis = f"Summary: {summary}\n\nKey points:\n- Potential interest detected if keywords like 'price', 'timeline' present.\n- Objections and next steps should be confirmed on follow-up."
    return {"analysis": analysis}


