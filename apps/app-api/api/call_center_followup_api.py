"""
Call Center Follow-up Plan API - Generate AI-powered 5-day multi-touchpoint follow-up plans
Specifically designed for call center bulk import module with response options and objection tracking
Generates 3 touchpoints to be delivered within the first 5 days post initial unsuccessful phone call
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging
import json
import time
import uuid
import re
from datetime import datetime, timedelta
from middleware.auth import get_current_user
from services.supabase_client import get_supabase_client
from services.elevenlabs_rvm_service import get_rvm_service
import asyncio

router = APIRouter(prefix="/api/call-center/followup", tags=["call-center-followup"])

logger = logging.getLogger(__name__)

# Analysis semaphore for rate limiting
_analysis_semaphore = asyncio.Semaphore(5)

def get_analysis_semaphore():
    """Get the analysis semaphore for rate limiting"""
    return _analysis_semaphore


def _extract_patient_name(transcript: str, customer_name: str = None) -> str:
    """Extract patient/customer name from transcript using heuristics and LLM if needed"""
    # First, try simple patterns
    # Pattern 1: "Hi [Name]" or "Hello [Name]"
    pattern1 = r'(?:hi|hello|hey)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    match1 = re.search(pattern1, transcript[:500], re.IGNORECASE)  # Check first 500 chars
    if match1:
        name = match1.group(1).strip()
        # Validate it's not a common word
        if name.lower() not in ['there', 'this', 'that', 'how', 'what', 'when', 'where']:
            return name
    
    # Pattern 2: "This is [Name]" or "My name is [Name]"
    pattern2 = r'(?:this\s+is|my\s+name\s+is|i\'?m|i\s+am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    match2 = re.search(pattern2, transcript[:500], re.IGNORECASE)
    if match2:
        name = match2.group(1).strip()
        if name.lower() not in ['there', 'this', 'that', 'how', 'what', 'when', 'where']:
            return name
    
    # Pattern 3: Look for speaker labels like "Speaker 1:" or "Customer:" followed by name
    pattern3 = r'(?:speaker\s+\d+|customer|patient|client):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    match3 = re.search(pattern3, transcript[:500], re.IGNORECASE)
    if match3:
        name = match3.group(1).strip()
        if name.lower() not in ['there', 'this', 'that', 'how', 'what', 'when', 'where']:
            return name
    
    # Pattern 4: Look for "Thanks [Name]" or "Thank you [Name]"
    pattern4 = r'(?:thanks|thank\s+you)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    match4 = re.search(pattern4, transcript[:500], re.IGNORECASE)
    if match4:
        name = match4.group(1).strip()
        if name.lower() not in ['there', 'this', 'that', 'how', 'what', 'when', 'where']:
            return name
    
    # Fallback: use customer_name if provided, otherwise generic
    if customer_name and customer_name.lower() not in ['customer', 'patient', 'client']:
        return customer_name.split()[0] if customer_name.split() else "there"
    
    return "there"  # Final fallback


def _analyze_with_openai(prompt: str) -> str:
    """Analyze text using OpenAI"""
    import requests
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OpenAI API key not found")
    
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates 14-day multi-touchpoint follow-up plans for call centers."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    resp = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _analyze_with_gemini(prompt: str) -> str:
    """Analyze text using Gemini"""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError("google-generativeai package not installed")
    
    gemini_key = (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        os.getenv("GOOGLE_SERVICES_API_KEY")
    )
    if not gemini_key:
        raise ValueError("Gemini API key not found")
    
    genai.configure(api_key=gemini_key)
    
    # Try to list available models first, then use them
    model_names = []
    try:
        # Try to get available models
        available_models = genai.list_models()
        model_names = [m.name.split('/')[-1] for m in available_models if 'generateContent' in m.supported_generation_methods]
        logger.info(f"Found {len(model_names)} available Gemini models: {model_names[:5]}")
    except Exception as e:
        logger.warning(f"Could not list available models: {e}, using fallback list")
    
    # Fallback to common model names if listing failed
    if not model_names:
        model_names = [
            'gemini-1.5-pro-latest',
            'gemini-1.5-flash-latest', 
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-pro',
            'gemini-1.0-pro'
        ]
    
    last_error = None
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.2}
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            last_error = e
            continue
    
    raise Exception(f"All Gemini models failed. Last error: {last_error}")


def _get_org_analysis_settings(supabase, user_id: str):
    """Get organization analysis settings to determine provider priority"""
    try:
        # Get user's organization
        user_result = supabase.from_('users').select('organization_id').eq('id', user_id).execute()
        if not user_result.data:
            # Default to Gemini, then OpenAI
            return ['gemini', 'openai'], ['gemini', 'openai']
        
        org_id = user_result.data[0].get('organization_id')
        if not org_id:
            return ['gemini', 'openai'], ['gemini', 'openai']
        
        # Get org settings
        settings_result = supabase.from_('organization_analysis_settings').select('*').eq('organization_id', org_id).execute()
        
        if settings_result.data:
            settings = settings_result.data[0]
            provider_order = settings.get('provider_priority', ['gemini', 'openai'])
            enabled_providers = settings.get('enabled_providers', ['gemini', 'openai'])
            return provider_order, enabled_providers
        
        # Default
        return ['gemini', 'openai'], ['gemini', 'openai']
    except Exception as e:
        logger.warning(f"Error getting org settings: {e}, using defaults")
        return ['gemini', 'openai'], ['gemini', 'openai']


class GenerateCallCenterFollowUpPlanPayload(BaseModel):
    callRecordId: str
    transcript: str
    analysisData: Dict[str, Any]
    customerName: str
    salespersonName: str
    provider: Optional[str] = None  # 'auto', 'gemini', or 'openai'


class GenerateRVMAudioPayload(BaseModel):
    message_id: str
    salesperson_name: str
    contact_number: str


def _build_followup_prompt(
    transcript: str,
    analysis_data: Dict[str, Any],
    customer_name: str,
    salesperson_name: str,
    call_category: Optional[str] = None,
    call_type: Optional[str] = None
) -> str:
    """Build the prompt for generating a 5-day multi-touchpoint follow-up plan"""
    
    # Extract patient name from transcript
    patient_name = _extract_patient_name(transcript, customer_name)
    
    # Extract key insights from analysis
    sentiment = analysis_data.get('sentiment', {})
    urgency = analysis_data.get('urgencyScoring', {})
    personality = analysis_data.get('customerPersonality', {})
    objections = analysis_data.get('objections', [])
    objection_overcomes = analysis_data.get('objection_overcomes', [])
    
    # Get call classification (from analysis_data or parameters)
    call_category = call_category or analysis_data.get('category')
    call_type = call_type or analysis_data.get('call_type')
    
    # Build call type context for personalized messaging
    call_type_context = ""
    if call_type:
        call_type_descriptions = {
            'scheduling': 'The call was primarily about scheduling a new appointment',
            'pricing': 'The call was about pricing, costs, or payment options',
            'directions': 'The call was asking for directions or location information',
            'billing': 'The call was about billing issues, invoices, or payment problems',
            'complaint': 'The call expressed a complaint or dissatisfaction',
            'transfer_to_office': 'The call requested to be transferred to an office/department',
            'general_question': 'The call was a general inquiry or question',
            'reschedule': 'The call was to reschedule an existing appointment',
            'confirming_existing_appointment': 'The call was to confirm an existing appointment',
            'cancellation': 'The call was to cancel an appointment or service'
        }
        call_type_desc = call_type_descriptions.get(call_type, f'The call type was: {call_type}')
        call_type_context = f"\n\nCALL TYPE CONTEXT:\n- Call Type: {call_type.replace('_', ' ').title()}\n- Description: {call_type_desc}\n- Use this context to tailor the follow-up messaging. For example:\n  * If call_type is 'pricing', focus on value propositions and payment options\n  * If call_type is 'reschedule', acknowledge the scheduling change and offer flexibility\n  * If call_type is 'complaint', prioritize addressing concerns and rebuilding trust\n  * If call_type is 'billing', focus on resolving payment issues and providing clarity\n"
    
    # Filter unresolved objections (those without overcomes)
    resolved_objection_ids = {oc.get('objection_id') for oc in objection_overcomes if oc.get('objection_id')}
    unresolved_objections = [
        obj for obj in objections 
        if obj.get('id') not in resolved_objection_ids
    ]
    
    # Sort unresolved objections by confidence score (descending) - highest priority first
    unresolved_objections.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # Build objection context with priority order
    objection_context = ""
    if unresolved_objections:
        objection_context = "\n\nUNRESOLVED OBJECTIONS (MUST ADDRESS IN FOLLOW-UP - SORTED BY PRIORITY/IMPORTANCE):\n"
        for i, obj in enumerate(unresolved_objections, 1):
            objection_context += f"{i}. Type: {obj.get('objection_type', 'unknown')}\n"
            objection_context += f"   Text: {obj.get('objection_text', 'N/A')}\n"
            if obj.get('transcript_segment'):
                objection_context += f"   Quote: \"{obj.get('transcript_segment')}\"\n"
            objection_context += f"   Confidence/Priority Score: {obj.get('confidence', 0)} (HIGHER = MORE IMPORTANT)\n\n"
    
    prompt = f"""
You are an expert sales strategist specializing in healthcare consumer psychology and follow-up optimization. 
Generate a focused, multi-touchpoint 5-day follow-up plan based on this call analysis.
Generate exactly 3 touchpoints to be delivered within the first 5 days post initial unsuccessful phone call.

CRITICAL FOR RVM MESSAGES:
- RVM scripts MUST focus on a single unresolved objection — choose the highest priority unresolved objection and center the script on resolving it
- Mine the transcript for signals about what resonated with the prospect (e.g., benefits they reacted positively to, reassurances that lowered tension) and weave those cues into the script
- Mirror the salesperson's personality and tone from the call so the RVM feels like a natural continuation of their conversation
- Use an appropriate overall tone that matches the prospect's personality type: {personality.get('personalityType', 'unknown')}
- Include specific details and quotes from the transcript to show you listened
- Make it conversational and natural (30-60 seconds when read aloud)
- MUST include placeholders [SALESPERSON_NAME] and [CONTACT_NUMBER] for later insertion

CRITICAL CONSTRAINTS:
- ONLY SMS and RVM (Ringless Voicemail) channels are permitted. EMAIL IS NOT ALLOWED.
- The patient name "{patient_name}" MUST be used in every message/script
- All messages must directly address the unresolved objections listed below
- Reference specific conversation details and quotes from the transcript

CALL ANALYSIS SUMMARY:
- Patient Name (extracted from transcript): {patient_name}
- Customer/Project: {customer_name}
- Salesperson: {salesperson_name}
- Call Status: {call_category or 'unknown'} ({'✅ Appointment Scheduled' if call_category == 'consult_scheduled' else '❌ Appointment Not Scheduled' if call_category == 'consult_not_scheduled' else '❓ Other Question'})
- Call Type: {call_type or 'not specified'} (What the call was about)
- Overall Sentiment: {sentiment.get('overall', 'neutral')}
- Customer Engagement: {sentiment.get('customerEngagement', 5)}/10
- Urgency Level: {urgency.get('overallUrgency', 5)}/10
- Personality Type: {personality.get('personalityType', 'unknown')}
- Total Objections Raised: {len(objections)}
- Unresolved Objections: {len(unresolved_objections)}
{call_type_context}
{objection_context}
FULL TRANSCRIPT:
{transcript}

Generate a JSON follow-up plan with this EXACT structure (designed for a 5-day cadence with exactly 3 touchpoints):

{{
  "strategy_type": "sms-rvm|multi-channel",
  "recommended_timing": "immediate|24_hours|3_days|1_week",
  "priority_score": 8,
  "customer_urgency": "high|medium|low",
  "next_action": "Specific next action to take",
  "reasoning": "Why this strategy fits this customer's psychology and situation",
  "compliance_notes": "Any compliance considerations (HIPAA, consent, etc.)",
  "messages": [
    {{
      "channel_type": "sms",
      "message_content": "Day 1 SMS text using patient name '{patient_name}' and addressing highest priority objection. MUST end with a question and response options (1, 2, 3 - no more than 3 options).",
      "response_options": [
        {{"option": 1, "text": "Option 1 text that patient can reply with"}},
        {{"option": 2, "text": "Option 2 text that patient can reply with"}},
        {{"option": 3, "text": "Option 3 text that patient can reply with"}}
      ],
      "targeted_objection_id": "ID of the objection this message addresses (from unresolved list)",
      "estimated_send_time": "+1 day",
      "tone": "warm",
      "call_to_action": "Soft check-in CTA with question",
      "personalization_notes": "Why personalized, which objection addressed",
      "status": "draft"
    }},
    {{
      "channel_type": "rvm",
      "rvm_script": "Hi {patient_name}, this is [SALESPERSON_NAME] from [COMPANY]. I wanted to follow up on our conversation about [TOPIC]. I understand you had concerns about [OBJECTION]. I'd like to address that and share some information that might help. [PERSONALIZED_CONTENT_ADDRESSING_OBJECTION]. If you have any questions or would like to schedule a consultation, please call me back at [CONTACT_NUMBER]. You can also reply to this message with 1 for Yes, 2 for Maybe, or 3 for Call me. Looking forward to hearing from you!",
      "response_options": [
        {{"option": 1, "text": "Yes, interested"}},
        {{"option": 2, "text": "Maybe, need more info"}},
        {{"option": 3, "text": "Call me"}}
      ],
      "targeted_objection_id": "ID of the objection this message addresses",
      "estimated_send_time": "+2 days",
      "tone": "supportive",
      "call_to_action": "Address objection CTA with question",
      "personalization_notes": "Why personalized, which objection addressed",
      "status": "draft",
      "salesperson_name_placeholder": "[SALESPERSON_NAME]",
      "contact_number_placeholder": "[CONTACT_NUMBER]"
    }}
    {{
      "channel_type": "sms",
      "message_content": "Day 5 SMS text using patient name '{patient_name}' and addressing final objection or strong CTA. MUST end with a question and response options (1, 2, 3 - no more than 3 options).",
      "response_options": [
        {{"option": 1, "text": "Option 1 text"}},
        {{"option": 2, "text": "Option 2 text"}},
        {{"option": 3, "text": "Option 3 text"}}
      ],
      "targeted_objection_id": "ID of the objection this message addresses",
      "estimated_send_time": "+5 days",
      "tone": "direct",
      "call_to_action": "Strong final CTA with question",
      "personalization_notes": "Why personalized, which objection addressed",
      "status": "draft"
    }}
  ],
  "drip_campaign_template": {{
    "description": "After initial 5-day plan (if no appointment scheduled), transition to ongoing 5-day drip campaign cycles",
    "frequency": "Every 5 days (cyclical)",
    "message_mix": [
      "General patient engagement messages (60%)",
      "Periodic objection reminders in descending order of objection score (40%)"
    ],
    "objection_reminder_schedule": "Mention objections in order of priority score (highest first), rotating through them",
    "plan_structure": "Each drip campaign cycle consists of exactly 3 touchpoints over 5 days (same structure as initial plan)"
  }}
}}

IMPORTANT: The "messages" array MUST contain EXACTLY 3 message objects. All messages must be delivered within the first 5 days.

REQUIREMENTS:
1. **MANDATORY: Generate EXACTLY 3 messages** spread across the first 5 days. This is a focused, short-term sequence.
2. **MANDATORY: Each message must have a different estimated_send_time** - distribute across days 1, 3, 5 (or similar 5-day spread like 1, 2, 5 or 2, 3, 5)
3. **MANDATORY: Mix of SMS and RVM** - Use a good mix (e.g., 2 SMS and 1 RVM, or 1 SMS and 2 RVM)
4. **MANDATORY: Response Options** - EVERY message MUST include response options (1, 2, 3 - NO MORE THAN 3 OPTIONS) that the patient can easily reply with. Structure the message as: [Information/Value] + [Question] + "Reply 1 for [option], 2 for [option], 3 for [option]"
5. **MANDATORY: Progressive Objection Addressing** - Address unresolved objections in descending order of confidence/priority score. Message 1 addresses the highest priority objection, Message 2 addresses the next highest, etc. As you progress, focus on remaining unresolved objections.
6. **MANDATORY: Track Addressed Objections** - Each message must specify which objection it targets via "targeted_objection_id". Don't repeat the same objection in multiple messages unless it's a follow-up.
7. ONLY use SMS and RVM channels - NO EMAIL ALLOWED
8. EVERY message/script MUST include the patient name "{patient_name}"
9. EVERY message/script MUST address at least one unresolved objection from the list above (in priority order)
10. Reference specific quotes and conversation details from the transcript
11. Messages should progress in urgency and personalization - start softer, build to stronger CTAs
12. Each message should build on the previous one - create a narrative arc that moves toward scheduling
13. Response options should be easy to understand and reply to (e.g., "1 for Yes, 2 for Maybe, 3 for Call me" - maximum 3 options)
14. Personalize based on customer personality, urgency, and objections
15. Include compliance notes for healthcare context (HIPAA, consent, etc.)
16. Ensure CTAs are specific and actionable, getting stronger as the sequence progresses
17. RVM scripts MUST:
    - Be conversational, natural, and address concerns directly (30-60 seconds when read aloud)
    - Mirror the salesperson's tone, pace, and personality so the message sounds like them
    - Focus on resolving exactly one unresolved objection — always the highest priority unresolved objection available
    - Include placeholders [SALESPERSON_NAME] and [CONTACT_NUMBER] where the salesperson's name and phone number should be inserted
    - Mention response options clearly (1, 2, 3 - no more than 3 options)
    - Reference specific conversation details and quotes from the transcript, especially the parts that resonated with the prospect
    - Personalize based on the patient's objection context, concerns, and demonstrated preferences during the call
18. SMS messages should be concise but personalized (under 160 characters when possible, but can exceed if needed for response options)
19. The goal is to elicit patient responses that will be captured by the system and used to recompute subsequent touchpoints
20. Focus on the highest priority objections in these 3 messages - address the most important unresolved objections first
21. After the initial 5-day plan, if no appointment is scheduled, the system will transition to ongoing 5-day drip campaign cycles (see drip_campaign_template structure above)
22. Return ONLY valid JSON, no markdown or code fences
23. Return the JSON object directly at the root level (not wrapped in another key)

CRITICAL: 
- You MUST generate EXACTLY 3 messages in the "messages" array. This is not optional.
- Each message must have a unique estimated_send_time spread across the first 5 days (e.g., days 1, 3, 5 or 1, 2, 5)
- ALL messages must be delivered within 5 days of the initial call
- EVERY message MUST include response options (1, 2, 3 - NO MORE THAN 3 OPTIONS) that patients can easily reply with
- Address objections in descending order of confidence/priority score (highest first)
- Each message should target a different objection (use "targeted_objection_id" field)
- Focus on the top 3 highest priority unresolved objections
- Return the JSON object with the exact structure shown above. Do NOT wrap it in another object like {{"follow_up_plan": ...}}. Return the JSON directly.
- Every message MUST use the patient name "{patient_name}"
- Every message MUST reference unresolved objections and conversation context
- The goal is to get the patient to respond (via options 1-3, maximum 3 options) and schedule an appointment - design the sequence to achieve this outcome
- Patient responses will be captured by the system and used to recompute subsequent touchpoints dynamically

EXAMPLE STRUCTURE (you must generate exactly 3 messages with response options):
- Day 1: Soft SMS check-in addressing highest priority objection + question with options 1-3 (max 3 options)
- Day 3: RVM addressing second highest priority objection + question with options 1-3 (max 3 options)
- Day 5: Final SMS with strong CTA addressing third priority objection or value proposition + question with options 1-3 (max 3 options)

OBJECTION PRIORITY ORDER (use this order - highest confidence first):
{chr(10).join([f"- Objection {i+1}: {obj.get('objection_type', 'unknown')} (confidence: {obj.get('confidence', 0)})" for i, obj in enumerate(unresolved_objections[:10])])}

Return the complete JSON object with exactly 3 messages now:
"""
    return prompt


def _parse_followup_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response and extract follow-up plan JSON"""
    # Strip code fences if present
    cleaned = response_text.strip()
    if cleaned.startswith('```'):
        # Remove markdown code fences
        lines = cleaned.split('\n')
        # Find first line with {
        start_idx = 0
        for i, line in enumerate(lines):
            if '{' in line:
                start_idx = i
                # Remove the ```json or ``` from this line
                lines[i] = line.split('```')[-1].strip()
                break
        # Find last line with }
        end_idx = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if '}' in lines[i]:
                end_idx = i
                # Remove ``` from this line
                lines[i] = lines[i].split('```')[0].strip()
                break
        cleaned = '\n'.join(lines[start_idx:end_idx + 1])
    
    # Try to extract JSON between first { and last }
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    
    try:
        parsed = json.loads(cleaned)
        # Handle nested response structure (e.g., {"follow_up_plan": {...}})
        if 'follow_up_plan' in parsed and isinstance(parsed['follow_up_plan'], dict):
            logger.info("🔍 DEBUG: Found nested 'follow_up_plan' key, extracting inner structure")
            return parsed['follow_up_plan']
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse follow-up plan JSON: {e}")
        logger.error(f"Response text: {response_text[:500]}")
        raise ValueError(f"Invalid JSON response from LLM: {str(e)}")


def _calculate_send_time(timing: str, base_time: datetime, day_offset: int = 0) -> datetime:
    """Calculate actual send time from timing string"""
    if timing == 'immediate':
        return base_time + timedelta(hours=1)
    elif timing == '24_hours':
        return base_time + timedelta(days=1 + day_offset)
    elif timing == '3_days':
        return base_time + timedelta(days=3 + day_offset)
    elif timing == '1_week':
        return base_time + timedelta(days=7 + day_offset)
    else:
        # Default to 1 day
        return base_time + timedelta(days=1 + day_offset)


@router.post("/generate-rvm-audio", response_model=dict)
async def generate_rvm_audio(
    payload: GenerateRVMAudioPayload,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate RVM audio for a specific follow-up message using ElevenLabs.
    
    Args:
        payload: Contains message_id, salesperson_name, and contact_number
    
    Returns:
        Dict with audio_url, audio_id, and metadata
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        
        # Fetch the message
        message_result = supabase.from_('follow_up_messages').select('*').eq('id', payload.message_id).eq('user_id', user_id).execute()
        
        if not message_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        message = message_result.data[0]
        message_data = message.get('message_data', {})
        
        if message_data.get('channel_type', '').lower() != 'rvm':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is not an RVM message"
            )
        
        script = message_data.get('rvm_script', '')
        if not script:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RVM script not found in message"
            )
        
        # Generate audio using ElevenLabs service (now with real API integration)
        rvm_service = get_rvm_service()
        audio_result = rvm_service.generate_rvm_audio(
            script=script,
            salesperson_name=payload.salesperson_name,
            contact_number=payload.contact_number
        )
        
        # Note: audio_result now contains:
        # - audio_id: unique ID for the audio
        # - file_path: local path where audio is saved
        # - audio_bytes: raw audio bytes
        # - audio_url: None (can be set after uploading to storage)
        # - duration_seconds: estimated duration
        # - metadata: additional metadata
        
        # Update message with audio file path and metadata
        # TODO: Upload audio file to Supabase Storage or S3 and get a public URL
        # For now, store the file_path and audio_id
        audio_url = audio_result.get('audio_url')  # May be None if not uploaded to storage yet
        file_path = audio_result.get('file_path')  # Local file path
        
        try:
            update_data = {
                'rvm_audio_id': audio_result['audio_id'],
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Add audio URL if available (from storage upload)
            if audio_url:
                update_data['rvm_audio_url'] = audio_url
            elif file_path:
                # Store file path for now (can be uploaded to storage later)
                update_data['rvm_audio_file_path'] = file_path
                logger.info(f"📁 Audio saved to: {file_path}")
            
            supabase.from_('follow_up_messages').update(update_data).eq('id', payload.message_id).execute()
            logger.info(f"✅ Updated message {payload.message_id} with audio ID: {audio_result['audio_id']}")
        except Exception as update_error:
            logger.warning(f"⚠️ Failed to update message with audio info: {update_error}")
            # Continue even if update fails
        
        return {
            'success': True,
            'audio_id': audio_result['audio_id'],
            'audio_url': audio_url,  # May be None if not uploaded to storage
            'file_path': file_path,  # Local file path
            'duration_seconds': audio_result['duration_seconds'],
            'metadata': audio_result['metadata']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate RVM audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate RVM audio: {str(e)}"
        )


@router.post("/generate", response_model=dict)
async def generate_call_center_followup_plan(
    payload: GenerateCallCenterFollowUpPlanPayload,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a 5-day multi-touchpoint follow-up plan from call transcript and analysis data.
    Specifically designed for call center bulk import module with:
    - Exactly 3 messages with response options (1, 2, 3 - maximum 3 options)
    - All messages delivered within the first 5 days post initial unsuccessful call
    - Progressive objection addressing in priority order
    - SMS and RVM only (no email)
    - Patient name extraction and usage
    
    Saves to follow_up_plans and follow_up_messages tables.
    """
    if not payload.transcript or not payload.analysisData:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript and analysis data are required"
        )
    
    # Rate limiting: acquire semaphore
    async with get_analysis_semaphore():
        logger.info(f"Generating call center follow-up plan for call {payload.callRecordId}")
        
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        
        # Fetch call_record to get call_category and call_type if not in analysisData
        call_record_result = supabase.table("call_records").select("call_category,call_type").eq("id", payload.callRecordId).maybe_single().execute()
        call_category = None
        call_type = None
        if call_record_result.data:
            call_category = call_record_result.data.get("call_category")
            call_type = call_record_result.data.get("call_type")
        
        # Build prompt with call classification context
        prompt = _build_followup_prompt(
            payload.transcript,
            payload.analysisData,
            payload.customerName,
            payload.salespersonName,
            call_category=call_category,
            call_type=call_type
        )
        
        # Get provider settings
        provider_order, enabled_providers = _get_org_analysis_settings(supabase, user_id)
        
        # Determine which provider to use
        use_provider = payload.provider
        if use_provider == 'auto':
            use_provider = None  # Let it try providers in order
        
        if use_provider and use_provider in enabled_providers:
            provider_order = [use_provider] + [p for p in provider_order if p != use_provider]
        
        # Try each provider
        last_error = None
        response_text = None
        used_provider = None
        
        for provider in provider_order:
            try:
                logger.info(f"Attempting call center follow-up plan generation with {provider}")
                start_time = time.time()
                
                if provider == "openai":
                    response_text = _analyze_with_openai(prompt)
                    used_provider = "openai"
                elif provider == "gemini":
                    response_text = _analyze_with_gemini(prompt)
                    used_provider = "gemini"
                else:
                    continue
                
                generation_time = int((time.time() - start_time) * 1000)
                logger.info(f"Call center follow-up plan generated with {used_provider} in {generation_time}ms")
                break
                
            except Exception as e:
                logger.error(f"{provider} failed: {e}")
                last_error = e
                continue
        
        if not response_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"All providers failed. Last error: {str(last_error)}"
            )
        
        # Parse response
        try:
            plan_data = _parse_followup_response(response_text)
            logger.info(f"🔍 DEBUG: Parsed plan_data keys: {list(plan_data.keys())}")
            
            # Handle nested response structure (e.g., {"follow_up_plan": {...}})
            if 'follow_up_plan' in plan_data and isinstance(plan_data['follow_up_plan'], dict):
                logger.info("🔍 DEBUG: Found nested 'follow_up_plan' key, extracting inner structure")
                plan_data = plan_data['follow_up_plan']
            
            # Extract patient name for validation
            patient_name = _extract_patient_name(payload.transcript, payload.customerName)
            
            # Re-extract unresolved objections for validation (same logic as in prompt building)
            analysis_data = payload.analysisData or {}
            objections = analysis_data.get('objections', [])
            objection_overcomes = analysis_data.get('objection_overcomes', [])
            resolved_objection_ids = {oc.get('objection_id') for oc in objection_overcomes if oc.get('objection_id')}
            unresolved_objections = [
                obj for obj in objections 
                if obj.get('id') not in resolved_objection_ids
            ]
            unresolved_objections.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Validate plan structure
            messages = plan_data.get('messages', [])
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    messages[i] = None
                    continue
                    
                channel = msg.get('channel_type', '').lower()
                # Reject email channels
                if 'email' in channel:
                    logger.warning(f"⚠️ Message {i+1} has email channel, removing it")
                    messages[i] = None
                    continue
                # Ensure only SMS or RVM
                if channel not in ['sms', 'rvm']:
                    logger.warning(f"⚠️ Message {i+1} has invalid channel '{channel}', changing to SMS")
                    msg['channel_type'] = 'sms'
                
                # Validate patient name is in message/script
                content = msg.get('message_content', '') or msg.get('rvm_script', '')
                if patient_name.lower() not in content.lower() and patient_name.lower() != 'there':
                    logger.warning(f"⚠️ Message {i+1} missing patient name '{patient_name}', adding it")
                    if msg.get('channel_type') == 'rvm':
                        script = msg.get('rvm_script', '')
                        msg['rvm_script'] = f"Hi {patient_name}, {script}" if not script.startswith(patient_name) else script
                    else:
                        sms = msg.get('message_content', '')
                        msg['message_content'] = f"Hi {patient_name}, {sms}" if not sms.startswith(patient_name) else sms
                
                # For RVM messages, ensure placeholders are present
                if msg.get('channel_type') == 'rvm':
                    script = msg.get('rvm_script', '')
                    if '[SALESPERSON_NAME]' not in script and '[CONTACT_NUMBER]' not in script:
                        logger.warning(f"⚠️ RVM message {i+1} missing placeholders, adding them")
                        # Add placeholders if missing
                        if '[SALESPERSON_NAME]' not in script:
                            script = script.replace('this is', 'this is [SALESPERSON_NAME]', 1) if 'this is' in script.lower() else f"[SALESPERSON_NAME] - {script}"
                        if '[CONTACT_NUMBER]' not in script:
                            script = f"{script} Please call me back at [CONTACT_NUMBER]."
                        msg['rvm_script'] = script
                
                # Validate response options exist (max 3 options)
                response_options = msg.get('response_options', [])
                if len(response_options) > 3:
                    logger.warning(f"⚠️ Message {i+1} has {len(response_options)} response options (max 3 allowed), truncating to first 3")
                    msg['response_options'] = response_options[:3]
                    response_options = msg['response_options']
                
                if not response_options or len(response_options) < 1:
                    logger.warning(f"⚠️ Message {i+1} missing response_options, adding default options (max 3)")
                    msg['response_options'] = [
                        {"option": 1, "text": "Yes, interested"},
                        {"option": 2, "text": "Maybe, need more info"},
                        {"option": 3, "text": "Call me"}
                    ]
                    # Also add response options to the message content if not present
                    content = msg.get('message_content', '') or msg.get('rvm_script', '')
                    if 'reply 1' not in content.lower() and 'option 1' not in content.lower():
                        options_text = "Reply 1 for Yes, 2 for Maybe, 3 for Call me"
                        if msg.get('channel_type') == 'rvm':
                            msg['rvm_script'] = f"{content} {options_text}"
                        else:
                            msg['message_content'] = f"{content} {options_text}"
                
                # Ensure targeted_objection_id is set if we have objections
                if not msg.get('targeted_objection_id') and unresolved_objections:
                    # Assign the first unassigned objection
                    assigned_objection_ids = {m.get('targeted_objection_id') for m in messages[:i] if m and isinstance(m, dict)}
                    for obj in unresolved_objections:
                        if obj.get('id') not in assigned_objection_ids:
                            msg['targeted_objection_id'] = obj.get('id')
                            break
            
            # Remove None messages
            plan_data['messages'] = [m for m in messages if m is not None]
            
            logger.info(f"🔍 DEBUG: plan_data structure - has 'messages' key: {'messages' in plan_data}")
            messages_list = plan_data.get('messages', [])
            logger.info(f"🔍 DEBUG: Number of messages in plan_data: {len(messages_list)}")
            
            # Validate we have exactly 3 messages
            if len(messages_list) != 3:
                logger.warning(f"⚠️ Expected exactly 3 messages, but got {len(messages_list)}. This may not meet the 5-day plan requirements.")
                if len(messages_list) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="LLM failed to generate any messages. Please try again."
                    )
                if len(messages_list) < 3:
                    logger.warning(f"⚠️ Only {len(messages_list)} messages generated, expected exactly 3 for the 5-day plan.")
                if len(messages_list) > 3:
                    logger.warning(f"⚠️ {len(messages_list)} messages generated, expected exactly 3. Using first 3 messages.")
                    messages_list = messages_list[:3]
                    plan_data['messages'] = messages_list
            
            if messages_list:
                logger.info(f"🔍 DEBUG: First message keys: {list(messages_list[0].keys()) if isinstance(messages_list[0], dict) else 'Not a dict'}")
                # Log message distribution
                sms_count = sum(1 for m in messages_list if m.get('channel_type', '').lower() == 'sms')
                rvm_count = sum(1 for m in messages_list if m.get('channel_type', '').lower() == 'rvm')
                logger.info(f"🔍 DEBUG: Message distribution - SMS: {sms_count}, RVM: {rvm_count}, Total: {len(messages_list)}")
            else:
                logger.warning(f"🔍 DEBUG: Messages array exists but is EMPTY")
        except ValueError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Response text (first 1000 chars): {response_text[:1000]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse LLM response: {str(e)}"
            )
        
        # Save to database
        try:
            # Delete existing plan for this call (if any)
            existing_plan = supabase.from_('follow_up_plans').select('id').eq('call_record_id', payload.callRecordId).eq('user_id', user_id).execute()
            
            if existing_plan.data:
                plan_id = existing_plan.data[0]['id']
                # Delete associated messages
                supabase.from_('follow_up_messages').delete().eq('follow_up_plan_id', plan_id).execute()
                # Delete plan
                supabase.from_('follow_up_plans').delete().eq('id', plan_id).execute()
            
            # Create new plan
            plan_id = str(uuid.uuid4())
            base_time = datetime.utcnow()
            
            # Build plan record
            if not plan_data:
                raise ValueError("plan_data is required but was empty")
            
            if not isinstance(plan_data, dict):
                raise ValueError(f"plan_data must be a dict, got {type(plan_data)}")
            
            plan_record = {
                'id': plan_id,
                'call_record_id': payload.callRecordId,
                'user_id': user_id,
                'status': 'active',
                'plan_data': plan_data,
                'created_at': base_time.isoformat() + 'Z',
                'updated_at': base_time.isoformat() + 'Z'
            }
            
            # Add optional fields
            optional_fields = {
                'strategy_type': plan_data.get('strategy_type', 'sms-rvm'),
                'recommended_timing': plan_data.get('recommended_timing', '24_hours'),
                'priority_score': plan_data.get('priority_score', 5),
                'next_action': plan_data.get('next_action', 'Follow up with patient'),
                'reasoning': plan_data.get('reasoning', ''),
                'customer_urgency': plan_data.get('customer_urgency', 'medium'),
                'customer_name': payload.customerName,
                'salesperson_name': payload.salespersonName,
                'compliance_notes': plan_data.get('compliance_notes'),
            }
            
            for key, value in optional_fields.items():
                if value is not None:
                    plan_record[key] = value
            
            # Try to insert, with retry logic that removes missing columns
            max_retries = 10
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    if 'plan_data' not in plan_record or plan_record['plan_data'] is None:
                        raise ValueError("plan_data was removed or is None - this should never happen")
                    
                    supabase.from_('follow_up_plans').insert(plan_record).execute()
                    logger.info(f"✅ Successfully saved call center follow-up plan {plan_id} with {len(plan_record)} fields: {list(plan_record.keys())}")
                    break
                except Exception as insert_error:
                    error_str = str(insert_error)
                    error_msg = error_str.lower()
                    
                    if 'pgrst204' in error_msg or 'could not find' in error_msg:
                        missing_column = None
                        quoted_col_match = re.search(r"['\"]([^'\"]+)['\"]", error_str)
                        if quoted_col_match:
                            potential_col = quoted_col_match.group(1)
                            if potential_col in plan_record:
                                missing_column = potential_col
                        
                        if not missing_column:
                            protected_columns = ['id', 'call_record_id', 'user_id', 'status', 'created_at', 'updated_at', 'plan_data']
                            for col_name in list(plan_record.keys()):
                                if (f"'{col_name}'" in error_str or f'"{col_name}"' in error_str or col_name in error_msg) and col_name not in protected_columns:
                                    missing_column = col_name
                                    break
                        
                        if missing_column and retry_count < max_retries:
                            logger.warning(f"⚠️ Column '{missing_column}' doesn't exist, removing it (attempt {retry_count + 1}/{max_retries})")
                            plan_record.pop(missing_column, None)
                            retry_count += 1
                            continue
                        else:
                            logger.error(f"❌ Save failed after {retry_count} retries: {insert_error}")
                            raise
                    else:
                        logger.error(f"❌ Save failed with non-column error: {insert_error}")
                        raise
            
            if retry_count > max_retries:
                raise Exception(f"Failed to save follow-up plan after {max_retries} retries")
            
            # Create messages
            messages = plan_data.get('messages', [])
            logger.info(f"🔍 DEBUG: Extracted messages from plan_data: {len(messages)} messages")
            
            if not messages:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="LLM failed to generate any messages for the 5-day follow-up plan. Please try again."
                )
            
            if len(messages) != 3:
                logger.warning(f"⚠️ Expected exactly 3 messages, got {len(messages)}. This may not meet the 5-day plan requirements.")
                if len(messages) > 3:
                    logger.warning(f"⚠️ Truncating to first 3 messages.")
                    messages = messages[:3]
            
            logger.info(f"🔍 DEBUG: Using {len(messages)} message(s) from LLM response")
            
            message_records = []
            for idx, msg in enumerate(messages):
                # Calculate send time
                timing_str = msg.get('estimated_send_time', plan_data.get('recommended_timing', '24_hours'))
                if isinstance(timing_str, str) and timing_str.startswith('+'):
                    days = int(timing_str.split()[0][1:]) if timing_str.split()[0][1:].isdigit() else 1
                    send_time = base_time + timedelta(days=days + idx)
                elif 'T' in timing_str or timing_str.endswith('Z'):
                    try:
                        send_time = datetime.fromisoformat(timing_str.replace('Z', '+00:00'))
                    except:
                        send_time = _calculate_send_time(plan_data.get('recommended_timing', '24_hours'), base_time, idx)
                else:
                    send_time = _calculate_send_time(timing_str, base_time, idx)
                
                # Store full message data in JSONB
                channel_type = msg.get('channel_type', 'sms')
                message_type = channel_type
                message_content = msg.get('message_content', '')
                rvm_script = msg.get('rvm_script', '')
                response_options = msg.get('response_options', [])
                targeted_objection_id = msg.get('targeted_objection_id')
                
                message_record = {
                    'id': str(uuid.uuid4()),
                    'follow_up_plan_id': plan_id,
                    'user_id': user_id,
                    'message_data': msg,  # Store full message data as JSONB
                    'message_type': message_type,
                    'status': msg.get('status', 'draft'),
                    'created_at': base_time.isoformat() + 'Z',
                    'updated_at': base_time.isoformat() + 'Z'
                }
                
                if message_content:
                    message_record['content'] = message_content
                    message_record['message_content'] = message_content
                
                message_records.append(message_record)
            
            # Insert messages
            if message_records:
                try:
                    supabase.from_('follow_up_messages').insert(message_records).execute()
                    logger.info(f"Successfully saved {len(message_records)} call center follow-up messages")
                except Exception as msg_error:
                    error_str = str(msg_error)
                    error_msg = error_str.lower()
                    
                    if 'pgrst204' in error_msg or 'could not find' in error_msg:
                        if 'message_data' in error_str:
                            logger.warning(f"⚠️ message_data column doesn't exist, trying with minimal fields")
                            minimal_messages = []
                            for msg_record in message_records:
                                msg_data = msg_record.get('message_data', {})
                                content = msg_data.get('message_content', '') if isinstance(msg_data, dict) else ''
                                
                                minimal_msg = {
                                    'id': msg_record['id'],
                                    'follow_up_plan_id': msg_record['follow_up_plan_id'],
                                    'user_id': msg_record['user_id'],
                                    'message_type': msg_record.get('message_type', 'sms'),
                                    'status': msg_record['status'],
                                    'created_at': msg_record['created_at'],
                                    'updated_at': msg_record['updated_at']
                                }
                                
                                if content:
                                    minimal_msg['content'] = content
                                
                                minimal_messages.append(minimal_msg)
                            
                            try:
                                supabase.from_('follow_up_messages').insert(minimal_messages).execute()
                                logger.warning(f"⚠️ Saved {len(minimal_messages)} messages with minimal fields")
                            except Exception as fallback_error:
                                logger.error(f"❌ Failed to save messages even with minimal fields: {fallback_error}")
                        else:
                            logger.error(f"❌ Failed to save messages: {msg_error}")
                    else:
                        logger.error(f"❌ Failed to save messages: {msg_error}")
            
            logger.info(f"Successfully saved call center follow-up plan {plan_id} with {len(message_records)} messages")
            
            return {
                'success': True,
                'provider': used_provider,
                'plan_id': plan_id,
                'messages_count': len(message_records)
            }
            
        except Exception as e:
            logger.error(f"Failed to save call center follow-up plan: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save follow-up plan: {str(e)}"
            )

