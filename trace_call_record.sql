-- Trace call record: d86ccd95-d525-4f38-a6d6-7c41a604841d
-- This script shows all related data for the CallAnalysisPanel

\echo '=== CALL RECORD DETAILS ==='
SELECT 
  id,
  customer_name,
  salesperson_name,
  user_id,
  center_id,
  patient_id,
  created_at,
  duration_seconds,
  status,
  transcript IS NOT NULL as has_transcript,
  CASE 
    WHEN transcript IS NULL THEN 'NULL'
    WHEN transcript = 'Transcribing audio...' THEN 'IN_PROGRESS'
    WHEN transcript LIKE '%failed%' THEN 'FAILED'
    ELSE 'COMPLETED'
  END as transcript_status,
  LENGTH(transcript) as transcript_length,
  audio_file_url,
  diarization_segments IS NOT NULL as has_diarization,
  CASE 
    WHEN diarization_segments IS NULL THEN 'NULL'
    WHEN jsonb_typeof(diarization_segments) = 'array' 
      THEN jsonb_array_length(diarization_segments)::text || ' segments'
    ELSE 'INVALID'
  END as diarization_info,
  speaker_mapping IS NOT NULL as has_speaker_mapping,
  vendor_insights IS NOT NULL as has_vendor_insights,
  total_chunks,
  chunks_uploaded,
  recording_complete
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== TRANSCRIPT PREVIEW (first 500 chars) ==='
SELECT 
  CASE 
    WHEN transcript IS NULL THEN 'NULL'
    WHEN LENGTH(transcript) > 500 THEN LEFT(transcript, 500) || '... (truncated)'
    ELSE transcript
  END as transcript_preview
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== DIARIZATION SEGMENTS PREVIEW ==='
SELECT 
  CASE 
    WHEN diarization_segments IS NULL THEN 'NULL'
    WHEN jsonb_typeof(diarization_segments) = 'array' THEN
      jsonb_pretty(diarization_segments->0) || E'\n... (showing first segment)'
    ELSE 'INVALID_TYPE: ' || jsonb_typeof(diarization_segments)
  END as first_segment
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== SPEAKER MAPPING ==='
SELECT 
  CASE 
    WHEN speaker_mapping IS NULL THEN 'NULL'
    ELSE jsonb_pretty(speaker_mapping)
  END as speaker_mapping
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== CALL ANALYSIS ==='
SELECT 
  id,
  call_record_id,
  user_id,
  status,
  model_used,
  analysis_version,
  created_at,
  updated_at,
  -- Extracted metrics
  overall_sentiment,
  overall_urgency,
  customer_engagement,
  trust_level,
  personality_type,
  motivation_category,
  sales_performance_score,
  objections_count,
  action_items_count,
  -- Check if analysis_data exists
  analysis_data IS NOT NULL as has_full_analysis,
  CASE 
    WHEN analysis_data IS NULL THEN 'NULL'
    WHEN jsonb_typeof(analysis_data) = 'object' THEN 'OBJECT'
    ELSE 'INVALID'
  END as analysis_data_type,
  -- Check nested fields that CallAnalysisPanel expects
  (analysis_data->'sentiment') IS NOT NULL as has_sentiment,
  (analysis_data->'customerPersonality') IS NOT NULL as has_customer_personality,
  (analysis_data->'urgencyScoring') IS NOT NULL as has_urgency_scoring,
  (analysis_data->'salesPerformance') IS NOT NULL as has_sales_performance,
  (analysis_data->'financialPsychology') IS NOT NULL as has_financial_psychology,
  (analysis_data->'trustAndSafety') IS NOT NULL as has_trust_and_safety,
  (analysis_data->'summary') IS NOT NULL as has_summary,
  (analysis_data->'objections') IS NOT NULL as has_objections,
  (analysis_data->'actionItems') IS NOT NULL as has_action_items,
  (analysis_data->'coachingRecommendations') IS NOT NULL as has_coaching_recommendations,
  (analysis_data->'personalizedRecommendations') IS NOT NULL as has_personalized_recommendations
FROM call_analyses
WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== ANALYSIS DATA STRUCTURE PREVIEW ==='
SELECT 
  jsonb_pretty(jsonb_build_object(
    'summary', analysis_data->'summary',
    'modelUsed', analysis_data->'modelUsed',
    'sentiment_overall', analysis_data->'sentiment'->'overall',
    'customerPersonality_type', analysis_data->'customerPersonality'->'personalityType',
    'urgencyScoring_overallUrgency', analysis_data->'urgencyScoring'->'overallUrgency',
    'objections_count', jsonb_array_length(COALESCE(analysis_data->'objections', '[]'::jsonb)),
    'actionItems_count', jsonb_array_length(COALESCE(analysis_data->'actionItems', '[]'::jsonb))
  )) as analysis_preview
FROM call_analyses
WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== CALL CHUNKS (if any) ==='
SELECT 
  id,
  call_record_id,
  chunk_number,
  chunk_size,
  uploaded_at,
  status
FROM call_chunks
WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'
ORDER BY chunk_number;

\echo ''
\echo '=== FOLLOW-UP PLANS (if any) ==='
SELECT 
  id,
  call_record_id,
  customer_name,
  salesperson_name,
  created_at,
  follow_up_type,
  scheduled_date,
  status
FROM follow_up_plans
WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'
ORDER BY created_at DESC;

\echo ''
\echo '=== STORAGE AUDIO FILE CHECK ==='
SELECT 
  CASE 
    WHEN audio_file_url IS NULL THEN 'NULL - No audio file URL'
    WHEN audio_file_url LIKE 'call-recordings/%' THEN audio_file_url || ' (in bucket: call-recordings)'
    ELSE audio_file_url || ' (path format unclear)'
  END as audio_file_info
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== SUMMARY DIAGNOSTICS ==='
SELECT 
  'Call Record' as component,
  CASE 
    WHEN id IS NULL THEN '❌ MISSING'
    ELSE '✅ EXISTS'
  END as status
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'

UNION ALL

SELECT 
  'Transcript' as component,
  CASE 
    WHEN transcript IS NULL THEN '❌ NULL'
    WHEN transcript = 'Transcribing audio...' THEN '⏳ IN_PROGRESS'
    WHEN transcript LIKE '%failed%' THEN '❌ FAILED'
    WHEN LENGTH(transcript) = 0 THEN '⚠️ EMPTY'
    ELSE '✅ COMPLETE (' || LENGTH(transcript) || ' chars)'
  END as status
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'

UNION ALL

SELECT 
  'Audio File' as component,
  CASE 
    WHEN audio_file_url IS NULL THEN '❌ NULL'
    ELSE '✅ ' || audio_file_url
  END as status
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'

UNION ALL

SELECT 
  'Analysis Record' as component,
  CASE 
    WHEN id IS NULL THEN '❌ MISSING'
    ELSE '✅ EXISTS (status: ' || status || ')'
  END as status
FROM call_analyses
WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'

UNION ALL

SELECT 
  'Analysis Data' as component,
  CASE 
    WHEN analysis_data IS NULL THEN '❌ NULL'
    WHEN (analysis_data->'sentiment') IS NULL THEN '⚠️ INCOMPLETE (missing sentiment)'
    WHEN (analysis_data->'customerPersonality') IS NULL THEN '⚠️ INCOMPLETE (missing customerPersonality)'
    WHEN (analysis_data->'urgencyScoring') IS NULL THEN '⚠️ INCOMPLETE (missing urgencyScoring)'
    WHEN (analysis_data->'salesPerformance') IS NULL THEN '⚠️ INCOMPLETE (missing salesPerformance)'
    WHEN (analysis_data->'financialPsychology') IS NULL THEN '⚠️ INCOMPLETE (missing financialPsychology)'
    ELSE '✅ COMPLETE'
  END as status
FROM call_analyses
WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'

UNION ALL

SELECT 
  'Diarization' as component,
  CASE 
    WHEN diarization_segments IS NULL THEN '❌ NULL'
    WHEN jsonb_typeof(diarization_segments) = 'array' THEN 
      '✅ ' || jsonb_array_length(diarization_segments)::text || ' segments'
    ELSE '⚠️ INVALID_TYPE'
  END as status
FROM call_records
WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d';

\echo ''
\echo '=== RECOMMENDATION ==='
SELECT 
  CASE 
    -- Missing call record
    WHEN NOT EXISTS (SELECT 1 FROM call_records WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d') THEN
      '❌ Call record does not exist. Check ID.'
    -- Missing transcript
    WHEN EXISTS (
      SELECT 1 FROM call_records 
      WHERE id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d' 
      AND (transcript IS NULL OR transcript = 'Transcribing audio...' OR transcript LIKE '%failed%')
    ) THEN
      '⏳ Transcript not ready. Wait for transcription to complete or check transcription status.'
    -- Missing analysis
    WHEN NOT EXISTS (
      SELECT 1 FROM call_analyses 
      WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'
    ) THEN
      '⏳ Analysis not started yet. Analysis should auto-trigger when transcript is ready.'
    -- Incomplete analysis
    WHEN EXISTS (
      SELECT 1 FROM call_analyses 
      WHERE call_record_id = 'd86ccd95-d525-4f38-a6d6-7c41a604841d'
      AND (
        analysis_data IS NULL 
        OR (analysis_data->'sentiment') IS NULL
        OR (analysis_data->'customerPersonality') IS NULL
        OR (analysis_data->'urgencyScoring') IS NULL
        OR (analysis_data->'salesPerformance') IS NULL
        OR (analysis_data->'financialPsychology') IS NULL
      )
    ) THEN
      '⚠️ Analysis exists but is incomplete. CallAnalysisPanel will show "Analysis in progress" fallback.'
    -- Everything looks good
    ELSE
      '✅ All data present. CallAnalysisPanel should render fully.'
  END as recommendation;

