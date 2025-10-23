/**
 * Organization Hierarchy Tree View Component
 * Visual tree component for displaying organization hierarchy with feature inheritance
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { OrganizationHierarchyProps, OrganizationTreeNode } from '../types/rag-features';
import { ragFeaturesApi } from '@/lib/api/rag-features';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { 
  ChevronRight, 
  ChevronDown, 
  Building2, 
  Users, 
  Settings, 
  BarChart3,
  Eye,
  Edit,
  Plus,
  Minus,
  Search,
  Filter
} from 'lucide-react';

// ==================== COMPONENT IMPLEMENTATION ====================

export const OrganizationHierarchy: React.FC<OrganizationHierarchyProps> = ({
  rootOrganizationId,
  onOrganizationSelect,
  onFeatureInheritanceView,
  className = ""
}) => {
  // ==================== STATE ====================
  const [treeData, setTreeData] = useState<OrganizationTreeNode | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [showOnlyWithFeatures, setShowOnlyWithFeatures] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ==================== DATA FETCHING ====================
  useEffect(() => {
    fetchHierarchyData();
  }, [rootOrganizationId]);

  const fetchHierarchyData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await ragFeaturesApi.getOrganizationHierarchy(rootOrganizationId);
      setTreeData(data[0] || null); // API returns array, take first element
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch hierarchy data');
      console.error('Error fetching hierarchy:', err);
    } finally {
      setLoading(false);
    }
  };

  // ==================== COMPUTED VALUES ====================
  const filteredTreeData = useMemo(() => {
    if (!treeData) return null;
    
    const filterNode = (node: OrganizationTreeNode): OrganizationTreeNode | null => {
      // Apply search filter
      if (searchTerm && !node.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        // Check if any children match
        const filteredChildren = node.children
          .map(child => filterNode(child))
          .filter((child): child is OrganizationTreeNode => child !== null);
        
        if (filteredChildren.length === 0) {
          return null;
        }
        
        return {
          ...node,
          children: filteredChildren
        };
      }
      
      // Apply feature filter
      if (showOnlyWithFeatures && (!node.feature_count || node.feature_count === 0)) {
        return null;
      }
      
      // Recursively filter children
      const filteredChildren = node.children
        .map(child => filterNode(child))
        .filter((child): child is OrganizationTreeNode => child !== null);
      
      return {
        ...node,
        children: filteredChildren
      };
    };
    
    return filterNode(treeData);
  }, [treeData, searchTerm, showOnlyWithFeatures]);

  // ==================== EVENT HANDLERS ====================
  const handleToggleExpanded = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const handleOrganizationClick = (node: OrganizationTreeNode) => {
    onOrganizationSelect?.(node);
  };

  const handleFeatureInheritanceClick = (node: OrganizationTreeNode) => {
    onFeatureInheritanceView?.(node);
  };

  const handleExpandAll = () => {
    const allNodeIds = new Set<string>();
    const collectIds = (node: OrganizationTreeNode) => {
      allNodeIds.add(node.id);
      node.children.forEach(collectIds);
    };
    if (treeData) {
      collectIds(treeData);
    }
    setExpandedNodes(allNodeIds);
  };

  const handleCollapseAll = () => {
    setExpandedNodes(new Set());
  };

  // ==================== RENDER HELPERS ====================
  const renderNode = (node: OrganizationTreeNode, depth: number = 0): React.ReactNode => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children.length > 0;
    const indentStyle = { marginLeft: `${depth * 20}px` };

    return (
      <div key={node.id} className="select-none">
        <div 
          className={`
            flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer
            ${depth === 0 ? 'bg-blue-50 border border-blue-200' : ''}
          `}
          style={indentStyle}
        >
          {/* Expand/Collapse Button */}
          <div className="flex items-center mr-2">
            {hasChildren ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleExpanded(node.id);
                }}
                className="h-6 w-6 p-0"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            ) : (
              <div className="w-6" />
            )}
          </div>

          {/* Organization Icon */}
          <div className="mr-3">
            <Building2 className={`h-5 w-5 ${depth === 0 ? 'text-blue-600' : 'text-gray-600'}`} />
          </div>

          {/* Organization Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className={`font-medium truncate ${depth === 0 ? 'text-blue-900' : 'text-gray-900'}`}>
                {node.name}
              </h3>
              {depth > 0 && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  Level {node.level}
                </span>
              )}
            </div>
            
            {/* Feature Stats */}
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <Settings className="h-3 w-3" />
                <span>{node.feature_count || 0} features</span>
              </div>
              <div className="flex items-center space-x-1">
                <BarChart3 className="h-3 w-3" />
                <span>{node.enabled_features || 0} enabled</span>
              </div>
              {node.feature_count && node.enabled_features && (
                <div className="text-xs">
                  {Math.round((node.enabled_features / node.feature_count) * 100)}% enabled
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-1">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleOrganizationClick(node);
              }}
              className="h-8 px-2"
            >
              <Eye className="h-3 w-3 mr-1" />
              View
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleFeatureInheritanceClick(node);
              }}
              className="h-8 px-2"
            >
              <Settings className="h-3 w-3 mr-1" />
              Features
            </Button>
          </div>
        </div>

        {/* Children */}
        {isExpanded && hasChildren && (
          <div>
            {node.children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const renderHeader = () => {
    return (
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Building2 className="h-6 w-6 text-gray-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Organization Hierarchy</h1>
              <p className="text-sm text-gray-600">
                Manage organization structure and feature inheritance
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={handleExpandAll}
              disabled={loading}
            >
              <Plus className="h-4 w-4 mr-2" />
              Expand All
            </Button>
            
            <Button
              variant="outline"
              onClick={handleCollapseAll}
              disabled={loading}
            >
              <Minus className="h-4 w-4 mr-2" />
              Collapse All
            </Button>
            
            <Button
              variant="outline"
              onClick={fetchHierarchyData}
              disabled={loading}
            >
              <Settings className="h-4 w-4 mr-2" />
              Refresh
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
              <input
                type="text"
                placeholder="Search organizations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Feature Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showOnlyWithFeatures}
                onChange={(e) => setShowOnlyWithFeatures(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Only show organizations with features</span>
            </label>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading organization hierarchy...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-8 text-center">
          <div className="text-red-500 mb-4">
            <Building2 className="h-8 w-8 mx-auto mb-2" />
            <p className="text-red-600">Error loading hierarchy: {error}</p>
          </div>
          <Button onClick={fetchHierarchyData} variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      );
    }

    if (!filteredTreeData) {
      return (
        <div className="p-8 text-center">
          <Building2 className="h-8 w-8 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600">No organizations found</p>
          {searchTerm && (
            <p className="text-sm text-gray-500 mt-2">
              Try adjusting your search criteria
            </p>
          )}
        </div>
      );
    }

    return (
      <div className="p-6">
        {renderNode(filteredTreeData)}
      </div>
    );
  };

  // ==================== RENDER ====================
  return (
    <div className={`bg-gray-100 min-h-screen ${className}`}>
      {renderHeader()}
      {renderFilters()}
      <Card className="mx-6 my-6 overflow-hidden">
        {renderContent()}
      </Card>
    </div>
  );
};

// ==================== SIMPLIFIED VERSION ====================

/**
 * Simplified version for basic hierarchy display
 */
export const SimpleOrganizationHierarchy: React.FC<{
  organizations: OrganizationTreeNode[];
  onSelect?: (org: OrganizationTreeNode) => void;
  className?: string;
}> = ({
  organizations,
  onSelect,
  className = ""
}) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const handleToggleExpanded = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const renderSimpleNode = (node: OrganizationTreeNode, depth: number = 0): React.ReactNode => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children.length > 0;

    return (
      <div key={node.id} className="select-none">
        <div 
          className="flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer"
          style={{ marginLeft: `${depth * 16}px` }}
          onClick={() => onSelect?.(node)}
        >
          {/* Expand/Collapse */}
          {hasChildren && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleToggleExpanded(node.id);
              }}
              className="h-6 w-6 p-0 mr-2"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          )}

          {/* Organization Info */}
          <Building2 className="h-4 w-4 mr-2 text-gray-600" />
          <span className="font-medium text-gray-900">{node.name}</span>
          
          {/* Feature Count */}
          {node.feature_count && (
            <span className="ml-auto text-sm text-gray-500">
              {node.enabled_features}/{node.feature_count} features
            </span>
          )}
        </div>

        {/* Children */}
        {isExpanded && hasChildren && (
          <div>
            {node.children.map(child => renderSimpleNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`border border-gray-200 rounded-lg ${className}`}>
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <h3 className="font-medium text-gray-900">Organization Hierarchy</h3>
      </div>
      <div className="p-4">
        {organizations.map(org => renderSimpleNode(org))}
      </div>
    </div>
  );
};

// ==================== EXPORTS ====================

export default OrganizationHierarchy;
