#!/usr/bin/env node

// Cleanup Supabase Storage for Donald Duck and Goofy call recordings
// Deletes ALL storage objects associated with these customers' calls.
// Requirements:
// - Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
// - Bucket: call-recordings
// Usage:
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node scripts/cleanup_donald_duck_and_goofy_storage.mjs

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
  console.log('Fetching call records for Donald Duck and Goofy...')
  const { data, error } = await supabase
    .from('call_records')
    .select('id, audio_file_url, customer_name, created_at')
    .or('customer_name.ilike.Donald Duck,customer_name.ilike.Goofy')

  if (error) {
    console.error('Failed to fetch call_records:', error)
    process.exit(1)
  }

  const calls = (data || []).filter(r => !!r.audio_file_url)
  if (calls.length === 0) {
    console.log('No calls with audio found for Donald Duck or Goofy. Nothing to do.')
    return
  }

  console.log(`Found ${calls.length} call(s) with audio files:`)
  calls.forEach(c => {
    console.log(`  - ${c.customer_name} (${c.id}): ${c.audio_file_url}`)
  })

  const pathsToDelete = calls
    .map(r => r.audio_file_url)
    .filter(p => typeof p === 'string' && p.trim().length > 0)

  if (pathsToDelete.length === 0) {
    console.log('No storage paths to delete.')
    return
  }

  console.log(`\nDeleting ${pathsToDelete.length} storage object(s) from bucket '${BUCKET}'...`)
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
    console.log(`Batch ${i + 1}/${batches.length} deleted: ${delData?.length ?? 0} files`)
  }

  console.log('\n✅ Storage cleanup complete. All audio files removed.')
  console.log('⚠️  Note: Database records are NOT deleted by this script.')
  console.log('   Run cleanup_donald_duck_and_goofy.sql to delete database records.')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

