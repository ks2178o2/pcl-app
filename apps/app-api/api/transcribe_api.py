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
    enable_diarization: Optional[str] = Form("true"),  # Default to True, accept as string
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
        valid_extensions = ['.mp3', '.wav', '.m4a', '.webm', '.ogg']
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
        
        # Parse enable_diarization (Form data comes as string)
        enable_diarization_bool = enable_diarization.lower() in ('true', '1', 'yes') if enable_diarization else True
        
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
                enable_diarization_bool,
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
    enable_diarization: bool = True,
    call_record_id: Optional[str] = None,  # Add optional call_record_id parameter
    file_id: Optional[str] = None,  # Add optional file_id parameter for updating bulk_import_files status
):
    """Background task: download audio via signed URL, send to provider, update DB.
    This implementation simulates provider processing and writes progress to
    public.transcription_queue when available.
    """
    print(f"🎬 _process_transcription_background CALLED: upload_id={upload_id}, provider={provider}, public_url_length={len(public_url) if public_url else 0}, call_record_id={call_record_id}")
    print(f"🎬 DEBUG: call_record_id parameter value: {call_record_id}, type: {type(call_record_id)}")
    logger.info(f"🎬 _process_transcription_background CALLED: upload_id={upload_id}, provider={provider}, call_record_id={call_record_id}")
    supabase = get_supabase_client()
    
    # Force flush stdout to ensure logs appear immediately
    import sys
    sys.stdout.flush()

    # Helper to update DB if table exists
    def _update(fields: dict):
        try:
            supabase.from_("transcription_queue").update(fields).eq("id", upload_id).execute()
        except Exception:
            pass

    # Mark processing
    print(f"📝 Updating transcription_queue status to processing for upload_id={upload_id}")
    _update({"status": "processing", "progress": 5, "error": None})

    try:
        # Download audio (signed URL works for private bucket)
        if not public_url:
            error_msg = "missing signed/public URL for audio fetch"
            print(f"❌ ERROR: {error_msg} for upload_id={upload_id}")
            raise RuntimeError(error_msg)
        
        print(f"📥 Downloading audio from signed URL for upload_id={upload_id} (provider={provider})")

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
        # Use call_record_id from parameter if provided, otherwise try to look it up
        if call_record_id is None:
            try:
                # Try to get call_record_id from transcription_queue
                print(f"🔍 Attempting to fetch call_record_id from transcription_queue for upload_id={upload_id}")
                queue_result = supabase.from_('transcription_queue').select('call_record_id').eq('id', upload_id).maybe_single().execute()
                if queue_result.data:
                    call_record_id = queue_result.data.get('call_record_id')
                    print(f"✅ Found call_record_id={call_record_id} from transcription_queue")
                else:
                    print(f"⚠️ No transcription_queue entry found for upload_id={upload_id} (will try call_id instead)")
            except Exception as e:
                print(f"⚠️ Error fetching call_record_id from transcription_queue: {e}")
                # Try with call_id instead (different schema versions)
                try:
                    queue_result = supabase.from_('transcription_queue').select('call_id').eq('id', upload_id).maybe_single().execute()
                    if queue_result.data:
                        call_record_id = queue_result.data.get('call_id')
                        print(f"✅ Found call_record_id={call_record_id} from transcription_queue (using call_id column)")
                except Exception as e2:
                    print(f"⚠️ Also failed to fetch call_id: {e2}")
        else:
            print(f"✅ Using call_record_id from parameter: {call_record_id}")
            
        if not call_record_id:
            print(f"⚠️ WARNING: No call_record_id available - transcript will not be saved to call_records table")

        for p in provider_order:
            if enabled and p not in enabled:
                print(f"⏭️ Skipping provider {p} (not enabled) for upload_id={upload_id}")
                continue
            try:
                print(f"🎙️ Calling transcription API: provider={p}, upload_id={upload_id}")
                if p == 'assemblyai':
                    result = _transcribe_with_assemblyai(public_url, enable_diarization)
                elif p == 'deepgram':
                    result = _transcribe_with_deepgram(public_url, enable_diarization)
                else:
                    print(f"⏭️ Unknown provider {p}, skipping for upload_id={upload_id}")
                    continue
                print(f"✅ Transcription API call completed for provider={p}, upload_id={upload_id}, transcript_length={len(result.get('transcript', '')) if result else 0}")

                transcript_text = result.get('transcript', '')
                diarization_segments = result.get('diarization_segments')
                diarization_confidence = result.get('diarization_confidence')

                update_fields = {
                    "status": "completed",
                    "progress": 100,
                    "transcript": transcript_text,
                    "provider": p,
                    "completed_at": datetime.utcnow().isoformat() + "Z",
                }
                
                if diarization_segments:
                    update_fields["diarization_segments"] = diarization_segments
                if diarization_confidence is not None:
                    update_fields["diarization_confidence"] = diarization_confidence

                print(f"📝 Updating transcription_queue with completed status for upload_id={upload_id}")
                _update(update_fields)

                # Update call_records if we have a call_record_id
                print(f"🔍 Checking for call_record_id: upload_id={upload_id}, call_record_id={call_record_id}, call_record_id type={type(call_record_id)}")
                if call_record_id:
                    print(f"✅ Found call_record_id={call_record_id}, updating call_records table with transcript (length: {len(transcript_text)} chars)")
                    try:
                        # Only update the transcript field - this is the core requirement
                        # Other fields like transcription_provider, diarization_segments, diarization_confidence
                        # may not exist in the call_records table schema
                        call_update = {
                            "transcript": transcript_text,
                        }
                        
                        # Validate transcript is complete before saving
                        if not transcript_text or len(transcript_text.strip()) < 10:
                            logger.warning(f"⚠️ Transcript too short or empty (length: {len(transcript_text) if transcript_text else 0}), skipping database update")
                            print(f"⚠️ TRANSCRIPTION INCOMPLETE: transcript too short (length: {len(transcript_text) if transcript_text else 0})")
                            return  # Don't update database or trigger analysis
                        
                        print(f"📝 Updating call_records table: call_record_id={call_record_id}, transcript_length={len(transcript_text)}")
                        print(f"📝 Update payload: transcript only (length={len(transcript_text)})")
                        update_result = supabase.from_('call_records').update(call_update).eq('id', call_record_id).execute()
                        if update_result.data:
                            logger.info(f"✅ Successfully updated call_record {call_record_id} with transcript (length: {len(transcript_text)} chars, provider: {p})")
                            print(f"✅ TRANSCRIPTION COMPLETE: call_record_id={call_record_id}, transcript_length={len(transcript_text)}, provider={p}")
                            import sys
                            sys.stdout.flush()
                            
                            # IMPORTANT: Only trigger analysis AFTER transcript is successfully saved to database
                            # This ensures analysis runs with the complete, final transcript
                            print(f"📊 Waiting 2 seconds before triggering analysis to ensure transcript is fully saved...")
                            import time
                            time.sleep(2)  # Brief pause to ensure database write is committed
                            
                            # Trigger analysis pipeline after successful transcription
                            # This will categorize the call, detect objections, and analyze objection overcomes
                            try:
                                print(f"📊 Triggering analysis pipeline for call_record_id={call_record_id}")
                                import asyncio
                                from services.call_analysis_service import CallAnalysisService
                                
                                # Create analysis service
                                analysis_service = CallAnalysisService(supabase)
                                
                                # Run analysis in async context
                                async def run_analysis():
                                    try:
                                        # Determine provider from environment: Gemini (primary) -> OpenAI (secondary)
                                        import os
                                        provider = "gemini"  # Default to Gemini (primary)
                                        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
                                            if os.getenv("OPENAI_API_KEY"):
                                                provider = "openai"
                                            else:
                                                provider = "heuristic"  # Last resort
                                        
                                        print(f"📊 Step 1: Categorizing call {call_record_id} with provider={provider}")
                                        category_result = await analysis_service.categorize_call(
                                            transcript=transcript_text,
                                            call_record_id=call_record_id,
                                            provider=provider
                                        )
                                        print(f"✅ Categorization complete: category={category_result.get('category')}, confidence={category_result.get('confidence')}")
                                        
                                        print(f"📊 Step 2: Detecting objections for call {call_record_id}")
                                        objections = await analysis_service.detect_objections(
                                            transcript=transcript_text,
                                            call_record_id=call_record_id,
                                            provider=provider
                                        )
                                        print(f"✅ Objection detection complete: found {len(objections) if objections else 0} objections")
                                        
                                        # If consult was scheduled, analyze objection overcome
                                        # Note: call_type is already stored in call_record from categorization
                                        if category_result.get("category") == "consult_scheduled" and objections:
                                            print(f"📊 Step 3: Analyzing objection overcomes for call {call_record_id}")
                                            call_type = category_result.get("call_type")
                                            if call_type:
                                                logger.info(f"Using call_type context '{call_type}' for objection overcome analysis")
                                            await analysis_service.analyze_objection_overcome(
                                                transcript=transcript_text,
                                                call_record_id=call_record_id,
                                                objections=objections,
                                                provider=provider
                                            )
                                            print(f"✅ Objection overcome analysis complete")
                                        
                                        print(f"✅ ANALYSIS PIPELINE COMPLETE: call_record_id={call_record_id}")
                                        
                                        # Update bulk_import_files status to "completed" if file_id is provided
                                        if file_id:
                                            try:
                                                supabase_for_update = get_supabase_client()
                                                if supabase_for_update:
                                                    update_result = supabase_for_update.table("bulk_import_files").update({
                                                        "status": "completed"
                                                    }).eq("id", file_id).execute()
                                                    if update_result.data:
                                                        logger.info(f"✅ Updated bulk_import_files {file_id} status to completed")
                                                        print(f"✅ Updated bulk_import_files {file_id} status to completed")
                                                    else:
                                                        logger.warning(f"⚠️ No data returned when updating bulk_import_files {file_id}")
                                            except Exception as file_update_error:
                                                logger.warning(f"⚠️ Failed to update bulk_import_files status: {file_update_error}")
                                                print(f"⚠️ Failed to update bulk_import_files status: {file_update_error}")
                                    except Exception as analysis_error:
                                        logger.error(f"❌ Error in analysis pipeline: {analysis_error}", exc_info=True)
                                        print(f"❌ ANALYSIS ERROR: {analysis_error}")
                                        import traceback
                                        print(f"❌ Analysis traceback: {traceback.format_exc()}")
                                        
                                        # Update file status to failed if analysis errored and we have file_id
                                        if file_id:
                                            try:
                                                supabase_for_update = get_supabase_client()
                                                if supabase_for_update:
                                                    supabase_for_update.table("bulk_import_files").update({
                                                        "status": "failed",
                                                        "error_message": f"Analysis failed: {str(analysis_error)[:500]}"
                                                    }).eq("id", file_id).execute()
                                            except Exception:
                                                pass
                                
                                # Run analysis in a new event loop (since we're in a thread)
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    loop.run_until_complete(run_analysis())
                                finally:
                                    loop.close()
                                    
                            except Exception as trigger_error:
                                logger.error(f"❌ Failed to trigger analysis pipeline: {trigger_error}", exc_info=True)
                                print(f"❌ Failed to trigger analysis: {trigger_error}")
                        else:
                            logger.warning(f"⚠️ No data returned when updating call_record {call_record_id} with transcript")
                            print(f"⚠️ TRANSCRIPTION UPDATE FAILED: call_record_id={call_record_id} - no data returned")
                    except Exception as e:
                        logger.error(f"❌ Failed to update call_records with transcript for {call_record_id}: {e}", exc_info=True)
                        print(f"❌ ERROR updating call_records: {e}")
                        import traceback
                        print(f"❌ Traceback: {traceback.format_exc()}")
                else:
                    print(f"⚠️ No call_record_id found for upload_id={upload_id} - cannot update call_records table")
                    print(f"⚠️ DEBUG: call_record_id is None or falsy. Parameter value was: {call_record_id}")

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
    print(f"🔵 Starting AssemblyAI transcription (signed_url_length={len(signed_url)}, diarization={enable_diarization})")
    # Accept both env var spellings for convenience
    api_key = os.getenv('ASSEMBLYAI_API_KEY') or os.getenv('ASSEMBLY_AI_API_KEY')
    if not api_key:
        error_msg = 'ASSEMBLYAI_API_KEY not set'
        print(f"❌ ERROR: {error_msg}")
        raise RuntimeError(error_msg)
    print(f"✅ AssemblyAI API key found")

    # Create transcript job
    headers = {
        'authorization': api_key,
        'content-type': 'application/json',
    }
    payload = {
        'audio_url': signed_url,
        'speaker_labels': enable_diarization,
    }
    r = requests.post('https://api.assemblyai.com/v2/transcript', json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    job_id = r.json().get('id')
    if not job_id:
        raise RuntimeError('AssemblyAI: missing job id')

    # Poll until completed/failed
    for _ in range(60):  # up to ~60 * 2s = 2 minutes
        s = requests.get(f'https://api.assemblyai.com/v2/transcript/{job_id}', headers=headers, timeout=15)
        s.raise_for_status()
        data = s.json()
        status = data.get('status')
        if status == 'completed':
            transcript_text = data.get('text') or ''
            result = {'transcript': transcript_text}
            
            # Extract diarization segments if available
            if enable_diarization and 'utterances' in data:
                utterances = data.get('utterances', [])
                diarization_segments = []
                for utt in utterances:
                    diarization_segments.append({
                        'speaker': f"Speaker {utt.get('speaker', 'A')}",
                        'text': utt.get('text', ''),
                        'start': utt.get('start', 0) / 1000.0,  # Convert ms to seconds
                        'end': utt.get('end', 0) / 1000.0,
                        'confidence': utt.get('confidence', 1.0)
                    })
                result['diarization_segments'] = diarization_segments
                # Calculate average confidence
                if diarization_segments:
                    avg_confidence = sum(seg.get('confidence', 1.0) for seg in diarization_segments) / len(diarization_segments)
                    result['diarization_confidence'] = avg_confidence
            
            return result
        if status == 'error':
            raise RuntimeError(f"AssemblyAI error: {data.get('error')}")
        # sleep 2s
        import time
        time.sleep(2)
    raise RuntimeError('AssemblyAI timeout')


def _transcribe_with_deepgram(signed_url: str, enable_diarization: bool = True) -> dict:
    print(f"🟣 Starting Deepgram transcription (signed_url_length={len(signed_url)}, diarization={enable_diarization})")
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        error_msg = 'DEEPGRAM_API_KEY not set'
        print(f"❌ ERROR: {error_msg}")
        raise RuntimeError(error_msg)
    print(f"✅ Deepgram API key found")

    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Build query parameters
    params = ['smart_format=true']
    if enable_diarization:
        params.append('diarize=true')
    
    url = f'https://api.deepgram.com/v1/listen?{"&".join(params)}'
    payload = { 'url': signed_url }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    
    # Extract transcript from Deepgram JSON
    try:
        result_data = data['results']['channels'][0]['alternatives'][0]
        transcript_text = result_data.get('transcript', '')
        result = {'transcript': transcript_text}
        
        # Extract diarization segments if available
        if enable_diarization and 'words' in result_data:
            words = result_data.get('words', [])
            diarization_segments = []
            current_speaker = None
            current_segment = None
            
            for word in words:
                speaker = word.get('speaker', 0)
                text = word.get('word', '')
                start = word.get('start', 0)
                end = word.get('end', 0)
                confidence = word.get('confidence', 1.0)
                
                if speaker != current_speaker:
                    # Save previous segment
                    if current_segment:
                        diarization_segments.append(current_segment)
                    # Start new segment
                    current_speaker = speaker
                    current_segment = {
                        'speaker': f"Speaker {speaker}",
                        'text': text,
                        'start': start,
                        'end': end,
                        'confidence': confidence
                    }
                else:
                    # Append to current segment
                    if current_segment:
                        current_segment['text'] += ' ' + text
                        current_segment['end'] = end
                        current_segment['confidence'] = (current_segment['confidence'] + confidence) / 2
            
            # Add final segment
            if current_segment:
                diarization_segments.append(current_segment)
            
            if diarization_segments:
                result['diarization_segments'] = diarization_segments
                # Calculate average confidence
                avg_confidence = sum(seg.get('confidence', 1.0) for seg in diarization_segments) / len(diarization_segments)
                result['diarization_confidence'] = avg_confidence
        
        return result
    except Exception as e:
        raise RuntimeError(f'Deepgram: unable to parse transcript: {str(e)}')

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


@router.post("/call-record/{call_record_id}", response_model=TranscriptionUploadResponse)
async def transcribe_call_record(
    call_record_id: str,
    enable_diarization: bool = True,  # Default to True
    provider: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger transcription for an existing call record by ID.
    Fetches the audio file from the call record and starts transcription.
    """
    supabase = get_supabase_client()
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        # Fetch call record from database
        call_record_result = supabase.from_('call_records').select('*').eq('id', call_record_id).single().execute()
        
        if not call_record_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call record {call_record_id} not found"
            )
        
        call_record = call_record_result.data
        
        # Verify user has access to this call record (check organization_id or center_id)
        user_org_id = current_user.get('organization_id')
        call_org_id = call_record.get('organization_id')
        
        # For now, allow if user's org matches or if org is None (admin)
        # TODO: Add proper RLS/permission checks
        if user_org_id and call_org_id and user_org_id != call_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this call record"
            )
        
        # Get audio file URL
        audio_file_url = call_record.get('audio_file_url')
        if not audio_file_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Call record has no audio file"
            )
        
        # Generate a signed URL for the audio file
        try:
            # Extract bucket and path from audio_file_url
            # Format is typically: "bucket/path/to/file" or just "path/to/file"
            signed_url_data = supabase.storage.from_('call-recordings').create_signed_url(
                audio_file_url,
                3600  # 1 hour expiry
            )
            
            if signed_url_data.get('error'):
                raise Exception(f"Failed to create signed URL: {signed_url_data.get('error')}")
            
            public_url = signed_url_data.get('signedURL') or signed_url_data.get('signedUrl')
        except Exception as e:
            logger.error(f"Error creating signed URL for audio file: {e}")
            # Try to use the audio_file_url directly if it's already public
            public_url = audio_file_url
        
        # Create upload_id for tracking
        upload_id = str(uuid.uuid4())
        
        # Get file extension from URL
        file_extension = os.path.splitext(audio_file_url)[1].lower() or '.webm'
        
        # Determine provider
        if not provider:
            provider_order, _ = _get_provider_settings(supabase, upload_id)
            provider = provider_order[0] if provider_order else 'deepgram'
        
        # Get customer and salesperson names from call record
        customer_name = call_record.get('customer_name') or 'Customer'
        salesperson_name = call_record.get('salesperson_name') or current_user.get('full_name') or current_user.get('email', 'User')
        
        # Create transcription_queue entry
        transcription_queue_data = {
            'id': upload_id,
            'user_id': current_user['user_id'],
            'organization_id': user_org_id or call_org_id,
            'storage_path': audio_file_url,
            'file_name': os.path.basename(audio_file_url),
            'status': 'queued',
            'progress': 0,
            'provider': provider,
            'call_record_id': call_record_id,  # Link to call record
        }
        
        try:
            supabase.from_('transcription_queue').insert(transcription_queue_data).execute()
        except Exception as e:
            logger.warning(f"Failed to insert into transcription_queue (table may not exist): {e}")
        
        # Update call record with upload_id in vendor_insights
        try:
            vendor_insights = call_record.get('vendor_insights') or {}
            if not isinstance(vendor_insights, dict):
                vendor_insights = {}
            
            vendor_insights['transcription_upload_id'] = upload_id
            supabase.from_('call_records').update({
                'vendor_insights': vendor_insights,
                'transcript': 'Transcribing audio...'
            }).eq('id', call_record_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update call record vendor_insights: {e}")
        
        # Start transcription in background
        transcription_started = False
        try:
            # Use background task to process transcription (non-blocking)
            if background_tasks:
                background_tasks.add_task(
                    _process_transcription_background,
                    upload_id,
                    audio_file_url,
                    public_url,
                    provider,
                    file_extension,
                    salesperson_name,
                    customer_name,
                    None,  # language
                    enable_diarization  # Pass diarization flag
                )
            else:
                # Fallback: run in thread if BackgroundTasks not available
                import threading
                thread = threading.Thread(
                    target=_process_transcription_background,
                    args=(upload_id, audio_file_url, public_url, provider, file_extension, salesperson_name, customer_name, None, enable_diarization),
                    daemon=True
                )
                thread.start()
            transcription_started = True
        except Exception as e:
            transcription_started = False
            logger.error(f"Failed to schedule background transcription: {e}")
        
        return TranscriptionUploadResponse(
            success=True,
            upload_id=upload_id,
            storage_path=audio_file_url,
            file_name=os.path.basename(audio_file_url),
            file_size=0,  # Size unknown without fetching
            transcript_job_id=upload_id if transcription_started else None,
            message="Transcription job queued successfully." if transcription_started else "Transcription will start shortly."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing call record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing call record: {str(e)}"
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

