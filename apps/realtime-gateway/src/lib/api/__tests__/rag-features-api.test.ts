/**
 * API Client Tests for RAG Feature Management
 * Tests the API client functions with proper mocking
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ragFeaturesApi } from '../../lib/api/rag-features';
import { EffectiveRAGFeature, OrganizationTreeNode, SharingRequest } from '../../types/rag-features';

// Mock fetch
global.fetch = vi.fn();

describe('RAG Features API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getGlobalFeatures', () => {
    it('should fetch global RAG features successfully', async () => {
      const mockFeatures = [
        {
          rag_feature: 'best_practice_kb',
          name: 'Best Practice Knowledge Base',
          description: 'Sales best practices',
          category: 'sales',
          default_enabled: true,
        },
      ];

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeatures,
      } as Response);

      const result = await ragFeaturesApi.getGlobalFeatures();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/rag-features',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockFeatures);
    });

    it('should handle API errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      } as Response);

      await expect(ragFeaturesApi.getGlobalFeatures()).rejects.toThrow();
    });

    it('should handle network errors', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

      await expect(ragFeaturesApi.getGlobalFeatures()).rejects.toThrow('Network error');
    });
  });

  describe('getOrganizationToggles', () => {
    it('should fetch organization toggles successfully', async () => {
      const mockToggles = {
        success: true,
        toggles: [
          {
            rag_feature: 'best_practice_kb',
            enabled: true,
            is_inherited: false,
          },
        ],
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockToggles,
      } as Response);

      const result = await ragFeaturesApi.getOrganizationToggles('org-123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-123/rag-toggles',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'X-User-Roles': 'org_admin',
          }),
        })
      );
      expect(result).toEqual(mockToggles);
    });

    it('should include user roles in headers', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, toggles: [] }),
      } as Response);

      await ragFeaturesApi.getOrganizationToggles('org-123', ['system_admin', 'org_admin']);

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-User-Roles': 'system_admin,org_admin',
          }),
        })
      );
    });
  });

  describe('getEnabledFeatures', () => {
    it('should fetch enabled features successfully', async () => {
      const mockEnabledFeatures = {
        success: true,
        enabled_features: [
          {
            rag_feature: 'best_practice_kb',
            name: 'Best Practice Knowledge Base',
            enabled: true,
            is_inherited: false,
          },
        ],
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEnabledFeatures,
      } as Response);

      const result = await ragFeaturesApi.getEnabledFeatures('org-123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-123/rag-toggles/enabled',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockEnabledFeatures);
    });

    it('should filter by category', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, enabled_features: [] }),
      } as Response);

      await ragFeaturesApi.getEnabledFeatures('org-123', 'sales');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-123/rag-toggles/enabled?category=sales',
        expect.any(Object)
      );
    });
  });

  describe('updateToggle', () => {
    it('should update toggle successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Toggle updated successfully',
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await ragFeaturesApi.updateToggle('org-123', 'best_practice_kb', true);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-123/rag-toggles/best_practice_kb',
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({ enabled: true }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should include reason when provided', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      await ragFeaturesApi.updateToggle('org-123', 'best_practice_kb', true, 'Q4 sales push');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ enabled: true, reason: 'Q4 sales push' }),
        })
      );
    });
  });

  describe('bulkUpdateToggles', () => {
    it('should bulk update toggles successfully', async () => {
      const mockResponse = {
        success: true,
        total_updated: 2,
        updated_toggles: [
          { rag_feature: 'best_practice_kb', enabled: true },
          { rag_feature: 'customer_insight_rag', enabled: false },
        ],
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const updates = {
        best_practice_kb: true,
        customer_insight_rag: false,
      };

      const result = await ragFeaturesApi.bulkUpdateToggles('org-123', updates);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-123/rag-toggles/bulk',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ updates }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getOrganizationHierarchy', () => {
    it('should fetch organization hierarchy successfully', async () => {
      const mockHierarchy: OrganizationTreeNode[] = [
        {
          id: 'org-123',
          name: 'Parent Organization',
          parent_organization_id: null,
          children: [
            {
              id: 'org-456',
              name: 'Child Organization',
              parent_organization_id: 'org-123',
              children: [],
              level: 1,
              path: ['org-123', 'org-456'],
            },
          ],
          level: 0,
          path: ['org-123'],
        },
      ];

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHierarchy,
      } as Response);

      const result = await ragFeaturesApi.getOrganizationHierarchy('org-123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-123/hierarchy',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockHierarchy);
    });
  });

  describe('getPendingSharingRequests', () => {
    it('should fetch pending sharing requests successfully', async () => {
      const mockRequests: SharingRequest[] = [
        {
          id: 'req-1',
          source_organization_id: 'parent-org',
          target_organization_id: 'org-456',
          rag_feature: 'best_practice_kb',
          item_id: 'item-123',
          sharing_type: 'hierarchy_down',
          status: 'pending',
          shared_by: 'admin@parent.com',
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
        },
      ];

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRequests,
      } as Response);

      const result = await ragFeaturesApi.getPendingSharingRequests('org-456');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/orgs/org-456/sharing/pending',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockRequests);
    });
  });

  describe('approveSharingRequest', () => {
    it('should approve sharing request successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      await ragFeaturesApi.approveSharingRequest('req-1', 'admin-123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sharing/req-1/approve',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ approved_by: 'admin-123' }),
        })
      );
    });
  });

  describe('rejectSharingRequest', () => {
    it('should reject sharing request successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      await ragFeaturesApi.rejectSharingRequest('req-1', 'admin-123', 'Not relevant');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sharing/req-1/reject',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ rejected_by: 'admin-123', reason: 'Not relevant' }),
        })
      );
    });

    it('should reject without reason', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      await ragFeaturesApi.rejectSharingRequest('req-1', 'admin-123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sharing/req-1/reject',
        expect.objectContaining({
          body: JSON.stringify({ rejected_by: 'admin-123', reason: undefined }),
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle HTTP errors with proper error messages', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'RAG feature not found' }),
      } as Response);

      await expect(ragFeaturesApi.getGlobalFeatures()).rejects.toThrow();
    });

    it('should handle malformed JSON responses', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      } as Response);

      await expect(ragFeaturesApi.getGlobalFeatures()).rejects.toThrow();
    });

    it('should handle network timeouts', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Request timeout'));

      await expect(ragFeaturesApi.getGlobalFeatures()).rejects.toThrow('Request timeout');
    });
  });

  describe('Environment Configuration', () => {
    it('should use default API URL when VITE_API_URL is not set', async () => {
      const originalEnv = import.meta.env.VITE_API_URL;
      delete import.meta.env.VITE_API_URL;

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

      await ragFeaturesApi.getGlobalFeatures();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/rag-features',
        expect.any(Object)
      );

      // Restore original env
      import.meta.env.VITE_API_URL = originalEnv;
    });

    it('should use custom API URL when VITE_API_URL is set', async () => {
      const originalEnv = import.meta.env.VITE_API_URL;
      import.meta.env.VITE_API_URL = 'https://api.example.com';

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

      await ragFeaturesApi.getGlobalFeatures();

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/v1/rag-features',
        expect.any(Object)
      );

      // Restore original env
      import.meta.env.VITE_API_URL = originalEnv;
    });
  });
});
