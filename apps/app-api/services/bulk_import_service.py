"""
Bulk Import Service - Handles the actual processing of bulk audio imports
"""
import logging
import os
import re
import asyncio
import aiohttp
import aiofiles
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from pathlib import Path
import tempfile
import shutil
from supabase import Client
import json

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.webm', '.ogg']
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB


class BulkImportService:
    """Service to handle bulk audio file imports and processing"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.session: Optional[aiohttp.ClientSession] = None

    async def process_import_job(
        self,
        job_id: str,
        customer_name: str,
        source_url: str,
        bucket_name: str,
        user_id: str,
        provider: str = "openai",
        call_log_file_url: Optional[str] = None
    ):
        """Main processing function for a bulk import job"""
        try:
            # Update job status to discovering
            await self._update_job_status(job_id, "discovering", error_message=None)

            # Step 0: Check for call log file mapping (if provided)
            call_log_mapping_skipped = False
            if not call_log_file_url:
                call_log_mapping_skipped = True
                logger.info(f"Call log file URL not provided for job {job_id}. Skipping call log mapping step.")
                # Store skip status in job metadata - append to existing error_message if it exists
                # This preserves any existing messages while adding the skip notice
                existing_result = self.supabase.table("bulk_import_jobs").select("error_message").eq("id", job_id).maybe_single().execute()
                existing_msg = existing_result.data.get("error_message") if existing_result.data else None
                skip_msg = "Call log file mapping skipped: No call log file provided"
                new_msg = f"{skip_msg}. {existing_msg}" if existing_msg and existing_msg != skip_msg else skip_msg
                self.supabase.table("bulk_import_jobs").update({
                    "error_message": new_msg
                }).eq("id", job_id).execute()
            else:
                logger.info(f"Call log file URL provided: {call_log_file_url}. Will attempt mapping.")
                # TODO: Implement call log file mapping logic here
                # For now, we'll skip the actual mapping but mark it as attempted

            # Step 1: Discover audio files from source URL
            logger.info(f"Discovering audio files from {source_url}")
            try:
                audio_files = await self._discover_audio_files(source_url)
                logger.info(f"Discovery completed. Found {len(audio_files)} audio files")
            except Exception as discover_error:
                logger.error(f"Error discovering audio files: {discover_error}", exc_info=True)
                # Update job to show discovery failed
                self.supabase.table("bulk_import_jobs").update({
                    "status": "failed",
                    "error_message": f"Failed to discover audio files: {str(discover_error)}",
                    "total_files": 0
                }).eq("id", job_id).execute()
                raise
            
            # Update job with total files count immediately after discovery
            logger.info(f"Updating job {job_id} with total_files={len(audio_files)}")
            try:
                update_result = self.supabase.table("bulk_import_jobs").update({
                    "total_files": len(audio_files),
                    "status": "converting" if len(audio_files) > 0 else "completed"
                }).eq("id", job_id).execute()
                
                if update_result.data:
                    logger.info(f"Successfully updated job {job_id}: total_files={len(audio_files)}, status=converting")
                else:
                    logger.warning(f"Update returned no data for job {job_id}. Checking if update succeeded...")
                    # Verify the update by reading back
                    check_result = self.supabase.table("bulk_import_jobs").select("total_files, status").eq("id", job_id).execute()
                    if check_result.data:
                        logger.info(f"Job {job_id} current state: total_files={check_result.data[0].get('total_files')}, status={check_result.data[0].get('status')}")
            except Exception as update_error:
                logger.error(f"Error updating total_files for job {job_id}: {update_error}", exc_info=True)
            
            if not audio_files:
                logger.warning(f"No audio files found at source URL: {source_url}")
                await self._update_job_status(
                    job_id,
                    "completed",
                    completed_at=True,
                    error_message="No audio files found at source URL"
                )
                return
            
            # Build discovery details before deduplication
            try:
                discovered_entries = []
                found_file_names = set()
                for fi in audio_files:
                    name = fi.get("name", "unknown")
                    discovered_entries.append({
                        "name": name,
                        "url": fi.get("url"),
                        "file_id": fi.get("file_id"),
                    })
                    found_file_names.add(name.lower())
                
                # Log which file names we found
                logger.info(f"Discovered file names: {sorted(found_file_names)}")
                
                # Detect duplicates by URL in the discovered list
                url_counts: Dict[str, int] = {}
                for fi in audio_files:
                    u = fi.get("url", "")
                    if not u:
                        continue
                    url_counts[u] = url_counts.get(u, 0) + 1
                duplicates = [ {"url": u, "count": c} for u, c in url_counts.items() if c > 1 ]
                discovery_payload = {
                    "discovered": len(audio_files),
                    "duplicates_by_url": duplicates,
                    "entries": discovered_entries,
                    "found_file_names": sorted(found_file_names),  # Add for debugging
                }
                # Persist into error_message with a recognizable prefix. Preserve any existing error_message by appending.
                job_read = self.supabase.table("bulk_import_jobs").select("error_message").eq("id", job_id).maybe_single().execute()
                prev = (job_read.data or {}).get("error_message") if job_read and hasattr(job_read, 'data') else None
                merged = f"DISCOVERY_JSON::{json.dumps(discovery_payload)}"
                if prev and isinstance(prev, str) and "DISCOVERY_JSON::" not in prev:
                    merged = f"{prev}\n{merged}"
                self.supabase.table("bulk_import_jobs").update({
                    "error_message": merged
                }).eq("id", job_id).execute()
            except Exception as _capture_err:
                logger.debug(f"Could not persist discovery details: {_capture_err}")
            
            # Create file records for all discovered files immediately (before processing)
            # Deduplicate by URL to avoid creating duplicate records
            seen_urls = set()
            unique_files = []
            for file_info in audio_files:
                file_url = file_info.get("url", "")
                if file_url and file_url not in seen_urls:
                    seen_urls.add(file_url)
                    unique_files.append(file_info)
                elif not file_url:
                    # Include files without URL (shouldn't happen, but be safe)
                    unique_files.append(file_info)
            
            if len(unique_files) < len(audio_files):
                logger.info(f"Deduplicated files: {len(audio_files)} -> {len(unique_files)} unique files")
            
            logger.info(f"Creating file records for {len(unique_files)} unique discovered files")
            for file_info in unique_files:
                try:
                    # Check if record already exists (in case of retries)
                    file_url = file_info.get("url", "")
                    existing_result = self.supabase.table("bulk_import_files").select("id").eq(
                        "job_id", job_id
                    ).eq("original_url", file_url).maybe_single().execute()
                    
                    # Handle None response or missing data attribute
                    if not existing_result or not hasattr(existing_result, 'data') or not existing_result.data:
                        await self._create_file_record(
                            job_id=job_id,
                            file_name=file_info.get("name", "unknown"),
                            original_url=file_url,
                            status="pending",
                            error_message=None
                        )
                    else:
                        logger.debug(f"File record already exists for {file_info.get('name')}, skipping creation")
                except Exception as file_record_error:
                    logger.warning(f"Failed to create file record for {file_info.get('name')}: {file_record_error}")
            
            # Use deduplicated list for processing
            audio_files = unique_files

            # Step 2: Process each file
            processed = 0
            failed = 0

            for file_info in audio_files:
                try:
                    await self._process_file(
                        job_id=job_id,
                        file_info=file_info,
                        bucket_name=bucket_name,
                        user_id=user_id,
                        customer_name=customer_name,
                        provider=provider
                    )
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_info.get('url')}: {e}", exc_info=True)
                    failed += 1
                    # Update existing file record with error status
                    try:
                        file_url = file_info.get("url", "")
                        result = self.supabase.table("bulk_import_files").select("id").eq(
                            "job_id", job_id
                        ).eq("original_url", file_url).maybe_single().execute()
                        
                        # Handle None response or missing data attribute
                        if result and hasattr(result, 'data') and result.data:
                            file_id = result.data["id"]
                            await self._update_file_record(file_id, {
                                "status": "failed",
                                "error_message": str(e)[:500]  # Limit error message length
                            })
                        else:
                            # No existing record, create one with error
                            await self._create_file_record(
                                job_id=job_id,
                                file_name=file_info.get("name", "unknown"),
                                original_url=file_url,
                                status="failed",
                                error_message=str(e)[:500]
                            )
                    except Exception as update_error:
                        logger.warning(f"Failed to update file record status: {update_error}")
                        # Fallback: create new record if update fails
                        try:
                            await self._create_file_record(
                                job_id=job_id,
                                file_name=file_info.get("name", "unknown"),
                                original_url=file_info.get("url", ""),
                                status="failed",
                                error_message=str(e)[:500]
                            )
                        except Exception:
                            pass  # Give up if we can't create or update

                # Update job progress after each file
                update_result = self.supabase.table("bulk_import_jobs").update({
                    "processed_files": processed,
                    "failed_files": failed,
                    "status": "analyzing" if processed > 0 else ("uploading" if processed + failed < len(audio_files) else "completed")
                }).eq("id", job_id).execute()
                
                if update_result.data:
                    logger.debug(f"Updated progress for job {job_id}: processed={processed}, failed={failed}")

            # Mark job as completed
            await self._update_job_status(
                job_id,
                "completed",
                completed_at=True,
                error_message=None
            )

            logger.info(f"Bulk import job {job_id} completed: {processed} processed, {failed} failed")

        except Exception as e:
            logger.error(f"Error in bulk import job {job_id}: {e}", exc_info=True)
            await self._update_job_status(job_id, "failed", error_message=str(e))
            raise
        finally:
            # Clean up HTTP session
            if self.session:
                try:
                    await self.session.close()
                    self.session = None
                    logger.debug("Closed aiohttp session")
                except Exception as cleanup_error:
                    logger.warning(f"Error closing session: {cleanup_error}")

    async def _discover_audio_files(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Discover audio files from a web URL.
        Supports:
        - Direct file links
        - Directory listings (HTML)
        - Google Drive folders (shared publicly)
        - S3/GCS public buckets
        - Simple web servers
        """
        audio_files = []

        try:
            # Check if it's a Google Drive URL
            if "drive.google.com" in source_url.lower():
                logger.info(f"Detected Google Drive URL: {source_url}")
                audio_files = await self._discover_google_drive_files(source_url)
                return audio_files

            # Create HTTP session if needed
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "Mozilla/5.0 (compatible; BulkImport/1.0)"}
                )

            async with self.session.get(source_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to access source URL: {response.status}")

                content_type = response.headers.get("Content-Type", "").lower()
                
                # If it's a direct audio file
                if any(ext in content_type for ext in ["audio", "video"]):
                    file_name = os.path.basename(urlparse(source_url).path) or "audio_file"
                    file_ext = os.path.splitext(file_name)[1].lower()
                    if file_ext in SUPPORTED_FORMATS:
                        audio_files.append({
                            "url": source_url,
                            "name": file_name
                        })
                    return audio_files

                # If it's HTML, try to parse for links
                if "text/html" in content_type:
                    html_content = await response.text()
                    # Simple regex to find audio file links
                    # Look for common patterns: <a href="...">, direct links, etc.
                    audio_urls = self._extract_audio_links_from_html(html_content, source_url)
                    audio_files.extend(audio_urls)

                # If it's JSON (API response), try to parse
                elif "application/json" in content_type:
                    json_data = await response.json()
                    audio_files.extend(self._extract_audio_links_from_json(json_data, source_url))

        except Exception as e:
            logger.error(f"Error discovering audio files: {e}", exc_info=True)
            raise

        return audio_files

    async def _discover_google_drive_files(self, drive_url: str) -> List[Dict[str, Any]]:
        """
        Discover audio files from a Google Drive folder.
        Handles both folder sharing URLs and direct file links.
        """
        audio_files = []
        
        try:
            # Extract folder ID or file ID from URL
            # Format: https://drive.google.com/drive/folders/FOLDER_ID
            # Format: https://drive.google.com/drive/u/9/folders/FOLDER_ID (with user path)
            # Format: https://drive.google.com/file/d/FILE_ID/view
            folder_id_match = re.search(r'/folders/([a-zA-Z0-9_-]+)', drive_url)
            file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
            
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=60),
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                )
            
            if folder_id_match:
                # It's a folder - extract file IDs from the page
                folder_id = folder_id_match.group(1)
                logger.info(f"Extracting files from Google Drive folder: {folder_id}")
                
                # Fetch the folder page
                folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
                async with self.session.get(folder_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to access Google Drive folder: {response.status}")
                    
                    html_content = await response.text()
                    
                    # Google Drive embeds file metadata in JavaScript variables and JSON data
                    # The folder page contains file data in various JavaScript structures
                    # We need to extract file IDs from these structures
                    
                    found_ids = set()
                    
                    # First, try to extract from JavaScript data structures directly
                    # Google Drive often embeds data in window['_DRIVE_ivd'] or similar
                    # Look for patterns like: var _DRIVE_ivd = '...'; or window['_DRIVE_ivd'] = {...}
                    js_data_patterns = [
                        r'window\[["\']_DRIVE_ivd["\']\]\s*=\s*({[^}]+})',
                        r'var\s+_DRIVE_ivd\s*=\s*({[^}]+})',
                        r'\["([a-zA-Z0-9_-]{33})"\]',  # Direct array of file IDs
                        r'"([a-zA-Z0-9_-]{33})"',  # Quoted file IDs in JSON
                    ]
                    
                    for pattern in js_data_patterns:
                        matches = re.finditer(pattern, html_content)
                        for match in matches:
                            if len(match.groups()) > 0:
                                potential_id = match.group(1)
                                if len(potential_id) == 33 and potential_id != folder_id:
                                    # Additional validation
                                    if not any(skip in potential_id.lower() for skip in ['aiza', 'http', 'google']):
                                        found_ids.add(potential_id)
                    
                    # Also look for JSON-LD structured data
                    json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
                    json_ld_matches = re.finditer(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
                    for match in json_ld_matches:
                        try:
                            import json
                            json_data = json.loads(match.group(1))
                            # Recursively search for file IDs in JSON
                            def find_ids_in_json(obj):
                                if isinstance(obj, dict):
                                    for v in obj.values():
                                        find_ids_in_json(v)
                                elif isinstance(obj, list):
                                    for item in obj:
                                        find_ids_in_json(item)
                                elif isinstance(obj, str) and len(obj) == 33:
                                    if obj != folder_id and not any(skip in obj.lower() for skip in ['aiza', 'http']):
                                        found_ids.add(obj)
                            find_ids_in_json(json_data)
                        except:
                            pass
                    
                    # Use BeautifulSoup for more reliable HTML parsing
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Method 1: Look for actual file links in the HTML (most reliable)
                        # Google Drive uses specific patterns for file links
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            # Only match actual /file/d/ links (not folders)
                            # Google Drive file IDs are EXACTLY 33 characters
                            file_match = re.search(r'/file/d/([a-zA-Z0-9_-]{33})', href)
                            if file_match:
                                file_id = file_match.group(1)
                                if len(file_id) == 33 and file_id != folder_id:
                                    found_ids.add(file_id)
                        
                        # Method 2: Look for data attributes that specifically indicate files
                        # Google Drive uses data-id for file items, but be careful - not all data-id are files
                        for element in soup.find_all(attrs={'data-id': True}):
                            file_id = element.get('data-id', '')
                            # Google Drive file IDs are EXACTLY 33 characters
                            # Only include if it's exactly 33 characters and in a file-related context
                            if len(file_id) == 33 and file_id != folder_id:
                                parent_classes = ' '.join(element.get('class', []))
                                # Check if the element is in a file list context
                                if 'file' in parent_classes.lower() or element.name in ['div', 'tr']:
                                    found_ids.add(file_id)
                        
                        # Method 3: Look in script tags for file data arrays (more specific patterns)
                        # Google Drive embeds file lists in JavaScript - this is critical for finding files
                        for script in soup.find_all('script'):
                            script_text = script.string
                            if script_text:
                                # Look specifically for /file/d/ patterns in scripts (most reliable)
                                # Google Drive file IDs are EXACTLY 33 characters
                                script_file_matches = re.finditer(r'/file/d/([a-zA-Z0-9_-]{33})', script_text)
                                for match in script_file_matches:
                                    file_id = match.group(1)
                                    if len(file_id) == 33 and file_id != folder_id:
                                        found_ids.add(file_id)
                                
                                # Look for file arrays - Google Drive often stores file IDs in arrays
                                # Pattern: ["33charid1", "33charid2"] or ['33charid1', '33charid2']
                                array_patterns = [
                                    r'\["([a-zA-Z0-9_-]{33})"',
                                    r"\['([a-zA-Z0-9_-]{33})'",
                                    r'\["([a-zA-Z0-9_-]{33})"',
                                ]
                                for array_pattern in array_patterns:
                                    array_matches = re.finditer(array_pattern, script_text)
                                    for match in array_matches:
                                        file_id = match.group(1)
                                        # Only add if it's exactly 33 characters (Google Drive file ID length)
                                        if len(file_id) == 33 and file_id != folder_id:
                                            # Additional check: should not contain common non-ID patterns
                                            if not any(skip in file_id.lower() for skip in ['http', 'https', 'www', 'google', 'drive', 'aiza']):
                                                found_ids.add(file_id)
                                
                                # Look for Google Drive's specific data structures
                                # Pattern: "id":"33charid" or 'id':'33charid'
                                id_patterns = [
                                    r'["\']id["\']\s*:\s*["\']([a-zA-Z0-9_-]{33})["\']',
                                    r'["\']fileId["\']\s*:\s*["\']([a-zA-Z0-9_-]{33})["\']',
                                    r'["\']file_id["\']\s*:\s*["\']([a-zA-Z0-9_-]{33})["\']',
                                ]
                                for id_pattern in id_patterns:
                                    id_matches = re.finditer(id_pattern, script_text)
                                    for match in id_matches:
                                        file_id = match.group(1)
                                        if len(file_id) == 33 and file_id != folder_id:
                                            if not any(skip in file_id.lower() for skip in ['aiza', 'http']):
                                                found_ids.add(file_id)
                        
                        logger.info(f"Found {len(found_ids)} potential file IDs using BeautifulSoup parsing")
                        
                        # Also look for download links - these are more reliable
                        # Google Drive download links contain file IDs
                        for link in soup.find_all('a', href=True, string=re.compile('Download', re.I)):
                            href = link.get('href', '')
                            # Download links might be relative or absolute
                            # Pattern: /file/d/FILE_ID/view or /file/d/FILE_ID/download
                            download_match = re.search(r'/file/d/([a-zA-Z0-9_-]{33})', href)
                            if download_match:
                                file_id = download_match.group(1)
                                if len(file_id) == 33 and file_id != folder_id:
                                    found_ids.add(file_id)
                                    logger.debug(f"Found file ID from download link: {file_id}")
                        
                    except ImportError:
                        logger.warning("BeautifulSoup not available, using basic regex parsing")
                        # Fallback to basic regex
                        # Google Drive file IDs are EXACTLY 33 characters
                        file_link_pattern = r'href=["\'](/file/d/([a-zA-Z0-9_-]{33}))["\']'
                        link_matches = re.finditer(file_link_pattern, html_content, re.IGNORECASE)
                        for match in link_matches:
                            file_id = match.group(2)
                            if len(file_id) == 33 and file_id != folder_id:
                                found_ids.add(file_id)
                    
                    logger.info(f"Total file IDs found after all parsing methods: {len(found_ids)}")
                    logger.info(f"Sample file IDs found: {list(found_ids)[:5]}")
                    
                    # ADDITIONAL: Extract ALL 33-character alphanumeric strings that could be file IDs
                    # This is a catch-all to find any IDs we might have missed
                    all_33char_pattern = r'\b([a-zA-Z0-9_-]{33})\b'
                    all_33char_matches = re.finditer(all_33char_pattern, html_content)
                    for match in all_33char_matches:
                        potential_id = match.group(1)
                        if potential_id != folder_id:
                            # Only add if it looks like a valid Google Drive ID (alphanumeric + dash/underscore)
                            if re.match(r'^[a-zA-Z0-9_-]{33}$', potential_id):
                                found_ids.add(potential_id)
                    
                    logger.info(f"After catch-all extraction: {len(found_ids)} total file IDs found")
                    
                    # ADDITIONAL METHOD: Look for file names in HTML and try to find nearby file IDs
                    # Google Drive often shows file names with their IDs nearby
                    # Look for patterns like "conversation (5).wav" and find the closest file_id
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Find all text that looks like file names (ending in .wav, .mp3, etc.)
                        file_name_pattern = r'conversation\s*\(\d+\)\.wav'
                        name_matches = re.finditer(file_name_pattern, html_content, re.IGNORECASE)
                        
                        for name_match in name_matches:
                            name_text = name_match.group(0)
                            match_start = name_match.start()
                            # Look for file IDs within 500 characters before or after the name
                            context_start = max(0, match_start - 500)
                            context_end = min(len(html_content), match_start + len(name_text) + 500)
                            context = html_content[context_start:context_end]
                            
                            # Find all 33-char IDs in this context
                            context_ids = re.findall(r'\b([a-zA-Z0-9_-]{33})\b', context)
                            for potential_id in context_ids:
                                if potential_id != folder_id and re.match(r'^[a-zA-Z0-9_-]{33}$', potential_id):
                                    if not any(skip in potential_id.lower() for skip in ['http', 'https', 'www', 'google', 'drive', 'aiza']):
                                        found_ids.add(potential_id)
                                        logger.debug(f"Found file_id {potential_id} near filename {name_text}")
                    except Exception as name_extract_error:
                        logger.debug(f"Error extracting IDs from file names: {name_extract_error}")
                    
                    logger.info(f"After name-based extraction: {len(found_ids)} total file IDs found")
                    
                    # Filter out obviously invalid IDs
                    # Google Drive file IDs are EXACTLY 33 characters (very specific pattern)
                    filtered_ids = set()
                    skipped_ids = []
                    for file_id in found_ids:
                        # Skip if it contains obvious non-ID patterns
                        skip_patterns = ['http', 'https', 'www', 'google', 'drive', 'com', 'gstatic', 'apis', 'youtube', 'gmail', 
                                       'anonymous', 'viewer', 'remove', 'scrim', 'exit', 'off', 'on', 'ai', 'az', 'recaptcha',
                                       'aiza', 'googleapis']
                        if any(pattern in file_id.lower() for pattern in skip_patterns):
                            skipped_ids.append(f"{file_id} (contains skip pattern)")
                            continue
                        # Google Drive file IDs are EXACTLY 33 characters (this is the key!)
                        if len(file_id) != 33:
                            continue
                        # Skip if it contains spaces or special chars that aren't in Google IDs
                        if re.search(r'[^a-zA-Z0-9_-]', file_id):
                            continue
                        # Skip if it looks like an API key (starts with AIza, contains Sy, etc.)
                        if file_id.startswith('AIza') or 'AIza' in file_id:
                            continue
                        # Skip if it contains common non-ID patterns
                        if re.search(r'[A-Z]{2,}', file_id):  # Too many consecutive uppercase (unlikely for file IDs)
                            # Actually, file IDs can have uppercase, so be careful here
                            # But if it's all uppercase or has patterns like "AIzaSy", skip it
                            if 'AIza' in file_id or file_id.isupper():
                                continue
                        filtered_ids.add(file_id)
                    
                    logger.info(f"Filtered to {len(filtered_ids)} file IDs after removing invalid patterns (from {len(found_ids)} candidates)")
                    if skipped_ids:
                        logger.debug(f"Skipped {len(skipped_ids)} IDs: {skipped_ids[:5]}")
                    
                    # Additional filtering: Only keep IDs that appear in file-related contexts
                    # This helps eliminate false positives from random long strings
                    # NOTE: For Google Drive, the /file/d/{file_id} pattern is the most reliable indicator
                    # We'll be less strict with context filtering to avoid false negatives
                    context_filtered = set()
                    for file_id in filtered_ids:
                        # Check if it's in a /file/d/ URL pattern (most reliable for Google Drive)
                        if f'/file/d/{file_id}' in html_content:
                            context_filtered.add(file_id)
                            logger.debug(f"Found file_id {file_id} in /file/d/ URL pattern")
                            continue
                        
                        # Also check if the ID appears near file-related keywords (less strict)
                        # This is a heuristic to reduce false positives, but we'll be more lenient
                        file_id_pattern = re.escape(file_id)
                        # Look for the ID near file-related terms (with more flexible matching)
                        context_patterns = [
                            rf'{file_id_pattern}.*?file',
                            rf'file.*?{file_id_pattern}',
                            rf'{file_id_pattern}.*?drive',
                            rf'drive.*?{file_id_pattern}',
                            rf'["\']{file_id_pattern}["\']',  # ID in quotes (common in JSON/JS data)
                            rf'id["\']?\s*:\s*["\']?{file_id_pattern}',  # ID in id: "..." pattern
                        ]
                        
                        matches_context = False
                        for pattern in context_patterns:
                            if re.search(pattern, html_content, re.IGNORECASE):
                                matches_context = True
                                logger.debug(f"Found file_id {file_id} in context pattern: {pattern}")
                                break
                        
                        if matches_context:
                            context_filtered.add(file_id)
                        else:
                            # ALWAYS include file IDs that passed the initial filter, even without context match
                            # This prevents false negatives - if it's a valid 33-char ID, it's likely a real file
                            logger.debug(f"File_id {file_id} not found in strict context, but including anyway (to avoid false negatives)")
                            context_filtered.add(file_id)
                    
                    logger.info(f"Context-filtered to {len(context_filtered)} file IDs (from {len(filtered_ids)} candidates)")
                    filtered_ids = context_filtered
                    
                    # Validate file IDs by checking if they're actually accessible
                    validated_ids = []
                    logger.info(f"Validating {len(filtered_ids)} file IDs...")
                    
                    # Limit validation to avoid too many requests
                    validation_limit = 20  # Only validate first 20 to avoid timeouts
                    ids_to_validate = list(filtered_ids)[:validation_limit]
                    
                    for file_id in ids_to_validate:
                        try:
                            # Try to access the file info page with a HEAD request
                            test_url = f"https://drive.google.com/file/d/{file_id}/view"
                            async with self.session.head(test_url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=3)) as test_response:
                                # If we get a 200 or redirect, it's likely a valid file
                                if test_response.status in [200, 301, 302, 303, 307, 308]:
                                    validated_ids.append(file_id)
                                    logger.debug(f"Validated file_id {file_id}: status {test_response.status}")
                                else:
                                    logger.debug(f"Skipping file_id {file_id}: status {test_response.status}")
                        except Exception as validation_error:
                            logger.debug(f"Could not validate file_id {file_id}: {validation_error}")
                            # If validation fails, we'll still try to process it - might be a valid file
                            # but validation failed due to network/permissions
                            validated_ids.append(file_id)
                    
                    # For IDs beyond validation limit, include them if they passed the filter
                    if len(filtered_ids) > validation_limit:
                        remaining_ids = list(filtered_ids)[validation_limit:]
                        logger.info(f"Including {len(remaining_ids)} additional file IDs without validation (validation limit reached)")
                        validated_ids.extend(remaining_ids)
                    
                    logger.info(f"Final validated file IDs: {len(validated_ids)}")
                    found_ids = set(validated_ids)
                    
                    # For each file ID, try to get file info and create download link
                    for file_id in found_ids:
                        # Skip the folder ID itself
                        if file_id == folder_id:
                            continue
                        
                        # Try to get file metadata
                        try:
                            # Create direct download URL
                            # Format: https://drive.google.com/uc?export=download&id=FILE_ID
                            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                            
                            # Try to get file name by fetching file info
                            # Google Drive file info endpoint
                            file_info_url = f"https://drive.google.com/file/d/{file_id}/view"
                            
                            file_name = f"file_{file_id}.wav"  # Default name
                            
                            try:
                                async with self.session.get(file_info_url, allow_redirects=False) as info_response:
                                    # Try to extract filename from headers
                                    content_disposition = info_response.headers.get('Content-Disposition', '')
                                    if content_disposition:
                                        filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^\s;]+)', content_disposition)
                                        if filename_match:
                                            file_name = filename_match.group(1).strip('\'"')
                                    
                                    # If not in headers, try to get from HTML title
                                    if file_name == f"file_{file_id}.wav":
                                        html = await info_response.text()
                                        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                                        if title_match:
                                            title = title_match.group(1).strip()
                                            # Remove "Google Drive" suffix if present
                                            title = re.sub(r'\s*-\s*Google\s+Drive\s*$', '', title, flags=re.IGNORECASE)
                                            if title:
                                                file_name = title
                            except Exception as name_error:
                                logger.warning(f"Could not get filename for {file_id}: {name_error}, using default")
                            
                            # Check if file extension is supported (we'll verify on download)
                            # For now, add all files and filter later
                            audio_files.append({
                                "url": download_url,
                                "name": file_name,
                                "file_id": file_id
                            })
                            
                        except Exception as file_error:
                            logger.warning(f"Error processing Google Drive file {file_id}: {file_error}")
                            continue
                    
                    # If we still didn't find files, try a more direct approach
                    if not audio_files and found_ids:
                        logger.warning(f"Found {len(found_ids)} file IDs but couldn't process them. This might indicate a parsing issue.")
            
            elif file_id_match:
                # It's a direct file link
                file_id = file_id_match.group(1)
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                file_name = f"google_drive_file_{file_id}.wav"  # Default name
                
                audio_files.append({
                    "url": download_url,
                    "name": file_name,
                    "file_id": file_id
                })
            else:
                raise Exception("Could not extract folder or file ID from Google Drive URL")
            
            # Filter to only audio files based on URL patterns or file extensions
            # We'll do a more thorough check when downloading
            filtered_files = []
            for file_info in audio_files:
                url = file_info.get("url", "")
                name = file_info.get("name", "")
                
                # Check if it looks like an audio file
                if any(ext in name.lower() for ext in ['.wav', '.mp3', '.m4a', '.webm', '.ogg']):
                    filtered_files.append(file_info)
                # Also check if URL suggests it's an audio file
                elif any(ext in url.lower() for ext in ['.wav', '.mp3', '.m4a', '.webm', '.ogg']):
                    filtered_files.append(file_info)
                # For Google Drive, we might not know the extension, so include it and check on download
                elif "drive.google.com" in url:
                    filtered_files.append(file_info)
            
            logger.info(f"Found {len(filtered_files)} audio files from Google Drive")
            
            if not filtered_files:
                # Provide helpful error message
                error_msg = (
                    "No audio files found in Google Drive folder. "
                    "Please ensure:\n"
                    "1. The folder is shared with 'Anyone with the link'\n"
                    "2. The folder contains audio files (WAV, MP3, M4A, WebM, OGG)\n"
                    "3. You're using the folder sharing URL (not the internal Drive URL)\n"
                    "Alternative: Share individual file links directly"
                )
                logger.warning(error_msg)
                raise Exception(error_msg)
            
            return filtered_files
            
        except Exception as e:
            logger.error(f"Error discovering Google Drive files: {e}", exc_info=True)
            # Provide more helpful error message
            if "No audio files found" not in str(e):
                error_msg = f"Failed to access Google Drive folder: {str(e)}. Please ensure the folder is shared publicly with 'Anyone with the link'."
                raise Exception(error_msg)
            raise

    def _extract_audio_links_from_html(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract audio file links from HTML content"""
        audio_files = []
        
        # Find all <a> tags with href attributes
        href_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
        matches = re.finditer(href_pattern, html, re.IGNORECASE)
        
        for match in matches:
            href = match.group(1)
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            # Check if it's an audio file
            file_ext = os.path.splitext(urlparse(full_url).path)[1].lower()
            if file_ext in SUPPORTED_FORMATS:
                file_name = os.path.basename(urlparse(full_url).path)
                audio_files.append({
                    "url": full_url,
                    "name": file_name
                })

        return audio_files

    def _extract_audio_links_from_json(self, json_data: Any, base_url: str) -> List[Dict[str, Any]]:
        """Extract audio file links from JSON response"""
        audio_files = []
        
        def find_urls(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    find_urls(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_urls(item, f"{path}[{i}]")
            elif isinstance(obj, str) and obj.startswith(("http://", "https://")):
                file_ext = os.path.splitext(urlparse(obj).path)[1].lower()
                if file_ext in SUPPORTED_FORMATS:
                    file_name = os.path.basename(urlparse(obj).path)
                    audio_files.append({
                        "url": obj,
                        "name": file_name
                    })

        find_urls(json_data)
        return audio_files

    async def _process_file(
        self,
        job_id: str,
        file_info: Dict[str, Any],
        bucket_name: str,
        user_id: str,
        customer_name: str,
        provider: str
    ):
        """Process a single audio file"""
        file_url = file_info["url"]
        file_name = file_info["name"]

        try:
            # Find existing file record (created during discovery) or create new one
            # We create file records upfront during discovery, so we should update that record
            existing_record = None
            try:
                result = self.supabase.table("bulk_import_files").select("*").eq(
                    "job_id", job_id
                ).eq("original_url", file_url).maybe_single().execute()
                
                # Handle None response or missing data attribute
                if result and hasattr(result, 'data') and result.data:
                    existing_record = result.data
                    file_id = existing_record["id"]
                    # Update status to downloading
                    await self._update_file_record(file_id, {"status": "downloading"})
                    logger.debug(f"Found existing file record {file_id} for {file_name}, updating status")
                else:
                    # No existing record, create new one
                    file_record = await self._create_file_record(
                        job_id=job_id,
                        file_name=file_name,
                        original_url=file_url,
                        status="downloading"
                    )
                    file_id = file_record["id"]
                    logger.debug(f"Created new file record {file_id} for {file_name}")
            except Exception as record_error:
                logger.warning(f"Error finding/updating file record: {record_error}, creating new one")
                try:
                    file_record = await self._create_file_record(
                        job_id=job_id,
                        file_name=file_name,
                        original_url=file_url,
                        status="downloading"
                    )
                    file_id = file_record["id"]
                except Exception as create_error:
                    logger.error(f"Failed to create file record: {create_error}")
                    raise

            # Download file
            logger.info(f"Downloading {file_name} from {file_url}")
            audio_data = await self._download_file(file_url)

            # Check file size
            if len(audio_data) > MAX_FILE_SIZE:
                file_size_mb = len(audio_data) / (1024 * 1024)
                max_size_gb = MAX_FILE_SIZE / (1024 * 1024 * 1024)
                raise Exception(f"File size {file_size_mb:.2f}MB exceeds maximum {max_size_gb}GB")

            # Convert if needed (ensure format compatibility)
            audio_data, file_format = await self._ensure_format_compatibility(audio_data, file_name)

            # Upload to storage
            storage_path = f"{user_id}/{job_id}/{file_name}"
            logger.info(f"Uploading {file_name} to storage")
            
            await self._update_file_status(file_id, "uploading")
            
            # Upload to Supabase storage
            # The upload method will raise an exception on error, so we don't need to check for error attribute
            try:
                upload_result = self.supabase.storage.from_(bucket_name).upload(
                    storage_path,
                    audio_data,
                    file_options={"content-type": self._get_content_type(file_format), "upsert": "true"}
                )
                # If we get here, upload was successful
                # upload_result should have a 'path' attribute if successful
                if hasattr(upload_result, 'path'):
                    logger.debug(f"Upload successful: {upload_result.path}")
                else:
                    logger.debug(f"Upload successful: {storage_path}")
            except Exception as upload_error:
                raise Exception(f"Upload failed: {str(upload_error)}")

            # Update file record
            file_ext = os.path.splitext(file_name)[1].lower()
            await self._update_file_record(
                file_id,
                {
                    "storage_path": storage_path,
                    "file_size": len(audio_data),
                    "file_format": file_ext or file_format,
                    "status": "transcribing"
                }
            )

            # Create call record
            call_record = await self._create_call_record(
                job_id=job_id,
                user_id=user_id,
                customer_name=customer_name,
                file_name=file_name,
                storage_path=storage_path,
                bucket_name=bucket_name
            )

            # Update file record with call_record_id
            await self._update_file_record(file_id, {"call_record_id": call_record["id"]})

            # Update file status to analyzing
            await self._update_file_status(file_id, "analyzing")
            
            # Trigger transcription and analysis (pass file_id so it can update status when done)
            await self._trigger_transcription_and_analysis(
                call_record_id=call_record["id"],
                storage_path=storage_path,
                bucket_name=bucket_name,
                file_name=file_name,
                user_id=user_id,
                customer_name=customer_name,
                provider=provider,
                file_id=file_id  # Pass file_id so we can update status after analysis
            )

        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}", exc_info=True)
            raise

    async def _download_file(self, url: str) -> bytes:
        """Download a file from URL"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes for large files
                headers={"User-Agent": "Mozilla/5.0 (compatible; BulkImport/1.0)"}
            )

        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file: {response.status}")
            return await response.read()

    async def _ensure_format_compatibility(self, audio_data: bytes, file_name: str) -> tuple[bytes, str]:
        """
        Ensure audio format is compatible.
        For now, we'll just validate the format.
        Actual conversion would require ffmpeg or similar.
        """
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext in SUPPORTED_FORMATS:
            return audio_data, file_ext
        
        # If format is not supported, we'd need to convert
        # For now, raise an error
        raise Exception(f"Unsupported audio format: {file_ext}")

    def _get_content_type(self, file_format: str) -> str:
        """Get MIME type for file format"""
        mime_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".webm": "audio/webm",
            ".ogg": "audio/ogg"
        }
        return mime_types.get(file_format.lower(), "audio/mpeg")

    async def _create_file_record(
        self,
        job_id: str,
        file_name: str,
        original_url: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a file record in the database"""
        result = self.supabase.table("bulk_import_files").insert({
            "job_id": job_id,
            "file_name": file_name,
            "original_url": original_url,
            "status": status,
            "error_message": error_message
        }).execute()

        if not result.data:
            raise Exception("Failed to create file record")
        return result.data[0]

    async def _update_file_record(self, file_id: str, updates: Dict[str, Any]):
        """Update a file record"""
        self.supabase.table("bulk_import_files").update(updates).eq("id", file_id).execute()

    async def _update_file_status(self, file_id: str, status: str, error_message: Optional[str] = None):
        """Update file status"""
        await self._update_file_record(file_id, {"status": status, "error_message": error_message})

    async def _create_call_record(
        self,
        job_id: str,
        user_id: str,
        customer_name: str,
        file_name: str,
        storage_path: str,
        bucket_name: str
    ) -> Dict[str, Any]:
        """Create a call record in the database"""
        # Construct audio_file_url in format: bucket_name/storage_path
        audio_file_url = f"{bucket_name}/{storage_path}"
        
        result = self.supabase.table("call_records").insert({
            "user_id": user_id,
            "customer_name": customer_name,
            "start_time": "now()",
            "end_time": "now()",
            "transcript": "Processing...",
            "total_chunks": 1,
            "chunks_uploaded": 1,
            "recording_complete": True,
            "bulk_import_job_id": job_id,
            "audio_file_url": audio_file_url  # Set audio_file_url so transcription can access it
        }).execute()

        if not result.data:
            raise Exception("Failed to create call record")
        return result.data[0]

    async def _trigger_transcription_and_analysis(
        self,
        call_record_id: str,
        storage_path: str,
        bucket_name: str,
        file_name: str,
        user_id: str,
        customer_name: str,
        provider: str,
        file_id: Optional[str] = None
    ):
        """
        Trigger transcription and analysis pipeline.
        This integrates with the existing transcribe_api and analysis_api.
        """
        import uuid
        from datetime import datetime
        from services.call_analysis_service import CallAnalysisService
        
        # Get signed URL for the audio file
        public_url = None
        try:
            signed_url_response = self.supabase.storage.from_(bucket_name).create_signed_url(
                storage_path,
                3600  # 1 hour expiry
            )
            
            # The create_signed_url method returns a dict or raises an exception
            # Handle both cases
            if isinstance(signed_url_response, dict):
                public_url = signed_url_response.get("signedURL") or signed_url_response.get("signed_url")
            elif hasattr(signed_url_response, 'data'):
                signed_data = signed_url_response.data
                if isinstance(signed_data, dict):
                    public_url = signed_data.get("signedURL") or signed_data.get("signed_url")
            elif hasattr(signed_url_response, 'get'):
                public_url = signed_url_response.get("signedURL") or signed_url_response.get("signed_url")
            
            if not public_url:
                logger.warning(f"Could not extract signed URL from response: {signed_url_response}")
        except Exception as e:
            logger.warning(f"Could not get signed URL for audio file: {e}. Continuing with storage path.")
            # Continue without signed URL - will use storage path
            public_url = None

        # Determine transcription provider (check which API keys are available)
        import os
        deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        assemblyai_key = os.getenv("ASSEMBLY_AI_API_KEY") or os.getenv("ASSEMBLYAI_API_KEY")
        
        transcription_provider = "deepgram"  # Default
        if deepgram_key:
            transcription_provider = "deepgram"
            logger.debug("Using Deepgram for transcription (DEEPGRAM_API_KEY found)")
        elif assemblyai_key:
            transcription_provider = "assemblyai"
            logger.debug("Using AssemblyAI for transcription (ASSEMBLY_AI_API_KEY found)")
        else:
            logger.warning("No transcription API keys found (DEEPGRAM_API_KEY or ASSEMBLY_AI_API_KEY). Defaulting to deepgram.")
        
        # Create transcription queue entry (if table exists)
        # Note: transcription_queue table may have different column names
        # Some versions use 'call_id' instead of 'call_record_id'
        upload_id = str(uuid.uuid4())
        try:
            # Try with call_record_id first
            transcription_data = {
                "id": upload_id,
                "storage_path": storage_path,
                "status": "pending",
                "progress": 0,
                "provider": transcription_provider,  # Use detected provider
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
            # Add URL if available
            if public_url:
                transcription_data["public_url"] = public_url
            
            # Try call_record_id first, then call_id
            try:
                transcription_data["call_record_id"] = call_record_id
                self.supabase.table("transcription_queue").insert(transcription_data).execute()
                logger.debug(f"Created transcription_queue entry with call_record_id: {upload_id}")
            except Exception as e1:
                # Try with call_id instead
                if "call_record_id" in str(e1).lower() or "column" in str(e1).lower():
                    try:
                        transcription_data.pop("call_record_id", None)
                        transcription_data["call_id"] = call_record_id
                        self.supabase.table("transcription_queue").insert(transcription_data).execute()
                        logger.debug(f"Created transcription_queue entry with call_id: {upload_id}")
                    except Exception as e2:
                        # Table might not exist or have different structure - skip it
                        logger.debug(f"Could not create transcription_queue entry (tried both call_record_id and call_id): {e2}")
                else:
                    raise
        except Exception as e:
            logger.debug(f"Could not create transcription_queue entry: {e}")
            # Continue - transcription queue might not exist or have different schema

        # Trigger background transcription processing
        # This would typically be done via a background task
        # For now, we'll trigger it directly
        try:
            from api.transcribe_api import _process_transcription_background
            
            # Get file extension
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Trigger transcription in background
            # Note: This is a simplified approach - in production, use proper task queue
            import asyncio
            import threading
            
            # Run transcription in a separate thread
            def run_transcription():
                try:
                    _process_transcription_background(
                        upload_id,
                        storage_path,
                        public_url,
                        transcription_provider,  # Use detected provider
                        file_ext,
                        "Salesperson",  # Default salesperson name
                        customer_name,
                        None,  # language
                        True,  # enable_diarization
                        call_record_id,  # Pass call_record_id directly
                        file_id  # Pass file_id so status can be updated to "completed" when done
                    )
                except Exception as e:
                    logger.error(f"Error in transcription thread: {e}")
            
            transcription_thread = threading.Thread(target=run_transcription, daemon=True)
            transcription_thread.start()
            
            # NOTE: _process_transcription_background already triggers analysis internally
            # We need to wait for the entire pipeline (transcription + analysis) to complete
            # before moving to the next file to ensure sequential processing
            logger.info(f"✅ Transcription thread started for {call_record_id}. Analysis will be triggered automatically by _process_transcription_background when transcript completes.")
            print(f"✅ Transcription thread started for {call_record_id}. Analysis will be triggered automatically.")
            
            # Update file status to transcribing
            if file_id:
                try:
                    await self._update_file_status(file_id, "transcribing")
                    logger.debug(f"File {file_name} status updated to transcribing")
                except Exception as e:
                    logger.warning(f"Failed to update file status: {e}")
            
            # Wait for transcription and analysis to complete before returning
            # This ensures sequential processing - next file only starts after current one is fully done
            if file_id:
                logger.info(f"⏳ Waiting for transcription and analysis to complete for file {file_name} (call_record_id={call_record_id})...")
                print(f"⏳ Waiting for pipeline completion for file {file_name}...")
                
                max_wait_time = 600  # 10 minutes max wait time
                poll_interval = 3  # Check every 3 seconds
                waited = 0
                
                while waited < max_wait_time:
                    try:
                        # Check file status
                        file_result = self.supabase.table("bulk_import_files").select("status").eq("id", file_id).maybe_single().execute()
                        
                        if file_result and hasattr(file_result, 'data') and file_result.data:
                            file_status = file_result.data.get("status")
                            
                            # Check if pipeline is complete
                            if file_status == "completed":
                                logger.info(f"✅ Pipeline completed for file {file_name} (status: {file_status})")
                                print(f"✅ Pipeline completed for file {file_name} after {waited}s")
                                break
                            elif file_status == "failed":
                                logger.warning(f"⚠️ Pipeline failed for file {file_name} (status: {file_status})")
                                print(f"⚠️ Pipeline failed for file {file_name} after {waited}s")
                                break
                            else:
                                # Still processing - log intermediate status
                                if waited % 30 == 0:  # Log every 30 seconds
                                    logger.debug(f"⏳ Still processing file {file_name}: status={file_status}, waited={waited}s")
                                    print(f"⏳ Still processing file {file_name}: status={file_status}, waited={waited}s")
                        
                        # Also check call_record to see if transcript is ready
                        call_result = self.supabase.table("call_records").select("transcript, call_category, call_type").eq("id", call_record_id).maybe_single().execute()
                        if call_result and hasattr(call_result, 'data') and call_result.data:
                            transcript = call_result.data.get("transcript", "")
                            call_category = call_result.data.get("call_category")
                            call_type = call_result.data.get("call_type")
                            
                            # If we have a valid transcript and category, analysis is likely complete
                            invalid_transcripts = ["Processing...", "Transcribing audio...", "Transcription timeout"]
                            if transcript and transcript not in invalid_transcripts and len(transcript.strip()) > 10:
                                if call_category:
                                    # Both transcript and category exist - analysis is likely complete
                                    # call_type is optional but preferred for better context
                                    analysis_info = f"category={call_category}"
                                    if call_type:
                                        analysis_info += f", call_type={call_type}"
                                    # Check file status one more time to confirm
                                    file_result = self.supabase.table("bulk_import_files").select("status").eq("id", file_id).maybe_single().execute()
                                    if file_result and hasattr(file_result, 'data') and file_result.data:
                                        file_status = file_result.data.get("status")
                                        if file_status in ["completed", "categorized", "failed"]:
                                            logger.info(f"✅ Analysis appears complete for file {file_name} (transcript ready, {analysis_info})")
                                            print(f"✅ Analysis appears complete for file {file_name} after {waited}s")
                                            break
                        
                    except Exception as poll_error:
                        logger.debug(f"Error polling file status: {poll_error}")
                    
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                
                if waited >= max_wait_time:
                    logger.warning(f"⚠️ Pipeline timeout for file {file_name} after {max_wait_time}s - proceeding to next file")
                    print(f"⚠️ Pipeline timeout for file {file_name} after {max_wait_time}s")
                else:
                    logger.info(f"✅ Sequential processing: File {file_name} completed, proceeding to next file")
                    print(f"✅ Sequential processing: File {file_name} completed, proceeding to next file")
            else:
                # No file_id - can't track status, wait a bit for thread to start
                logger.warning(f"⚠️ No file_id provided, cannot track completion. Waiting 5 seconds for thread to start...")
                await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in transcription/analysis pipeline: {e}", exc_info=True)
            # Update file status to failed if we have file_id
            if file_id:
                try:
                    await self._update_file_status(file_id, "failed", error_message=str(e)[:500])
                except Exception:
                    pass
            # Don't fail the entire import - just log the error

    async def _update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        completed_at: bool = False
    ):
        """Update job status"""
        update_data = {"status": status}
        if error_message is not None:
            update_data["error_message"] = error_message
        if completed_at:
            from datetime import datetime
            update_data["completed_at"] = datetime.utcnow().isoformat()
        
        self.supabase.table("bulk_import_jobs").update(update_data).eq("id", job_id).execute()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

