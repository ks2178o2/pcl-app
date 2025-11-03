"""
Transcribe API - Handle audio file uploads for transcription
Supports AssemblyAI and Deepgram providers
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import os
import uuid
from services.supabase_client import get_supabase_client
from middleware.auth import get_current_user

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
    current_user: dict = Depends(get_current_user)
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
        
        if upload_result.error:
            logger.error(f"Storage upload failed: {upload_result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
        
        # Get public URL
        public_url_result = supabase.storage.from_('audio-transcriptions').get_public_url(storage_path)
        public_url = public_url_result.data.get('publicUrl') if public_url_result.data else None
        
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
        
        # Invoke Edge Function to start transcription
        transcription_started = False
        try:
            # Build payload for transcribe-audio-v2 edge function
            edge_function_payload = {
                'upload_id': upload_id,
                'storage_path': storage_path,
                'public_url': public_url,
                'provider': provider,
                'file_type': file_extension,
                'salespersonName': salesperson_name or 'User',
                'customerName': customer_name or 'Customer',
                'language': language
            }
            
            # Invoke Supabase Edge Function (async processing)
            edge_result = supabase.functions.invoke(
                'transcribe-audio-v2',
                body=edge_function_payload
            )
            
            if edge_result.data:
                transcription_started = True
                logger.info(f"Transcription job started for upload {upload_id} with {provider}")
        except Exception as e:
            logger.error(f"Failed to start transcription via edge function: {e}")
            # Continue even if edge function fails - user can retry later
        
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

