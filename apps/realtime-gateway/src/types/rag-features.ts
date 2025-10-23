/**
 * RAG Feature Management - TypeScript Types and Constants
 * Defines types, interfaces, and constants for RAG feature management
 */

// ==================== CORE TYPES ====================

export type RAGFeatureCategory = 'sales' | 'manager' | 'admin';

export type UserRole = 'system_admin' | 'org_admin' | 'manager' | 'salesperson' | 'user';

export type ToggleStatus = 'enabled' | 'disabled' | 'inherited';

export type FeatureSource = 'own' | 'inherited' | 'none';

// ==================== INTERFACES ====================

export interface RAGFeature {
  id?: string;
  rag_feature: string;
  name: string;
  description?: string;
  category: RAGFeatureCategory;
  icon?: string;
  color?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
}

export interface RAGToggle {
  id?: string;
  organization_id: string;
  rag_feature: string;
  enabled: boolean;
  category?: RAGFeatureCategory;
  is_inherited: boolean;
  inherited_from?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RAGFeatureWithToggle extends RAGFeature {
  enabled: boolean;
  is_inherited: boolean;
  inherited_from?: string;
  source_type: FeatureSource;
}

export interface User {
  id: string;
  role: UserRole;
  organization_id: string;
  name?: string;
  email?: string;
}

export interface Organization {
  id: string;
  name: string;
  parent_organization_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RAGFeatureSummary {
  total_features: number;
  enabled_features: number;
  disabled_features: number;
  inherited_features: number;
  own_features: number;
  category_breakdown: Record<RAGFeatureCategory, { total: number; enabled: number }>;
  enabled_percentage: number;
}

// ==================== API RESPONSE TYPES ====================

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  total?: number;
}

export interface RAGFeatureResponse extends APIResponse<RAGFeature> {}
export interface RAGFeatureListResponse extends APIResponse<RAGFeature[]> {}
export interface RAGToggleResponse extends APIResponse<RAGToggle> {}
export interface RAGToggleListResponse extends APIResponse<RAGToggle[]> {}
export interface EnabledFeaturesResponse extends APIResponse<string[]> {}
export interface RAGFeatureSummaryResponse extends APIResponse<RAGFeatureSummary> {}

// ==================== REQUEST TYPES ====================

export interface RAGFeatureCreateRequest {
  rag_feature: string;
  name: string;
  description?: string;
  category: RAGFeatureCategory;
  icon?: string;
  color?: string;
}

export interface RAGFeatureUpdateRequest {
  name?: string;
  description?: string;
  category?: RAGFeatureCategory;
  icon?: string;
  color?: string;
  is_active?: boolean;
}

export interface RAGToggleUpdateRequest {
  enabled: boolean;
}

export interface BulkToggleUpdateRequest {
  updates: Record<string, boolean>;
}

// ==================== COMPONENT PROPS TYPES ====================

export interface RAGFeatureSelectorProps {
  value: string;
  onChange: (feature: string) => void;
  organizationId: string;
  filterByCategory?: RAGFeatureCategory;
  placeholder?: string;
  disabled?: boolean;
  showOnlyEnabled?: boolean;
  className?: string;
}

export interface RAGFeatureToggleCardProps {
  feature: RAGFeatureWithToggle;
  onToggle: (enabled: boolean) => void;
  disabled?: boolean;
  showInheritedBadge?: boolean;
  className?: string;
}

export interface RAGFeatureCategorySectionProps {
  category: RAGFeatureCategory;
  features: RAGFeatureWithToggle[];
  onToggle: (feature: string, enabled: boolean) => void;
  onBulkToggle: (enabled: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export interface RAGFeatureManagementProps {
  organizationId: string;
  className?: string;
}

export interface OrganizationTreeNode {
  id: string;
  name: string;
  parent_organization_id: string | null;
  children: OrganizationTreeNode[];
  level: number;
  path: string[];
  feature_count?: number;
  enabled_features?: number;
}

export interface SharingRequest {
  id: string;
  source_organization_id: string;
  target_organization_id: string;
  rag_feature: string;
  item_id: string;
  sharing_type: 'hierarchy_up' | 'hierarchy_down' | 'cross_org';
  status: 'pending' | 'approved' | 'rejected';
  shared_by: string;
  created_at: string;
  updated_at: string;
  approved_by?: string;
  rejected_by?: string;
  rejection_reason?: string;
}

export interface OrganizationHierarchyProps {
  rootOrganizationId: string;
  onOrganizationSelect?: (organization: OrganizationTreeNode) => void;
  onFeatureInheritanceView?: (organization: OrganizationTreeNode) => void;
  className?: string;
}

export interface SharingApprovalsProps {
  organizationId: string;
  className?: string;
}

// ==================== HOOK TYPES ====================

export interface UseRAGFeaturesReturn {
  features: RAGFeatureWithToggle[];
  enabledFeatures: string[];
  loading: boolean;
  error: string | null;
  toggleFeature: (feature: string, enabled: boolean) => Promise<void>;
  bulkToggle: (updates: Record<string, boolean>) => Promise<void>;
  refetch: () => Promise<void>;
  summary: RAGFeatureSummary | null;
}

export interface UseRAGFeatureCatalogReturn {
  catalog: RAGFeature[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// ==================== CONSTANTS ====================

export const RAG_FEATURE_CATEGORIES: Record<RAGFeatureCategory, {
  label: string;
  color: string;
  icon: string;
  description: string;
}> = {
  sales: {
    label: 'Sales-Focused',
    color: 'blue',
    icon: 'users',
    description: 'Features designed for salespeople and customer-facing roles'
  },
  manager: {
    label: 'Manager-Focused', 
    color: 'purple',
    icon: 'bar-chart',
    description: 'Features designed for managers and team leaders'
  },
  admin: {
    label: 'Admin-Focused',
    color: 'red', 
    icon: 'shield',
    description: 'Features designed for administrators and system managers'
  }
};

export const USER_ROLES: Record<UserRole, {
  label: string;
  level: number;
  permissions: string[];
}> = {
  system_admin: {
    label: 'System Administrator',
    level: 5,
    permissions: ['manage_global_features', 'manage_all_orgs', 'view_all_data']
  },
  org_admin: {
    label: 'Organization Administrator', 
    level: 4,
    permissions: ['manage_org_features', 'manage_org_users', 'view_org_data']
  },
  manager: {
    label: 'Manager',
    level: 3,
    permissions: ['view_team_data', 'manage_team_features']
  },
  salesperson: {
    label: 'Salesperson',
    level: 2,
    permissions: ['use_enabled_features', 'view_own_data']
  },
  user: {
    label: 'User',
    level: 1,
    permissions: ['use_enabled_features']
  }
};

export const DEFAULT_RAG_FEATURES: RAGFeature[] = [
  // Sales-Focused Features
  {
    rag_feature: 'best_practice_kb',
    name: 'Best Practice Knowledge Base',
    description: 'Sales best practices and proven methodologies',
    category: 'sales',
    icon: 'book-open',
    color: 'blue',
    is_active: true
  },
  {
    rag_feature: 'customer_insight_rag',
    name: 'Customer Intelligence',
    description: 'Customer history, preferences, and behavior patterns',
    category: 'sales',
    icon: 'users',
    color: 'blue',
    is_active: true
  },
  {
    rag_feature: 'success_pattern_rag',
    name: 'Success Pattern Analysis',
    description: 'Successful sales patterns and winning strategies',
    category: 'sales',
    icon: 'trending-up',
    color: 'blue',
    is_active: true
  },
  {
    rag_feature: 'content_personalization_rag',
    name: 'Content Personalization',
    description: 'Personalized content generation for prospects',
    category: 'sales',
    icon: 'target',
    color: 'blue',
    is_active: true
  },
  {
    rag_feature: 'live_call_coaching_rag',
    name: 'Live Call Coaching',
    description: 'Real-time assistance during sales calls',
    category: 'sales',
    icon: 'phone',
    color: 'blue',
    is_active: true
  },
  {
    rag_feature: 'unified_customer_view_rag',
    name: 'Unified Customer View',
    description: '360-degree view of customer interactions',
    category: 'sales',
    icon: 'eye',
    color: 'blue',
    is_active: true
  },

  // Manager-Focused Features
  {
    rag_feature: 'performance_improvement_rag',
    name: 'Performance Improvement',
    description: 'Team performance insights and recommendations',
    category: 'manager',
    icon: 'bar-chart',
    color: 'purple',
    is_active: true
  },
  {
    rag_feature: 'predictive_analytics_rag',
    name: 'Predictive Analytics',
    description: 'Sales forecasting and trend prediction',
    category: 'manager',
    icon: 'crystal-ball',
    color: 'purple',
    is_active: true
  },
  {
    rag_feature: 'performance_benchmarking_rag',
    name: 'Performance Benchmarking',
    description: 'Team benchmarking against industry standards',
    category: 'manager',
    icon: 'award',
    color: 'purple',
    is_active: true
  },
  {
    rag_feature: 'trend_analysis_rag',
    name: 'Trend Analysis',
    description: 'Market trend analysis and insights',
    category: 'manager',
    icon: 'line-chart',
    color: 'purple',
    is_active: true
  },
  {
    rag_feature: 'knowledge_sharing_rag',
    name: 'Knowledge Sharing',
    description: 'Cross-team knowledge sharing platform',
    category: 'manager',
    icon: 'share-2',
    color: 'purple',
    is_active: true
  },
  {
    rag_feature: 'best_practice_transfer_rag',
    name: 'Best Practice Transfer',
    description: 'Distribution of best practices across teams',
    category: 'manager',
    icon: 'repeat',
    color: 'purple',
    is_active: true
  },
  {
    rag_feature: 'resource_optimization_rag',
    name: 'Resource Optimization',
    description: 'Resource allocation and optimization',
    category: 'manager',
    icon: 'cpu',
    color: 'purple',
    is_active: true
  },

  // Admin-Focused Features
  {
    rag_feature: 'regulatory_guidance_rag',
    name: 'Regulatory Guidance',
    description: 'Compliance and regulatory information',
    category: 'admin',
    icon: 'shield',
    color: 'red',
    is_active: true
  },
  {
    rag_feature: 'legal_knowledge_rag',
    name: 'Legal Knowledge Base',
    description: 'Legal documentation and guidance',
    category: 'admin',
    icon: 'scale',
    color: 'red',
    is_active: true
  },
  {
    rag_feature: 'scheduling_intelligence_rag',
    name: 'Scheduling Intelligence',
    description: 'Team scheduling and resource planning',
    category: 'admin',
    icon: 'calendar',
    color: 'red',
    is_active: true
  },
  {
    rag_feature: 'dynamic_content_rag',
    name: 'Dynamic Content Management',
    description: 'Dynamic content creation and management',
    category: 'admin',
    icon: 'edit',
    color: 'red',
    is_active: true
  },
  {
    rag_feature: 'multi_channel_optimization_rag',
    name: 'Multi-Channel Optimization',
    description: 'Channel optimization and management',
    category: 'admin',
    icon: 'layers',
    color: 'red',
    is_active: true
  },
  {
    rag_feature: 'document_intelligence_integration',
    name: 'Document Intelligence',
    description: 'Document processing and analysis',
    category: 'admin',
    icon: 'file-text',
    color: 'red',
    is_active: true
  },
  {
    rag_feature: 'historical_context_rag',
    name: 'Historical Context',
    description: 'Historical data analysis and insights',
    category: 'admin',
    icon: 'clock',
    color: 'red',
    is_active: true
  }
];

// ==================== UTILITY FUNCTIONS ====================

export const getCategoryInfo = (category: RAGFeatureCategory) => {
  return RAG_FEATURE_CATEGORIES[category];
};

export const getUserRoleInfo = (role: UserRole) => {
  return USER_ROLES[role];
};

export const canUserManageFeatures = (userRole: UserRole): boolean => {
  return USER_ROLES[userRole].level >= USER_ROLES.org_admin.level;
};

export const canUserViewFeatures = (userRole: UserRole): boolean => {
  return USER_ROLES[userRole].level >= USER_ROLES.salesperson.level;
};

export const getFeaturesByCategory = (features: RAGFeature[]): Record<RAGFeatureCategory, RAGFeature[]> => {
  const result: Record<RAGFeatureCategory, RAGFeature[]> = {
    sales: [],
    manager: [],
    admin: []
  };

  features.forEach(feature => {
    if (result[feature.category]) {
      result[feature.category].push(feature);
    }
  });

  return result;
};

export const getEnabledFeatures = (features: RAGFeatureWithToggle[]): string[] => {
  return features
    .filter(feature => feature.enabled)
    .map(feature => feature.rag_feature);
};

export const getInheritedFeatures = (features: RAGFeatureWithToggle[]): RAGFeatureWithToggle[] => {
  return features.filter(feature => feature.is_inherited);
};

export const getOwnFeatures = (features: RAGFeatureWithToggle[]): RAGFeatureWithToggle[] => {
  return features.filter(feature => !feature.is_inherited);
};

// ==================== VALIDATION FUNCTIONS ====================

export const validateRAGFeature = (feature: string, enabledFeatures: string[]): { valid: boolean; error?: string } => {
  if (!feature) {
    return { valid: false, error: 'RAG feature is required' };
  }

  if (!enabledFeatures.includes(feature)) {
    return { valid: false, error: 'Feature not enabled for your organization' };
  }

  return { valid: true };
};

export const validateFeatureToggle = (feature: RAGFeatureWithToggle, isParent: boolean): { valid: boolean; error?: string } => {
  if (feature.is_inherited && !isParent) {
    return { valid: false, error: 'Cannot disable inherited features' };
  }

  return { valid: true };
};

// ==================== ERROR TYPES ====================

export interface RAGFeatureError {
  code: string;
  message: string;
  details?: any;
}

export const RAG_FEATURE_ERRORS = {
  FEATURE_NOT_ENABLED: 'FEATURE_NOT_ENABLED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  ORGANIZATION_NOT_FOUND: 'ORGANIZATION_NOT_FOUND',
  INVALID_FEATURE: 'INVALID_FEATURE',
  INHERITANCE_VIOLATION: 'INHERITANCE_VIOLATION',
  NETWORK_ERROR: 'NETWORK_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR'
} as const;

export type RAGFeatureErrorCode = typeof RAG_FEATURE_ERRORS[keyof typeof RAG_FEATURE_ERRORS];
