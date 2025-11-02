/**
 * RAG Feature Management Panel
 * Main admin interface for managing RAG features for an organization
 */

import React, { useState, useMemo } from 'react';
import { RAGFeatureManagementProps, RAGFeatureCategory, RAGFeatureWithToggle } from '@/types/rag-features';
import { useRAGFeatures, useRAGFeaturesByCategory } from '@/hooks/useRAGFeatures';
import { RAGFeatureCategorySection } from '../rag/RAGFeatureCategorySection';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { 
  Settings, 
  Search, 
  RefreshCw, 
  Save, 
  X, 
  CheckCircle, 
  AlertCircle,
  Users,
  BarChart3,
  Shield,
  Filter
} from 'lucide-react';

// ==================== COMPONENT IMPLEMENTATION ====================

export const RAGFeatureManagement: React.FC<RAGFeatureManagementProps> = ({
  organizationId,
  className = ""
}) => {
  // ==================== STATE ====================
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<RAGFeatureCategory | 'all'>('all');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // ==================== DATA FETCHING ====================
  const { 
    features, 
    loading, 
    error, 
    toggleFeature, 
    bulkToggle, 
    refetch, 
    summary 
  } = useRAGFeatures(organizationId);

  const { featuresByCategory } = useRAGFeaturesByCategory(organizationId);

  // ==================== COMPUTED VALUES ====================
  const filteredFeatures = useMemo(() => {
    let filtered = features;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(f => f.category === selectedCategory);
    }

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(f => 
        f.name.toLowerCase().includes(term) ||
        f.description?.toLowerCase().includes(term) ||
        f.rag_feature.toLowerCase().includes(term)
      );
    }

    return filtered;
  }, [features, selectedCategory, searchTerm]);

  const filteredFeaturesByCategory = useMemo(() => {
    const result: Record<RAGFeatureCategory, RAGFeatureWithToggle[]> = {
      sales: [],
      manager: [],
      admin: []
    };

    filteredFeatures.forEach(feature => {
      result[feature.category].push(feature);
    });

    return result;
  }, [filteredFeatures]);

  // ==================== EVENT HANDLERS ====================
  const handleFeatureToggle = async (featureName: string, enabled: boolean) => {
    try {
      await toggleFeature(featureName, enabled);
      setHasUnsavedChanges(true);
    } catch (error) {
      console.error('Error toggling feature:', error);
    }
  };

  const handleBulkToggle = async (enabled: boolean) => {
    try {
      const updates: Record<string, boolean> = {};
      filteredFeatures.forEach(feature => {
        if (feature.enabled !== enabled) {
          updates[feature.rag_feature] = enabled;
        }
      });
      
      await bulkToggle(updates);
      setHasUnsavedChanges(true);
    } catch (error) {
      console.error('Error bulk toggling features:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // The optimistic updates are already applied
      // This could trigger a final sync or validation
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Error saving changes:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      await refetch();
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Error resetting changes:', error);
    }
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedCategory('all');
  };

  // ==================== RENDER HELPERS ====================
  const renderHeader = () => {
    return (
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Settings className="h-6 w-6 text-gray-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">RAG Feature Management</h1>
              <p className="text-sm text-gray-600">
                Manage RAG features for organization: {organizationId}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {hasUnsavedChanges && (
              <div className="flex items-center space-x-2 text-sm text-orange-600">
                <AlertCircle className="h-4 w-4" />
                <span>Unsaved changes</span>
              </div>
            )}
            
            <Button
              variant="outline"
              onClick={handleReset}
              disabled={loading || isSaving}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Reset
            </Button>

            <Button
              onClick={handleSave}
              disabled={!hasUnsavedChanges || loading || isSaving}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>
    );
  };

  const renderFilters = () => {
    return (
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search features..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as RAGFeatureCategory | 'all')}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Categories</option>
              <option value="sales">Sales-Focused</option>
              <option value="manager">Manager-Focused</option>
              <option value="admin">Admin-Focused</option>
            </select>
          </div>

          {/* Clear Filters */}
          {(searchTerm || selectedCategory !== 'all') && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearFilters}
            >
              <X className="h-4 w-4 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </div>
    );
  };

  const renderSummary = () => {
    if (!summary) return null;

    return (
      <div className="bg-white px-6 py-4 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{summary.total_features}</div>
            <div className="text-sm text-gray-600">Total Features</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{summary.enabled_features}</div>
            <div className="text-sm text-gray-600">Enabled</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{summary.disabled_features}</div>
            <div className="text-sm text-gray-600">Disabled</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{summary.enabled_percentage}%</div>
            <div className="text-sm text-gray-600">Enabled</div>
          </div>
        </div>
      </div>
    );
  };

  const renderBulkActions = () => {
    const enabledCount = filteredFeatures.filter(f => f.enabled).length;
    const disabledCount = filteredFeatures.filter(f => !f.enabled).length;

    if (filteredFeatures.length === 0) return null;

    return (
      <div className="bg-blue-50 px-6 py-3 border-b border-blue-200">
        <div className="flex items-center justify-between">
          <div className="text-sm text-blue-800">
            Showing {filteredFeatures.length} features
            {searchTerm && ` matching "${searchTerm}"`}
            {selectedCategory !== 'all' && ` in ${selectedCategory} category`}
          </div>
          
          <div className="flex items-center space-x-2">
            {disabledCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkToggle(true)}
                disabled={loading}
                className="text-blue-700 border-blue-300 hover:bg-blue-100"
              >
                Enable All ({disabledCount})
              </Button>
            )}
            
            {enabledCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkToggle(false)}
                disabled={loading}
                className="text-red-700 border-red-300 hover:bg-red-100"
              >
                Disable All ({enabledCount})
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderCategories = () => {
    if (loading) {
      return (
        <div className="p-8 text-center">
          <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin text-gray-400" />
          <p className="text-gray-600">Loading RAG features...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-8 text-center">
          <AlertCircle className="h-8 w-8 mx-auto mb-4 text-red-500" />
          <p className="text-red-600 mb-4">Error loading RAG features: {error}</p>
          <Button onClick={refetch} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      );
    }

    if (filteredFeatures.length === 0) {
      return (
        <div className="p-8 text-center">
          <Search className="h-8 w-8 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600 mb-2">No features found</p>
          <p className="text-sm text-gray-500">
            {searchTerm || selectedCategory !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'No RAG features are available for this organization'
            }
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-6 p-6">
        {(['sales', 'manager', 'admin'] as RAGFeatureCategory[]).map(category => {
          const categoryFeatures = filteredFeaturesByCategory[category];
          if (categoryFeatures.length === 0) return null;

          return (
            <RAGFeatureCategorySection
              key={category}
              category={category}
              features={categoryFeatures}
              onToggle={handleFeatureToggle}
              onBulkToggle={handleBulkToggle}
              disabled={loading}
            />
          );
        })}
      </div>
    );
  };

  // ==================== RENDER ====================
  return (
    <div className={`bg-gray-100 min-h-screen ${className}`}>
      {renderHeader()}
      {renderFilters()}
      {renderSummary()}
      {renderBulkActions()}
      {renderCategories()}
    </div>
  );
};

// ==================== EXPORTS ====================

export default RAGFeatureManagement;
