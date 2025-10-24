/**
 * RAG Feature Category Section Component
 * A collapsible section for organizing RAG features by category
 */

import React, { useState, useMemo } from 'react';
import { RAGFeatureCategorySectionProps, RAGFeatureCategory, getCategoryInfo } from '@/types/rag-features';
import { RAGFeatureToggleCard, CompactRAGFeatureToggleCard } from './RAGFeatureToggleCard';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// ==================== COMPONENT IMPLEMENTATION ====================

export const RAGFeatureCategorySection: React.FC<RAGFeatureCategorySectionProps> = ({
  category,
  features,
  onToggle,
  onBulkToggle,
  disabled = false,
  className = ""
}) => {
  // ==================== STATE ====================
  const [isExpanded, setIsExpanded] = useState(true);
  const [showCompact, setShowCompact] = useState(false);

  // ==================== COMPUTED VALUES ====================
  const categoryInfo = getCategoryInfo(category);
  
  const sortedFeatures = useMemo(() => {
    return [...features].sort((a, b) => {
      // Sort by enabled status first, then by name
      if (a.enabled !== b.enabled) {
        return a.enabled ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
  }, [features]);

  const enabledCount = useMemo(() => {
    return features.filter(f => f.enabled).length;
  }, [features]);

  const inheritedCount = useMemo(() => {
    return features.filter(f => f.is_inherited).length;
  }, [features]);

  const ownCount = useMemo(() => {
    return features.filter(f => !f.is_inherited).length;
  }, [features]);

  // ==================== EVENT HANDLERS ====================
  const handleBulkEnable = () => {
    const updates: Record<string, boolean> = {};
    features.forEach(feature => {
      if (!feature.enabled) {
        updates[feature.rag_feature] = true;
      }
    });
    onBulkToggle(true);
  };

  const handleBulkDisable = () => {
    const updates: Record<string, boolean> = {};
    features.forEach(feature => {
      if (feature.enabled && !feature.is_inherited) {
        updates[feature.rag_feature] = false;
      }
    });
    onBulkToggle(false);
  };

  const handleToggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const handleToggleView = () => {
    setShowCompact(!showCompact);
  };

  // ==================== RENDER HELPERS ====================
  const renderHeader = () => {
    return (
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          {/* Category Icon */}
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${categoryInfo.color}20` }}
          >
            <span className="text-lg">{categoryInfo.icon}</span>
          </div>

          {/* Category Info */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {categoryInfo.label}
            </h3>
            <p className="text-sm text-gray-600">
              {features.length} features • {enabledCount} enabled • {inheritedCount} inherited
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          {/* View Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleView}
            className="text-xs"
          >
            {showCompact ? 'Card View' : 'Compact View'}
          </Button>

          {/* Bulk Actions */}
          {enabledCount < features.length && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkEnable}
              disabled={disabled}
              className="text-xs"
            >
              Enable All
            </Button>
          )}

          {enabledCount > 0 && ownCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkDisable}
              disabled={disabled}
              className="text-xs"
            >
              Disable Own
            </Button>
          )}

          {/* Expand/Collapse */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleExpanded}
            className="text-xs"
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
      </div>
    );
  };

  const renderFeaturesList = () => {
    if (!isExpanded) return null;

    if (sortedFeatures.length === 0) {
      return (
        <div className="p-8 text-center text-gray-500">
          <div 
            className="w-12 h-12 mx-auto mb-4 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${categoryInfo.color}20` }}
          >
            <span className="text-2xl">{categoryInfo.icon}</span>
          </div>
          <p className="text-sm">No {categoryInfo.label.toLowerCase()} features available</p>
        </div>
      );
    }

    return (
      <div className="p-4">
        <div className={`grid gap-4 ${showCompact ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}`}>
          {sortedFeatures.map(feature => {
            const ToggleCard = showCompact ? CompactRAGFeatureToggleCard : RAGFeatureToggleCard;
            return (
              <ToggleCard
                key={feature.rag_feature}
                feature={feature}
                onToggle={(enabled) => onToggle(feature.rag_feature, enabled)}
                disabled={disabled}
                showInheritedBadge={true}
              />
            );
          })}
        </div>
      </div>
    );
  };

  const renderSummary = () => {
    if (!isExpanded) return null;

    return (
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>
              <span className="font-medium text-green-600">{enabledCount}</span> enabled
            </span>
            <span>
              <span className="font-medium text-gray-600">{features.length - enabledCount}</span> disabled
            </span>
            {inheritedCount > 0 && (
              <span>
                <span className="font-medium text-yellow-600">{inheritedCount}</span> inherited
              </span>
            )}
          </div>
          
          <div className="text-xs text-gray-500">
            {Math.round((enabledCount / features.length) * 100)}% enabled
          </div>
        </div>
      </div>
    );
  };

  // ==================== RENDER ====================
  return (
    <Card className={`overflow-hidden ${className}`}>
      {renderHeader()}
      {renderFeaturesList()}
      {renderSummary()}
    </Card>
  );
};

// ==================== SIMPLIFIED VERSION ====================

/**
 * Simplified version for basic category display
 */
export const SimpleRAGFeatureCategorySection: React.FC<{
  category: RAGFeatureCategory;
  features: RAGFeatureCategorySectionProps['features'];
  onToggle: RAGFeatureCategorySectionProps['onToggle'];
  disabled?: boolean;
  className?: string;
}> = ({
  category,
  features,
  onToggle,
  disabled = false,
  className = ""
}) => {
  const categoryInfo = getCategoryInfo(category);
  const enabledCount = features.filter(f => f.enabled).length;

  return (
    <div className={`border border-gray-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div 
              className="w-6 h-6 rounded flex items-center justify-center"
              style={{ backgroundColor: `${categoryInfo.color}20` }}
            >
              <span className="text-sm">{categoryInfo.icon}</span>
            </div>
            <h3 className="font-medium text-gray-900">{categoryInfo.label}</h3>
            <span className="text-sm text-gray-500">({enabledCount}/{features.length})</span>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="p-3 space-y-2">
        {features.map(feature => (
          <CompactRAGFeatureToggleCard
            key={feature.rag_feature}
            feature={feature}
            onToggle={(enabled) => onToggle(feature.rag_feature, enabled)}
            disabled={disabled}
            showInheritedBadge={true}
          />
        ))}
      </div>
    </div>
  );
};

// ==================== EXPORTS ====================

export default RAGFeatureCategorySection;
