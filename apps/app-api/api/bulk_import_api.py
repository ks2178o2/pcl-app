"""
Bulk Import API - Handle bulk audio file imports from web sources
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os
import re
import httpx
from services.supabase_client import get_supabase_client
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/bulk-import", tags=["bulk-import"])

logger = logging.getLogger(__name__)

# Maximum file size: 1GB
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB

# Supported audio formats
SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.webm', '.ogg']


class BulkImportRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    source_url: HttpUrl
    provider: Optional[str] = Field("openai", pattern="^(openai|gemini)$")
    call_log_file_url: Optional[HttpUrl] = Field(None, description="Optional URL to call log file for mapping")


class BulkImportJobResponse(BaseModel):
    success: bool
    job_id: str
    customer_name: str
    storage_bucket_name: str
    message: str


class BulkImportStatusResponse(BaseModel):
    job_id: str
    status: str
    customer_name: str
    total_files: int
    processed_files: int
    failed_files: int
    progress_percentage: float
    error_message: Optional[str] = None
    call_log_mapping_skipped: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    files: Optional[List[Dict[str, Any]]] = None


@router.post("/start", response_model=BulkImportJobResponse, status_code=status.HTTP_201_CREATED)
async def start_bulk_import(
    request: BulkImportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Start a bulk import job for a customer.
    Creates storage bucket, discovers audio files, and starts processing.
    """
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )

    try:
        # Sanitize customer name for bucket name (alphanumeric, hyphens, underscores only)
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '-', request.customer_name.lower())
        sanitized_name = re.sub(r'-+', '-', sanitized_name).strip('-')
        if not sanitized_name:
            sanitized_name = f"customer-{datetime.now().strftime('%Y%m%d')}"
        
        bucket_name = f"customer-{sanitized_name}"
        
        # Create storage bucket if it doesn't exist
        try:
            # Check if bucket exists
            buckets = supabase.storage.list_buckets()
            bucket_exists = any(b.name == bucket_name for b in buckets)
            
            if not bucket_exists:
                # Create bucket using REST API directly (Supabase Python client has issues)
                try:
                    supabase_url = os.getenv('SUPABASE_URL', 'https://xxdahmkfioqzgqvyabek.supabase.co')
                    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
                    
                    if supabase_key:
                        # Use REST API to create bucket
                        api_url = f"{supabase_url}/storage/v1/bucket"
                        headers = {
                            "Authorization": f"Bearer {supabase_key}",
                            "Content-Type": "application/json",
                            "apikey": supabase_key
                        }
                        # Create bucket with minimal settings to avoid payload size issues
                        # Start with just name and public flag, then we can update settings if needed
                        payload = {
                            "name": bucket_name,
                            "public": False
                        }
                        
                        with httpx.Client() as client:
                            response = client.post(api_url, json=payload, headers=headers, timeout=10.0)
                            if response.status_code in [200, 201]:
                                logger.info(f"Created storage bucket: {bucket_name} via REST API")
                            elif response.status_code == 409:
                                logger.info(f"Storage bucket already exists: {bucket_name}")
                            else:
                                logger.warning(f"Bucket creation failed: {response.status_code} - {response.text}")
                except Exception as create_error:
                    logger.warning(f"Bucket creation failed: {create_error}. Bucket may need to be created manually.")
                    # Don't raise - continue anyway, bucket might exist or be created manually
            else:
                logger.info(f"Storage bucket already exists: {bucket_name}")
        except Exception as e:
            logger.warning(f"Bucket creation/check failed (may already exist): {e}")
            # Continue - bucket might already exist

        # Create analysis sub-bucket
        analysis_bucket_name = f"{bucket_name}-analysis"
        try:
            analysis_buckets = supabase.storage.list_buckets()
            analysis_bucket_exists = any(b.name == analysis_bucket_name for b in analysis_buckets)
            
            if not analysis_bucket_exists:
                try:
                    # Create analysis bucket using REST API directly
                    supabase_url = os.getenv('SUPABASE_URL', 'https://xxdahmkfioqzgqvyabek.supabase.co')
                    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
                    
                    if supabase_key:
                        api_url = f"{supabase_url}/storage/v1/bucket"
                        headers = {
                            "Authorization": f"Bearer {supabase_key}",
                            "Content-Type": "application/json",
                            "apikey": supabase_key
                        }
                        payload = {
                            "name": analysis_bucket_name,
                            "public": False,
                            "allowed_mime_types": ["application/json", "text/plain"],
                            "file_size_limit": 10 * 1024 * 1024
                        }
                        
                        with httpx.Client() as client:
                            response = client.post(api_url, json=payload, headers=headers, timeout=10.0)
                            if response.status_code in [200, 201]:
                                logger.info(f"Created analysis storage bucket: {analysis_bucket_name} via REST API")
                            elif response.status_code == 409:
                                logger.info(f"Analysis bucket already exists: {analysis_bucket_name}")
                            else:
                                logger.warning(f"Analysis bucket creation failed: {response.status_code} - {response.text}")
                except Exception as create_error:
                    logger.warning(f"Analysis bucket creation failed: {create_error}. Bucket may need to be created manually.")
                    # Continue anyway - bucket might already exist or be created manually
        except Exception as e:
            logger.warning(f"Analysis bucket creation/check failed: {e}")

        # Create bulk import job record
        job_data = {
            "user_id": current_user["id"],
            "customer_name": request.customer_name,
            "source_url": str(request.source_url),
            "storage_bucket_name": bucket_name,
            "status": "pending"
        }

        result = supabase.table("bulk_import_jobs").insert(job_data).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create import job"
            )

        job_id = result.data[0]["id"]
        logger.info(f"Created bulk import job: {job_id} for customer: {request.customer_name}")

        # Start background processing
        background_tasks.add_task(
            process_bulk_import,
            job_id=job_id,
            customer_name=request.customer_name,
            source_url=str(request.source_url),
            bucket_name=bucket_name,
            user_id=current_user["id"],
            provider=request.provider or "openai",
            call_log_file_url=str(request.call_log_file_url) if request.call_log_file_url else None
        )
        logger.info(f"Background task queued for job: {job_id}")

        return BulkImportJobResponse(
            success=True,
            job_id=job_id,
            customer_name=request.customer_name,
            storage_bucket_name=bucket_name,
            message=f"Bulk import job started for {request.customer_name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bulk import: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bulk import: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=BulkImportStatusResponse)
async def get_import_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    include_files: bool = False,
):
    """Get the status of a bulk import job"""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )

    try:
        # Get job
        job_result = supabase.table("bulk_import_jobs").select("*").eq("id", job_id).eq("user_id", current_user["id"]).execute()
        
        if not job_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found"
            )

        job = job_result.data[0]

        # Calculate progress
        total = job.get("total_files", 0)
        processed = job.get("processed_files", 0)
        progress = (processed / total * 100) if total > 0 else 0.0

        # Check if call log mapping was skipped
        error_msg = job.get("error_message", "")
        call_log_mapping_skipped = "Call log file mapping skipped" in error_msg if error_msg else False
        
        # Extract discovery details if present
        discovery_details = None
        try:
            if error_msg and "DISCOVERY_JSON::" in error_msg:
                # Extract JSON after the marker - find the last occurrence
                parts = error_msg.split("DISCOVERY_JSON::")
                if len(parts) > 1:
                    # Take everything after the last marker
                    payload_str = parts[-1].strip()
                    # Try to parse as JSON
                    import json as _json
                    discovery_details = _json.loads(payload_str)
                    logger.info(f"Extracted discovery_details: discovered={discovery_details.get('discovered')}, entries={len(discovery_details.get('entries', []))}")
        except Exception as parse_error:
            logger.warning(f"Failed to parse discovery_details from error_message: {parse_error}")
            discovery_details = None
        
        response_data = {
            "job_id": job_id,
            "status": job["status"],
            "customer_name": job["customer_name"],
            "total_files": total,
            "processed_files": processed,
            "failed_files": job.get("failed_files", 0),
            "progress_percentage": round(progress, 2),
            "error_message": job.get("error_message"),
            "call_log_mapping_skipped": call_log_mapping_skipped,
            "discovery_details": discovery_details,
            "created_at": datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")),
            "updated_at": datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00")),
            "completed_at": datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00")) if job.get("completed_at") else None,
        }

        # Add discovery counts: discovered (from job.total_files) and unique (from bulk_import_files count)
        try:
            unique_count_result = supabase.table("bulk_import_files").select("id", count="exact").eq("job_id", job_id).execute()
            # Some client versions return count on the result object, others in data length
            unique_files_count = None
            if hasattr(unique_count_result, 'count') and unique_count_result.count is not None:
                unique_files_count = unique_count_result.count
            elif unique_count_result.data is not None:
                unique_files_count = len(unique_count_result.data)
            else:
                unique_files_count = 0
            response_data["discovered_files"] = int(total or 0)
            response_data["unique_files"] = int(unique_files_count or 0)
        except Exception as _:
            response_data["discovered_files"] = int(total or 0)
            response_data["unique_files"] = None

        # Include file details if requested
        if include_files:
            files_result = supabase.table("bulk_import_files").select("*").eq("job_id", job_id).execute()
            files = files_result.data if files_result.data else []
            logger.info(f"Found {len(files)} files for job {job_id}")
            
            # Batch fetch all nested data to avoid N+1 queries
            call_record_ids = [f.get("call_record_id") for f in files if f.get("call_record_id")]
            logger.info(f"Found {len(call_record_ids)} call_record_ids: {call_record_ids}")
            
            if call_record_ids:
                try:
                    # Batch fetch all call records in one query
                    # Only select columns that actually exist in the database
                    call_records_result = supabase.table("call_records").select(
                        "id,transcript,call_category,call_type,categorization_confidence,categorization_notes"
                    ).in_("id", call_record_ids).execute()
                    logger.info(f"🔍 Backend: Fetched {len(call_records_result.data) if call_records_result.data else 0} call_records for job {job_id}")
                    # Log sample transcript lengths
                    if call_records_result.data:
                        for cr in call_records_result.data[:3]:
                            transcript_len = len(cr.get("transcript", "") or "") if cr.get("transcript") else 0
                            logger.info(f"🔍 Backend: call_record {cr['id']}: transcript_length={transcript_len}, has_transcript={bool(cr.get('transcript'))}")
                            print(f"🔍 Backend: call_record {cr['id']}: transcript_length={transcript_len}, transcript_preview={str(cr.get('transcript', ''))[:50] if cr.get('transcript') else 'None'}")
                    
                    call_records_map = {}
                    if call_records_result.data:
                        call_records_map = {cr["id"]: cr for cr in call_records_result.data}
                        logger.info(f"Fetched {len(call_records_map)} call_records. Sample: {list(call_records_map.keys())[:3]}")
                        # Log sample transcript lengths
                        for cr_id, cr_data in list(call_records_map.items())[:2]:
                            transcript_len = len(cr_data.get("transcript", "") or "")
                            logger.info(f"Call record {cr_id}: transcript length={transcript_len}, category={cr_data.get('call_category')}")
                    else:
                        logger.warning(f"No call_records found for IDs: {call_record_ids}")
                    
                    # Batch fetch all objections in one query
                    objections_result = supabase.table("call_objections").select("*").in_("call_record_id", call_record_ids).execute()
                    objections_map = {}
                    if objections_result.data:
                        for obj in objections_result.data:
                            cr_id = obj.get("call_record_id")
                            if cr_id not in objections_map:
                                objections_map[cr_id] = []
                            objections_map[cr_id].append(obj)
                        logger.info(f"Fetched {len(objections_result.data)} objections across {len(objections_map)} call records")
                    else:
                        logger.info("No objections found for any call records")
                    
                    # Batch fetch all objection overcomes in one query
                    objection_ids = [obj["id"] for obj_list in objections_map.values() for obj in obj_list if obj.get("id")]
                    overcomes_map = {}
                    if objection_ids:
                        try:
                            overcomes_result = supabase.table("objection_overcome_details").select("*").in_("objection_id", objection_ids).execute()
                            if overcomes_result.data:
                                for overcome in overcomes_result.data:
                                    obj_id = overcome.get("objection_id")
                                    if obj_id not in overcomes_map:
                                        overcomes_map[obj_id] = []
                                    overcomes_map[obj_id].append(overcome)
                        except Exception as overcome_error:
                            logger.warning(f"Error batch fetching objection overcomes: {overcome_error}")
                    
                    # Match data to files
                    files_with_data = 0
                    for file_data in files:
                        call_record_id = file_data.get("call_record_id")
                        if call_record_id:
                            if call_record_id in call_records_map:
                                call_record_data = call_records_map[call_record_id].copy()
                                # Derive consult_scheduled from call_category for frontend compatibility
                                call_record_data["consult_scheduled"] = call_record_data.get("call_category") == "consult_scheduled"
                                # Derive objection_detected from whether objections exist
                                call_record_data["objection_detected"] = call_record_id in objections_map and len(objections_map.get(call_record_id, [])) > 0
                                file_data["call_record"] = call_record_data
                                files_with_data += 1
                                
                                # Attach objections for this call record
                                if call_record_id in objections_map:
                                    file_data["objections"] = objections_map[call_record_id]
                                    
                                    # Attach objection overcomes
                                    file_objection_overcomes = []
                                    for obj in file_data["objections"]:
                                        obj_id = obj.get("id")
                                        if obj_id and obj_id in overcomes_map:
                                            file_objection_overcomes.extend(overcomes_map[obj_id])
                                    
                                    if file_objection_overcomes:
                                        file_data["objection_overcomes"] = file_objection_overcomes
                            else:
                                logger.warning(f"Call record {call_record_id} not found in call_records_map for file {file_data.get('file_name')}")
                    logger.info(f"Matched data to {files_with_data} files out of {len(files)} total files")
                
                except Exception as e:
                    logger.error(f"Error batch fetching nested data for job {job_id}: {e}", exc_info=True)
                    # Fall back to individual queries if batch fails
                    for file_data in files:
                        call_record_id = file_data.get("call_record_id")
                        if call_record_id:
                            try:
                                call_result = supabase.table("call_records").select(
                                    "id,transcript,call_category,call_type,categorization_confidence,categorization_notes"
                                ).eq("id", call_record_id).maybe_single().execute()
                                
                                if call_result.data:
                                    call_record_data = call_result.data.copy()
                                    # Derive consult_scheduled from call_category for frontend compatibility
                                    call_record_data["consult_scheduled"] = call_record_data.get("call_category") == "consult_scheduled"
                                    
                                    try:
                                        objections_result = supabase.table("call_objections").select("*").eq("call_record_id", call_record_id).execute()
                                        if objections_result.data:
                                            file_data["objections"] = objections_result.data
                                            # Set objection_detected based on whether objections exist
                                            call_record_data["objection_detected"] = len(objections_result.data) > 0
                                            
                                            objection_ids = [obj["id"] for obj in objections_result.data if obj.get("id")]
                                            if objection_ids:
                                                try:
                                                    overcome_result = supabase.table("objection_overcome_details").select("*").in_("objection_id", objection_ids).execute()
                                                    if overcome_result.data:
                                                        file_data["objection_overcomes"] = overcome_result.data
                                                except Exception as overcome_error:
                                                    logger.debug(f"Error fetching objection overcomes: {overcome_error}")
                                        else:
                                            call_record_data["objection_detected"] = False
                                    except Exception as objection_error:
                                        logger.debug(f"Error fetching objections: {objection_error}")
                                        call_record_data["objection_detected"] = False
                                    
                                    file_data["call_record"] = call_record_data
                            except Exception as e:
                                logger.debug(f"Error fetching call record data for {call_record_id}: {e}")
            
            response_data["files"] = files

        return BulkImportStatusResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get import status: {str(e)}"
        )


@router.post("/retranscribe/{call_record_id}", status_code=status.HTTP_200_OK)
async def retranscribe_call(
    call_record_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retry transcription for a specific call record"""
    logger.info(f"🔄 RETRANSCRIBE REQUEST: call_record_id={call_record_id}, user_id={current_user.get('id')}")
    print(f"🔄 RETRANSCRIBE REQUEST: call_record_id={call_record_id}, user_id={current_user.get('id')}")
    
    supabase = get_supabase_client()
    if not supabase:
        logger.error("❌ RETRANSCRIBE FAILED: Supabase client not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        # Get call record
        logger.info(f"📋 Step 1: Fetching call record {call_record_id}")
        print(f"📋 Step 1: Fetching call record {call_record_id}")
        call_result = supabase.table("call_records").select("*").eq("id", call_record_id).eq("user_id", current_user["id"]).execute()
        
        if not call_result.data:
            logger.warning(f"⚠️ RETRANSCRIBE FAILED: Call record {call_record_id} not found for user {current_user.get('id')}")
            print(f"⚠️ RETRANSCRIBE FAILED: Call record {call_record_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call record not found"
            )
        
        call_record = call_result.data[0]
        logger.info(f"✅ Step 1: Found call record - customer: {call_record.get('customer_name')}, transcript: {call_record.get('transcript', '')[:50]}...")
        print(f"✅ Step 1: Found call record - customer: {call_record.get('customer_name')}")
        
        # Get file_id from bulk_import_files for status updates (needed regardless of audio_file_url path)
        file_id = None
        try:
            file_result = supabase.table("bulk_import_files").select("id, storage_path").eq("call_record_id", call_record_id).limit(1).execute()
            if file_result.data:
                file_id = file_result.data[0].get("id")
                logger.info(f"📋 Step 2a: Found file_id={file_id} for call_record_id={call_record_id}")
        except Exception as e:
            logger.debug(f"Could not fetch file_id: {e}")
        
        # Check if audio_file_url exists
        logger.info(f"📋 Step 2: Checking audio_file_url")
        audio_file_url = call_record.get("audio_file_url")
        if not audio_file_url:
            logger.warning(f"⚠️ audio_file_url not found in call_record, trying to construct from job_id")
            # Try to construct from bulk_import_job_id and storage path
            job_id = call_record.get("bulk_import_job_id")
            if job_id:
                logger.info(f"📋 Step 2b: Fetching file record for job_id={job_id}")
                # Get the file record to find storage_path (file_id already fetched above)
                if file_result and file_result.data and file_result.data[0].get("storage_path"):
                    storage_path = file_result.data[0].get("storage_path")
                    logger.info(f"📋 Step 2c: Found storage_path={storage_path}, fetching bucket name")
                    # Get job to find bucket name
                    job_result = supabase.table("bulk_import_jobs").select("storage_bucket_name").eq("id", job_id).execute()
                    if job_result.data:
                        bucket_name = job_result.data[0].get("storage_bucket_name")
                        audio_file_url = f"{bucket_name}/{storage_path}"
                        logger.info(f"✅ Step 2: Constructed audio_file_url={audio_file_url}")
            
            if not audio_file_url:
                logger.error(f"❌ RETRANSCRIBE FAILED: Cannot construct audio_file_url")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot retranscribe: audio file URL not found. Please re-import the file."
                )
        else:
            logger.info(f"✅ Step 2: Found audio_file_url={audio_file_url}")
        
        # Parse bucket and path from audio_file_url
        # Format: bucket_name/storage_path
        logger.info(f"📋 Step 3: Parsing audio_file_url")
        url_parts = audio_file_url.split('/', 1)
        if len(url_parts) != 2:
            logger.error(f"❌ RETRANSCRIBE FAILED: Invalid audio_file_url format: {audio_file_url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio_file_url format: {audio_file_url}"
            )
        
        bucket_name = url_parts[0]
        storage_path = url_parts[1]
        logger.info(f"✅ Step 3: Parsed - bucket={bucket_name}, path={storage_path}")
        
        # Generate signed URL
        logger.info(f"📋 Step 4: Generating signed URL for bucket={bucket_name}, path={storage_path}")
        print(f"📋 Step 4: Generating signed URL for bucket={bucket_name}, path={storage_path}")
        try:
            signed_url_response = supabase.storage.from_(bucket_name).create_signed_url(
                storage_path,
                3600  # 1 hour expiry
            )
            
            if isinstance(signed_url_response, dict):
                public_url = signed_url_response.get("signedURL") or signed_url_response.get("signed_url")
            elif hasattr(signed_url_response, 'data'):
                signed_data = signed_url_response.data
                if isinstance(signed_data, dict):
                    public_url = signed_data.get("signedURL") or signed_data.get("signed_url")
            else:
                public_url = None
            
            if not public_url:
                logger.error(f"❌ RETRANSCRIBE FAILED: Could not extract signed URL from response: {signed_url_response}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate signed URL for audio file"
                )
            logger.info(f"✅ Step 4: Generated signed URL (length: {len(public_url)} chars)")
            print(f"✅ Step 4: Generated signed URL (length: {len(public_url)} chars)")
        except Exception as e:
            logger.error(f"❌ RETRANSCRIBE FAILED: Error generating signed URL: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate signed URL: {str(e)}"
            )
        
        # Determine transcription provider
        logger.info(f"📋 Step 5: Determining transcription provider")
        import os
        deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        assemblyai_key = os.getenv("ASSEMBLY_AI_API_KEY") or os.getenv("ASSEMBLYAI_API_KEY")
        
        transcription_provider = "deepgram"  # Default
        if deepgram_key:
            transcription_provider = "deepgram"
            logger.info(f"✅ Step 5: Using Deepgram (DEEPGRAM_API_KEY found)")
        elif assemblyai_key:
            transcription_provider = "assemblyai"
            logger.info(f"✅ Step 5: Using AssemblyAI (ASSEMBLY_AI_API_KEY found)")
        else:
            logger.error(f"❌ RETRANSCRIBE FAILED: No transcription API keys configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No transcription API keys configured (DEEPGRAM_API_KEY or ASSEMBLY_AI_API_KEY)"
            )
        
        # Delete existing analysis data (objections, objection overcomes, categorization) before retranscribing
        logger.info(f"📋 Step 6a: Deleting existing analysis data for call_record {call_record_id}")
        try:
            # Delete objection overcome details first (they reference objections)
            overcome_delete_result = supabase.table("objection_overcome_details").delete().eq("call_record_id", call_record_id).execute()
            logger.info(f"✅ Step 6a: Deleted objection overcome details for call_record {call_record_id}")
        except Exception as overcome_delete_error:
            logger.warning(f"⚠️ Step 6a: Error deleting objection overcome details: {overcome_delete_error}")
        
        try:
            # Delete objections
            objection_delete_result = supabase.table("call_objections").delete().eq("call_record_id", call_record_id).execute()
            logger.info(f"✅ Step 6a: Deleted objections for call_record {call_record_id}")
        except Exception as objection_delete_error:
            logger.warning(f"⚠️ Step 6a: Error deleting objections: {objection_delete_error}")
        
        # Update call record to show transcription is in progress and clear analysis data
        logger.info(f"📋 Step 6: Updating call_record transcript to 'Processing...' and clearing analysis data")
        update_result = supabase.table("call_records").update({
            "transcript": "Processing...",
            "call_category": None,
            "call_type": None,
            "categorization_confidence": None,
            "categorization_notes": None
        }).eq("id", call_record_id).execute()
        if update_result.data:
            logger.info(f"✅ Step 6: Updated call_record transcript status and cleared analysis data")
        else:
            logger.warning(f"⚠️ Step 6: Update returned no data")
        
        # Trigger transcription in background
        logger.info(f"📋 Step 7: Setting up background transcription thread")
        from api.transcribe_api import _process_transcription_background
        import threading
        import uuid
        from datetime import datetime
        
        upload_id = str(uuid.uuid4())
        file_ext = os.path.splitext(storage_path)[1].lower() or ".wav"
        customer_name = call_record.get("customer_name", "Customer")
        
        logger.info(f"📋 Step 7: Transcription params - upload_id={upload_id}, provider={transcription_provider}, file_ext={file_ext}, customer={customer_name}")
        
        def run_transcription():
            try:
                logger.info(f"🎙️ TRANSCRIPTION THREAD STARTED: upload_id={upload_id}, call_record_id={call_record_id}, provider={transcription_provider}")
                print(f"🎙️ TRANSCRIPTION THREAD STARTED: upload_id={upload_id}, call_record_id={call_record_id}, provider={transcription_provider}")
                print(f"🎙️ Thread details: storage_path={storage_path}, public_url_length={len(public_url) if public_url else 0}, file_ext={file_ext}")
                print(f"🎙️ DEBUG: About to call _process_transcription_background with call_record_id={call_record_id}, type={type(call_record_id)}")
                import sys
                sys.stdout.flush()
                
                # Pass call_record_id to transcription function so it can update the correct record
                # We need to modify _process_transcription_background to accept call_record_id
                # For now, let's create a transcription_queue entry with call_record_id
                try:
                    supabase.from_("transcription_queue").upsert({
                        "id": upload_id,
                        "call_record_id": call_record_id,
                        "status": "pending",
                        "progress": 0
                    }).execute()
                    print(f"✅ Created/updated transcription_queue entry with call_record_id={call_record_id}")
                except Exception as queue_error:
                    print(f"⚠️ Could not create transcription_queue entry (may not exist): {queue_error}")
                    # Try with call_id instead
                    try:
                        supabase.from_("transcription_queue").upsert({
                            "id": upload_id,
                            "call_id": call_record_id,
                            "status": "pending",
                            "progress": 0
                        }).execute()
                        print(f"✅ Created/updated transcription_queue entry with call_id={call_record_id}")
                    except Exception:
                        pass
                
                _process_transcription_background(
                    upload_id,
                    storage_path,
                    public_url,
                    transcription_provider,
                    file_ext,
                    "Salesperson",  # Default salesperson name
                    customer_name,
                    None,  # language
                    True,  # enable_diarization
                    call_record_id,  # Pass call_record_id directly
                    file_id  # Pass file_id for status updates
                )
                logger.info(f"✅ TRANSCRIPTION THREAD COMPLETED: upload_id={upload_id}, call_record_id={call_record_id}")
                print(f"✅ TRANSCRIPTION THREAD COMPLETED: upload_id={upload_id}, call_record_id={call_record_id}")
            except Exception as e:
                logger.error(f"❌ TRANSCRIPTION THREAD ERROR: upload_id={upload_id}, call_record_id={call_record_id}, error={e}", exc_info=True)
                print(f"❌ TRANSCRIPTION THREAD ERROR: upload_id={upload_id}, call_record_id={call_record_id}, error={e}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
                # Update call record with error
                try:
                    supabase.table("call_records").update({
                        "transcript": f"Transcription error: {str(e)[:200]}"
                    }).eq("id", call_record_id).execute()
                    logger.info(f"⚠️ Updated call_record with error message")
                    print(f"⚠️ Updated call_record with error message")
                except Exception as update_error:
                    logger.error(f"❌ Failed to update call_record with error: {update_error}")
                    print(f"❌ Failed to update call_record with error: {update_error}")
        
        transcription_thread = threading.Thread(target=run_transcription, daemon=True)
        transcription_thread.start()
        
        # Verify thread started
        import time
        time.sleep(0.5)  # Brief pause to let thread start
        if transcription_thread.is_alive():
            logger.info(f"✅ RETRANSCRIBE SUCCESS: call_record_id={call_record_id}, upload_id={upload_id}, provider={transcription_provider}, thread_started=True, thread_alive=True")
            print(f"✅ RETRANSCRIBE SUCCESS: call_record_id={call_record_id}, upload_id={upload_id}, provider={transcription_provider}, thread_started=True, thread_alive=True")
        else:
            logger.error(f"❌ RETRANSCRIBE FAILED: Thread died immediately after starting for call_record {call_record_id}")
            print(f"❌ RETRANSCRIBE FAILED: Thread died immediately after starting for call_record {call_record_id}")
        
        return {
            "success": True,
            "message": "Transcription restarted successfully",
            "call_record_id": call_record_id,
            "provider": transcription_provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retranscribing call {call_record_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retranscribe: {str(e)}"
        )


@router.get("/jobs", response_model=List[BulkImportStatusResponse])
async def list_import_jobs(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """List all bulk import jobs for the current user"""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )

    try:
        # Check if table exists first (migration might not have been run)
        try:
            result = (
                supabase.table("bulk_import_jobs")
                .select("*")
                .eq("user_id", current_user["id"])
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as table_error:
            # If table doesn't exist, return empty list instead of error
            if "relation" in str(table_error).lower() or "does not exist" in str(table_error).lower():
                logger.warning(f"bulk_import_jobs table does not exist yet. Run migration 002_bulk_import_schema.sql")
                return []
            raise

        jobs = []
        for job in (result.data or []):
            total = job.get("total_files", 0)
            processed = job.get("processed_files", 0)
            progress = (processed / total * 100) if total > 0 else 0.0

            # Handle datetime parsing more safely
            try:
                created_at = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
            except Exception:
                created_at = datetime.fromisoformat(job["created_at"])
            
            try:
                updated_at = datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
            except Exception:
                updated_at = datetime.fromisoformat(job["updated_at"])
            
            completed_at = None
            if job.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00"))
                except Exception:
                    completed_at = datetime.fromisoformat(job["completed_at"])

            jobs.append(BulkImportStatusResponse(
                job_id=job["id"],
                status=job["status"],
                customer_name=job["customer_name"],
                total_files=total,
                processed_files=processed,
                failed_files=job.get("failed_files", 0),
                progress_percentage=round(progress, 2),
                error_message=job.get("error_message"),
                created_at=created_at,
                updated_at=updated_at,
                completed_at=completed_at,
            ))

        return jobs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing import jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list import jobs: {str(e)}"
        )


# Background processing function (to be implemented)
async def process_bulk_import(
    job_id: str,
    customer_name: str,
    source_url: str,
    bucket_name: str,
    user_id: str,
    provider: str = "openai",
    call_log_file_url: Optional[str] = None
):
    """Background task to process bulk import job"""
    from services.bulk_import_service import BulkImportService
    
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not available for bulk import processing")
        return
    
    service = BulkImportService(supabase)
    await service.process_import_job(
        job_id=job_id,
        customer_name=customer_name,
        source_url=source_url,
        bucket_name=bucket_name,
        user_id=user_id,
        provider=provider,
        call_log_file_url=call_log_file_url
    )

