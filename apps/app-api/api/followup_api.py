"""
Follow-up Plan API - Generate AI-powered follow-up plans from call analysis
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging
import json
import time
import random
import uuid
import re
from datetime import datetime, timedelta
from middleware.auth import get_current_user
from services.supabase_client import get_supabase_client
# Import analysis functions - these may not exist in analysis_api, so define fallbacks
try:
    from api.analysis_api import (
        _analyze_with_openai,
        _analyze_with_gemini,
        _get_org_analysis_settings,
        _retry_with_backoff,
        get_analysis_semaphore
    )
except ImportError:
    # Fallback: define these functions locally if they don't exist in analysis_api
    # These are actually defined in call_center_followup_api, but we'll import from there as fallback
    try:
        from api.call_center_followup_api import (
            _analyze_with_openai,
            _analyze_with_gemini,
            _get_org_analysis_settings,
            get_analysis_semaphore
        )
    except ImportError:
        # If that also fails, define minimal stubs (shouldn't happen in practice)
        def _analyze_with_openai(prompt: str) -> str:
            raise NotImplementedError("_analyze_with_openai not available")
        
        def _analyze_with_gemini(prompt: str) -> str:
            raise NotImplementedError("_analyze_with_gemini not available")
        
        def _get_org_analysis_settings(supabase, user_id: str):
            return ([], [])
        
        def get_analysis_semaphore():
            import asyncio
            return asyncio.Semaphore(5)

router = APIRouter(prefix="/api/followup", tags=["followup"])

logger = logging.getLogger(__name__)


class GenerateFollowUpPlanPayload(BaseModel):
    callRecordId: str
    transcript: str
    analysisData: Dict[str, Any]
    customerName: str
    salespersonName: str
    provider: Optional[str] = None  # 'auto', 'gemini', or 'openai'


def _build_followup_prompt(
    transcript: str,
    analysis_data: Dict[str, Any],
    customer_name: str,
    salesperson_name: str
) -> str:
    """Build the prompt for generating a follow-up plan"""
    
    # Extract key insights from analysis
    sentiment = analysis_data.get('sentiment', {})
    urgency = analysis_data.get('urgencyScoring', {})
    personality = analysis_data.get('customerPersonality', {})
    objections = analysis_data.get('objections', [])
    action_items = analysis_data.get('actionItems', [])
    
    prompt = f"""
You are an expert sales strategist specializing in healthcare consumer psychology and follow-up optimization. 
Generate a comprehensive, multi-touchpoint follow-up plan based on this call analysis.

CALL ANALYSIS SUMMARY:
- Customer: {customer_name}
- Salesperson: {salesperson_name}
- Overall Sentiment: {sentiment.get('overall', 'neutral')}
- Customer Engagement: {sentiment.get('customerEngagement', 5)}/10
- Urgency Level: {urgency.get('overallUrgency', 5)}/10
- Personality Type: {personality.get('personalityType', 'unknown')}
- Objections Raised: {len(objections)}
- Action Items: {len(action_items)}

TRANSCRIPT:
{transcript[:3000]}

ANALYSIS DATA:
{json.dumps(analysis_data, indent=2, default=str)[:2000]}

Generate a JSON follow-up plan with this EXACT structure:

{{
  "strategy_type": "email|sms|phone|multi-channel",
  "recommended_timing": "immediate|24_hours|3_days|1_week",
  "priority_score": 8,
  "customer_urgency": "high|medium|low",
  "next_action": "Specific next action to take",
  "reasoning": "Why this strategy fits this customer's psychology and situation",
  "compliance_notes": "Any compliance considerations (HIPAA, consent, etc.)",
  "messages": [
    {{
      "channel_type": "email|sms|phone",
      "subject_line": "Email subject (if email)",
      "message_content": "Full message content",
      "personalization_notes": "Why this message is personalized for this customer",
      "tone": "professional|warm|supportive|direct",
      "call_to_action": "Specific CTA for this message",
      "estimated_send_time": "ISO 8601 datetime (e.g., 2025-01-10T14:00:00Z) or relative like '+1 day'",
      "status": "draft"
    }}
  ]
}}

REQUIREMENTS:
1. Generate 3-7 follow-up messages spanning multiple days
2. Vary channels (email, SMS) for multi-touchpoint strategy
3. Personalize based on customer personality, urgency, and objections
4. Include compliance notes for healthcare context
5. Ensure CTAs are specific and actionable
6. Calculate estimated_send_time based on recommended_timing
7. Return ONLY valid JSON, no markdown or code fences

Return the complete JSON object now:
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
        return json.loads(cleaned)
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


@router.post("/generate", response_model=dict)
async def generate_followup_plan(
    payload: GenerateFollowUpPlanPayload,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a follow-up plan from call transcript and analysis data.
    Saves to follow_up_plans and follow_up_messages tables.
    """
    if not payload.transcript or not payload.analysisData:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript and analysis data are required"
        )
    
    # Rate limiting: acquire semaphore
    async with get_analysis_semaphore():
        logger.info(f"Generating follow-up plan for call {payload.callRecordId}")
        
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        
        # Build prompt
        prompt = _build_followup_prompt(
            payload.transcript,
            payload.analysisData,
            payload.customerName,
            payload.salespersonName
        )
        
        # Get provider settings (similar to analysis API)
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
                logger.info(f"Attempting follow-up plan generation with {provider}")
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
                logger.info(f"Follow-up plan generated with {used_provider} in {generation_time}ms")
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
            logger.info(f"🔍 DEBUG: plan_data structure - has 'messages' key: {'messages' in plan_data}")
            if 'messages' in plan_data:
                messages_list = plan_data.get('messages', [])
                logger.info(f"🔍 DEBUG: Number of messages in plan_data: {len(messages_list)}")
                if messages_list:
                    logger.info(f"🔍 DEBUG: First message keys: {list(messages_list[0].keys()) if isinstance(messages_list[0], dict) else 'Not a dict'}")
                else:
                    logger.warning(f"🔍 DEBUG: Messages array exists but is EMPTY")
            else:
                logger.warning(f"🔍 DEBUG: 'messages' key NOT FOUND in plan_data")
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
            
            # Build plan record - start with core required columns, then add optional ones
            # Ensure plan_data is properly set (required field)
            if not plan_data:
                raise ValueError("plan_data is required but was empty")
            
            # Store plan_data as dict (Supabase Python client auto-serializes dicts to JSONB)
            # Ensure it's a valid dict
            if not isinstance(plan_data, dict):
                raise ValueError(f"plan_data must be a dict, got {type(plan_data)}")
            
            plan_record = {
                'id': plan_id,
                'call_record_id': payload.callRecordId,
                'user_id': user_id,
                'status': 'active',
                'plan_data': plan_data,  # Store full plan data as JSONB (Supabase auto-serializes dicts)
                'created_at': base_time.isoformat() + 'Z',
                'updated_at': base_time.isoformat() + 'Z'
            }
            
            logger.info(f"Plan record keys before optional fields: {list(plan_record.keys())}, plan_data has {len(plan_data)} keys")
            
            # Add optional fields - these will be removed by retry logic if they don't exist
            optional_fields = {
                'strategy_type': plan_data.get('strategy_type', 'email'),
                'recommended_timing': plan_data.get('recommended_timing', '24_hours'),
                'priority_score': plan_data.get('priority_score', 5),
                'next_action': plan_data.get('next_action', 'Follow up with customer'),
                'reasoning': plan_data.get('reasoning', ''),
                'customer_urgency': plan_data.get('customer_urgency', 'medium'),
                'customer_name': payload.customerName,
                'salesperson_name': payload.salespersonName,
                'compliance_notes': plan_data.get('compliance_notes'),
            }
            
            # Add all optional fields to plan_record (will be removed if they don't exist)
            for key, value in optional_fields.items():
                if value is not None:  # Only add non-None values
                    plan_record[key] = value
            
            # Try to insert, with retry logic that removes missing columns
            max_retries = 10  # Allow for multiple missing columns
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # Ensure plan_data is still present (should never be removed)
                    if 'plan_data' not in plan_record or plan_record['plan_data'] is None:
                        raise ValueError("plan_data was removed or is None - this should never happen")
                    
                    supabase.from_('follow_up_plans').insert(plan_record).execute()
                    logger.info(f"✅ Successfully saved follow-up plan {plan_id} with {len(plan_record)} fields: {list(plan_record.keys())}")
                    break  # Success!
                except Exception as insert_error:
                    error_str = str(insert_error)
                    error_msg = error_str.lower()
                    
                    # Check if this is a missing column error (PGRST204)
                    if 'pgrst204' in error_msg or 'could not find' in error_msg:
                        # Extract column name from error message
                        # Error format: "Could not find the 'column_name' column..." or "{'message': \"Could not find the 'column_name' column...\"}"
                        missing_column = None
                        
                        # Try to extract column name using regex pattern: 'column_name' or "column_name"
                        # Look for patterns like 'column_name' or "column_name" in the error
                        quoted_col_match = re.search(r"['\"]([^'\"]+)['\"]", error_str)
                        if quoted_col_match:
                            potential_col = quoted_col_match.group(1)
                            # Check if this column is in our plan_record
                            if potential_col in plan_record:
                                missing_column = potential_col
                        
                        # Fallback: check all columns in plan_record
                        if not missing_column:
                            protected_columns = ['id', 'call_record_id', 'user_id', 'status', 'created_at', 'updated_at', 'plan_data']
                            for col_name in list(plan_record.keys()):
                                # Check if column name (with or without quotes) appears in error
                                if (f"'{col_name}'" in error_str or f'"{col_name}"' in error_str or col_name in error_msg) and col_name not in protected_columns:
                                    missing_column = col_name
                                    break
                        
                        if missing_column and retry_count < max_retries:
                            logger.warning(f"⚠️ Column '{missing_column}' doesn't exist, removing it (attempt {retry_count + 1}/{max_retries})")
                            plan_record.pop(missing_column, None)  # Remove the problematic column
                            retry_count += 1
                            continue
                        else:
                            # Max retries or couldn't identify column
                            logger.error(f"❌ Save failed after {retry_count} retries: {insert_error}")
                            raise
                    else:
                        # Not a missing column error
                        logger.error(f"❌ Save failed with non-column error: {insert_error}")
                        raise  # Re-raise the error
            
            # If we get here and haven't succeeded, something went wrong
            if retry_count > max_retries:
                raise Exception(f"Failed to save follow-up plan after {max_retries} retries")
            
            # Create messages
            messages = plan_data.get('messages', [])
            logger.info(f"🔍 DEBUG: Extracted messages from plan_data: {len(messages)} messages")
            if not messages:
                logger.warning(f"⚠️ FALLBACK TRIGGERED: No messages found in plan_data, creating default single message")
                logger.warning(f"⚠️ plan_data keys available: {list(plan_data.keys())}")
                # Create a default message if none provided
                messages = [{
                    'channel_type': 'email',
                    'message_content': f'Thank you for your interest, {payload.customerName}. We look forward to following up with you.',
                    'tone': 'professional',
                    'call_to_action': 'Schedule a consultation',
                    'status': 'draft'
                }]
                logger.info(f"🔍 DEBUG: Created {len(messages)} default message(s)")
            else:
                logger.info(f"🔍 DEBUG: Using {len(messages)} message(s) from LLM response")
            
            message_records = []
            for idx, msg in enumerate(messages):
                # Calculate send time
                timing_str = msg.get('estimated_send_time', plan_data.get('recommended_timing', '24_hours'))
                if isinstance(timing_str, str) and timing_str.startswith('+'):
                    # Relative time like "+1 day"
                    days = int(timing_str.split()[0][1:]) if timing_str.split()[0][1:].isdigit() else 1
                    send_time = base_time + timedelta(days=days + idx)
                elif 'T' in timing_str or timing_str.endswith('Z'):
                    # ISO 8601 format
                    try:
                        send_time = datetime.fromisoformat(timing_str.replace('Z', '+00:00'))
                    except:
                        send_time = _calculate_send_time(plan_data.get('recommended_timing', '24_hours'), base_time, idx)
                else:
                    send_time = _calculate_send_time(timing_str, base_time, idx)
                
                # Store full message data in JSONB, only save essential fields as columns
                # Note: message_type is required by database (derived from channel_type)
                channel_type = msg.get('channel_type', 'email')
                message_type = channel_type  # Use channel_type as message_type (email, sms, phone)
                message_content = msg.get('message_content', '')
                
                message_record = {
                    'id': str(uuid.uuid4()),
                    'follow_up_plan_id': plan_id,
                    'user_id': user_id,
                    'message_data': msg,  # Store full message data as JSONB (like plan_data)
                    'message_type': message_type,  # Required column - derive from channel_type
                    'status': msg.get('status', 'draft'),
                    'created_at': base_time.isoformat() + 'Z',
                    'updated_at': base_time.isoformat() + 'Z'
                }
                
                # Add optional columns if they might be required (for backward compatibility)
                # These can be nullable but some databases might have them as required
                if message_content:
                    message_record['content'] = message_content  # Some schemas use 'content' instead of 'message_content'
                    message_record['message_content'] = message_content
                
                message_records.append(message_record)
            
            # Insert messages - store everything in message_data JSONB (cleaner approach)
            if message_records:
                try:
                    supabase.from_('follow_up_messages').insert(message_records).execute()
                    logger.info(f"Successfully saved {len(message_records)} messages")
                except Exception as msg_error:
                    error_str = str(msg_error)
                    error_msg = error_str.lower()
                    
                    # If message_data column doesn't exist, try without it (fallback)
                    if 'pgrst204' in error_msg or 'could not find' in error_msg:
                        if 'message_data' in error_str:
                            logger.warning(f"⚠️ message_data column doesn't exist, trying with minimal fields")
                            # Fallback: only save essential fields (including required message_type and content)
                            minimal_messages = []
                            for msg_record in message_records:
                                # Get message content from message_data if available
                                msg_data = msg_record.get('message_data', {})
                                content = msg_data.get('message_content', '') if isinstance(msg_data, dict) else ''
                                
                                minimal_msg = {
                                    'id': msg_record['id'],
                                    'follow_up_plan_id': msg_record['follow_up_plan_id'],
                                    'user_id': msg_record['user_id'],
                                    'message_type': msg_record.get('message_type', 'email'),  # Required column
                                    'status': msg_record['status'],
                                    'created_at': msg_record['created_at'],
                                    'updated_at': msg_record['updated_at']
                                }
                                
                                # Add content if the column exists and is required
                                if content:
                                    minimal_msg['content'] = content
                                
                                minimal_messages.append(minimal_msg)
                            
                            try:
                                supabase.from_('follow_up_messages').insert(minimal_messages).execute()
                                logger.warning(f"⚠️ Saved {len(minimal_messages)} messages with minimal fields (message_data column missing)")
                            except Exception as fallback_error:
                                logger.error(f"❌ Failed to save messages even with minimal fields: {fallback_error}")
                        else:
                            logger.error(f"❌ Failed to save messages: {msg_error}")
                    else:
                        logger.error(f"❌ Failed to save messages: {msg_error}")
            
            logger.info(f"Successfully saved follow-up plan {plan_id} with {len(message_records)} messages")
            
            return {
                'success': True,
                'provider': used_provider,
                'plan_id': plan_id,
                'messages_count': len(message_records)
            }
            
        except Exception as e:
            logger.error(f"Failed to save follow-up plan: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save follow-up plan: {str(e)}"
            )
