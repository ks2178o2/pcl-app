/**
 * RAG Feature Selector Dropdown Component
 * A reusable dropdown component for selecting RAG features
 */

import React, { useState, useMemo } from 'react';
import { RAGFeatureSelectorProps, RAGFeatureCategory, getCategoryInfo } from '../types/rag-features';
import { useEnabledRAGFeatures } from '../hooks/useRAGFeatures';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

// ==================== COMPONENT IMPLEMENTATION ====================

export const RAGFeatureSelector: React.FC<RAGFeatureSelectorProps> = ({
  value,
  onChange,
  organizationId,
  filterByCategory,
  placeholder = "Select a RAG feature...",
  disabled = false,
  showOnlyEnabled = true,
  className = ""
}) => {
  // ==================== STATE ====================
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // ==================== DATA FETCHING ====================
  const { enabledFeatures, loading, error } = useEnabledRAGFeatures(
    organizationId,
    filterByCategory
  );

  // ==================== COMPUTED VALUES ====================
  const filteredFeatures = useMemo(() => {
    if (!enabledFeatures) return [];

    let features = enabledFeatures;

    // Filter by search term
    if (searchTerm) {
      features = features.filter(feature =>
        feature.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return features;
  }, [enabledFeatures, searchTerm]);

  const selectedFeatureName = useMemo(() => {
    if (!value) return '';
    
    // Find the display name for the selected feature
    // For now, we'll use the feature name as-is
    // In a real implementation, you might want to fetch the display name from the catalog
    return value;
  }, [value]);

  // ==================== EVENT HANDLERS ====================
  const handleFeatureSelect = (feature: string) => {
    onChange(feature);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleToggleDropdown = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setSearchTerm('');
    }
  };

  // ==================== RENDER HELPERS ====================
  const renderFeatureItem = (feature: string) => {
    const categoryInfo = getCategoryInfo(filterByCategory || 'sales');
    
    return (
      <div
        key={feature}
        className="px-3 py-2 hover:bg-gray-100 cursor-pointer flex items-center justify-between"
        onClick={() => handleFeatureSelect(feature)}
      >
        <div className="flex items-center space-x-2">
          <div 
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: categoryInfo.color }}
          />
          <span className="text-sm font-medium">{feature}</span>
        </div>
        {filterByCategory && (
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {categoryInfo.label}
          </span>
        )}
      </div>
    );
  };

  const renderEmptyState = () => {
    if (loading) {
      return (
        <div className="px-3 py-2 text-sm text-gray-500">
          Loading features...
        </div>
      );
    }

    if (error) {
      return (
        <div className="px-3 py-2 text-sm text-red-500">
          Error: {error}
        </div>
      );
    }

    if (searchTerm && filteredFeatures.length === 0) {
      return (
        <div className="px-3 py-2 text-sm text-gray-500">
          No features found matching "{searchTerm}"
        </div>
      );
    }

    if (filteredFeatures.length === 0) {
      return (
        <div className="px-3 py-2 text-sm text-gray-500">
          {filterByCategory 
            ? `No ${getCategoryInfo(filterByCategory).label.toLowerCase()} features available`
            : 'No features available'
          }
        </div>
      );
    }

    return null;
  };

  // ==================== RENDER ====================
  return (
    <div className={`relative ${className}`}>
      {/* Label */}
      <Label htmlFor="rag-feature-selector" className="block text-sm font-medium text-gray-700 mb-1">
        RAG Feature
      </Label>

      {/* Dropdown Button */}
      <Button
        type="button"
        variant="outline"
        onClick={handleToggleDropdown}
        disabled={disabled || loading}
        className="w-full justify-between text-left"
        id="rag-feature-selector"
      >
        <span className={selectedFeatureName ? 'text-gray-900' : 'text-gray-500'}>
          {selectedFeatureName || placeholder}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </Button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-hidden">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <Input
              type="text"
              placeholder="Search features..."
              value={searchTerm}
              onChange={handleSearchChange}
              onKeyDown={handleKeyDown}
              className="w-full text-sm"
              autoFocus
            />
          </div>

          {/* Features List */}
          <div className="max-h-48 overflow-y-auto">
            {filteredFeatures.length > 0 ? (
              filteredFeatures.map(renderFeatureItem)
            ) : (
              renderEmptyState()
            )}
          </div>

          {/* Footer */}
          {filteredFeatures.length > 0 && (
            <div className="px-3 py-2 text-xs text-gray-500 border-t border-gray-200 bg-gray-50">
              {filteredFeatures.length} feature{filteredFeatures.length !== 1 ? 's' : ''} available
            </div>
          )}
        </div>
      )}

      {/* Click Outside Handler */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setIsOpen(false);
            setSearchTerm('');
          }}
        />
      )}
    </div>
  );
};

// ==================== SIMPLIFIED VERSION ====================

/**
 * Simplified RAG Feature Selector for basic use cases
 */
export const SimpleRAGFeatureSelector: React.FC<{
  value: string;
  onChange: (value: string) => void;
  organizationId: string;
  category?: RAGFeatureCategory;
  disabled?: boolean;
  className?: string;
}> = ({
  value,
  onChange,
  organizationId,
  category,
  disabled = false,
  className = ""
}) => {
  const { enabledFeatures, loading, error } = useEnabledRAGFeatures(organizationId, category);

  if (loading) {
    return (
      <div className={className}>
        <Label className="block text-sm font-medium text-gray-700 mb-1">
          RAG Feature
        </Label>
        <div className="w-full p-2 border border-gray-300 rounded-md bg-gray-50 text-sm text-gray-500">
          Loading features...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <Label className="block text-sm font-medium text-gray-700 mb-1">
          RAG Feature
        </Label>
        <div className="w-full p-2 border border-red-300 rounded-md bg-red-50 text-sm text-red-500">
          Error: {error}
        </div>
      </div>
    );
  }

  if (!enabledFeatures || enabledFeatures.length === 0) {
    return (
      <div className={className}>
        <Label className="block text-sm font-medium text-gray-700 mb-1">
          RAG Feature
        </Label>
        <div className="w-full p-2 border border-gray-300 rounded-md bg-gray-50 text-sm text-gray-500">
          No features available
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <Label htmlFor="simple-rag-feature-select" className="block text-sm font-medium text-gray-700 mb-1">
        RAG Feature
      </Label>
      <select
        id="simple-rag-feature-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="">Select a feature...</option>
        {enabledFeatures.map(feature => (
          <option key={feature} value={feature}>
            {feature}
          </option>
        ))}
      </select>
    </div>
  );
};

// ==================== EXPORTS ====================

export default RAGFeatureSelector;
