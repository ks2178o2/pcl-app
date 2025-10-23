-- Enhanced RAG Context Management Schema
-- This extends the existing rag_context_items table with app-wide capabilities

-- Create global_context_items table for app-wide knowledge
CREATE TABLE IF NOT EXISTS public.global_context_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    rag_feature TEXT NOT NULL,
    item_id TEXT NOT NULL UNIQUE, -- Global uniqueness
    item_type TEXT NOT NULL,
    item_title TEXT NOT NULL,
    item_content TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    priority INTEGER DEFAULT 1,
    confidence_score DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    source TEXT, -- Where this knowledge came from
    tags TEXT[], -- Array of tags for categorization
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for global_context_items
CREATE INDEX IF NOT EXISTS idx_global_context_items_feature ON public.global_context_items(rag_feature);
CREATE INDEX IF NOT EXISTS idx_global_context_items_status ON public.global_context_items(status);
CREATE INDEX IF NOT EXISTS idx_global_context_items_item_id ON public.global_context_items(item_id);
CREATE INDEX IF NOT EXISTS idx_global_context_items_tags ON public.global_context_items USING GIN(tags);

-- Create tenant_context_access table for controlling access to global context
CREATE TABLE IF NOT EXISTS public.tenant_context_access (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL,
    rag_feature TEXT NOT NULL,
    access_level TEXT DEFAULT 'read' CHECK (access_level IN ('read', 'write', 'admin')),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, rag_feature)
);

-- Create indexes for tenant_context_access
CREATE INDEX IF NOT EXISTS idx_tenant_context_access_org ON public.tenant_context_access(organization_id);
CREATE INDEX IF NOT EXISTS idx_tenant_context_access_feature ON public.tenant_context_access(rag_feature);

-- Create context_sharing table for cross-tenant knowledge sharing
CREATE TABLE IF NOT EXISTS public.context_sharing (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_organization_id UUID NOT NULL,
    target_organization_id UUID NOT NULL,
    rag_feature TEXT NOT NULL,
    item_id TEXT NOT NULL,
    sharing_type TEXT DEFAULT 'read_only' CHECK (sharing_type IN ('read_only', 'collaborative')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'revoked')),
    shared_by UUID REFERENCES auth.users(id),
    approved_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_organization_id, target_organization_id, rag_feature, item_id)
);

-- Create indexes for context_sharing
CREATE INDEX IF NOT EXISTS idx_context_sharing_source ON public.context_sharing(source_organization_id);
CREATE INDEX IF NOT EXISTS idx_context_sharing_target ON public.context_sharing(target_organization_id);
CREATE INDEX IF NOT EXISTS idx_context_sharing_status ON public.context_sharing(status);

-- Create organization_context_quotas table for managing tenant limits
CREATE TABLE IF NOT EXISTS public.organization_context_quotas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL UNIQUE,
    max_context_items INTEGER DEFAULT 1000,
    max_global_access_features INTEGER DEFAULT 10,
    max_sharing_requests INTEGER DEFAULT 50,
    current_context_items INTEGER DEFAULT 0,
    current_global_access INTEGER DEFAULT 0,
    current_sharing_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for organization_context_quotas
CREATE INDEX IF NOT EXISTS idx_org_context_quotas_org ON public.organization_context_quotas(organization_id);

-- Create context_upload_logs table for tracking uploads
CREATE TABLE IF NOT EXISTS public.context_upload_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID,
    upload_type TEXT NOT NULL CHECK (upload_type IN ('individual', 'bulk', 'file', 'web_scrape', 'api')),
    rag_feature TEXT NOT NULL,
    items_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    upload_source TEXT, -- File path, URL, API endpoint, etc.
    uploaded_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for context_upload_logs
CREATE INDEX IF NOT EXISTS idx_context_upload_logs_org ON public.context_upload_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_context_upload_logs_type ON public.context_upload_logs(upload_type);
CREATE INDEX IF NOT EXISTS idx_context_upload_logs_created ON public.context_upload_logs(created_at);

-- Add RLS policies for security
ALTER TABLE public.global_context_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_context_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.context_sharing ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_context_quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.context_upload_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for global_context_items (system admins can manage, tenants can read based on access)
CREATE POLICY "System admins can manage global context" ON public.global_context_items
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() AND role = 'system_admin'
        )
    );

CREATE POLICY "Tenants can read global context based on access" ON public.global_context_items
    FOR SELECT USING (
        status = 'active' AND EXISTS (
            SELECT 1 FROM public.tenant_context_access tca
            JOIN public.profiles p ON p.organization_id = tca.organization_id
            WHERE tca.rag_feature = global_context_items.rag_feature
            AND tca.enabled = true
            AND p.user_id = auth.uid()
        )
    );

-- RLS Policies for tenant_context_access (org admins can manage their org's access)
CREATE POLICY "Org admins can manage their tenant access" ON public.tenant_context_access
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = tenant_context_access.organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

-- RLS Policies for context_sharing (participating organizations can manage)
CREATE POLICY "Organizations can manage their sharing" ON public.context_sharing
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id IN (context_sharing.source_organization_id, context_sharing.target_organization_id)
            AND role IN ('org_admin', 'system_admin')
        )
    );

-- RLS Policies for organization_context_quotas (org admins can view, system admins can manage)
CREATE POLICY "Org admins can view their quotas" ON public.organization_context_quotas
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = organization_context_quotas.organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

CREATE POLICY "System admins can manage all quotas" ON public.organization_context_quotas
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() AND role = 'system_admin'
        )
    );

-- RLS Policies for context_upload_logs (users can view their org's logs)
CREATE POLICY "Users can view their org's upload logs" ON public.context_upload_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = context_upload_logs.organization_id
        )
    );

CREATE POLICY "System admins can view all upload logs" ON public.context_upload_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() AND role = 'system_admin'
        )
    );
