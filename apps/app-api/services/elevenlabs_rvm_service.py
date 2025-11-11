"""
ElevenLabs Ringless Voicemail (RVM) Service
Integrated from SAR project - tested and working implementation
"""
import logging
import os
import tempfile
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)


class ElevenLabsRVMService:
    """Service for generating RVM audio using ElevenLabs API"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
        self.base_url = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID") or os.getenv("ELEVEN_VOICE_ID")
        
        if not self.api_key:
            logger.warning("⚠️ ELEVENLABS_API_KEY or ELEVEN_API_KEY not found in environment")
        if not self.voice_id:
            logger.warning("⚠️ ELEVENLABS_VOICE_ID or ELEVEN_VOICE_ID not found in environment")
    
    def generate_rvm_audio(
        self,
        script: str,
        salesperson_name: str,
        contact_number: str,
        voice_settings: Optional[Dict[str, Any]] = None,
        save_to_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate RVM audio from script using ElevenLabs API
        
        Args:
            script: RVM script text (with placeholders [SALESPERSON_NAME] and [CONTACT_NUMBER])
            salesperson_name: Salesperson's name to replace [SALESPERSON_NAME]
            contact_number: Contact number to replace [CONTACT_NUMBER]
            voice_settings: Optional voice settings (stability, similarity_boost, style, speed, etc.)
            save_to_file: Optional path to save the audio file. If not provided, uses temporary file.
        
        Returns:
            Dict with audio_url, audio_id, duration, audio_bytes, file_path, and metadata
        """
        if not self.api_key or not self.voice_id:
            raise ValueError("ElevenLabs API key and voice ID must be configured")
        
        # Replace placeholders in script
        final_script = script.replace("[SALESPERSON_NAME]", salesperson_name)
        final_script = final_script.replace("[CONTACT_NUMBER]", contact_number)
        
        logger.info(f"🎙️ Generating RVM audio using ElevenLabs (script length: {len(final_script)} chars)")
        logger.debug(f"🎙️ Script preview: {final_script[:200]}...")
        
        # Call ElevenLabs API
        audio_bytes = self._call_elevenlabs_api(final_script, voice_settings)
        
        # Generate unique ID for this audio
        audio_id = str(uuid.uuid4())
        
        # Save to file (temporary or specified path)
        if save_to_file:
            audio_path = save_to_file
        else:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, f"rvm_{audio_id}.mp3")
        
        # Write audio bytes to file
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Estimate duration (roughly 150 words per minute for speech)
        word_count = len(final_script.split())
        estimated_duration = max(10, int((word_count / 150) * 60))  # Minimum 10 seconds
        
        result = {
            "success": True,
            "audio_id": audio_id,
            "audio_url": None,  # Will be set by caller if uploaded to storage
            "audio_bytes": audio_bytes,
            "file_path": audio_path,
            "duration_seconds": estimated_duration,
            "script": final_script,
            "voice_id": self.voice_id,
            "metadata": {
                "word_count": word_count,
                "character_count": len(final_script),
                "salesperson_name": salesperson_name,
                "contact_number": contact_number,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "service": "elevenlabs",
                "file_size_bytes": len(audio_bytes)
            }
        }
        
        logger.info(f"✅ RVM audio generated: {audio_id} ({estimated_duration}s, {len(audio_bytes)} bytes)")
        
        return result
    
    def _call_elevenlabs_api(self, script: str, voice_settings: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Actual ElevenLabs API call - integrated from SAR project
        
        Args:
            script: Text to convert to speech
            voice_settings: Optional voice settings dict
        
        Returns:
            Audio bytes (MP3 format)
        """
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Default voice settings (from SAR project)
        default_settings = {
            "stability": 0.4,
            "similarity_boost": 0.90,
            "use_speaker_boost": True,
            "style": 0.5,
            "speed": 0.9
        }
        
        # Merge with provided settings
        final_voice_settings = {**default_settings}
        if voice_settings:
            final_voice_settings.update(voice_settings)
        
        data = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": final_voice_settings
        }
        
        logger.debug(f"🔁 Calling ElevenLabs API: {url}")
        logger.debug(f"🔁 Voice settings: {final_voice_settings}")
        
        try:
            response = requests.post(url, headers=headers, json=data, stream=True, timeout=60)
            
            content_type = response.headers.get("Content-Type", "")
            logger.debug(f"🔁 ElevenLabs response status: {response.status_code}")
            logger.debug(f"🔁 ElevenLabs response content-type: {content_type}")
            
            if not content_type.startswith("audio/"):
                error_text = response.text
                logger.error(f"❌ Unexpected content type from ElevenLabs: {content_type}")
                logger.error(f"❌ Response: {error_text}")
                raise ValueError(f"ElevenLabs did not return audio. Response: {error_text}")
            
            response.raise_for_status()
            
            # Stream and collect audio bytes
            audio_bytes = b""
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    audio_bytes += chunk
            
            logger.info(f"✅ Received {len(audio_bytes)} bytes of audio from ElevenLabs")
            return audio_bytes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ElevenLabs API error: {e}")
            raise RuntimeError(f"Failed to generate audio with ElevenLabs: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error calling ElevenLabs: {e}")
            raise


def get_rvm_service() -> ElevenLabsRVMService:
    """Get or create ElevenLabs RVM service instance"""
    return ElevenLabsRVMService()

