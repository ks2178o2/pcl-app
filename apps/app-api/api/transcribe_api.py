"""
Transcribe API - Handle audio file uploads for transcription
Supports AssemblyAI and Deepgram providers
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import os
import uuid
import requests
from services.supabase_client import get_supabase_client
from middleware.auth import get_current_user
from middleware.auth import require_system_admin, require_org_admin

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])

logger = logging.getLogger(__name__)

# Provider choices
class TranscriptionProvider(str):
    ASSEMBLYAI = "assemblyai"
    DEEPGRAM = "deepgram"


# ===========================================
# Pydantic Models
# ===========================================

class TranscriptionUploadResponse(BaseModel):
    success: bool
    upload_id: str
    storage_path: str
    file_name: str
    file_size: int
    transcript_job_id: Optional[str] = None
    message: str


class TranscriptionStatusResponse(BaseModel):
    upload_id: str
    status: str
    progress: Optional[float] = None
    transcript: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TranscriptionListResponse(BaseModel):
    transcriptions: List[dict]
    total: int


# ===========================================
# API Endpoints
# ===========================================

@router.post("/upload", response_model=TranscriptionUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio_for_transcription(
    file: UploadFile = File(...),
    provider: str = Form(..., pattern="^(assemblyai|deepgram)$"),
    language: Optional[str] = Form(None),
    salesperson_name: Optional[str] = Form(None),
    customer_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """
    Upload audio file for transcription
    Pushes transcription job to AssemblyAI or Deepgram queue
    
    Supported file types:
    - MP3, WAV, M4A, WebM, OGG
    - File size limit: 100MB
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        # Validate file type
        valid_extensions = ['.mp3', '.wav', '.m4a', '.webm', '.ogg', '.flac']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(valid_extensions)}"
            )
        
        # Validate file size (100MB limit)
        max_size = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds 100MB limit. Size: {len(file_content) / (1024*1024):.2f}MB"
            )
        
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Upload to Supabase Storage
        storage_path = f"transcriptions/{current_user['user_id']}/{upload_id}{file_extension}"
        
        upload_result = supabase.storage.from_('audio-transcriptions').upload(
            storage_path,
            file_content,
            file_options={'content-type': file.content_type or 'audio/mpeg'}
        )

        # Tolerate different client return shapes (dict or object)
        upload_error = None
        try:
            if isinstance(upload_result, dict):
                upload_error = upload_result.get('error')
            else:
                upload_error = getattr(upload_result, 'error', None)
        except Exception:
            upload_error = None

        if upload_error:
            logger.error(f"Storage upload failed: {upload_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
        
        # Obtain an access URL for the uploaded file.
        # If the bucket is private, generate a short‑lived signed URL; otherwise fall back to public URL.
        public_url = None
        try:
            # Try signed URL first (works for private buckets)
            signed = supabase.storage.from_('audio-transcriptions').create_signed_url(storage_path, 3600)
            # Handle multiple possible response shapes from supabase-py
            signed_url = None
            if isinstance(signed, dict):
                d = signed.get('data') if isinstance(signed.get('data'), dict) else signed
                if isinstance(d, dict):
                    signed_url = (
                        d.get('signedUrl') or d.get('signedURL') or d.get('signed_url')
                    )
            else:
                data = getattr(signed, 'data', None)
                if isinstance(data, dict):
                    signed_url = data.get('signedUrl') or data.get('signedURL') or data.get('signed_url')
                else:
                    # Some clients return the URL directly on the object
                    signed_url = getattr(signed, 'signedUrl', None) or getattr(signed, 'signedURL', None)

            if signed_url:
                public_url = signed_url
        except Exception:
            # Fallback to public URL (for public buckets)
            try:
                public_url_result = supabase.storage.from_('audio-transcriptions').get_public_url(storage_path)
                public_url = public_url_result.data.get('publicUrl') if public_url_result.data else None
            except Exception:
                public_url = None
        
        # Create transcription record in database
        transcription_record = {
            'id': upload_id,
            'user_id': current_user['user_id'],
            'organization_id': current_user.get('organization_id'),
            'file_name': file.filename,
            'file_size': len(file_content),
            'storage_path': storage_path,
            'public_url': public_url,
            'file_type': file_extension,
            'provider': provider,
            'language': language,
            'salesperson_name': salesperson_name,
            'customer_name': customer_name,
            'status': 'queued',
            'progress': 0
        }
        
        # Check if transcription_queue table exists and insert
        try:
            supabase.from_('transcription_queue').insert(transcription_record).execute()
        except Exception as e:
            logger.warning(f"Could not insert to transcription_queue table (may not exist): {e}")
            # Continue without database tracking if table doesn't exist
        
        # Start local background processing (portable across clouds)
        transcription_started = True
        try:
            background_tasks.add_task(
                _process_transcription_background,
                upload_id,
                storage_path,
                public_url,
                provider,
                file_extension,
                salesperson_name or 'User',
                customer_name or 'Customer',
                language,
            )
        except Exception as e:
            transcription_started = False
            logger.error(f"Failed to schedule background transcription: {e}")
        
        return TranscriptionUploadResponse(
            success=True,
            upload_id=upload_id,
            storage_path=storage_path,
            file_name=file.filename,
            file_size=len(file_content),
            transcript_job_id=upload_id if transcription_started else None,
            message="File uploaded successfully. Transcription job queued." if transcription_started else "File uploaded successfully. Transcription will start shortly."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file for transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


def _process_transcription_background(
    upload_id: str,
    storage_path: str,
    public_url: Optional[str],
    provider: str,
    file_extension: str,
    salesperson_name: str,
    customer_name: str,
    language: Optional[str],
):
    """Background task: download audio via signed URL, send to provider, update DB.
    This implementation simulates provider processing and writes progress to
    public.transcription_queue when available.
    """
    supabase = get_supabase_client()

    # Helper to update DB if table exists
    def _update(fields: dict):
        try:
            supabase.from_("transcription_queue").update(fields).eq("id", upload_id).execute()
        except Exception:
            pass

    # Mark processing
    _update({"status": "processing", "progress": 5, "error": None})

    try:
        # Download audio (signed URL works for private bucket)
        if not public_url:
            raise RuntimeError("missing signed/public URL for audio fetch")

        with requests.get(public_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            # In a real implementation we would stream to the provider here.
            # Simulate a small read to verify URL works.
            _ = next(r.iter_content(chunk_size=32768))

        # Determine provider order & enabled providers
        provider_order, enabled = _get_provider_settings(supabase, upload_id)
        # If a provider was requested, force it to be the only provider we try
        if provider in ("assemblyai", "deepgram"):
            provider_order = [provider]

        last_error = None
        for p in provider_order:
            if enabled and p not in enabled:
                continue
            try:
                if p == 'assemblyai':
                    result = _transcribe_with_assemblyai(public_url, enable_diarization=False)
                    transcript_text = result['transcript']
                elif p == 'deepgram':
                    result = _transcribe_with_deepgram(public_url, enable_diarization=False)
                    transcript_text = result['transcript']
                else:
                    continue

                _update({
                    "status": "completed",
                    "progress": 100,
                    "transcript": transcript_text,
                    "provider": p,
                    "completed_at": datetime.utcnow().isoformat() + "Z",
                })
                return
            except Exception as prov_exc:
                last_error = str(prov_exc)
                _update({"status": "processing", "progress": 50, "error": last_error})

        # All providers failed
        raise RuntimeError(last_error or "all providers failed")
    except Exception as exc:
        _update({"status": "failed", "error": str(exc)})


def _get_provider_settings(supabase, upload_id: str) -> tuple[list[str], Optional[list[str]]]:
    """Fetch provider order and enabled providers from transcription_settings.
    Falls back to env defaults if table missing or row absent.
    """
    # Define the allowed providers and default order; both can be configured via env
    # Start from env defaults
    # Prefer Deepgram by default for higher success rate
    env_available = os.getenv('TRANSCRIBE_AVAILABLE_PROVIDERS', 'deepgram,assemblyai')
    available = [p.strip() for p in env_available.split(',') if p.strip()]
    env_default = os.getenv('TRANSCRIBE_PROVIDER_ORDER', ','.join(available))
    default_order = [p.strip() for p in env_default.split(',') if p.strip()]

    # Try system-level settings first (sysadmin-managed)
    try:
        sysres = (
            supabase
            .from_('transcription_system_settings')
            .select('allowed_providers, default_order')
            .limit(1)
            .single()
            .execute()
        )
        if sysres and sysres.data:
            sys_allowed = sysres.data.get('allowed_providers')
            sys_default = sysres.data.get('default_order')
            if isinstance(sys_allowed, str):
                sys_allowed = [p.strip() for p in sys_allowed.split(',') if p.strip()]
            if isinstance(sys_default, str):
                sys_default = [p.strip() for p in sys_default.split(',') if p.strip()]
            if sys_allowed:
                available = [p for p in sys_allowed]
            if sys_default:
                default_order = [p for p in sys_default]
    except Exception:
        pass
    enabled = None

    try:
        # Join upload to get organization_id (if present)
        res = supabase.from_('transcription_queue').select('organization_id').eq('id', upload_id).single().execute()
        org_id = res.data.get('organization_id') if res and res.data else None
        if not org_id:
            return default_order, enabled

        st = (
            supabase
            .from_('transcription_settings')
            .select('provider_order, enabled_providers')
            .eq('organization_id', org_id)
            .single()
            .execute()
        )
        if st and st.data:
            order = st.data.get('provider_order') or default_order
            enabled = st.data.get('enabled_providers') or None
            # normalize
            if isinstance(order, str):
                order = [p.strip() for p in order.split(',') if p.strip()]
            if isinstance(enabled, str):
                enabled = [p.strip() for p in enabled.split(',') if p.strip()]
            # Enforce: only known providers and at most 3 in order
            order = [p for p in order if p in available][:3]
            if enabled is not None:
                enabled = [p for p in enabled if p in available]
            return order, enabled
    except Exception:
        pass
    # Fallback: clamp to available and at most 3
    return [p for p in default_order if p in available][:3], enabled


# ==========================
# Admin Settings Endpoints
# ==========================

@router.get('/system-settings', response_model=dict)
async def get_system_settings(user=Depends(require_system_admin)):
    """System-level transcription settings (allowed providers, default order)."""
    supabase = get_supabase_client()
    try:
        res = (
            supabase
            .from_('transcription_system_settings')
            .select('allowed_providers, default_order')
            .limit(1)
            .single()
            .execute()
        )
        data = res.data or {}
    except Exception:
        data = {}

    # Fallback to env if no row
    if not data:
        env_allowed = os.getenv('TRANSCRIBE_AVAILABLE_PROVIDERS', 'assemblyai,deepgram')
        env_default = os.getenv('TRANSCRIBE_PROVIDER_ORDER', env_allowed)
        return {
            'allowed_providers': [p.strip() for p in env_allowed.split(',') if p.strip()],
            'default_order': [p.strip() for p in env_default.split(',') if p.strip()][:3]
        }
    return data


class SystemSettingsPayload(BaseModel):
    allowed_providers: Optional[List[str]] = None
    default_order: Optional[List[str]] = None


@router.put('/system-settings', response_model=dict)
async def update_system_settings(payload: SystemSettingsPayload, user=Depends(require_system_admin)):
    supabase = get_supabase_client()
    allowed = payload.allowed_providers
    default = payload.default_order

    # Normalize
    if allowed is not None:
        allowed = [p.strip() for p in allowed if p and p.strip()]
    if default is not None:
        default = [p.strip() for p in default if p and p.strip()][:3]
    if allowed is not None and default is not None:
        # default must be subset of allowed
        default = [p for p in default if p in allowed]

    try:
        # Upsert single row
        record = {}
        if allowed is not None:
            record['allowed_providers'] = allowed
        if default is not None:
            record['default_order'] = default
        if not record:
            raise HTTPException(status_code=400, detail='No fields to update')

        supabase.from_('transcription_system_settings').upsert(record).execute()
        return {'success': True, **record}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'System settings update failed: {e}')
        raise HTTPException(status_code=500, detail='Failed to update system settings')


@router.get('/settings', response_model=dict)
async def get_org_settings(user=Depends(require_org_admin)):
    supabase = get_supabase_client()
    try:
        # Lookup org from profiles
        prof = supabase.table('profiles').select('organization_id').eq('user_id', user['user_id']).single().execute()
        org_id = prof.data.get('organization_id') if prof and prof.data else None
        if not org_id:
            return {}
        st = supabase.from_('transcription_settings').select('provider_order, enabled_providers').eq('organization_id', org_id).single().execute()
        return st.data or {}
    except Exception:
        return {}


class OrgSettingsPayload(BaseModel):
    provider_order: Optional[List[str]] = None
    enabled_providers: Optional[List[str]] = None


@router.put('/settings', response_model=dict)
async def update_org_settings(payload: OrgSettingsPayload, user=Depends(require_org_admin)):
    supabase = get_supabase_client()
    # Get system allowed list for validation
    sys_allowed, _ = _get_provider_settings(supabase, upload_id='')  # upload_id unused here
    allowed_set = set(sys_allowed) if sys_allowed else set(os.getenv('TRANSCRIBE_AVAILABLE_PROVIDERS', 'assemblyai,deepgram').split(','))

    try:
        # Lookup org id
        prof = supabase.table('profiles').select('organization_id').eq('user_id', user['user_id']).single().execute()
        org_id = prof.data.get('organization_id') if prof and prof.data else None
        if not org_id:
            raise HTTPException(status_code=400, detail='No organization context')

        record = {'organization_id': org_id}
        if payload.provider_order is not None:
            po = [p.strip() for p in payload.provider_order if p and p.strip()]
            po = [p for p in po if p in allowed_set][:3]
            record['provider_order'] = po
        if payload.enabled_providers is not None:
            en = [p.strip() for p in payload.enabled_providers if p and p.strip()]
            en = [p for p in en if p in allowed_set]
            record['enabled_providers'] = en
        if len(record) == 1:
            raise HTTPException(status_code=400, detail='No fields to update')

        supabase.from_('transcription_settings').upsert(record).execute()
        return {'success': True, **record}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Org settings update failed: {e}')
        raise HTTPException(status_code=500, detail='Failed to update org settings')


def _transcribe_with_assemblyai(signed_url: str, enable_diarization: bool = True) -> dict:
    """
    Transcribe audio with AssemblyAI, optionally with speaker diarization.
    Returns dict with 'transcript' and 'diarization_segments' keys.
    """
    # Accept both env var spellings for convenience
    api_key = os.getenv('ASSEMBLYAI_API_KEY') or os.getenv('ASSEMBLY_AI_API_KEY')
    if not api_key:
        raise RuntimeError('ASSEMBLYAI_API_KEY not set')

    # Create transcript job with speaker diarization enabled
    headers = {
        'authorization': api_key,
        'content-type': 'application/json',
    }
    payload = {
        'audio_url': signed_url,
        'speaker_labels': enable_diarization,  # Enable speaker diarization
    }
    r = requests.post('https://api.assemblyai.com/v2/transcript', json=payload, headers=headers, timeout=30)
    if not r.ok:
        logger.error(f"AssemblyAI create error: {r.status_code} {r.text}")
        r.raise_for_status()
    job_id = r.json().get('id')
    if not job_id:
        raise RuntimeError('AssemblyAI: missing job id')

    # Poll until completed/failed
    import time
    for _ in range(60):  # up to ~60 * 2s = 2 minutes
        s = requests.get(f'https://api.assemblyai.com/v2/transcript/{job_id}', headers=headers, timeout=15)
        if not s.ok:
            logger.error(f"AssemblyAI poll error: {s.status_code} {s.text}")
            s.raise_for_status()
        data = s.json()
        status = data.get('status')
        if status == 'completed':
            transcript = data.get('text') or ''
            
            # Extract diarization segments if available
            diarization_segments = []
            if enable_diarization and data.get('utterances'):
                for utterance in data.get('utterances', []):
                    diarization_segments.append({
                        'speaker': f"Speaker {utterance.get('speaker', 'A')}",
                        'start': utterance.get('start', 0) / 1000.0,  # Convert ms to seconds
                        'end': utterance.get('end', 0) / 1000.0,
                        'text': utterance.get('text', ''),
                        'confidence': utterance.get('confidence', 0.0)
                    })
            
            return {
                'transcript': transcript,
                'diarization_segments': diarization_segments if diarization_segments else None,
                'num_speakers': len(set(seg.get('speaker') for seg in diarization_segments)) if diarization_segments else None
            }
        if status == 'error':
            raise RuntimeError(f"AssemblyAI error: {data.get('error')}")
        # sleep 2s
        time.sleep(2)
    raise RuntimeError('AssemblyAI timeout')


def _transcribe_with_deepgram(signed_url: str, enable_diarization: bool = True) -> dict:
    """
    Transcribe audio with Deepgram, optionally with speaker diarization.
    Returns dict with 'transcript' and 'diarization_segments' keys.
    """
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise RuntimeError('DEEPGRAM_API_KEY not set')

    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    payload = { 'url': signed_url }
    
    # Build query parameters for diarization
    params = ['smart_format=true']
    if enable_diarization:
        params.append('diarize=true')
        params.append('punctuate=true')
    
    preview = signed_url[:80] + ('...' if len(signed_url) > 80 else '')
    logger.info(f"Deepgram request starting for URL: {preview} (diarization: {enable_diarization})")
    
    url = f"https://api.deepgram.com/v1/listen?{'&'.join(params)}"
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if not r.ok:
        logger.error(f"Deepgram error: {r.status_code} {r.text}")
        r.raise_for_status()
    data = r.json()
    
    # Extract transcript and diarization segments from Deepgram JSON
    try:
        channel = data['results']['channels'][0]
        alternative = channel['alternatives'][0]
        transcript = alternative['transcript']
        
        diarization_segments = []
        if enable_diarization and alternative.get('paragraphs'):
            # Deepgram paragraphs format includes speaker information
            for para in alternative.get('paragraphs', {}).get('paragraphs', []):
                speaker = para.get('speaker', 0)
                start = para.get('start', 0)
                end = para.get('end', 0)
                text = para.get('sentences', [{}])[0].get('text', '') if para.get('sentences') else ''
                
                diarization_segments.append({
                    'speaker': f"Speaker {speaker}",
                    'start': start,
                    'end': end,
                    'text': text,
                    'confidence': para.get('confidence', 0.0)
                })
        elif enable_diarization and alternative.get('words'):
            # Fallback: use words with speaker labels if paragraphs not available
            current_speaker = None
            current_start = None
            current_end = None
            current_words = []
            
            for word in alternative.get('words', []):
                word_speaker = word.get('speaker', 0)
                word_start = word.get('start', 0)
                word_end = word.get('end', 0)
                word_text = word.get('word', '')
                
                if current_speaker is None or word_speaker != current_speaker:
                    # Save previous segment
                    if current_speaker is not None and current_words:
                        diarization_segments.append({
                            'speaker': f"Speaker {current_speaker}",
                            'start': current_start,
                            'end': current_end,
                            'text': ' '.join(current_words),
                            'confidence': 0.85  # Default confidence
                        })
                    # Start new segment
                    current_speaker = word_speaker
                    current_start = word_start
                    current_end = word_end
                    current_words = [word_text]
                else:
                    current_end = word_end
                    current_words.append(word_text)
            
            # Save last segment
            if current_speaker is not None and current_words:
                diarization_segments.append({
                    'speaker': f"Speaker {current_speaker}",
                    'start': current_start,
                    'end': current_end,
                    'text': ' '.join(current_words),
                    'confidence': 0.85
                })
        
        return {
            'transcript': transcript,
            'diarization_segments': diarization_segments if diarization_segments else None,
            'num_speakers': len(set(seg.get('speaker') for seg in diarization_segments)) if diarization_segments else None
        }
    except Exception as e:
        logger.error(f"Deepgram parsing error: {e}")
        raise RuntimeError(f'Deepgram: unable to parse transcript - {str(e)}')

@router.get("/status/{upload_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get transcription status by upload ID
    """
    supabase = get_supabase_client()
    
    try:
        # Try to get from transcription_queue table
        result = supabase.from_('transcription_queue').select('*').eq('id', upload_id).single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        # Verify ownership
        if result.data.get('user_id') != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transcription"
            )
        
        return TranscriptionStatusResponse(
            upload_id=upload_id,
            status=result.data.get('status', 'unknown'),
            progress=result.data.get('progress'),
            transcript=result.data.get('transcript'),
            provider=result.data.get('provider'),
            error=result.data.get('error'),
            created_at=result.data.get('created_at'),
            completed_at=result.data.get('completed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching status: {str(e)}"
        )


@router.get("/self-test", response_model=dict)
async def transcribe_self_test(user=Depends(get_current_user)):
    """Quick provider self-test using a public audio URL.
    Returns provider results or error details to validate keys/connectivity.
    """
    deepgram_key = os.getenv('DEEPGRAM_API_KEY')
    assembly_key = os.getenv('ASSEMBLYAI_API_KEY') or os.getenv('ASSEMBLY_AI_API_KEY')
    # Public test audio sample (small file)
    test_url = os.getenv('TRANSCRIBE_TEST_URL', 'https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav')
    results = {}
    if deepgram_key:
        try:
            txt = _transcribe_with_deepgram(test_url)
            results['deepgram'] = {'ok': True, 'sample': txt[:160]}
        except Exception as e:
            results['deepgram'] = {'ok': False, 'error': str(e)}
    if assembly_key:
        try:
            txt = _transcribe_with_assemblyai(test_url)
            results['assemblyai'] = {'ok': True, 'sample': txt[:160]}
        except Exception as e:
            results['assemblyai'] = {'ok': False, 'error': str(e)}
    if not results:
        return {'warning': 'No provider keys set', 'test_url': test_url}
    return {'test_url': test_url, 'results': results}


@router.get("/list", response_model=TranscriptionListResponse)
async def list_transcriptions(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List user's transcriptions
    """
    supabase = get_supabase_client()
    
    try:
        query = supabase.from_('transcription_queue').select('*', count='exact').eq('user_id', current_user['user_id'])
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return TranscriptionListResponse(
            transcriptions=result.data if result.data else [],
            total=result.count if result.count else 0
        )
        
    except Exception as e:
        logger.error(f"Error listing transcriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing transcriptions: {str(e)}"
        )


@router.post("/call-record/{call_record_id}", response_model=dict)
async def transcribe_call_record(
    call_record_id: str,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None,
    enable_diarization: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """
    Transcribe a call_record with optional speaker diarization.
    Updates call_records table with transcript and diarization_segments.
    """
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        # Fetch call record
        call_result = supabase.from_('call_records').select('*').eq('id', call_record_id).single().execute()
        
        if not call_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call record not found"
            )
        
        call_record = call_result.data
        
        # Verify ownership
        if call_record.get('user_id') != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this call record"
            )
        
        # Get audio file URL
        audio_url = call_record.get('audio_file_url')
        if not audio_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No audio file URL found for this call record"
            )
        
        # Determine provider
        transcription_provider = provider or call_record.get('transcription_provider') or 'deepgram'
        
        # Start transcription in background
        background_tasks.add_task(
            _transcribe_call_record_background,
            call_record_id,
            audio_url,
            transcription_provider,
            enable_diarization,
        )
        
        return {
            'success': True,
            'message': 'Transcription started',
            'call_record_id': call_record_id,
            'provider': transcription_provider,
            'diarization_enabled': enable_diarization
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting transcription: {str(e)}"
        )


def _transcribe_call_record_background(
    call_record_id: str,
    audio_url: str,
    provider: str,
    enable_diarization: bool,
):
    """Background task: transcribe audio and update call_records with transcript and diarization."""
    supabase = get_supabase_client()
    
    # Helper to update call_records
    def _update_call_record(fields: dict):
        try:
            result = supabase.from_("call_records").update(fields).eq("id", call_record_id).execute()
            logger.debug(f"Updated call_records with fields: {list(fields.keys())}")
            return result
        except Exception as e:
            logger.error(f"Failed to update call_records: {e}")
            raise  # Re-raise so caller knows update failed
    
    # Mark as transcribing
    _update_call_record({"status": "transcribing"})
    
    try:
        # Convert storage path to signed URL if needed
        # audio_url might be just a path like "folder/file.webm" or already a full URL
        signed_url = audio_url
        if not audio_url.startswith('http://') and not audio_url.startswith('https://'):
            # It's a storage path, create a signed URL
            try:
                # Create signed URL valid for 1 hour (same pattern as used elsewhere in codebase)
                signed = supabase.storage.from_('call-recordings').create_signed_url(audio_url, 3600)
                signed_url = None
                
                # Handle different possible return formats from Supabase Python client
                if isinstance(signed, dict):
                    signed_url = (
                        signed.get('signedUrl') or 
                        signed.get('signedURL') or 
                        signed.get('signed_url') or
                        signed.get('url')
                    )
                elif hasattr(signed, 'signedUrl'):
                    signed_url = getattr(signed, 'signedUrl', None) or getattr(signed, 'signedURL', None)
                elif isinstance(signed, str):
                    signed_url = signed
                
                if signed_url:
                    logger.info(f"Created signed URL for storage path: {audio_url[:50]}... -> {signed_url[:80]}...")
                else:
                    logger.warning(f"Failed to extract signed URL from response: {signed}")
                    # Try to construct public URL as fallback
                    supabase_url = os.getenv('SUPABASE_URL', '')
                    if supabase_url:
                        signed_url = f"{supabase_url}/storage/v1/object/public/call-recordings/{audio_url}"
                        logger.info(f"Using public URL fallback: {signed_url[:80]}...")
            except Exception as e:
                logger.error(f"Error creating signed URL for {audio_url}: {e}")
                # Try to construct public URL as fallback
                supabase_url = os.getenv('SUPABASE_URL', '')
                if supabase_url:
                    signed_url = f"{supabase_url}/storage/v1/object/public/call-recordings/{audio_url}"
                    logger.info(f"Using public URL fallback: {signed_url[:80]}...")
        
        # Determine provider order
        provider_order = [provider] if provider in ("assemblyai", "deepgram") else ["deepgram", "assemblyai"]
        
        last_error = None
        result = None
        
        for p in provider_order:
            try:
                if p == 'assemblyai':
                    result = _transcribe_with_assemblyai(signed_url, enable_diarization=enable_diarization)
                elif p == 'deepgram':
                    result = _transcribe_with_deepgram(signed_url, enable_diarization=enable_diarization)
                else:
                    continue
                
                # Success - update call_records
                transcript_text = result.get('transcript', '') or ''
                # Only include fields that exist in the database
                update_fields = {
                    "transcript": transcript_text,
                    "status": "completed",
                }
                # Only add transcription_provider if column exists (optional field)
                # We'll try to add it, but handle errors gracefully
                
                # Log diarization info
                has_segments = bool(result.get('diarization_segments'))
                segments_count = len(result['diarization_segments']) if has_segments else 0
                logger.info(f"Transcription result for {call_record_id}: transcript_length={len(transcript_text)}, enable_diarization={enable_diarization}, has_segments={has_segments}, segments_count={segments_count}")
                logger.info(f"Transcript preview (first 200 chars): {transcript_text[:200]}")
                
                if enable_diarization and result.get('diarization_segments'):
                    update_fields['diarization_segments'] = result['diarization_segments']
                    # Try to add num_speakers if available, but don't fail if column doesn't exist
                    if result.get('num_speakers'):
                        update_fields['num_speakers'] = result['num_speakers']
                
                # Save the update (with or without num_speakers)
                try:
                    _update_call_record(update_fields)
                    if enable_diarization and result.get('diarization_segments'):
                        logger.info(f"✅ Successfully saved transcript (len={len(transcript_text)}) + {segments_count} diarization segments to call_record {call_record_id}")
                    else:
                        logger.warning(f"No diarization segments to save for {call_record_id}: enable_diarization={enable_diarization}, has_segments={has_segments}")
                except Exception as save_error:
                    # If save failed due to missing columns, retry without them
                    save_error_str = str(save_error)
                    save_error_msg = save_error_str.lower()
                    
                    # Identify which columns are missing
                    missing_columns = []
                    if 'num_speakers' in save_error_msg and 'num_speakers' in update_fields:
                        missing_columns.append('num_speakers')
                    if 'transcription_provider' in save_error_msg and 'transcription_provider' in update_fields:
                        missing_columns.append('transcription_provider')
                    
                    if missing_columns:
                        logger.warning(f"⚠️ Save failed due to missing columns: {missing_columns}, retrying without them: {save_error}")
                        update_fields_retry = {k: v for k, v in update_fields.items() if k not in missing_columns}
                        logger.info(f"Retry update fields (keys): {list(update_fields_retry.keys())}, transcript_length={len(update_fields_retry.get('transcript', '') or '')}")
                        try:
                            _update_call_record(update_fields_retry)
                            logger.info(f"✅ Successfully saved transcript (len={len(transcript_text)}) + {segments_count} diarization segments (without {missing_columns}) to call_record {call_record_id}")
                        except Exception as retry_error:
                            logger.error(f"❌ Retry save also failed: {retry_error}")
                            raise  # Re-raise if retry also fails
                    else:
                        logger.error(f"❌ Save failed with unknown error: {save_error}")
                        raise  # Re-raise if it's a different error
                logger.info(f"Successfully transcribed call_record {call_record_id} with {p}")
                return
                
            except Exception as prov_exc:
                last_error = str(prov_exc)
                logger.warning(f"Provider {p} failed: {last_error}")
                continue
        
        # All providers failed
        try:
            _update_call_record({
                "status": "completed",
                "transcript": "Transcription failed: " + (last_error or "all providers failed")
            })
        except Exception as update_err:
            logger.error(f"Failed to update call_record with failure status: {update_err}")
        raise RuntimeError(last_error or "all providers failed")
        
    except Exception as exc:
        logger.error(f"Transcription failed for call_record {call_record_id}: {exc}")
        try:
            _update_call_record({
                "status": "completed",
                "transcript": f"Transcription failed: {str(exc)}"
            })
        except Exception as update_err:
            logger.error(f"Failed to update call_record with error status: {update_err}")


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcription(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a transcription and its associated file
    """
    supabase = get_supabase_client()
    
    try:
        # Verify ownership
        result = supabase.from_('transcription_queue').select('storage_path').eq('id', upload_id).eq('user_id', current_user['user_id']).single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        storage_path = result.data.get('storage_path')
        
        # Delete from database
        supabase.from_('transcription_queue').delete().eq('id', upload_id).execute()
        
        # Delete file from storage
        if storage_path:
            supabase.storage.from_('audio-transcriptions').remove([storage_path])
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting transcription: {str(e)}"
        )


@router.post("/retry/{upload_id}", response_model=dict)
async def retry_transcription(
    upload_id: str,
    provider: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Retry a failed transcription with optional provider override
    """
    supabase = get_supabase_client()
    
    try:
        # Get transcription record
        result = supabase.from_('transcription_queue').select('*').eq('id', upload_id).eq('user_id', current_user['user_id']).single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        record = result.data
        
        # Update status to queued
        new_provider = provider or record.get('provider', 'deepgram')
        supabase.from_('transcription_queue').update({
            'status': 'queued',
            'progress': 0,
            'provider': new_provider,
            'error': None
        }).eq('id', upload_id).execute()
        
        # Invoke edge function to restart transcription
        edge_function_payload = {
            'upload_id': upload_id,
            'storage_path': record.get('storage_path'),
            'public_url': record.get('public_url'),
            'provider': new_provider,
            'file_type': record.get('file_type'),
            'salespersonName': record.get('salesperson_name') or 'User',
            'customerName': record.get('customer_name') or 'Customer',
            'language': record.get('language')
        }
        
        supabase.functions.invoke('transcribe-audio-v2', body=edge_function_payload)
        
        return {
            'success': True,
            'message': f'Transcription job restarted with {new_provider}'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrying transcription: {str(e)}"
        )

