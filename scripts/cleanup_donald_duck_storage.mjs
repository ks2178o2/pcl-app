#!/usr/bin/env node

// Cleanup Supabase Storage for Donald Duck call recordings
// Keeps ONLY the most recent upload; deletes older storage objects.
// Requirements:
// - Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
// - Bucket: call-recordings
// Usage:
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node scripts/cleanup_donald_duck_storage.mjs

import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.SUPABASE_URL
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY
const BUCKET = 'call-recordings'

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars')
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false }
})

function chunkArray(arr, size) {
  const out = []
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))
  return out
}

async function main() {
  console.log('Fetching Donald Duck call records...')
  const { data, error } = await supabase
    .from('call_records')
    .select('id, audio_file_url, created_at')
    .ilike('customer_name', 'Donald Duck')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Failed to fetch call_records:', error)
    process.exit(1)
  }

  const calls = (data || []).filter(r => !!r.audio_file_url)
  if (calls.length === 0) {
    console.log('No Donald Duck calls with audio found. Nothing to do.')
    return
  }

  const [mostRecent, ...older] = calls
  console.log('Most recent kept:', mostRecent.id, mostRecent.audio_file_url, mostRecent.created_at)

  const pathsToDelete = older
    .map(r => r.audio_file_url)
    .filter(p => typeof p === 'string' && p.trim().length > 0)

  if (pathsToDelete.length === 0) {
    console.log('No older storage objects to delete.')
    return
  }

  console.log(`Deleting ${pathsToDelete.length} older storage object(s) from bucket '${BUCKET}'...`)
  const batches = chunkArray(pathsToDelete, 100)
  for (let i = 0; i < batches.length; i++) {
    const batch = batches[i]
    const { data: delData, error: delErr } = await supabase
      .storage
      .from(BUCKET)
      .remove(batch)
    if (delErr) {
      console.error(`Delete batch ${i + 1}/${batches.length} failed:`, delErr)
      process.exit(1)
    }
    console.log(`Batch ${i + 1}/${batches.length} deleted:`, delData?.length ?? 0)
  }

  console.log('Storage cleanup complete. Older uploads removed; most recent kept.')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})


