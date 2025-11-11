-- Create analysis_settings table for tenant-configurable analysis provider settings
-- Allows organizations to configure which AI providers to use for transcript analysis
-- and in what order (primary/backup)

create table if not exists public.analysis_settings (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  provider_order text[] not null default array['openai', 'gemini']::text[],
  enabled_providers text[] not null default array['openai', 'gemini']::text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(organization_id)
);

-- Enable RLS
alter table public.analysis_settings enable row level security;

-- Policy: Authenticated users can read their own org's settings
create policy "analysis_settings_select_own_org"
on public.analysis_settings for select
to authenticated
using (
  organization_id in (
    select organization_id from public.profiles where user_id = auth.uid()
  )
);

-- Policy: System admins can read any org's settings
create policy "analysis_settings_select_system_admin"
on public.analysis_settings for select
to authenticated
using (
  exists (
    select 1 from public.user_roles ur
    where ur.user_id = auth.uid() and ur.role = 'system_admin'
  )
);

-- Policy: Org admins and system admins can insert/update their org's settings
create policy "analysis_settings_upsert_org_admin"
on public.analysis_settings for all
to authenticated
using (
  organization_id in (
    select organization_id from public.profiles where user_id = auth.uid()
  )
  and (
    exists (
      select 1 from public.user_roles ur
      where ur.user_id = auth.uid() 
      and ur.role in ('system_admin', 'org_admin')
    )
  )
)
with check (
  organization_id in (
    select organization_id from public.profiles where user_id = auth.uid()
  )
  and (
    exists (
      select 1 from public.user_roles ur
      where ur.user_id = auth.uid() 
      and ur.role in ('system_admin', 'org_admin')
    )
  )
);

-- Create index for faster lookups
create index if not exists idx_analysis_settings_org_id 
on public.analysis_settings(organization_id);

