/**
 * RAG Feature API Client
 * Provides functions to interact with RAG feature management APIs
 */

import {
  RAGFeature,
  RAGToggle,
  RAGFeatureWithToggle,
  RAGFeatureResponse,
  RAGFeatureListResponse,
  RAGToggleResponse,
  RAGToggleListResponse,
  EnabledFeaturesResponse,
  RAGFeatureSummaryResponse,
  RAGFeatureCreateRequest,
  RAGFeatureUpdateRequest,
  RAGToggleUpdateRequest,
  BulkToggleUpdateRequest,
  RAGFeatureCategory,
  OrganizationTreeNode,
  SharingRequest,
  APIResponse
} from '../types/rag-features';

// ==================== API CONFIGURATION ====================

import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth token from Supabase
const getAuthToken = async (): Promise<string | null> => {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
};

// Get headers with authentication
const getAuthHeaders = async (): Promise<HeadersInit> => {
  const token = await getAuthToken();
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

// ==================== UTILITY FUNCTIONS ====================

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
};

const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

// ==================== RAG FEATURE CATALOG API ====================

export const ragFeatureCatalogApi = {
  /**
   * Get the global RAG feature catalog
   */
  async getCatalog(params?: {
    category?: RAGFeatureCategory;
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<RAGFeatureListResponse> {
    const queryString = buildQueryString(params || {});
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/v1/rag-features/catalog${queryString}`, {
      method: 'GET',
      headers,
    });

    return handleResponse<RAGFeatureListResponse>(response);
  },

  /**
   * Get a specific RAG feature by name
   */
  async getFeature(featureName: string): Promise<RAGFeatureResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag-features/catalog/${encodeURIComponent(featureName)}`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<RAGFeatureResponse>(response);
  },

  /**
   * Create a new RAG feature (System Admin only)
   */
  async createFeature(request: RAGFeatureCreateRequest): Promise<RAGFeatureResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag-features/catalog`, {
      method: 'POST',
      headers: await getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    return handleResponse<RAGFeatureResponse>(response);
  },

  /**
   * Update an existing RAG feature (System Admin only)
   */
  async updateFeature(featureName: string, request: RAGFeatureUpdateRequest): Promise<RAGFeatureResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag-features/catalog/${encodeURIComponent(featureName)}`, {
      method: 'PATCH',
      headers: await getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    return handleResponse<RAGFeatureResponse>(response);
  },

  /**
   * Delete a RAG feature (System Admin only)
   */
  async deleteFeature(featureName: string): Promise<APIResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag-features/catalog/${encodeURIComponent(featureName)}`, {
      method: 'DELETE',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<APIResponse>(response);
  },

  /**
   * Get available RAG feature categories with counts
   */
  async getCategories(): Promise<APIResponse<Record<RAGFeatureCategory, any>>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag-features/catalog/categories`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<APIResponse<Record<RAGFeatureCategory, any>>>(response);
  }
};

// ==================== ORGANIZATION TOGGLE API ====================

export const organizationToggleApi = {
  /**
   * Get RAG feature toggles for an organization
   */
  async getToggles(orgId: string, params?: {
    category?: RAGFeatureCategory;
    enabled_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<RAGToggleListResponse> {
    const queryString = buildQueryString(params || {});
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles${queryString}`, {
      method: 'GET',
      headers,
    });
    
    return handleResponse<RAGToggleListResponse>(response);
  },

  /**
   * Get a specific RAG feature toggle for an organization
   */
  async getToggle(orgId: string, featureName: string): Promise<RAGToggleResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles/${encodeURIComponent(featureName)}`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<RAGToggleResponse>(response);
  },

  /**
   * Update a RAG feature toggle for an organization (Admin only)
   */
  async updateToggle(orgId: string, featureName: string, request: RAGToggleUpdateRequest): Promise<RAGToggleResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles/${encodeURIComponent(featureName)}`, {
      method: 'PATCH',
      headers: await getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    return handleResponse<RAGToggleResponse>(response);
  },

  /**
   * Bulk update RAG feature toggles for an organization (Admin only)
   */
  async bulkUpdateToggles(orgId: string, request: BulkToggleUpdateRequest): Promise<RAGToggleListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles/bulk`, {
      method: 'POST',
      headers: await getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    return handleResponse<RAGToggleListResponse>(response);
  },

  /**
   * Get only enabled RAG features for an organization
   */
  async getEnabledFeatures(orgId: string, category?: RAGFeatureCategory): Promise<EnabledFeaturesResponse> {
    const queryString = buildQueryString({ category });
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles/enabled${queryString}`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<EnabledFeaturesResponse>(response);
  },

  /**
   * Get RAG features inherited from parent organization
   */
  async getInheritedFeatures(orgId: string): Promise<RAGToggleListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles/inherited`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<RAGToggleListResponse>(response);
  },

  /**
   * Get summary statistics for RAG feature toggles
   */
  async getSummary(orgId: string): Promise<RAGFeatureSummaryResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/rag-toggles/summary`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<RAGFeatureSummaryResponse>(response);
  }
};

// ==================== COMBINED API FUNCTIONS ====================

export const ragFeaturesApi = {
  /**
   * Get RAG features with toggle status for an organization
   * Combines catalog and toggle data
   */
  async getFeaturesWithToggles(orgId: string, params?: {
    category?: RAGFeatureCategory;
    enabled_only?: boolean;
  }): Promise<RAGFeatureWithToggle[]> {
    try {
      // Get catalog and toggles in parallel
      const [catalogResponse, togglesResponse] = await Promise.all([
        ragFeatureCatalogApi.getCatalog({ is_active: true }),
        organizationToggleApi.getToggles(orgId, params)
      ]);

      if (!catalogResponse.success || !togglesResponse.success) {
        throw new Error('Failed to fetch RAG features data');
      }

      const catalog = catalogResponse.data || [];
      const toggles = togglesResponse.data || [];

      // Combine catalog and toggle data
      const featuresWithToggles: RAGFeatureWithToggle[] = catalog.map(feature => {
        const toggle = toggles.find(t => t.rag_feature === feature.rag_feature);
        
        return {
          ...feature,
          enabled: toggle?.enabled || false,
          is_inherited: toggle?.is_inherited || false,
          inherited_from: toggle?.inherited_from,
          source_type: toggle?.is_inherited ? 'inherited' : 'own'
        };
      });

      return featuresWithToggles;
    } catch (error) {
      console.error('Error fetching features with toggles:', error);
      throw error;
    }
  },

  /**
   * Get enabled features for an organization (simplified)
   */
  async getEnabledFeatures(orgId: string, category?: RAGFeatureCategory): Promise<string[]> {
    try {
      const response = await organizationToggleApi.getEnabledFeatures(orgId, category);
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch enabled features');
      }
      
      return response.data || [];
    } catch (error) {
      console.error('Error fetching enabled features:', error);
      throw error;
    }
  },

  /**
   * Toggle a single feature
   */
  async toggleFeature(orgId: string, featureName: string, enabled: boolean): Promise<void> {
    try {
      const response = await organizationToggleApi.updateToggle(orgId, featureName, { enabled });
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to toggle feature');
      }
    } catch (error) {
      console.error('Error toggling feature:', error);
      throw error;
    }
  },

  /**
   * Bulk toggle multiple features
   */
  async bulkToggleFeatures(orgId: string, updates: Record<string, boolean>): Promise<void> {
    try {
      const response = await organizationToggleApi.bulkUpdateToggles(orgId, { updates });
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to bulk toggle features');
      }
    } catch (error) {
      console.error('Error bulk toggling features:', error);
      throw error;
    }
  },

  /**
   * Get organization hierarchy tree
   */
  async getOrganizationHierarchy(orgId: string): Promise<OrganizationTreeNode[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/hierarchy`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<OrganizationTreeNode[]>(response);
  },

  /**
   * Get pending sharing requests for an organization
   */
  async getPendingSharingRequests(orgId: string): Promise<SharingRequest[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/orgs/${encodeURIComponent(orgId)}/sharing/pending`, {
      method: 'GET',
      headers: await getAuthHeaders(),
    });
    
    return handleResponse<SharingRequest[]>(response);
  },

  /**
   * Approve a sharing request
   */
  async approveSharingRequest(requestId: string, approvedBy: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sharing/${encodeURIComponent(requestId)}/approve`, {
      method: 'POST',
      headers: await getAuthHeaders(),
      body: JSON.stringify({ approved_by: approvedBy }),
    });
    
    await handleResponse<void>(response);
  },

  /**
   * Reject a sharing request
   */
  async rejectSharingRequest(requestId: string, rejectedBy: string, reason?: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sharing/${encodeURIComponent(requestId)}/reject`, {
      method: 'POST',
      headers: await getAuthHeaders(),
      body: JSON.stringify({ rejected_by: rejectedBy, reason }),
    });
    
    await handleResponse<void>(response);
  },

  /**
   * Get feature summary for an organization
   */
  async getFeatureSummary(orgId: string) {
    try {
      const response = await organizationToggleApi.getSummary(orgId);
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch feature summary');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching feature summary:', error);
      throw error;
    }
  }
};

// ==================== ERROR HANDLING ====================

export class RAGFeatureApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'RAGFeatureApiError';
  }
}

export const handleApiError = (error: any): RAGFeatureApiError => {
  if (error instanceof RAGFeatureApiError) {
    return error;
  }

  if (error.message?.includes('HTTP')) {
    const statusMatch = error.message.match(/HTTP (\d+)/);
    const status = statusMatch ? parseInt(statusMatch[1]) : undefined;
    
    return new RAGFeatureApiError(
      error.message,
      'NETWORK_ERROR',
      status,
      error
    );
  }

  return new RAGFeatureApiError(
    error.message || 'Unknown API error',
    'UNKNOWN_ERROR',
    undefined,
    error
  );
};

// ==================== EXPORTS ====================

export default {
  catalog: ragFeatureCatalogApi,
  toggles: organizationToggleApi,
  combined: ragFeaturesApi
};
