#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js'
import fetch from 'node-fetch'

const SUPABASE_URL = process.env.SUPABASE_URL
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY
const API_URL = process.env.API_URL || 'http://localhost:8001'

const LOOKBACK_MIN = parseInt(process.env.LOOKBACK_MIN || '240', 10) // 4h
const STUCK_TRANSCRIBING_MIN = parseInt(process.env.STUCK_TRANSCRIBING_MIN || '45', 10)
const ANALYSIS_LAG_MIN = parseInt(process.env.ANALYSIS_LAG_MIN || '30', 10)

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars')
  process.exit(2)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, { auth: { persistSession: false } })

function minutesAgo(min) {
  return new Date(Date.now() - min * 60 * 1000).toISOString()
}

async function checkApiHealth() {
  try {
    const resp = await fetch(`${API_URL}/health`, { timeout: 5000 })
    if (!resp.ok) return { ok: false, status: resp.status }
    const json = await resp.json().catch(() => ({}))
    return { ok: true, status: resp.status, json }
  } catch (e) {
    return { ok: false, error: e.message }
  }
}

async function checkTranscriptionPipeline() {
  // recent calls
  const since = minutesAgo(LOOKBACK_MIN)
  const { data: calls, error } = await supabase
    .from('call_records')
    .select('id, customer_name, created_at, transcript, duration_seconds')
    .gte('created_at', since)
    .order('created_at', { ascending: false })

  if (error) throw error
  const list = calls || []

  const inProgress = list.filter(c => c.transcript === 'Transcribing audio...' || c.transcript === 'Recording in progress...')
  const failed = list.filter(c => typeof c.transcript === 'string' && c.transcript.toLowerCase().includes('failed'))
  const completed = list.filter(c => c.transcript && c.transcript !== 'Transcribing audio...' && c.transcript !== 'Recording in progress...' && !c.transcript.toLowerCase().includes('failed'))

  // Stuck transcribing > STUCK_TRANSCRIBING_MIN
  const stuck = inProgress.filter(c => (Date.now() - new Date(c.created_at).getTime())/60000 > STUCK_TRANSCRIBING_MIN)

  return { list, inProgress, failed, completed, stuck }
}

async function checkAnalysisLag(completedCalls) {
  // For completed transcripts, check if analysis exists; if not within ANALYSIS_LAG_MIN => lagging
  const lagging = []
  for (const c of completedCalls) {
    const ageMin = (Date.now() - new Date(c.created_at).getTime())/60000
    if (ageMin < ANALYSIS_LAG_MIN) continue
    const { data, error } = await supabase
      .from('call_analyses')
      .select('id')
      .eq('call_record_id', c.id)
      .maybeSingle()
    if (!error && !data) lagging.push(c)
  }
  return lagging
}

;(async () => {
  const summary = { ok: true, checks: {} }

  // API health
  const api = await checkApiHealth()
  summary.checks.api = api
  if (!api.ok) summary.ok = false

  // Pipeline
  try {
    const pipeline = await checkTranscriptionPipeline()
    summary.checks.pipeline = {
      total_recent: pipeline.list.length,
      in_progress: pipeline.inProgress.length,
      failed: pipeline.failed.length,
      completed: pipeline.completed.length,
      stuck: pipeline.stuck.map(c => ({ id: c.id, created_at: c.created_at, customer_name: c.customer_name }))
    }

    const lagging = await checkAnalysisLag(pipeline.completed)
    summary.checks.analysis = {
      lagging_count: lagging.length,
      lagging_ids: lagging.map(c => c.id)
    }

    if (pipeline.stuck.length > 0 || lagging.length > 0) summary.ok = false
  } catch (e) {
    summary.ok = false
    summary.checks.pipeline_error = e.message
  }

  // Print report
  console.log(JSON.stringify(summary, null, 2))
  process.exit(summary.ok ? 0 : 1)
})()

