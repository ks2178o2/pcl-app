/**
 * Client-side validation utilities for RAG features
 * Provides validation functions for RAG feature operations
 */

import { 
  RAGFeature, 
  RAGFeatureWithToggle, 
  RAGFeatureCategory, 
  UserRole,
  validateRAGFeature,
  validateFeatureToggle
} from '../types/rag-features';

// ==================== VALIDATION TYPES ====================

export interface ValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
}

export interface RAGFeatureValidationOptions {
  organizationId: string;
  userRole: UserRole;
  enabledFeatures: string[];
  isParentOrganization?: boolean;
}

// ==================== CORE VALIDATION FUNCTIONS ====================

export const validateRAGFeatureSelection = (
  feature: string,
  options: RAGFeatureValidationOptions
): ValidationResult => {
  // Check if feature is provided
  if (!feature || feature.trim() === '') {
    return {
      valid: false,
      error: 'RAG feature is required'
    };
  }

  // Check if feature is enabled for the organization
  if (!options.enabledFeatures.includes(feature)) {
    return {
      valid: false,
      error: `Feature '${feature}' is not enabled for your organization`
    };
  }

  // Check user permissions for the feature
  const permissionResult = validateUserPermission(feature, options.userRole);
  if (!permissionResult.valid) {
    return permissionResult;
  }

  return { valid: true };
};

export const validateFeatureToggleOperation = (
  feature: RAGFeatureWithToggle,
  options: RAGFeatureValidationOptions
): ValidationResult => {
  // Check if user can manage features
  if (!canUserManageFeatures(options.userRole)) {
    return {
      valid: false,
      error: 'Insufficient permissions to toggle features'
    };
  }

  // Check inheritance rules
  if (feature.is_inherited && !options.isParentOrganization) {
    return {
      valid: false,
      error: 'Cannot modify inherited features. Contact your parent organization.'
    };
  }

  // Check if trying to enable a feature that parent has disabled
  if (feature.enabled && feature.is_inherited && !options.isParentOrganization) {
    return {
      valid: false,
      error: 'Cannot enable inherited features. Parent organization controls this feature.'
    };
  }

  return { valid: true };
};

export const validateBulkToggleOperation = (
  features: RAGFeatureWithToggle[],
  updates: Record<string, boolean>,
  options: RAGFeatureValidationOptions
): ValidationResult => {
  // Check if user can manage features
  if (!canUserManageFeatures(options.userRole)) {
    return {
      valid: false,
      error: 'Insufficient permissions for bulk operations'
    };
  }

  // Validate each update
  const errors: string[] = [];
  const warnings: string[] = [];

  for (const [featureName, enabled] of Object.entries(updates)) {
    const feature = features.find(f => f.rag_feature === featureName);
    if (!feature) {
      errors.push(`Feature '${featureName}' not found`);
      continue;
    }

    const validation = validateFeatureToggleOperation(feature, options);
    if (!validation.valid) {
      errors.push(`${featureName}: ${validation.error}`);
    }

    if (validation.warning) {
      warnings.push(`${featureName}: ${validation.warning}`);
    }
  }

  if (errors.length > 0) {
    return {
      valid: false,
      error: errors.join('; ')
    };
  }

  if (warnings.length > 0) {
    return {
      valid: true,
      warning: warnings.join('; ')
    };
  }

  return { valid: true };
};

export const validateUserPermission = (
  feature: string,
  userRole: UserRole
): ValidationResult => {
  // Define role-based feature access
  const rolePermissions: Record<UserRole, string[]> = {
    system_admin: ['*'], // Access to all features
    org_admin: ['sales', 'manager', 'admin'],
    manager: ['sales', 'manager'],
    salesperson: ['sales'],
    user: ['sales']
  };

  const userPermissions = rolePermissions[userRole] || [];
  
  // System admin has access to everything
  if (userPermissions.includes('*')) {
    return { valid: true };
  }

  // Check if user has permission for this feature category
  // This is a simplified check - in reality, you'd check against feature metadata
  const featureCategory = getFeatureCategory(feature);
  if (featureCategory && userPermissions.includes(featureCategory)) {
    return { valid: true };
  }

  return {
    valid: false,
    error: `Your role '${userRole}' does not have access to this feature`
  };
};

// ==================== FORM VALIDATION ====================

export const validateRAGFeatureForm = (formData: {
  rag_feature: string;
  name: string;
  description?: string;
  category: RAGFeatureCategory;
}, options: RAGFeatureValidationOptions): ValidationResult => {
  const errors: string[] = [];

  // Required fields
  if (!formData.rag_feature || formData.rag_feature.trim() === '') {
    errors.push('RAG feature identifier is required');
  }

  if (!formData.name || formData.name.trim() === '') {
    errors.push('Feature name is required');
  }

  if (!formData.category) {
    errors.push('Feature category is required');
  }

  // Format validation
  if (formData.rag_feature && !/^[a-z_]+$/.test(formData.rag_feature)) {
    errors.push('RAG feature identifier must contain only lowercase letters and underscores');
  }

  if (formData.name && formData.name.length > 100) {
    errors.push('Feature name must be 100 characters or less');
  }

  if (formData.description && formData.description.length > 500) {
    errors.push('Description must be 500 characters or less');
  }

  // Permission validation
  if (options.userRole !== 'system_admin') {
    errors.push('Only system administrators can create new RAG features');
  }

  if (errors.length > 0) {
    return {
      valid: false,
      error: errors.join('; ')
    };
  }

  return { valid: true };
};

export const validateOrganizationForm = (formData: {
  name: string;
  parent_organization_id?: string;
}, options: RAGFeatureValidationOptions): ValidationResult => {
  const errors: string[] = [];

  // Required fields
  if (!formData.name || formData.name.trim() === '') {
    errors.push('Organization name is required');
  }

  // Format validation
  if (formData.name && formData.name.length > 200) {
    errors.push('Organization name must be 200 characters or less');
  }

  // Permission validation
  if (options.userRole !== 'system_admin') {
    errors.push('Only system administrators can create organizations');
  }

  if (errors.length > 0) {
    return {
      valid: false,
      error: errors.join('; ')
    };
  }

  return { valid: true };
};

// ==================== SHARING VALIDATION ====================

export const validateSharingRequest = (request: {
  source_organization_id: string;
  target_organization_id: string;
  rag_feature: string;
  item_id: string;
}, options: RAGFeatureValidationOptions): ValidationResult => {
  const errors: string[] = [];

  // Required fields
  if (!request.source_organization_id) {
    errors.push('Source organization is required');
  }

  if (!request.target_organization_id) {
    errors.push('Target organization is required');
  }

  if (!request.rag_feature) {
    errors.push('RAG feature is required');
  }

  if (!request.item_id) {
    errors.push('Item ID is required');
  }

  // Business logic validation
  if (request.source_organization_id === request.target_organization_id) {
    errors.push('Cannot share with the same organization');
  }

  // Permission validation
  if (!canUserShareContent(options.userRole)) {
    errors.push('Insufficient permissions to share content');
  }

  if (errors.length > 0) {
    return {
      valid: false,
      error: errors.join('; ')
    };
  }

  return { valid: true };
};

// ==================== UTILITY FUNCTIONS ====================

export const canUserManageFeatures = (userRole: UserRole): boolean => {
  return ['system_admin', 'org_admin'].includes(userRole);
};

export const canUserViewFeatures = (userRole: UserRole): boolean => {
  return ['system_admin', 'org_admin', 'manager', 'salesperson'].includes(userRole);
};

export const canUserShareContent = (userRole: UserRole): boolean => {
  return ['system_admin', 'org_admin', 'manager'].includes(userRole);
};

export const canUserApproveSharing = (userRole: UserRole): boolean => {
  return ['system_admin', 'org_admin'].includes(userRole);
};

export const getFeatureCategory = (feature: string): RAGFeatureCategory | null => {
  // This is a simplified mapping - in reality, you'd get this from feature metadata
  const categoryMap: Record<string, RAGFeatureCategory> = {
    'best_practice_kb': 'sales',
    'customer_insight_rag': 'sales',
    'success_pattern_rag': 'sales',
    'content_personalization_rag': 'sales',
    'live_call_coaching_rag': 'sales',
    'unified_customer_view_rag': 'sales',
    'performance_improvement_rag': 'manager',
    'predictive_analytics_rag': 'manager',
    'performance_benchmarking_rag': 'manager',
    'trend_analysis_rag': 'manager',
    'knowledge_sharing_rag': 'manager',
    'best_practice_transfer_rag': 'manager',
    'resource_optimization_rag': 'manager',
    'regulatory_guidance_rag': 'admin',
    'legal_knowledge_rag': 'admin',
    'scheduling_intelligence_rag': 'admin',
    'dynamic_content_rag': 'admin',
    'multi_channel_optimization_rag': 'admin',
    'document_intelligence_integration': 'admin',
    'historical_context_rag': 'admin'
  };

  return categoryMap[feature] || null;
};

// ==================== REAL-TIME VALIDATION ====================

export const createRealTimeValidator = (
  options: RAGFeatureValidationOptions
) => {
  return {
    validateFeature: (feature: string) => validateRAGFeatureSelection(feature, options),
    validateToggle: (feature: RAGFeatureWithToggle) => validateFeatureToggleOperation(feature, options),
    validateBulk: (features: RAGFeatureWithToggle[], updates: Record<string, boolean>) => 
      validateBulkToggleOperation(features, updates, options),
    validateForm: (formData: any) => validateRAGFeatureForm(formData, options),
    validateSharing: (request: any) => validateSharingRequest(request, options)
  };
};

// ==================== VALIDATION HOOKS ====================

export const useRAGFeatureValidation = (options: RAGFeatureValidationOptions) => {
  const validator = createRealTimeValidator(options);

  const validateOnChange = (value: string, type: 'feature' | 'toggle' | 'form' | 'sharing') => {
    switch (type) {
      case 'feature':
        return validator.validateFeature(value);
      case 'form':
        return validator.validateForm(value);
      case 'sharing':
        return validator.validateSharing(value);
      default:
        return { valid: true };
    }
  };

  const validateOnSubmit = (data: any, type: 'form' | 'bulk' | 'sharing') => {
    switch (type) {
      case 'form':
        return validator.validateForm(data);
      case 'bulk':
        return validator.validateBulk(data.features, data.updates);
      case 'sharing':
        return validator.validateSharing(data);
      default:
        return { valid: true };
    }
  };

  return {
    validateOnChange,
    validateOnSubmit,
    validator,
    canManageFeatures: canUserManageFeatures(options.userRole),
    canViewFeatures: canUserViewFeatures(options.userRole),
    canShareContent: canUserShareContent(options.userRole),
    canApproveSharing: canUserApproveSharing(options.userRole)
  };
};

// ==================== EXPORTS ====================

export {
  validateRAGFeature,
  validateFeatureToggle
} from '../types/rag-features';
