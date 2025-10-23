
-- Create audit_logs table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON public.audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at);


-- Create rag_context_items table
CREATE TABLE IF NOT EXISTS public.rag_context_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL,
    rag_feature TEXT NOT NULL,
    item_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_title TEXT NOT NULL,
    item_content TEXT NOT NULL,
    status TEXT DEFAULT 'included' CHECK (status IN ('included', 'excluded', 'pending')),
    priority INTEGER DEFAULT 1,
    confidence_score DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for rag_context_items
CREATE INDEX IF NOT EXISTS idx_rag_context_items_org_id ON public.rag_context_items(organization_id);
CREATE INDEX IF NOT EXISTS idx_rag_context_items_feature ON public.rag_context_items(rag_feature);
CREATE INDEX IF NOT EXISTS idx_rag_context_items_status ON public.rag_context_items(status);
