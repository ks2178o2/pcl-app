#!/usr/bin/env python3
"""
Trace a call record through the database.
Usage: python scripts/trace_call_record.py d86ccd95-d525-4f38-a6d6-7c41a604841d
"""

import os
import sys
import json
import requests
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars", file=sys.stderr)
    sys.exit(2)

CALL_ID = sys.argv[1] if len(sys.argv) > 1 else 'd86ccd95-d525-4f38-a6d6-7c41a604841d'
REST_URL = f"{SUPABASE_URL}/rest/v1"

def sb_get(table, params):
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept": "application/json"
    }
    r = requests.get(f"{REST_URL}/{table}", headers=headers, params=params, timeout=30)
    if r.status_code == 200:
        return r.json(), None
    return None, {"status": r.status_code, "text": r.text[:200]}

def main():
    print(f"Tracing call record: {CALL_ID}\n")
    print("=" * 60)

    # 1. Call Record
    print("\n1. CALL RECORD:")
    calls, err = sb_get("call_records", {"id": f"eq.{CALL_ID}", "select": "*"})
    if err:
        print(f"   ❌ Error: {err}")
        return
    
    if not calls or len(calls) == 0:
        print(f"   ❌ Call record not found!")
        return
    
    call = calls[0]
    print(f"   ✅ Found")
    print(f"   Customer: {call.get('customer_name', 'N/A')}")
    print(f"   Salesperson: {call.get('salesperson_name', 'N/A')}")
    print(f"   Created: {call.get('created_at', 'N/A')}")
    print(f"   Duration: {call.get('duration_seconds', 0)}s")
    print(f"   Status: {call.get('status', 'N/A')}")
    
    # Transcript status
    transcript = call.get('transcript')
    if not transcript:
        print(f"   Transcript: ❌ NULL")
    elif transcript == 'Transcribing audio...':
        print(f"   Transcript: ⏳ IN_PROGRESS")
    elif 'failed' in transcript.lower():
        print(f"   Transcript: ❌ FAILED")
    else:
        print(f"   Transcript: ✅ ({len(transcript)} chars)")
        if len(transcript) > 0:
            preview = transcript[:200].replace('\n', ' ')
            print(f"             Preview: {preview}...")
    
    # Audio file
    audio_url = call.get('audio_file_url')
    if audio_url:
        print(f"   Audio: ✅ {audio_url}")
    else:
        print(f"   Audio: ❌ NULL")
    
    # Diarization
    diar = call.get('diarization_segments')
    if diar:
        if isinstance(diar, list):
            print(f"   Diarization: ✅ {len(diar)} segments")
        else:
            print(f"   Diarization: ⚠️ Invalid type")
    else:
        print(f"   Diarization: ❌ NULL")
    
    # Speaker mapping
    mapping = call.get('speaker_mapping')
    if mapping:
        print(f"   Speaker Mapping: ✅ {len(mapping)} mappings")
    else:
        print(f"   Speaker Mapping: ❌ NULL")

    # 2. Call Analysis
    print("\n2. CALL ANALYSIS:")
    analyses, err = sb_get("call_analyses", {"call_record_id": f"eq.{CALL_ID}", "select": "*"})
    if err:
        print(f"   ⚠️ Error fetching: {err}")
    elif not analyses or len(analyses) == 0:
        print(f"   ❌ No analysis found")
    else:
        analysis = analyses[0]
        print(f"   ✅ Found")
        print(f"   Status: {analysis.get('status', 'N/A')}")
        print(f"   Model: {analysis.get('model_used', 'N/A')}")
        print(f"   Created: {analysis.get('created_at', 'N/A')}")
        
        # Check analysis_data structure
        analysis_data = analysis.get('analysis_data')
        if not analysis_data:
            print(f"   Analysis Data: ❌ NULL")
        else:
            print(f"   Analysis Data: ✅ Present")
            # Check required fields
            checks = {
                'sentiment': analysis_data.get('sentiment'),
                'customerPersonality': analysis_data.get('customerPersonality'),
                'urgencyScoring': analysis_data.get('urgencyScoring'),
                'salesPerformance': analysis_data.get('salesPerformance'),
                'financialPsychology': analysis_data.get('financialPsychology'),
                'trustAndSafety': analysis_data.get('trustAndSafety'),
                'summary': analysis_data.get('summary'),
                'objections': analysis_data.get('objections'),
                'actionItems': analysis_data.get('actionItems'),
            }
            
            missing = [k for k, v in checks.items() if not v]
            if missing:
                print(f"   ⚠️ Missing fields: {', '.join(missing)}")
            else:
                print(f"   ✅ All required fields present")
            
            # Show summary preview
            if 'summary' in analysis_data:
                summary = analysis_data['summary']
                if isinstance(summary, str) and len(summary) > 0:
                    preview = summary[:150].replace('\n', ' ')
                    print(f"   Summary Preview: {preview}...")

    # 3. Call Chunks
    print("\n3. CALL CHUNKS:")
    chunks, err = sb_get("call_chunks", {"call_record_id": f"eq.{CALL_ID}", "select": "*"})
    if err:
        print(f"   ⚠️ Error: {err}")
    elif not chunks or len(chunks) == 0:
        print(f"   ⚪ None found (may not use chunks)")
    else:
        print(f"   ✅ {len(chunks)} chunks found")
        for c in chunks[:5]:  # Show first 5
            print(f"      Chunk {c.get('chunk_number', '?')}: {c.get('chunk_size', 0)} bytes, {c.get('status', 'N/A')}")

    # 4. Follow-up Plans
    print("\n4. FOLLOW-UP PLANS:")
    plans, err = sb_get("follow_up_plans", {"call_record_id": f"eq.{CALL_ID}", "select": "*"})
    if err:
        print(f"   ⚠️ Error: {err}")
    elif not plans or len(plans) == 0:
        print(f"   ⚪ None found")
    else:
        print(f"   ✅ {len(plans)} plan(s) found")
        for p in plans:
            print(f"      {p.get('follow_up_type', 'N/A')}: {p.get('status', 'N/A')}")

    # 5. Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    
    issues = []
    
    if not transcript or transcript == 'Transcribing audio...' or 'failed' in transcript.lower():
        issues.append("❌ Transcript not ready")
    
    if not analyses or len(analyses) == 0:
        issues.append("⏳ Analysis not started")
    else:
        a_data = analyses[0].get('analysis_data')
        if not a_data:
            issues.append("❌ Analysis data is NULL")
        else:
            required = ['sentiment', 'customerPersonality', 'urgencyScoring', 'salesPerformance', 'financialPsychology']
            missing = [r for r in required if not a_data.get(r)]
            if missing:
                issues.append(f"⚠️ Analysis incomplete: missing {', '.join(missing)}")
    
    if not audio_url:
        issues.append("⚠️ No audio file URL")
    
    if issues:
        print("\n   Issues found:")
        for issue in issues:
            print(f"      {issue}")
    else:
        print("\n   ✅ All data present - CallAnalysisPanel should render fully!")
    
    print()

if __name__ == "__main__":
    main()

