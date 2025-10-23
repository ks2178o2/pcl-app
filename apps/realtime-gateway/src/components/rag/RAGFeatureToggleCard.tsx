/**
 * RAG Feature Toggle Card Component
 * A card component for displaying and toggling individual RAG features
 */

import React from 'react';
import { RAGFeatureToggleCardProps, getCategoryInfo } from '../types/rag-features';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Label } from '../components/ui/label';

// ==================== COMPONENT IMPLEMENTATION ====================

export const RAGFeatureToggleCard: React.FC<RAGFeatureToggleCardProps> = ({
  feature,
  onToggle,
  disabled = false,
  showInheritedBadge = true,
  className = ""
}) => {
  // ==================== COMPUTED VALUES ====================
  const categoryInfo = getCategoryInfo(feature.category);
  const isInherited = feature.is_inherited;
  const canToggle = !disabled && (!isInherited || showInheritedBadge);

  // ==================== EVENT HANDLERS ====================
  const handleToggle = () => {
    if (canToggle) {
      onToggle(!feature.enabled);
    }
  };

  // ==================== RENDER HELPERS ====================
  const renderToggleSwitch = () => {
    return (
      <div className="flex items-center space-x-3">
        <button
          type="button"
          onClick={handleToggle}
          disabled={!canToggle}
          className={`
            relative inline-flex h-6 w-11 items-center rounded-full transition-colors
            ${feature.enabled 
              ? 'bg-blue-600' 
              : 'bg-gray-200'
            }
            ${canToggle 
              ? 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2' 
              : 'cursor-not-allowed opacity-50'
            }
          `}
          role="switch"
          aria-checked={feature.enabled}
          aria-label={`Toggle ${feature.name}`}
        >
          <span
            className={`
              inline-block h-4 w-4 transform rounded-full bg-white transition-transform
              ${feature.enabled ? 'translate-x-6' : 'translate-x-1'}
            `}
          />
        </button>
        <Label className="text-sm font-medium text-gray-700">
          {feature.enabled ? 'Enabled' : 'Disabled'}
        </Label>
      </div>
    );
  };

  const renderCategoryBadge = () => {
    return (
      <span 
        className={`
          inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
          ${categoryInfo.color === 'blue' ? 'bg-blue-100 text-blue-800' : ''}
          ${categoryInfo.color === 'purple' ? 'bg-purple-100 text-purple-800' : ''}
          ${categoryInfo.color === 'red' ? 'bg-red-100 text-red-800' : ''}
        `}
      >
        <div 
          className={`w-2 h-2 rounded-full mr-1`}
          style={{ backgroundColor: categoryInfo.color }}
        />
        {categoryInfo.label}
      </span>
    );
  };

  const renderInheritedBadge = () => {
    if (!isInherited || !showInheritedBadge) return null;

    return (
      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-yellow-100 text-yellow-800">
        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
        Inherited
      </span>
    );
  };

  const renderOverrideButton = () => {
    if (!isInherited || !showInheritedBadge) return null;

    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onToggle(false)}
        disabled={disabled}
        className="text-xs"
      >
        Override
      </Button>
    );
  };

  // ==================== RENDER ====================
  return (
    <Card className={`p-4 ${isInherited ? 'opacity-75' : ''} ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {feature.name}
            </h3>
            {renderCategoryBadge()}
            {renderInheritedBadge()}
          </div>

          {/* Description */}
          {feature.description && (
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {feature.description}
            </p>
          )}

          {/* Feature ID */}
          <p className="text-xs text-gray-500 font-mono mb-3">
            {feature.rag_feature}
          </p>

          {/* Toggle Switch */}
          <div className="flex items-center justify-between">
            {renderToggleSwitch()}
            {renderOverrideButton()}
          </div>

          {/* Inherited Info */}
          {isInherited && feature.inherited_from && (
            <div className="mt-2 text-xs text-gray-500">
              Inherited from organization: {feature.inherited_from}
            </div>
          )}
        </div>

        {/* Icon */}
        {feature.icon && (
          <div className="ml-4 flex-shrink-0">
            <div 
              className={`w-8 h-8 rounded-lg flex items-center justify-center`}
              style={{ backgroundColor: `${categoryInfo.color}20` }}
            >
              <span className="text-lg">{feature.icon}</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

// ==================== COMPACT VERSION ====================

/**
 * Compact version for use in lists or tables
 */
export const CompactRAGFeatureToggleCard: React.FC<RAGFeatureToggleCardProps> = ({
  feature,
  onToggle,
  disabled = false,
  showInheritedBadge = true,
  className = ""
}) => {
  const categoryInfo = getCategoryInfo(feature.category);
  const isInherited = feature.is_inherited;
  const canToggle = !disabled && (!isInherited || showInheritedBadge);

  const handleToggle = () => {
    if (canToggle) {
      onToggle(!feature.enabled);
    }
  };

  return (
    <div className={`flex items-center justify-between p-3 border border-gray-200 rounded-lg ${isInherited ? 'opacity-75' : ''} ${className}`}>
      <div className="flex items-center space-x-3 flex-1 min-w-0">
        {/* Category Indicator */}
        <div 
          className="w-3 h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: categoryInfo.color }}
        />

        {/* Feature Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-medium text-gray-900 truncate">
              {feature.name}
            </h4>
            {isInherited && showInheritedBadge && (
              <span className="text-xs text-yellow-600">(Inherited)</span>
            )}
          </div>
          <p className="text-xs text-gray-500 font-mono truncate">
            {feature.rag_feature}
          </p>
        </div>
      </div>

      {/* Toggle Switch */}
      <div className="flex items-center space-x-2">
        <button
          type="button"
          onClick={handleToggle}
          disabled={!canToggle}
          className={`
            relative inline-flex h-5 w-9 items-center rounded-full transition-colors
            ${feature.enabled ? 'bg-blue-600' : 'bg-gray-200'}
            ${canToggle ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}
          `}
        >
          <span
            className={`
              inline-block h-3 w-3 transform rounded-full bg-white transition-transform
              ${feature.enabled ? 'translate-x-5' : 'translate-x-1'}
            `}
          />
        </button>
        
        {isInherited && showInheritedBadge && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onToggle(false)}
            disabled={disabled}
            className="text-xs px-2 py-1 h-6"
          >
            Override
          </Button>
        )}
      </div>
    </div>
  );
};

// ==================== EXPORTS ====================

export default RAGFeatureToggleCard;
