-- Ensure RLS is enabled on call_records (no-op if already enabled)
alter table if exists call_records enable row level security;

-- Allow authenticated users to SELECT their own call records
do $$ begin
  if not exists (
    select 1 from pg_policies 
    where schemaname = 'public' 
      and tablename = 'call_records' 
      and policyname = 'read_own_call_records'
  ) then
    create policy "read_own_call_records"
    on public.call_records for select
    to authenticated
    using (user_id = auth.uid());
  end if;
end $$;

-- Optionally allow users to update their own transcripts/summaries only
do $$ begin
  if not exists (
    select 1 from pg_policies 
    where schemaname = 'public' 
      and tablename = 'call_records' 
      and policyname = 'update_own_call_transcript'
  ) then
    create policy "update_own_call_transcript"
    on public.call_records for update
    to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());
  end if;
end $$;


