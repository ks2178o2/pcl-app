/**
 * RAG Features State Management Hook
 * Provides state management and operations for RAG features
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  RAGFeatureWithToggle,
  RAGFeatureCategory,
  RAGFeatureSummary,
  UseRAGFeaturesReturn
} from '@/types/rag-features';
import { ragFeaturesApi, handleApiError } from '@/lib/api/rag-features';

// ==================== HOOK IMPLEMENTATION ====================

export const useRAGFeatures = (organizationId?: string): UseRAGFeaturesReturn => {
  // ==================== STATE ====================
  const [features, setFeatures] = useState<RAGFeatureWithToggle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RAGFeatureSummary | null>(null);

  // ==================== COMPUTED VALUES ====================
  const enabledFeatures = useMemo(() => {
    return features
      .filter(feature => feature.enabled)
      .map(feature => feature.rag_feature);
  }, [features]);

  // ==================== FETCH FUNCTIONS ====================
  const fetchFeatures = useCallback(async (category?: RAGFeatureCategory, enabledOnly?: boolean) => {
    if (!organizationId) {
      setError('Organization ID is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const featuresData = await ragFeaturesApi.getFeaturesWithToggles(organizationId, {
        category,
        enabled_only: enabledOnly
      });

      setFeatures(featuresData);

      // Fetch summary if we have features
      if (featuresData.length > 0) {
        try {
          const summaryData = await ragFeaturesApi.getFeatureSummary(organizationId);
          setSummary(summaryData);
        } catch (summaryError) {
          console.warn('Failed to fetch feature summary:', summaryError);
          // Don't fail the whole operation if summary fails
        }
      }
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      console.error('Error fetching RAG features:', apiError);
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  const refetch = useCallback(() => {
    return fetchFeatures();
  }, [fetchFeatures]);

  // ==================== OPERATIONS ====================
  const toggleFeature = useCallback(async (featureName: string, enabled: boolean) => {
    if (!organizationId) {
      throw new Error('Organization ID is required');
    }

    try {
      await ragFeaturesApi.toggleFeature(organizationId, featureName, enabled);

      // Optimistically update the local state
      setFeatures(prevFeatures =>
        prevFeatures.map(feature =>
          feature.rag_feature === featureName
            ? { ...feature, enabled }
            : feature
        )
      );

      // Update summary
      if (summary) {
        const updatedSummary = { ...summary };
        const feature = features.find(f => f.rag_feature === featureName);
        
        if (feature) {
          if (enabled) {
            updatedSummary.enabled_features += 1;
            updatedSummary.disabled_features -= 1;
            updatedSummary.category_breakdown[feature.category].enabled += 1;
          } else {
            updatedSummary.enabled_features -= 1;
            updatedSummary.disabled_features += 1;
            updatedSummary.category_breakdown[feature.category].enabled -= 1;
          }
          
          updatedSummary.enabled_percentage = Math.round(
            (updatedSummary.enabled_features / updatedSummary.total_features) * 100
          );
        }
        
        setSummary(updatedSummary);
      }
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      throw apiError;
    }
  }, [organizationId, features, summary]);

  const bulkToggle = useCallback(async (updates: Record<string, boolean>) => {
    if (!organizationId) {
      throw new Error('Organization ID is required');
    }

    try {
      await ragFeaturesApi.bulkToggleFeatures(organizationId, updates);

      // Optimistically update the local state
      setFeatures(prevFeatures =>
        prevFeatures.map(feature => {
          const newEnabled = updates[feature.rag_feature];
          return newEnabled !== undefined ? { ...feature, enabled: newEnabled } : feature;
        })
      );

      // Update summary
      if (summary) {
        const updatedSummary = { ...summary };
        let enabledDelta = 0;
        const categoryDeltas: Record<RAGFeatureCategory, number> = {
          sales: 0,
          manager: 0,
          admin: 0
        };

        Object.entries(updates).forEach(([featureName, enabled]) => {
          const feature = features.find(f => f.rag_feature === featureName);
          if (feature) {
            const wasEnabled = feature.enabled;
            if (enabled && !wasEnabled) {
              enabledDelta += 1;
              categoryDeltas[feature.category] += 1;
            } else if (!enabled && wasEnabled) {
              enabledDelta -= 1;
              categoryDeltas[feature.category] -= 1;
            }
          }
        });

        updatedSummary.enabled_features += enabledDelta;
        updatedSummary.disabled_features -= enabledDelta;
        
        Object.entries(categoryDeltas).forEach(([category, delta]) => {
          updatedSummary.category_breakdown[category as RAGFeatureCategory].enabled += delta;
        });
        
        updatedSummary.enabled_percentage = Math.round(
          (updatedSummary.enabled_features / updatedSummary.total_features) * 100
        );
        
        setSummary(updatedSummary);
      }
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      throw apiError;
    }
  }, [organizationId, features, summary]);

  // ==================== EFFECTS ====================
  useEffect(() => {
    if (organizationId) {
      fetchFeatures();
    }
  }, [organizationId, fetchFeatures]);

  // ==================== RETURN ====================
  return {
    features,
    enabledFeatures,
    loading,
    error,
    toggleFeature,
    bulkToggle,
    refetch,
    summary
  };
};

// ==================== SPECIALIZED HOOKS ====================

/**
 * Hook for getting only enabled features (for dropdowns, etc.)
 */
export const useEnabledRAGFeatures = (organizationId?: string, category?: RAGFeatureCategory) => {
  const [enabledFeatures, setEnabledFeatures] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEnabledFeatures = useCallback(async () => {
    if (!organizationId) {
      setError('Organization ID is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const features = await ragFeaturesApi.getEnabledFeatures(organizationId, category);
      setEnabledFeatures(features);
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      console.error('Error fetching enabled RAG features:', apiError);
    } finally {
      setLoading(false);
    }
  }, [organizationId, category]);

  useEffect(() => {
    if (organizationId) {
      fetchEnabledFeatures();
    }
  }, [organizationId, category, fetchEnabledFeatures]);

  return {
    enabledFeatures,
    loading,
    error,
    refetch: fetchEnabledFeatures
  };
};

/**
 * Hook for RAG feature catalog (system admin features)
 */
export const useRAGFeatureCatalog = (category?: RAGFeatureCategory) => {
  const [catalog, setCatalog] = useState<RAGFeatureWithToggle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await ragFeaturesApi.catalog.getCatalog({
        category,
        is_active: true
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch catalog');
      }

      // Convert to RAGFeatureWithToggle format
      const catalogData = (response.data || []).map(feature => ({
        ...feature,
        enabled: false, // Catalog doesn't have toggle status
        is_inherited: false,
        source_type: 'none' as const
      }));

      setCatalog(catalogData);
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      console.error('Error fetching RAG feature catalog:', apiError);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    fetchCatalog();
  }, [fetchCatalog]);

  return {
    catalog,
    loading,
    error,
    refetch: fetchCatalog
  };
};

/**
 * Hook for RAG feature summary statistics
 */
export const useRAGFeatureSummary = (organizationId?: string) => {
  const [summary, setSummary] = useState<RAGFeatureSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    if (!organizationId) {
      setError('Organization ID is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const summaryData = await ragFeaturesApi.getFeatureSummary(organizationId);
      setSummary(summaryData);
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      console.error('Error fetching RAG feature summary:', apiError);
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    if (organizationId) {
      fetchSummary();
    }
  }, [organizationId, fetchSummary]);

  return {
    summary,
    loading,
    error,
    refetch: fetchSummary
  };
};

// ==================== UTILITY HOOKS ====================

/**
 * Hook for filtering features by category
 */
export const useRAGFeaturesByCategory = (organizationId?: string) => {
  const { features, loading, error, refetch } = useRAGFeatures(organizationId);

  const featuresByCategory = useMemo(() => {
    const categorized: Record<RAGFeatureCategory, RAGFeatureWithToggle[]> = {
      sales: [],
      manager: [],
      admin: []
    };

    features.forEach(feature => {
      categorized[feature.category].push(feature);
    });

    return categorized;
  }, [features]);

  return {
    featuresByCategory,
    loading,
    error,
    refetch
  };
};

/**
 * Hook for inherited features
 */
export const useInheritedRAGFeatures = (organizationId?: string) => {
  const { features, loading, error, refetch } = useRAGFeatures(organizationId);

  const inheritedFeatures = useMemo(() => {
    return features.filter(feature => feature.is_inherited);
  }, [features]);

  return {
    inheritedFeatures,
    loading,
    error,
    refetch
  };
};

/**
 * Hook for own (non-inherited) features
 */
export const useOwnRAGFeatures = (organizationId?: string) => {
  const { features, loading, error, refetch } = useRAGFeatures(organizationId);

  const ownFeatures = useMemo(() => {
    return features.filter(feature => !feature.is_inherited);
  }, [features]);

  return {
    ownFeatures,
    loading,
    error,
    refetch
  };
};

// ==================== EXPORTS ====================

export default useRAGFeatures;
