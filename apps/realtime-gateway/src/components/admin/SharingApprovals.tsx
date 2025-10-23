/**
 * Sharing Approvals UI Component
 * Interface for managing context sharing requests and approvals
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SharingApprovalsProps, SharingRequest } from '../types/rag-features';
import { ragFeaturesApi } from '@/lib/api/rag-features';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { 
  CheckCircle, 
  XCircle, 
  Eye, 
  Clock, 
  Users, 
  FileText,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckSquare,
  Square
} from 'lucide-react';

// ==================== TYPES ====================

interface SharingStats {
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  total_count: number;
}

// ==================== COMPONENT IMPLEMENTATION ====================

export const SharingApprovals: React.FC<SharingApprovalsProps> = ({
  organizationId,
  className = ""
}) => {
  // ==================== STATE ====================
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
  const [selectedRequests, setSelectedRequests] = useState<Set<string>>(new Set());
  const [showPreview, setShowPreview] = useState<string | null>(null);

  const { data: requests = [], isLoading, error, refetch } = useQuery({
    queryKey: ['sharingRequests', organizationId],
    queryFn: () => ragFeaturesApi.getPendingSharingRequests(organizationId),
    enabled: !!organizationId,
  });

  const approveMutation = useMutation({
    mutationFn: (requestId: string) => ragFeaturesApi.approveSharingRequest(requestId, 'current-user-id'),
    onSuccess: () => {
      refetch();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ requestId, reason }: { requestId: string; reason?: string }) => 
      ragFeaturesApi.rejectSharingRequest(requestId, 'current-user-id', reason),
    onSuccess: () => {
      refetch();
    },
  });
  // Calculate stats from requests
  const stats = useMemo(() => {
    return {
      pending_count: requests.filter(r => r.status === 'pending').length,
      approved_count: requests.filter(r => r.status === 'approved').length,
      rejected_count: requests.filter(r => r.status === 'rejected').length,
      total_count: requests.length
    };
  }, [requests]);

  // ==================== COMPUTED VALUES ====================
  const filteredRequests = requests.filter(request => {
    const matchesSearch = !searchTerm || 
      request.item_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      request.rag_feature.toLowerCase().includes(searchTerm.toLowerCase()) ||
      request.source_org_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || request.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const pendingRequests = filteredRequests.filter(r => r.status === 'pending');

  // ==================== EVENT HANDLERS ====================
  const handleApproveRequest = async (requestId: string) => {
    try {
      await approveMutation.mutateAsync(requestId);
    } catch (err) {
      console.error('Error approving request:', err);
    }
  };

  const handleRejectRequest = async (requestId: string, reason?: string) => {
    try {
      await rejectMutation.mutateAsync({ requestId, reason });
    } catch (err) {
      console.error('Error rejecting request:', err);
    }
  };

  const handleBulkApprove = async () => {
    try {
      const selectedPendingRequests = Array.from(selectedRequests).filter(id => {
        const request = requests.find(r => r.id === id);
        return request?.status === 'pending';
      });
      
      for (const requestId of selectedPendingRequests) {
        await handleApproveRequest(requestId);
      }
      
      setSelectedRequests(new Set());
    } catch (err) {
      console.error('Error bulk approving requests:', err);
    }
  };

  const handleSelectRequest = (requestId: string) => {
    const newSelected = new Set(selectedRequests);
    if (newSelected.has(requestId)) {
      newSelected.delete(requestId);
    } else {
      newSelected.add(requestId);
    }
    setSelectedRequests(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedRequests.size === pendingRequests.length) {
      setSelectedRequests(new Set());
    } else {
      setSelectedRequests(new Set(pendingRequests.map(r => r.id)));
    }
  };

  // ==================== RENDER HELPERS ====================
  const renderHeader = () => {
    return (
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Users className="h-6 w-6 text-gray-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Sharing Approvals</h1>
              <p className="text-sm text-gray-600">
                Manage context sharing requests for organization: {organizationId}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>
    );
  };

  const renderStats = () => {
    return (
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{stats.pending_count}</div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.approved_count}</div>
            <div className="text-sm text-gray-600">Approved</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.rejected_count}</div>
            <div className="text-sm text-gray-600">Rejected</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{stats.total_count}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
        </div>
      </div>
    );
  };

  const renderFilters = () => {
    return (
      <div className="bg-white px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search requests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>
    );
  };

  const renderBulkActions = () => {
    if (pendingRequests.length === 0) return null;

    return (
      <div className="bg-blue-50 px-6 py-3 border-b border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectAll}
              className="text-blue-700"
            >
              {selectedRequests.size === pendingRequests.length ? (
                <CheckSquare className="h-4 w-4 mr-1" />
              ) : (
                <Square className="h-4 w-4 mr-1" />
              )}
              Select All ({pendingRequests.length})
            </Button>
            
            {selectedRequests.size > 0 && (
              <span className="text-sm text-blue-700">
                {selectedRequests.size} selected
              </span>
            )}
          </div>
          
          {selectedRequests.size > 0 && (
            <Button
              onClick={handleBulkApprove}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve Selected ({selectedRequests.size})
            </Button>
          )}
        </div>
      </div>
    );
  };

  const renderRequestCard = (request: SharingRequest) => {
    const isSelected = selectedRequests.has(request.id);
    const isPending = request.status === 'pending';

    return (
      <Card key={request.id} className={`p-4 ${isSelected ? 'ring-2 ring-blue-500' : ''}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1 min-w-0">
            {/* Selection Checkbox */}
            {isPending && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => handleSelectRequest(request.id)}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            )}

            {/* Request Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-medium text-gray-900 truncate">
                  {request.item_title}
                </h3>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  request.status === 'pending' ? 'bg-orange-100 text-orange-800' :
                  request.status === 'approved' ? 'bg-green-100 text-green-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {request.status}
                </span>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  request.sharing_type === 'hierarchy_down' ? 'bg-blue-100 text-blue-800' :
                  request.sharing_type === 'hierarchy_up' ? 'bg-purple-100 text-purple-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {request.sharing_type.replace('_', ' ')}
                </span>
              </div>

              <div className="text-sm text-gray-600 mb-2">
                <div className="flex items-center space-x-4">
                  <span>From: {request.source_org_name}</span>
                  <span>Feature: {request.rag_feature}</span>
                  <span>Shared: {new Date(request.shared_at).toLocaleDateString()}</span>
                </div>
              </div>

              {request.item_content && (
                <p className="text-sm text-gray-700 line-clamp-2 mb-3">
                  {request.item_content}
                </p>
              )}

              {request.status === 'rejected' && request.rejection_reason && (
                <div className="text-sm text-red-600 bg-red-50 p-2 rounded mb-3">
                  <strong>Rejection Reason:</strong> {request.rejection_reason}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2 ml-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPreview(showPreview === request.id ? null : request.id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              Preview
            </Button>

            {isPending && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleApproveRequest(request.id)}
                  className="text-green-700 border-green-300 hover:bg-green-100"
                >
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Approve
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const reason = prompt('Rejection reason (optional):');
                    handleRejectRequest(request.id, reason || undefined);
                  }}
                  className="text-red-700 border-red-300 hover:bg-red-100"
                >
                  <XCircle className="h-4 w-4 mr-1" />
                  Reject
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Preview */}
        {showPreview === request.id && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Content Preview</h4>
              <div className="text-sm text-gray-700 whitespace-pre-wrap">
                {request.item_content}
              </div>
            </div>
          </div>
        )}
      </Card>
    );
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="p-8 text-center">
          <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin text-gray-400" />
          <p className="text-gray-600">Loading sharing requests...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-8 text-center">
          <AlertCircle className="h-8 w-8 mx-auto mb-4 text-red-500" />
          <p className="text-red-600 mb-4">Error loading sharing requests: {error}</p>
          <Button onClick={() => refetch()} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      );
    }

    if (filteredRequests.length === 0) {
      return (
        <div className="p-8 text-center">
          <FileText className="h-8 w-8 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600 mb-2">No sharing requests found</p>
          <p className="text-sm text-gray-500">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'No sharing requests are available for this organization'
            }
          </p>
        </div>
      );
    }

    return (
      <div className="p-6 space-y-4">
        {filteredRequests.map(renderRequestCard)}
      </div>
    );
  };

  // ==================== RENDER ====================
  return (
    <div className={`bg-gray-100 min-h-screen ${className}`}>
      {renderHeader()}
      {renderStats()}
      {renderFilters()}
      {renderBulkActions()}
      <Card className="mx-6 my-6 overflow-hidden">
        {renderContent()}
      </Card>
    </div>
  );
};

// ==================== EXPORTS ====================

export default SharingApprovals;
