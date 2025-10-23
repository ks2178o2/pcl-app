-- RAG Feature Management Database Schema
-- Migration: Add hierarchical organization support and RAG feature metadata

-- 1. Add parent_organization_id to organizations table for hierarchy support
ALTER TABLE organizations 
ADD COLUMN IF NOT EXISTS parent_organization_id UUID REFERENCES organizations(id);

-- 2. Create index for efficient hierarchy queries
CREATE INDEX IF NOT EXISTS idx_organizations_parent_id ON organizations(parent_organization_id);

-- 3. Create rag_feature_metadata table with descriptions and role assignments
CREATE TABLE IF NOT EXISTS rag_feature_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rag_feature VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('sales', 'manager', 'admin')),
    icon VARCHAR(100),
    color VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- 4. Create index for efficient category queries
CREATE INDEX IF NOT EXISTS idx_rag_feature_metadata_category ON rag_feature_metadata(category);
CREATE INDEX IF NOT EXISTS idx_rag_feature_metadata_active ON rag_feature_metadata(is_active);

-- 5. Insert the 20 default RAG features with proper categorization
INSERT INTO rag_feature_metadata (rag_feature, name, description, category, icon, color) VALUES
-- Sales-Focused Features
('best_practice_kb', 'Best Practice Knowledge Base', 'Sales best practices and proven methodologies', 'sales', 'book-open', 'blue'),
('customer_insight_rag', 'Customer Intelligence', 'Customer history, preferences, and behavior patterns', 'sales', 'users', 'blue'),
('success_pattern_rag', 'Success Pattern Analysis', 'Successful sales patterns and winning strategies', 'sales', 'trending-up', 'blue'),
('content_personalization_rag', 'Content Personalization', 'Personalized content generation for prospects', 'sales', 'target', 'blue'),
('live_call_coaching_rag', 'Live Call Coaching', 'Real-time assistance during sales calls', 'sales', 'phone', 'blue'),
('unified_customer_view_rag', 'Unified Customer View', '360-degree view of customer interactions', 'sales', 'eye', 'blue'),

-- Manager-Focused Features
('performance_improvement_rag', 'Performance Improvement', 'Team performance insights and recommendations', 'manager', 'bar-chart', 'purple'),
('predictive_analytics_rag', 'Predictive Analytics', 'Sales forecasting and trend prediction', 'manager', 'crystal-ball', 'purple'),
('performance_benchmarking_rag', 'Performance Benchmarking', 'Team benchmarking against industry standards', 'manager', 'award', 'purple'),
('trend_analysis_rag', 'Trend Analysis', 'Market trend analysis and insights', 'manager', 'line-chart', 'purple'),
('knowledge_sharing_rag', 'Knowledge Sharing', 'Cross-team knowledge sharing platform', 'manager', 'share-2', 'purple'),
('best_practice_transfer_rag', 'Best Practice Transfer', 'Distribution of best practices across teams', 'manager', 'repeat', 'purple'),
('resource_optimization_rag', 'Resource Optimization', 'Resource allocation and optimization', 'manager', 'cpu', 'purple'),

-- Admin-Focused Features
('regulatory_guidance_rag', 'Regulatory Guidance', 'Compliance and regulatory information', 'admin', 'shield', 'red'),
('legal_knowledge_rag', 'Legal Knowledge Base', 'Legal documentation and guidance', 'admin', 'scale', 'red'),
('scheduling_intelligence_rag', 'Scheduling Intelligence', 'Team scheduling and resource planning', 'admin', 'calendar', 'red'),
('dynamic_content_rag', 'Dynamic Content Management', 'Dynamic content creation and management', 'admin', 'edit', 'red'),
('multi_channel_optimization_rag', 'Multi-Channel Optimization', 'Channel optimization and management', 'admin', 'layers', 'red'),
('document_intelligence_integration', 'Document Intelligence', 'Document processing and analysis', 'admin', 'file-text', 'red'),
('historical_context_rag', 'Historical Context', 'Historical data analysis and insights', 'admin', 'clock', 'red')

ON CONFLICT (rag_feature) DO NOTHING;

-- 6. Add category field to existing organization_rag_toggles table if it doesn't exist
ALTER TABLE organization_rag_toggles 
ADD COLUMN IF NOT EXISTS category VARCHAR(50) CHECK (category IN ('sales', 'manager', 'admin'));

-- 7. Update existing organization_rag_toggles with category information
UPDATE organization_rag_toggles 
SET category = (
    SELECT rfm.category 
    FROM rag_feature_metadata rfm 
    WHERE rfm.rag_feature = organization_rag_toggles.rag_feature
)
WHERE category IS NULL;

-- 8. Create index for efficient category filtering
CREATE INDEX IF NOT EXISTS idx_organization_rag_toggles_category ON organization_rag_toggles(category);

-- 9. Add inheritance tracking fields to organization_rag_toggles
ALTER TABLE organization_rag_toggles 
ADD COLUMN IF NOT EXISTS is_inherited BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS inherited_from UUID REFERENCES organizations(id);

-- 10. Create index for inheritance queries
CREATE INDEX IF NOT EXISTS idx_organization_rag_toggles_inherited ON organization_rag_toggles(is_inherited);
CREATE INDEX IF NOT EXISTS idx_organization_rag_toggles_inherited_from ON organization_rag_toggles(inherited_from);

-- 11. Create audit table for RAG feature toggle changes
CREATE TABLE IF NOT EXISTS rag_feature_toggle_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    rag_feature VARCHAR(100) NOT NULL,
    old_enabled BOOLEAN,
    new_enabled BOOLEAN,
    changed_by UUID NOT NULL REFERENCES users(id),
    change_reason TEXT,
    is_inherited BOOLEAN DEFAULT false,
    inherited_from UUID REFERENCES organizations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. Create indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_rag_feature_toggle_audit_org ON rag_feature_toggle_audit(organization_id);
CREATE INDEX IF NOT EXISTS idx_rag_feature_toggle_audit_feature ON rag_feature_toggle_audit(rag_feature);
CREATE INDEX IF NOT EXISTS idx_rag_feature_toggle_audit_created_at ON rag_feature_toggle_audit(created_at);

-- 13. Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 14. Create trigger for rag_feature_metadata updated_at
DROP TRIGGER IF EXISTS update_rag_feature_metadata_updated_at ON rag_feature_metadata;
CREATE TRIGGER update_rag_feature_metadata_updated_at
    BEFORE UPDATE ON rag_feature_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 15. Create view for organization hierarchy
CREATE OR REPLACE VIEW organization_hierarchy AS
WITH RECURSIVE org_tree AS (
    -- Base case: root organizations (no parent)
    SELECT 
        id,
        name,
        parent_organization_id,
        0 as level,
        ARRAY[id] as path,
        id as root_id
    FROM organizations 
    WHERE parent_organization_id IS NULL
    
    UNION ALL
    
    -- Recursive case: child organizations
    SELECT 
        o.id,
        o.name,
        o.parent_organization_id,
        ot.level + 1,
        ot.path || o.id,
        ot.root_id
    FROM organizations o
    JOIN org_tree ot ON o.parent_organization_id = ot.id
)
SELECT 
    id,
    name,
    parent_organization_id,
    level,
    path,
    root_id,
    array_length(path, 1) - 1 as depth
FROM org_tree
ORDER BY path;

-- 16. Create view for effective RAG features (own + inherited)
CREATE OR REPLACE VIEW effective_rag_features AS
WITH RECURSIVE org_hierarchy AS (
    -- Get all organizations with their hierarchy
    SELECT id, parent_organization_id, 0 as level
    FROM organizations
    WHERE parent_organization_id IS NULL
    
    UNION ALL
    
    SELECT o.id, o.parent_organization_id, oh.level + 1
    FROM organizations o
    JOIN org_hierarchy oh ON o.parent_organization_id = oh.id
),
inherited_features AS (
    -- Get features inherited from parent organizations
    SELECT DISTINCT
        ort.organization_id,
        ort.rag_feature,
        ort.enabled,
        ort.is_inherited,
        ort.inherited_from,
        rfm.category
    FROM organization_rag_toggles ort
    JOIN rag_feature_metadata rfm ON ort.rag_feature = rfm.rag_feature
    WHERE ort.is_inherited = true
),
own_features AS (
    -- Get features owned by the organization
    SELECT DISTINCT
        ort.organization_id,
        ort.rag_feature,
        ort.enabled,
        ort.is_inherited,
        ort.inherited_from,
        rfm.category
    FROM organization_rag_toggles ort
    JOIN rag_feature_metadata rfm ON ort.rag_feature = rfm.rag_feature
    WHERE ort.is_inherited = false
)
SELECT 
    COALESCE(of.organization_id, inf.organization_id) as organization_id,
    COALESCE(of.rag_feature, inf.rag_feature) as rag_feature,
    COALESCE(of.enabled, inf.enabled) as enabled,
    COALESCE(of.is_inherited, inf.is_inherited) as is_inherited,
    COALESCE(of.inherited_from, inf.inherited_from) as inherited_from,
    COALESCE(of.category, inf.category) as category,
    CASE 
        WHEN of.rag_feature IS NOT NULL THEN 'own'
        WHEN inf.rag_feature IS NOT NULL THEN 'inherited'
        ELSE 'none'
    END as source_type
FROM own_features of
FULL OUTER JOIN inherited_features inf 
    ON of.organization_id = inf.organization_id 
    AND of.rag_feature = inf.rag_feature;

-- 17. Add comments for documentation
COMMENT ON TABLE rag_feature_metadata IS 'Global catalog of RAG features with metadata and categorization';
COMMENT ON COLUMN organizations.parent_organization_id IS 'Parent organization for hierarchical structure';
COMMENT ON COLUMN organization_rag_toggles.category IS 'Category of the RAG feature (sales, manager, admin)';
COMMENT ON COLUMN organization_rag_toggles.is_inherited IS 'Whether this toggle is inherited from parent organization';
COMMENT ON COLUMN organization_rag_toggles.inherited_from IS 'Organization ID from which this feature is inherited';
COMMENT ON TABLE rag_feature_toggle_audit IS 'Audit trail for RAG feature toggle changes';
COMMENT ON VIEW organization_hierarchy IS 'Recursive view showing organization hierarchy tree';
COMMENT ON VIEW effective_rag_features IS 'View showing effective RAG features (own + inherited) for each organization';
