-- Additional schema for tenant isolation and RAG feature toggles
-- This extends the enhanced RAG context schema

-- Create tenant_isolation_policies table
CREATE TABLE IF NOT EXISTS public.tenant_isolation_policies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL,
    policy_type TEXT NOT NULL CHECK (policy_type IN ('data_access', 'cross_tenant', 'resource_sharing', 'api_access')),
    policy_name TEXT NOT NULL,
    policy_rules JSONB NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for tenant_isolation_policies
CREATE INDEX IF NOT EXISTS idx_tenant_isolation_policies_org ON public.tenant_isolation_policies(organization_id);
CREATE INDEX IF NOT EXISTS idx_tenant_isolation_policies_type ON public.tenant_isolation_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_tenant_isolation_policies_status ON public.tenant_isolation_policies(status);

-- Create cross_tenant_permissions table
CREATE TABLE IF NOT EXISTS public.cross_tenant_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    target_organization_id UUID NOT NULL,
    resource_type TEXT NOT NULL,
    permission_level TEXT DEFAULT 'read' CHECK (permission_level IN ('read', 'write', 'admin')),
    enabled BOOLEAN DEFAULT true,
    granted_by UUID REFERENCES auth.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for cross_tenant_permissions
CREATE INDEX IF NOT EXISTS idx_cross_tenant_permissions_user ON public.cross_tenant_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_cross_tenant_permissions_target ON public.cross_tenant_permissions(target_organization_id);
CREATE INDEX IF NOT EXISTS idx_cross_tenant_permissions_resource ON public.cross_tenant_permissions(resource_type);

-- Create organization_rag_toggles table
CREATE TABLE IF NOT EXISTS public.organization_rag_toggles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL,
    rag_feature TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, rag_feature)
);

-- Create indexes for organization_rag_toggles
CREATE INDEX IF NOT EXISTS idx_organization_rag_toggles_org ON public.organization_rag_toggles(organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_rag_toggles_feature ON public.organization_rag_toggles(rag_feature);
CREATE INDEX IF NOT EXISTS idx_organization_rag_toggles_enabled ON public.organization_rag_toggles(enabled);

-- Create quota_usage_logs table for tracking quota usage
CREATE TABLE IF NOT EXISTS public.quota_usage_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id UUID NOT NULL,
    quota_type TEXT NOT NULL CHECK (quota_type IN ('context_items', 'global_access', 'sharing_requests')),
    operation TEXT NOT NULL CHECK (operation IN ('increment', 'decrement', 'reset')),
    quantity INTEGER NOT NULL,
    previous_value INTEGER NOT NULL,
    new_value INTEGER NOT NULL,
    operation_reason TEXT,
    performed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for quota_usage_logs
CREATE INDEX IF NOT EXISTS idx_quota_usage_logs_org ON public.quota_usage_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_quota_usage_logs_type ON public.quota_usage_logs(quota_type);
CREATE INDEX IF NOT EXISTS idx_quota_usage_logs_created ON public.quota_usage_logs(created_at);

-- Create isolation_violation_logs table for security monitoring
CREATE TABLE IF NOT EXISTS public.isolation_violation_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    organization_id UUID NOT NULL,
    violation_type TEXT NOT NULL CHECK (violation_type IN ('cross_tenant_access', 'quota_exceeded', 'unauthorized_resource', 'policy_violation')),
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    violation_details JSONB,
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    blocked BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for isolation_violation_logs
CREATE INDEX IF NOT EXISTS idx_isolation_violation_logs_user ON public.isolation_violation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_isolation_violation_logs_org ON public.isolation_violation_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_isolation_violation_logs_type ON public.isolation_violation_logs(violation_type);
CREATE INDEX IF NOT EXISTS idx_isolation_violation_logs_severity ON public.isolation_violation_logs(severity);
CREATE INDEX IF NOT EXISTS idx_isolation_violation_logs_created ON public.isolation_violation_logs(created_at);

-- Add RLS policies for new tables
ALTER TABLE public.tenant_isolation_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cross_tenant_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_rag_toggles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quota_usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.isolation_violation_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for tenant_isolation_policies
CREATE POLICY "Org admins can manage their isolation policies" ON public.tenant_isolation_policies
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = tenant_isolation_policies.organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

-- RLS Policies for cross_tenant_permissions
CREATE POLICY "Users can view their cross-tenant permissions" ON public.cross_tenant_permissions
    FOR SELECT USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = cross_tenant_permissions.target_organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

CREATE POLICY "System admins can manage all cross-tenant permissions" ON public.cross_tenant_permissions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() AND role = 'system_admin'
        )
    );

-- RLS Policies for organization_rag_toggles
CREATE POLICY "Org admins can manage their RAG toggles" ON public.organization_rag_toggles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = organization_rag_toggles.organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

-- RLS Policies for quota_usage_logs
CREATE POLICY "Org admins can view their quota usage logs" ON public.quota_usage_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = quota_usage_logs.organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

CREATE POLICY "System admins can view all quota usage logs" ON public.quota_usage_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() AND role = 'system_admin'
        )
    );

-- RLS Policies for isolation_violation_logs
CREATE POLICY "Org admins can view their violation logs" ON public.isolation_violation_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() 
            AND organization_id = isolation_violation_logs.organization_id
            AND role IN ('org_admin', 'system_admin')
        )
    );

CREATE POLICY "System admins can view all violation logs" ON public.isolation_violation_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE user_id = auth.uid() AND role = 'system_admin'
        )
    );

-- Create functions for quota management
CREATE OR REPLACE FUNCTION update_quota_usage(
    org_id UUID,
    quota_type TEXT,
    operation TEXT,
    quantity INTEGER,
    reason TEXT DEFAULT NULL,
    user_id UUID DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    current_quota INTEGER;
    new_quota INTEGER;
    quota_record RECORD;
BEGIN
    -- Get current quota value
    SELECT * INTO quota_record 
    FROM organization_context_quotas 
    WHERE organization_id = org_id;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Organization quotas not found');
    END IF;
    
    -- Determine current value based on quota type
    CASE quota_type
        WHEN 'context_items' THEN current_quota := quota_record.current_context_items;
        WHEN 'global_access' THEN current_quota := quota_record.current_global_access;
        WHEN 'sharing_requests' THEN current_quota := quota_record.current_sharing_requests;
        ELSE RETURN jsonb_build_object('success', false, 'error', 'Invalid quota type');
    END CASE;
    
    -- Calculate new value
    IF operation = 'increment' THEN
        new_quota := current_quota + quantity;
    ELSIF operation = 'decrement' THEN
        new_quota := GREATEST(0, current_quota - quantity);
    ELSIF operation = 'reset' THEN
        new_quota := 0;
    ELSE
        RETURN jsonb_build_object('success', false, 'error', 'Invalid operation');
    END IF;
    
    -- Update quota
    CASE quota_type
        WHEN 'context_items' THEN 
            UPDATE organization_context_quotas 
            SET current_context_items = new_quota, updated_at = NOW()
            WHERE organization_id = org_id;
        WHEN 'global_access' THEN 
            UPDATE organization_context_quotas 
            SET current_global_access = new_quota, updated_at = NOW()
            WHERE organization_id = org_id;
        WHEN 'sharing_requests' THEN 
            UPDATE organization_context_quotas 
            SET current_sharing_requests = new_quota, updated_at = NOW()
            WHERE organization_id = org_id;
    END CASE;
    
    -- Log the operation
    INSERT INTO quota_usage_logs (
        organization_id, quota_type, operation, quantity, 
        previous_value, new_value, operation_reason, performed_by
    ) VALUES (
        org_id, quota_type, operation, quantity,
        current_quota, new_quota, reason, user_id
    );
    
    RETURN jsonb_build_object(
        'success', true,
        'previous_value', current_quota,
        'new_value', new_quota,
        'quota_type', quota_type
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check quota limits
CREATE OR REPLACE FUNCTION check_quota_limit(
    org_id UUID,
    quota_type TEXT,
    requested_quantity INTEGER
) RETURNS JSONB AS $$
DECLARE
    quota_record RECORD;
    current_value INTEGER;
    max_value INTEGER;
BEGIN
    -- Get quota record
    SELECT * INTO quota_record 
    FROM organization_context_quotas 
    WHERE organization_id = org_id;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Organization quotas not found');
    END IF;
    
    -- Get current and max values based on quota type
    CASE quota_type
        WHEN 'context_items' THEN 
            current_value := quota_record.current_context_items;
            max_value := quota_record.max_context_items;
        WHEN 'global_access' THEN 
            current_value := quota_record.current_global_access;
            max_value := quota_record.max_global_access_features;
        WHEN 'sharing_requests' THEN 
            current_value := quota_record.current_sharing_requests;
            max_value := quota_record.max_sharing_requests;
        ELSE 
            RETURN jsonb_build_object('success', false, 'error', 'Invalid quota type');
    END CASE;
    
    -- Check if limit would be exceeded
    IF current_value + requested_quantity > max_value THEN
        RETURN jsonb_build_object(
            'success', false,
            'quota_exceeded', true,
            'current_value', current_value,
            'max_value', max_value,
            'requested_quantity', requested_quantity,
            'quota_type', quota_type
        );
    END IF;
    
    RETURN jsonb_build_object(
        'success', true,
        'quota_check_passed', true,
        'current_value', current_value,
        'max_value', max_value,
        'requested_quantity', requested_quantity
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
