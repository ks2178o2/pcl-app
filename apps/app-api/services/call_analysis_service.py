"""
Call Analysis Service - Handles LLM-based call categorization and objection analysis
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List
from supabase import Client

logger = logging.getLogger(__name__)


class CallAnalysisService:
    """Service for analyzing calls using LLM providers"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.openai_key = os.getenv("OPENAI_API_KEY")
        # Support multiple possible env var names for Google/Gemini API key
        self.gemini_key = (
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("GOOGLE_SERVICES_API_KEY") or
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )
        
        # Log which API keys are available (without exposing the keys themselves)
        if self.openai_key:
            logger.info("OpenAI API key found - OpenAI provider available")
        else:
            logger.warning("OpenAI API key not found - OpenAI provider unavailable")
        
        if self.gemini_key:
            logger.info("Gemini API key found (from GOOGLE_API_KEY or other) - Gemini provider available")
        else:
            logger.warning("Gemini API key not found - Gemini provider unavailable")

    async def categorize_call(
        self,
        transcript: str,
        call_record_id: str,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Categorize a call transcript using LLM.
        Returns both:
        - call_category: consult_not_scheduled, consult_scheduled, other_question (success/failure)
        - call_type: scheduling, pricing, directions, billing, complaint, transfer_to_office, general_question, reschedule, confirming_existing_appointment, cancellation (granular category)
        """
        try:
            # Priority: Gemini (primary) -> OpenAI (secondary) -> Heuristic (last resort)
            if provider == "gemini" and self.gemini_key:
                try:
                    result = await self._categorize_with_gemini(transcript)
                except Exception as gemini_error:
                    logger.warning(f"Gemini categorization failed: {gemini_error}, falling back to OpenAI")
                    if self.openai_key:
                        result = await self._categorize_with_openai(transcript)
                    else:
                        result = self._categorize_with_heuristic(transcript)
            elif provider == "openai" and self.openai_key:
                result = await self._categorize_with_openai(transcript)
            else:
                # Auto-select provider: Gemini first, then OpenAI, then heuristic
                if self.gemini_key:
                    try:
                        result = await self._categorize_with_gemini(transcript)
                    except Exception as gemini_error:
                        logger.warning(f"Gemini categorization failed: {gemini_error}, falling back to OpenAI")
                        if self.openai_key:
                            result = await self._categorize_with_openai(transcript)
                        else:
                            result = self._categorize_with_heuristic(transcript)
                elif self.openai_key:
                    result = await self._categorize_with_openai(transcript)
                else:
                    result = self._categorize_with_heuristic(transcript)

            # Store categorization in call_records
            # Mark if this is a heuristic result (for frontend display)
            reasoning = result.get("reasoning", "")
            is_heuristic = "[HEURISTIC" in reasoning or result.get("category") == "other_question" and result.get("confidence", 0) == 0.5
            if is_heuristic and "[HEURISTIC" not in reasoning:
                reasoning = f"{reasoning} [HEURISTIC - Last Resort]"
            
            # Prepare update data with both call_category and call_type
            update_data = {
                "call_category": result["category"],
                "categorization_confidence": result.get("confidence", 0.8),
                "categorization_notes": reasoning
            }
            
            # Add call_type if it exists in the result
            if "call_type" in result:
                update_data["call_type"] = result["call_type"]
            
            update_result = self.supabase.table("call_records").update(update_data).eq("id", call_record_id).execute()
            
            if update_result.data:
                category_info = f"category: {result['category']}"
                if "call_type" in result:
                    category_info += f", call_type: {result['call_type']}"
                logger.info(f"✅ Successfully updated call_record {call_record_id} with {category_info}")
            else:
                logger.warning(f"⚠️ No data returned when updating call_record {call_record_id} with category")

            return result

        except Exception as e:
            logger.error(f"Error categorizing call {call_record_id}: {e}", exc_info=True)
            # Fallback to heuristic
            result = self._categorize_with_heuristic(transcript)
            update_data = {
                "call_category": result["category"],
                "categorization_confidence": result.get("confidence", 0.5),
                "categorization_notes": "Heuristic fallback due to LLM error"
            }
            if "call_type" in result:
                update_data["call_type"] = result["call_type"]
            self.supabase.table("call_records").update(update_data).eq("id", call_record_id).execute()
            return result

    async def detect_objections(
        self,
        transcript: str,
        call_record_id: str,
        provider: str = "openai"
    ) -> List[Dict[str, Any]]:
        """
        Detect objections and misgivings in the call transcript.
        Returns list of objection objects.
        """
        try:
            # Priority: Gemini (primary) -> OpenAI (secondary) -> Heuristic (last resort)
            if provider == "gemini" and self.gemini_key:
                try:
                    objections = await self._detect_objections_with_gemini(transcript)
                except Exception as gemini_error:
                    logger.warning(f"Gemini objection detection failed: {gemini_error}, falling back to OpenAI")
                    if self.openai_key:
                        objections = await self._detect_objections_with_openai(transcript)
                    else:
                        objections = self._detect_objections_with_heuristic(transcript)
            elif provider == "openai" and self.openai_key:
                objections = await self._detect_objections_with_openai(transcript)
            else:
                # Auto-select provider: Gemini first, then OpenAI, then heuristic
                if self.gemini_key:
                    try:
                        objections = await self._detect_objections_with_gemini(transcript)
                    except Exception as gemini_error:
                        logger.warning(f"Gemini objection detection failed: {gemini_error}, falling back to OpenAI")
                        if self.openai_key:
                            objections = await self._detect_objections_with_openai(transcript)
                        else:
                            objections = self._detect_objections_with_heuristic(transcript)
                elif self.openai_key:
                    objections = await self._detect_objections_with_openai(transcript)
                else:
                    objections = self._detect_objections_with_heuristic(transcript)

            # Delete existing objections for this call record to prevent duplicates
            logger.info(f"🗑️ Deleting existing objections for call_record {call_record_id} before inserting new ones")
            try:
                delete_result = self.supabase.table("call_objections").delete().eq("call_record_id", call_record_id).execute()
                logger.info(f"✅ Deleted existing objections for call_record {call_record_id}")
            except Exception as delete_error:
                logger.warning(f"⚠️ Error deleting existing objections: {delete_error}")
            
            # Detect if these are heuristic results (check for hardcoded confidence or placeholder text)
            is_heuristic = any(
                obj.get("confidence") == 0.6 or 
                obj.get("segment") == "Heuristic detection" or
                "heuristic" in obj.get("text", "").lower()
                for obj in objections
            )
            
            # Store objections in database
            inserted_count = 0
            for objection in objections:
                # Mark heuristic objections
                objection_text = objection["text"]
                if is_heuristic:
                    objection_text = f"{objection_text} [HEURISTIC]"
                insert_result = self.supabase.table("call_objections").insert({
                    "call_record_id": call_record_id,
                    "objection_type": objection["type"],
                    "objection_text": objection_text,
                    "speaker": objection.get("speaker"),
                    "confidence": objection.get("confidence", 0.8),
                    "transcript_segment": objection.get("segment", "")
                }).execute()
                
                if insert_result.data:
                    inserted_count += 1
                else:
                    logger.warning(f"⚠️ Failed to insert objection for call_record {call_record_id}: {objection.get('type')}")
            
            logger.info(f"✅ Inserted {inserted_count} objections for call_record {call_record_id}")

            return objections

        except Exception as e:
            logger.error(f"Error detecting objections for call {call_record_id}: {e}", exc_info=True)
            return []

    async def analyze_objection_overcome(
        self,
        transcript: str,
        call_record_id: str,
        objections: List[Dict[str, Any]],
        provider: str = "openai"
    ) -> List[Dict[str, Any]]:
        """
        Analyze how objections were overcome for calls where consult was scheduled.
        Only called for calls with category 'consult_scheduled'.
        Uses call_type context to provide more relevant analysis.
        """
        try:
            # Priority: Gemini (primary) -> OpenAI (secondary) -> Skip (last resort)
            if provider == "gemini" and self.gemini_key:
                try:
                    overcome_details = await self._analyze_overcome_with_gemini(transcript, objections)
                except Exception as gemini_error:
                    logger.warning(f"Gemini objection overcome analysis failed: {gemini_error}, falling back to OpenAI")
                    if self.openai_key:
                        overcome_details = await self._analyze_overcome_with_openai(transcript, objections)
                    else:
                        overcome_details = []
            elif provider == "openai" and self.openai_key:
                overcome_details = await self._analyze_overcome_with_openai(transcript, objections)
            else:
                # Auto-select provider: Gemini first, then OpenAI, then skip
                if self.gemini_key:
                    try:
                        overcome_details = await self._analyze_overcome_with_gemini(transcript, objections)
                    except Exception as gemini_error:
                        logger.warning(f"Gemini objection overcome analysis failed: {gemini_error}, falling back to OpenAI")
                        if self.openai_key:
                            overcome_details = await self._analyze_overcome_with_openai(transcript, objections)
                        else:
                            overcome_details = []
                elif self.openai_key:
                    overcome_details = await self._analyze_overcome_with_openai(transcript, objections)
                else:
                    overcome_details = []

            # Delete existing objection overcome details for this call record to prevent duplicates
            logger.info(f"🗑️ Deleting existing objection overcome details for call_record {call_record_id} before inserting new ones")
            try:
                delete_result = self.supabase.table("objection_overcome_details").delete().eq("call_record_id", call_record_id).execute()
                logger.info(f"✅ Deleted existing objection overcome details for call_record {call_record_id}")
            except Exception as delete_error:
                logger.warning(f"⚠️ Error deleting existing objection overcome details: {delete_error}")
            
            # Store objection overcome details
            for detail in overcome_details:
                # Find the corresponding objection ID
                objection_result = self.supabase.table("call_objections").select("id").eq(
                    "call_record_id", call_record_id
                ).eq("objection_type", detail["objection_type"]).limit(1).execute()

                objection_id = objection_result.data[0]["id"] if objection_result.data else None
                
                if not objection_id:
                    logger.warning(f"⚠️ Could not find objection_id for overcome detail: {detail.get('objection_type')}")
                    continue

                insert_result = self.supabase.table("objection_overcome_details").insert({
                    "call_record_id": call_record_id,
                    "objection_id": objection_id,
                    "overcome_method": detail["method"],
                    "transcript_quote": detail["quote"],
                    "speaker": detail.get("speaker"),
                    "confidence": detail.get("confidence", 0.8)
                }).execute()
                
                if not insert_result.data:
                    logger.warning(f"⚠️ Failed to insert objection overcome detail for call_record {call_record_id}, objection {objection_id}")

            logger.info(f"✅ Inserted {len(overcome_details)} objection overcome details for call_record {call_record_id}")
            return overcome_details

        except Exception as e:
            logger.error(f"Error analyzing objection overcome for call {call_record_id}: {e}", exc_info=True)
            return []

    async def _categorize_with_openai(self, transcript: str) -> Dict[str, Any]:
        """Categorize call using OpenAI"""
        import requests

        if not self.openai_key:
            logger.warning("OpenAI API key not available, falling back to heuristic")
            return self._categorize_with_heuristic(transcript)

        prompt = f"""Analyze this call transcript and categorize it in TWO ways:

1. CALL CATEGORY (success/failure status):
   - consult_scheduled: A consultation appointment was successfully scheduled
   - consult_not_scheduled: Call ended without scheduling a consultation
   - other_question: General question or inquiry, not related to scheduling

2. CALL TYPE (granular category - what the call was about):
   - scheduling: Call about scheduling a new appointment
   - pricing: Call about pricing, costs, or payment options
   - directions: Call asking for directions or location information
   - billing: Call about billing issues, invoices, or payment problems
   - complaint: Call expressing a complaint or dissatisfaction
   - transfer_to_office: Call requesting to be transferred to an office/department
   - general_question: General inquiry or question
   - reschedule: Call to reschedule an existing appointment
   - confirming_existing_appointment: Call to confirm an existing appointment
   - cancellation: Call to cancel an appointment or service

IMPORTANT: Calculate confidence based on how clear and unambiguous the evidence is:
- 0.9-1.0: Very clear, explicit evidence (e.g., "Let's schedule for next Tuesday" or "I'm not interested")
- 0.7-0.89: Clear evidence but some ambiguity
- 0.5-0.69: Some evidence but ambiguous or unclear
- 0.3-0.49: Weak evidence, mostly guessing
- 0.0-0.29: Very unclear, minimal evidence

Return your response as JSON with:
{{
  "category": "consult_not_scheduled|consult_scheduled|other_question",
  "call_type": "scheduling|pricing|directions|billing|complaint|transfer_to_office|general_question|reschedule|confirming_existing_appointment|cancellation",
  "confidence": <calculate based on evidence clarity, 0.0-1.0>,
  "reasoning": "Brief explanation of evidence found for both category and call_type"
}}

Transcript:
{transcript[:4000]}  # Limit to avoid token limits
"""

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        body = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a call analysis expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            logger.debug(f"Calling OpenAI API with model {model_name} for categorization")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            try:
                result = json.loads(content)
                confidence = float(result.get("confidence", 0.8))
                call_type = result.get("call_type", "general_question")
                logger.info(f"OpenAI categorization: category={result.get('category')}, call_type={call_type}, confidence={confidence}")
                return {
                    "category": result.get("category", "other_question"),
                    "call_type": call_type,
                    "confidence": confidence,
                    "reasoning": result.get("reasoning", "")
                }
            except json.JSONDecodeError as json_error:
                logger.warning(f"Failed to parse OpenAI JSON response: {json_error}, content: {content[:200]}")
                # Fallback parsing - try to extract JSON from response
                import re
                json_match = re.search(r'\{[^}]+"category"[^}]+\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        return {
                            "category": result.get("category", "other_question"),
                            "call_type": result.get("call_type", "general_question"),
                            "confidence": float(result.get("confidence", 0.8)),
                            "reasoning": result.get("reasoning", "")
                        }
                    except json.JSONDecodeError:
                        pass
                # Final fallback to heuristic
                logger.warning("Falling back to heuristic categorization")
                return self._categorize_with_heuristic(transcript)
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}", exc_info=True)
            return self._categorize_with_heuristic(transcript)
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI categorization: {e}", exc_info=True)
            return self._categorize_with_heuristic(transcript)

    async def _categorize_with_gemini(self, transcript: str) -> Dict[str, Any]:
        """Categorize call using Gemini"""
        try:
            import google.generativeai as genai
            
            if not self.gemini_key:
                logger.warning("Gemini API key not found, falling back to heuristic")
                return self._categorize_with_heuristic(transcript)
            
            genai.configure(api_key=self.gemini_key)
            # Try different Gemini model names - the API version may require different names
            # Available models vary by API version and region:
            # - gemini-pro (most common, stable)
            # - gemini-1.5-pro (more capable, longer context)
            # - gemini-1.5-flash (faster, cheaper)
            # - gemini-1.0-pro (older version)
            # - gemini-2.0-flash (newer, if available)
            # - gemini-2.5-flash (newest, if available)
            model = None
            model_names = [
                'gemini-pro',           # Most widely available, stable
                'gemini-1.0-pro',       # Older but reliable
                'gemini-1.5-pro',       # More capable, longer context
                'gemini-1.5-flash',     # Faster, cheaper
                'gemini-2.0-flash',     # Newer version (if available)
                'gemini-2.5-flash',     # Newest version (if available)
            ]
            last_error = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Successfully initialized Gemini model: {model_name}")
                    break  # Success, exit the loop
                except Exception as e:
                    logger.debug(f"Failed to initialize Gemini model {model_name}: {e}")
                    last_error = e
                    continue
            
            if model is None:
                logger.error(f"❌ Failed to initialize any Gemini model. Tried: {model_names}. Last error: {last_error}")
                logger.error(f"❌ Available models may vary by API version. Check Google's documentation for your API key's supported models.")
                raise Exception(f"All Gemini models failed. Tried: {', '.join(model_names)}. Last error: {last_error}")
            
            prompt = f"""Analyze this call transcript and categorize it in TWO ways:

1. CALL CATEGORY (success/failure status):
   - consult_scheduled: A consultation appointment was successfully scheduled
   - consult_not_scheduled: Call ended without scheduling a consultation
   - other_question: General question or inquiry, not related to scheduling

2. CALL TYPE (granular category - what the call was about):
   - scheduling: Call about scheduling a new appointment
   - pricing: Call about pricing, costs, or payment options
   - directions: Call asking for directions or location information
   - billing: Call about billing issues, invoices, or payment problems
   - complaint: Call expressing a complaint or dissatisfaction
   - transfer_to_office: Call requesting to be transferred to an office/department
   - general_question: General inquiry or question
   - reschedule: Call to reschedule an existing appointment
   - confirming_existing_appointment: Call to confirm an existing appointment
   - cancellation: Call to cancel an appointment or service

IMPORTANT: Calculate confidence based on how clear and unambiguous the evidence is:
- 0.9-1.0: Very clear, explicit evidence (e.g., "Let's schedule for next Tuesday" or "I'm not interested")
- 0.7-0.89: Clear evidence but some ambiguity
- 0.5-0.69: Some evidence but ambiguous or unclear
- 0.3-0.49: Weak evidence, mostly guessing
- 0.0-0.29: Very unclear, minimal evidence

Return your response as JSON with:
{{
  "category": "consult_not_scheduled|consult_scheduled|other_question",
  "call_type": "scheduling|pricing|directions|billing|complaint|transfer_to_office|general_question|reschedule|confirming_existing_appointment|cancellation",
  "confidence": <calculate based on evidence clarity, 0.0-1.0>,
  "reasoning": "Brief explanation of evidence found for both category and call_type"
}}

Transcript:
{transcript[:8000]}  # Gemini supports longer context
"""
            
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "response_mime_type": "application/json"
                    }
                )
                
                try:
                    result = json.loads(response.text)
                    raw_confidence = result.get("confidence")
                    confidence = float(raw_confidence) if raw_confidence is not None else 0.8
                    call_type = result.get("call_type", "general_question")
                    logger.info(f"✅ Gemini categorization: category={result.get('category')}, call_type={call_type}, confidence={confidence}")
                    print(f"✅ Gemini categorization: category={result.get('category')}, call_type={call_type}, confidence={confidence} (from LLM)")
                    return {
                        "category": result.get("category", "other_question"),
                        "call_type": call_type,
                        "confidence": confidence,
                        "reasoning": result.get("reasoning", "")
                    }
                except json.JSONDecodeError:
                    # Try to extract JSON from response if it's wrapped
                    import re
                    json_match = re.search(r'\{[^}]+"category"[^}]+\}', response.text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return {
                            "category": result.get("category", "other_question"),
                            "call_type": result.get("call_type", "general_question"),
                            "confidence": float(result.get("confidence", 0.8)),
                            "reasoning": result.get("reasoning", "")
                        }
                    logger.warning("Failed to parse Gemini JSON response, will raise to trigger OpenAI fallback")
                    raise Exception("Failed to parse Gemini JSON response")
            except Exception as gen_api_error:
                logger.error(f"❌ Gemini API call failed: {gen_api_error}")
                logger.info(f"🔄 This error will trigger fallback to OpenAI (if available)")
                raise  # Re-raise to trigger fallback in categorize_call
        except ImportError:
            logger.warning("google-generativeai package not installed. Install with: pip install google-generativeai")
            raise Exception("Gemini package not installed")  # Raise to trigger fallback
        except Exception as e:
            logger.error(f"❌ Error using Gemini API: {e}", exc_info=True)
            logger.info(f"🔄 This error will trigger fallback to OpenAI (if available). Error details: {str(e)[:200]}")
            raise  # Re-raise to trigger fallback in categorize_call

    def _categorize_with_heuristic(self, transcript: str) -> Dict[str, Any]:
        """Simple heuristic-based categorization (LAST RESORT FALLBACK - not real LLM analysis)"""
        logger.warning(f"⚠️ Using HEURISTIC categorization (LAST RESORT - not real LLM analysis)")
        print(f"⚠️ Using HEURISTIC categorization (LAST RESORT - confidence values are hardcoded)")
        transcript_lower = transcript.lower()
        
        # Keywords for scheduled consult
        scheduled_keywords = ["schedule", "appointment", "book", "set up", "when can", "available"]
        scheduled_score = sum(1 for kw in scheduled_keywords if kw in transcript_lower)
        
        # Keywords for not scheduled
        not_scheduled_keywords = ["not interested", "maybe later", "think about it", "not ready"]
        not_scheduled_score = sum(1 for kw in not_scheduled_keywords if kw in transcript_lower)
        
        # Determine call_type from keywords
        call_type = "general_question"  # Default
        if "price" in transcript_lower or "cost" in transcript_lower or "payment" in transcript_lower:
            call_type = "pricing"
        elif "direction" in transcript_lower or "location" in transcript_lower or "address" in transcript_lower or "where" in transcript_lower:
            call_type = "directions"
        elif "bill" in transcript_lower or "invoice" in transcript_lower or "charge" in transcript_lower:
            call_type = "billing"
        elif "complaint" in transcript_lower or "problem" in transcript_lower or "issue" in transcript_lower:
            call_type = "complaint"
        elif "transfer" in transcript_lower or "connect" in transcript_lower:
            call_type = "transfer_to_office"
        elif "reschedule" in transcript_lower or "rescheduling" in transcript_lower:
            call_type = "reschedule"
        elif "confirm" in transcript_lower and ("appointment" in transcript_lower or "meeting" in transcript_lower):
            call_type = "confirming_existing_appointment"
        elif "cancel" in transcript_lower or "cancellation" in transcript_lower:
            call_type = "cancellation"
        elif scheduled_score > 0 or "schedule" in transcript_lower or "appointment" in transcript_lower:
            call_type = "scheduling"
        
        if scheduled_score > 2:
            result = {
                "category": "consult_scheduled",
                "call_type": call_type,
                "confidence": 0.7,  # HARDCODED - this is a placeholder
                "reasoning": f"Keywords suggest appointment was scheduled, call_type={call_type} [HEURISTIC - Last Resort]"
            }
            logger.warning(f"⚠️ HEURISTIC categorization: category=consult_scheduled, call_type={call_type}, confidence=0.7 (HARDCODED)")
            return result
        elif not_scheduled_score > 0:
            result = {
                "category": "consult_not_scheduled",
                "call_type": call_type,
                "confidence": 0.6,  # HARDCODED - this is a placeholder
                "reasoning": f"Keywords suggest no appointment scheduled, call_type={call_type} [HEURISTIC - Last Resort]"
            }
            logger.warning(f"⚠️ HEURISTIC categorization: category=consult_not_scheduled, call_type={call_type}, confidence=0.6 (HARDCODED)")
            return result
        else:
            result = {
                "category": "other_question",
                "call_type": call_type,
                "confidence": 0.5,  # HARDCODED - this is a placeholder
                "reasoning": f"Unable to determine category, call_type={call_type} [HEURISTIC - Last Resort]"
            }
            logger.warning(f"⚠️ HEURISTIC categorization: category=other_question, call_type={call_type}, confidence=0.5 (HARDCODED)")
            return result

    async def _detect_objections_with_openai(self, transcript: str) -> List[Dict[str, Any]]:
        """Detect objections using OpenAI"""
        import requests

        if not self.openai_key:
            logger.warning("OpenAI API key not available, falling back to heuristic")
            return self._detect_objections_with_heuristic(transcript)

        prompt = f"""Analyze this call transcript and identify any objections, concerns, or misgivings expressed by the caller.

Return your response as JSON array with this structure:
{{
  "objections": [
    {{
      "type": "cost-value|timing|safety-risk|social-concerns|provider-trust|results-skepticism|other",
      "text": "Brief description of the objection",
      "speaker": "Customer name if identifiable",
      "confidence": 0.0-1.0,
      "segment": "Exact quote from transcript"
    }}
  ]
}}

Transcript:
{transcript[:4000]}
"""

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        body = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a sales call analysis expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            logger.debug(f"Calling OpenAI API with model {model_name} for objection detection")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            try:
                result = json.loads(content)
                objections = result.get("objections", [])
                logger.info(f"✅ OpenAI objection detection successful: found {len(objections)} objections")
                # Log confidence values from LLM
                for obj in objections:
                    logger.info(f"📊 OpenAI objection: type={obj.get('type')}, confidence={obj.get('confidence')}, raw_confidence_type={type(obj.get('confidence'))}")
                    print(f"📊 OpenAI objection: type={obj.get('type')}, confidence={obj.get('confidence')}")
                return objections
            except json.JSONDecodeError as json_error:
                logger.warning(f"Failed to parse OpenAI JSON response: {json_error}, content: {content[:200]}")
                # Fallback parsing
                import re
                json_match = re.search(r'\{"objections":\s*\[[^\]]+\]\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        return result.get("objections", [])
                    except json.JSONDecodeError:
                        pass
                return self._detect_objections_with_heuristic(transcript)
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}", exc_info=True)
            return self._detect_objections_with_heuristic(transcript)
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI objection detection: {e}", exc_info=True)
            return self._detect_objections_with_heuristic(transcript)

    async def _detect_objections_with_gemini(self, transcript: str) -> List[Dict[str, Any]]:
        """Detect objections using Gemini"""
        try:
            import google.generativeai as genai
            
            if not self.gemini_key:
                logger.warning("Gemini API key not found, falling back to heuristic")
                return self._detect_objections_with_heuristic(transcript)
            
            genai.configure(api_key=self.gemini_key)
            # Try different Gemini model names - the API version may require different names
            # Available models vary by API version and region:
            # - gemini-pro (most common, stable)
            # - gemini-1.5-pro (more capable, longer context)
            # - gemini-1.5-flash (faster, cheaper)
            # - gemini-1.0-pro (older version)
            # - gemini-2.0-flash (newer, if available)
            # - gemini-2.5-flash (newest, if available)
            model = None
            model_names = [
                'gemini-pro',           # Most widely available, stable
                'gemini-1.0-pro',       # Older but reliable
                'gemini-1.5-pro',       # More capable, longer context
                'gemini-1.5-flash',     # Faster, cheaper
                'gemini-2.0-flash',     # Newer version (if available)
                'gemini-2.5-flash',     # Newest version (if available)
            ]
            last_error = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Successfully initialized Gemini model: {model_name}")
                    break  # Success, exit the loop
                except Exception as e:
                    logger.debug(f"Failed to initialize Gemini model {model_name}: {e}")
                    last_error = e
                    continue
            
            if model is None:
                logger.error(f"❌ Failed to initialize any Gemini model. Tried: {model_names}. Last error: {last_error}")
                logger.error(f"❌ Available models may vary by API version. Check Google's documentation for your API key's supported models.")
                raise Exception(f"All Gemini models failed. Tried: {', '.join(model_names)}. Last error: {last_error}")
            
            prompt = f"""Analyze this call transcript and identify any objections, concerns, or misgivings expressed by the caller.

Return your response as JSON with this structure:
{{
  "objections": [
    {{
      "type": "cost-value|timing|safety-risk|social-concerns|provider-trust|results-skepticism|other",
      "text": "Brief description of the objection",
      "speaker": "Customer name if identifiable",
      "confidence": 0.0-1.0,
      "segment": "Exact quote from transcript"
    }}
  ]
}}

Transcript:
{transcript[:8000]}
"""
            
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "response_mime_type": "application/json"
                    }
                )
                
                try:
                    result = json.loads(response.text)
                    objections = result.get("objections", [])
                    logger.info(f"✅ Gemini objection detection successful: found {len(objections)} objections")
                    # Log confidence values from LLM
                    for obj in objections:
                        logger.info(f"📊 Gemini objection: type={obj.get('type')}, confidence={obj.get('confidence')}, raw_confidence_type={type(obj.get('confidence'))}")
                        print(f"📊 Gemini objection: type={obj.get('type')}, confidence={obj.get('confidence')}")
                    return objections
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{"objections":\s*\[[^\]]+\]\}', response.text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return result.get("objections", [])
                    logger.warning("Failed to parse Gemini JSON response, will raise to trigger OpenAI fallback")
                    raise Exception("Failed to parse Gemini JSON response")
            except Exception as gen_api_error:
                logger.error(f"❌ Gemini API call failed: {gen_api_error}")
                logger.info(f"🔄 This error will trigger fallback to OpenAI (if available)")
                raise  # Re-raise to trigger fallback in detect_objections
        except ImportError:
            logger.warning("google-generativeai package not installed. Install with: pip install google-generativeai")
            raise Exception("Gemini package not installed")  # Raise to trigger fallback
        except Exception as e:
            logger.error(f"❌ Error using Gemini API: {e}", exc_info=True)
            logger.info(f"🔄 This error will trigger fallback to OpenAI (if available)")
            raise  # Re-raise to trigger fallback in detect_objections

    def _detect_objections_with_heuristic(self, transcript: str) -> List[Dict[str, Any]]:
        """Simple heuristic-based objection detection (FALLBACK - not real LLM analysis)"""
        logger.warning(f"⚠️ Using HEURISTIC objection detection (not real LLM analysis) - this is a fallback method")
        print(f"⚠️ Using HEURISTIC objection detection (not real LLM analysis) - confidence values are hardcoded to 0.6")
        objections = []
        transcript_lower = transcript.lower()
        
        # Simple pattern matching
        objection_patterns = {
            "cost-value": ["expensive", "cost", "price", "afford", "budget"],
            "timing": ["not ready", "later", "think about it", "too soon"],
            "safety-risk": ["safe", "risk", "dangerous", "worried", "concerned"],
        }
        
        for obj_type, keywords in objection_patterns.items():
            matches = [kw for kw in keywords if kw in transcript_lower]
            if matches:
                objections.append({
                    "type": obj_type,
                    "text": f"Objection related to {obj_type}",
                    "confidence": 0.6,  # HARDCODED - this is a placeholder
                    "segment": "Heuristic detection"
                })
                logger.warning(f"⚠️ HEURISTIC objection detected: type={obj_type}, confidence=0.6 (HARDCODED)")
        
        return objections

    async def _analyze_overcome_with_openai(
        self,
        transcript: str,
        objections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze how objections were overcome using OpenAI"""
        import requests

        objections_text = "\n".join([
            f"- {obj['type']}: {obj['text']}" for obj in objections
        ])

        prompt = f"""For each objection listed below, identify how it was overcome in this transcript.
Provide the exact quote from the transcript that shows how the objection was addressed.

Return JSON with this structure:
{{
  "overcome_details": [
    {{
      "objection_type": "safety-risk|cost-value|timing|social-concerns|provider-trust|results-skepticism|other",
      "method": "Brief description of how it was overcome",
      "quote": "Exact quote from transcript",
      "speaker": "Speaker name if identifiable",
      "confidence": 0.0-1.0
    }}
  ]
}}

Objections:
{objections_text}

Transcript:
{transcript[:4000]}
"""

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": "You are a sales analysis expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        try:
            result = json.loads(content)
            return result.get("overcome_details", [])
        except json.JSONDecodeError:
            return []

    async def _analyze_overcome_with_gemini(
        self,
        transcript: str,
        objections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze objection overcome using Gemini"""
        try:
            import google.generativeai as genai
            
            if not self.gemini_key:
                logger.warning("Gemini API key not found")
                return []
            
            if not objections:
                return []
            
            genai.configure(api_key=self.gemini_key)
            # Try different Gemini model names - the API version may require different names
            # Available models vary by API version and region:
            # - gemini-pro (most common, stable)
            # - gemini-1.5-pro (more capable, longer context)
            # - gemini-1.5-flash (faster, cheaper)
            # - gemini-1.0-pro (older version)
            # - gemini-2.0-flash (newer, if available)
            # - gemini-2.5-flash (newest, if available)
            model = None
            model_names = [
                'gemini-pro',           # Most widely available, stable
                'gemini-1.0-pro',       # Older but reliable
                'gemini-1.5-pro',       # More capable, longer context
                'gemini-1.5-flash',     # Faster, cheaper
                'gemini-2.0-flash',     # Newer version (if available)
                'gemini-2.5-flash',     # Newest version (if available)
            ]
            last_error = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Successfully initialized Gemini model: {model_name}")
                    break  # Success, exit the loop
                except Exception as e:
                    logger.debug(f"Failed to initialize Gemini model {model_name}: {e}")
                    last_error = e
                    continue
            
            if model is None:
                logger.error(f"❌ Failed to initialize any Gemini model. Tried: {model_names}. Last error: {last_error}")
                logger.error(f"❌ Available models may vary by API version. Check Google's documentation for your API key's supported models.")
                raise Exception(f"All Gemini models failed. Tried: {', '.join(model_names)}. Last error: {last_error}")
            
            objections_text = "\n".join([
                f"- {obj.get('type', 'unknown')}: {obj.get('text', '')}" for obj in objections
            ])
            
            prompt = f"""For each objection listed below, identify how it was overcome in this transcript.
Provide the exact quote from the transcript that shows how the objection was addressed.

Return JSON with this structure:
{{
  "overcome_details": [
    {{
      "objection_type": "cost-value|timing|safety-risk|social-concerns|provider-trust|results-skepticism|other",
      "method": "Brief description of how it was overcome",
      "quote": "Exact quote from transcript",
      "speaker": "Speaker name if identifiable",
      "confidence": 0.0-1.0
    }}
  ]
}}

Objections:
{objections_text}

Transcript:
{transcript[:8000]}
"""
            
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "response_mime_type": "application/json"
                    }
                )
                
                try:
                    result = json.loads(response.text)
                    overcome_details = result.get("overcome_details", [])
                    logger.info(f"✅ Gemini objection overcome analysis successful: found {len(overcome_details)} overcome details")
                    return overcome_details
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{"overcome_details":\s*\[[^\]]+\]\}', response.text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return result.get("overcome_details", [])
                    logger.warning("Failed to parse Gemini JSON response, will raise to trigger OpenAI fallback")
                    raise Exception("Failed to parse Gemini JSON response")
            except Exception as gen_api_error:
                logger.error(f"❌ Gemini API call failed: {gen_api_error}")
                logger.info(f"🔄 This error will trigger fallback to OpenAI (if available)")
                raise  # Re-raise to trigger fallback in analyze_objection_overcome
        except ImportError:
            logger.warning("google-generativeai package not installed. Install with: pip install google-generativeai")
            raise Exception("Gemini package not installed")  # Raise to trigger fallback
        except Exception as e:
            logger.error(f"❌ Error using Gemini API: {e}", exc_info=True)
            logger.info(f"🔄 This error will trigger fallback to OpenAI (if available). Error details: {str(e)[:200]}")
            raise  # Re-raise to trigger fallback in analyze_objection_overcome

