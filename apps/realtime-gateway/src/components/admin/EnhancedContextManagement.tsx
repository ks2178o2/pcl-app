// apps/realtime-gateway/src/components/admin/EnhancedContextManagement.tsx

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Upload, 
  Globe, 
  Share2, 
  Users, 
  Settings, 
  FileText, 
  Link, 
  Database,
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3
} from 'lucide-react';
import { RAGFeatureSelector } from '@/components/rag/RAGFeatureSelector';
import { useUserRoles } from '@/hooks/useUserRoles';
import { useAuth } from '@/hooks/useAuth';

interface GlobalContextItem {
  id: string;
  rag_feature: string;
  item_id: string;
  item_type: string;
  item_title: string;
  item_content: string;
  status: string;
  priority: number;
  confidence_score: number;
  source?: string;
  tags: string[];
  created_at: string;
}

interface TenantAccess {
  id: string;
  organization_id: string;
  rag_feature: string;
  access_level: string;
  enabled: boolean;
}

interface ContextSharing {
  id: string;
  source_organization_id: string;
  target_organization_id: string;
  rag_feature: string;
  item_id: string;
  sharing_type: string;
  status: string;
  created_at: string;
}

interface OrganizationQuotas {
  id: string;
  organization_id: string;
  max_context_items: number;
  max_global_access_features: number;
  max_sharing_requests: number;
  current_context_items: number;
  current_global_access: number;
  current_sharing_requests: number;
}

export const EnhancedContextManagement: React.FC = () => {
  const { user } = useAuth();
  const { hasRole } = useUserRoles();
  
  // State management
  const [globalItems, setGlobalItems] = useState<GlobalContextItem[]>([]);
  const [tenantAccess, setTenantAccess] = useState<TenantAccess[]>([]);
  const [contextSharing, setContextSharing] = useState<ContextSharing[]>([]);
  const [organizationQuotas, setOrganizationQuotas] = useState<OrganizationQuotas[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('global');

  // Form states
  const [newGlobalItem, setNewGlobalItem] = useState({
    rag_feature: '',
    item_id: '',
    item_type: '',
    item_title: '',
    item_content: '',
    priority: 1,
    confidence_score: 0.8,
    tags: [] as string[]
  });

  const [newTenantAccess, setNewTenantAccess] = useState({
    organization_id: '',
    rag_feature: '',
    access_level: 'read'
  });

  const [newSharing, setNewSharing] = useState({
    target_organization_id: '',
    rag_feature: '',
    item_id: '',
    sharing_type: 'read_only'
  });

  // Permissions
  const canManageGlobal = hasRole('system_admin');
  const canManageAccess = hasRole('org_admin') || hasRole('system_admin');
  const canShare = hasRole('org_admin') || hasRole('system_admin');
  const canViewQuotas = hasRole('org_admin') || hasRole('system_admin');

  // Load data
  useEffect(() => {
    if (canManageGlobal) {
      loadGlobalItems();
    }
    if (canManageAccess) {
      loadTenantAccess();
    }
    if (canShare) {
      loadContextSharing();
    }
    if (canViewQuotas) {
      loadOrganizationQuotas();
    }
  }, [canManageGlobal, canManageAccess, canShare, canViewQuotas]);

  const loadGlobalItems = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/enhanced-context/global/items');
      const data = await response.json();
      if (data.success) {
        setGlobalItems(data.items);
      }
    } catch (error) {
      console.error('Error loading global items:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTenantAccess = async () => {
    setLoading(true);
    try {
      // This would be a custom endpoint to get all tenant access
      const response = await fetch('/api/enhanced-context/access/list');
      const data = await response.json();
      if (data.success) {
        setTenantAccess(data.access_list);
      }
    } catch (error) {
      console.error('Error loading tenant access:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadContextSharing = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/enhanced-context/sharing/received');
      const data = await response.json();
      if (data.success) {
        setContextSharing(data.shared_items);
      }
    } catch (error) {
      console.error('Error loading context sharing:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizationQuotas = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/enhanced-context/quotas/${user?.organization_id}`);
      const data = await response.json();
      if (data.success) {
        setOrganizationQuotas([data.quotas]);
      }
    } catch (error) {
      console.error('Error loading organization quotas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGlobalItem = async () => {
    try {
      const response = await fetch('/api/enhanced-context/global/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newGlobalItem),
      });
      
      const data = await response.json();
      if (data.success) {
        setNewGlobalItem({
          rag_feature: '',
          item_id: '',
          item_type: '',
          item_title: '',
          item_content: '',
          priority: 1,
          confidence_score: 0.8,
          tags: []
        });
        loadGlobalItems();
      } else {
        alert('Error adding global item: ' + data.error);
      }
    } catch (error) {
      console.error('Error adding global item:', error);
      alert('Error adding global item');
    }
  };

  const handleGrantAccess = async () => {
    try {
      const response = await fetch('/api/enhanced-context/access/grant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTenantAccess),
      });
      
      const data = await response.json();
      if (data.success) {
        setNewTenantAccess({
          organization_id: '',
          rag_feature: '',
          access_level: 'read'
        });
        loadTenantAccess();
      } else {
        alert('Error granting access: ' + data.error);
      }
    } catch (error) {
      console.error('Error granting access:', error);
      alert('Error granting access');
    }
  };

  const handleShareItem = async () => {
    try {
      const response = await fetch('/api/enhanced-context/sharing/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSharing),
      });
      
      const data = await response.json();
      if (data.success) {
        setNewSharing({
          target_organization_id: '',
          rag_feature: '',
          item_id: '',
          sharing_type: 'read_only'
        });
        loadContextSharing();
      } else {
        alert('Error sharing item: ' + data.error);
      }
    } catch (error) {
      console.error('Error sharing item:', error);
      alert('Error sharing item');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'inactive':
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Enhanced Context Management</h2>
          <p className="text-gray-600">
            Manage app-wide RAG context, tenant access, and knowledge sharing
          </p>
        </div>
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          <span className="text-sm text-gray-500">
            {organizationQuotas.length > 0 && (
              `${organizationQuotas[0].current_context_items}/${organizationQuotas[0].max_context_items} items`
            )}
          </span>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="global" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Global Context
          </TabsTrigger>
          <TabsTrigger value="access" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Tenant Access
          </TabsTrigger>
          <TabsTrigger value="sharing" className="flex items-center gap-2">
            <Share2 className="h-4 w-4" />
            Knowledge Sharing
          </TabsTrigger>
          <TabsTrigger value="quotas" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Quotas & Limits
          </TabsTrigger>
        </TabsList>

        {/* Global Context Tab */}
        <TabsContent value="global" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Global Context Items
              </CardTitle>
              <CardDescription>
                App-wide knowledge accessible to all tenants
              </CardDescription>
            </CardHeader>
            <CardContent>
              {canManageGlobal && (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="mb-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Global Item
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Add Global Context Item</DialogTitle>
                      <DialogDescription>
                        Create a new global context item accessible to all tenants
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <RAGFeatureSelector
                            value={newGlobalItem.rag_feature}
                            onChange={(value) => setNewGlobalItem({...newGlobalItem, rag_feature: value})}
                            organizationId={user?.organization_id || ''}
                            placeholder="Select RAG feature for global item..."
                          />
                        </div>
                        <div>
                          <Label htmlFor="item_id">Item ID</Label>
                          <Input
                            id="item_id"
                            value={newGlobalItem.item_id}
                            onChange={(e) => setNewGlobalItem({...newGlobalItem, item_id: e.target.value})}
                            placeholder="unique-item-id"
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="item_title">Title</Label>
                        <Input
                          id="item_title"
                          value={newGlobalItem.item_title}
                          onChange={(e) => setNewGlobalItem({...newGlobalItem, item_title: e.target.value})}
                          placeholder="Item title"
                        />
                      </div>
                      <div>
                        <Label htmlFor="item_content">Content</Label>
                        <Textarea
                          id="item_content"
                          value={newGlobalItem.item_content}
                          onChange={(e) => setNewGlobalItem({...newGlobalItem, item_content: e.target.value})}
                          placeholder="Item content"
                          rows={4}
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="priority">Priority</Label>
                          <Input
                            id="priority"
                            type="number"
                            value={newGlobalItem.priority}
                            onChange={(e) => setNewGlobalItem({...newGlobalItem, priority: parseInt(e.target.value)})}
                            min="1"
                            max="10"
                          />
                        </div>
                        <div>
                          <Label htmlFor="confidence_score">Confidence Score</Label>
                          <Input
                            id="confidence_score"
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            value={newGlobalItem.confidence_score}
                            onChange={(e) => setNewGlobalItem({...newGlobalItem, confidence_score: parseFloat(e.target.value)})}
                          />
                        </div>
                      </div>
                      <Button onClick={handleAddGlobalItem} className="w-full">
                        Add Global Item
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Feature</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {globalItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.rag_feature}</TableCell>
                      <TableCell>{item.item_title}</TableCell>
                      <TableCell>{item.item_type}</TableCell>
                      <TableCell>{item.priority}</TableCell>
                      <TableCell>{(item.confidence_score * 100).toFixed(1)}%</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(item.status)}
                          {item.status}
                        </div>
                      </TableCell>
                      <TableCell>
                        {new Date(item.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tenant Access Tab */}
        <TabsContent value="access" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Tenant Access Management
              </CardTitle>
              <CardDescription>
                Control which tenants can access global RAG features
              </CardDescription>
            </CardHeader>
            <CardContent>
              {canManageAccess && (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="mb-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Grant Access
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Grant Tenant Access</DialogTitle>
                      <DialogDescription>
                        Grant a tenant access to a global RAG feature
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="org_id">Organization ID</Label>
                        <Input
                          id="org_id"
                          value={newTenantAccess.organization_id}
                          onChange={(e) => setNewTenantAccess({...newTenantAccess, organization_id: e.target.value})}
                          placeholder="organization-uuid"
                        />
                      </div>
                      <div>
                        <RAGFeatureSelector
                          value={newTenantAccess.rag_feature}
                          onChange={(value) => setNewTenantAccess({...newTenantAccess, rag_feature: value})}
                          organizationId={user?.organization_id || ''}
                          placeholder="Select RAG feature for tenant access..."
                        />
                      </div>
                      <div>
                        <Label htmlFor="access_level">Access Level</Label>
                        <Select
                          value={newTenantAccess.access_level}
                          onValueChange={(value) => setNewTenantAccess({...newTenantAccess, access_level: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="read">Read Only</SelectItem>
                            <SelectItem value="write">Read & Write</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button onClick={handleGrantAccess} className="w-full">
                        Grant Access
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Organization</TableHead>
                    <TableHead>RAG Feature</TableHead>
                    <TableHead>Access Level</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tenantAccess.map((access) => (
                    <TableRow key={access.id}>
                      <TableCell>{access.organization_id}</TableCell>
                      <TableCell>{access.rag_feature}</TableCell>
                      <TableCell>{access.access_level}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(access.enabled ? 'active' : 'inactive')}
                          {access.enabled ? 'Enabled' : 'Disabled'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Knowledge Sharing Tab */}
        <TabsContent value="sharing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Share2 className="h-5 w-5" />
                Knowledge Sharing
              </CardTitle>
              <CardDescription>
                Share context items between tenants
              </CardDescription>
            </CardHeader>
            <CardContent>
              {canShare && (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="mb-4">
                      <Share2 className="h-4 w-4 mr-2" />
                      Share Item
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Share Context Item</DialogTitle>
                      <DialogDescription>
                        Share a context item with another tenant
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="target_org">Target Organization</Label>
                        <Input
                          id="target_org"
                          value={newSharing.target_organization_id}
                          onChange={(e) => setNewSharing({...newSharing, target_organization_id: e.target.value})}
                          placeholder="target-organization-uuid"
                        />
                      </div>
                      <div>
                        <RAGFeatureSelector
                          value={newSharing.rag_feature}
                          onChange={(value) => setNewSharing({...newSharing, rag_feature: value})}
                          organizationId={user?.organization_id || ''}
                          placeholder="Select RAG feature for sharing..."
                        />
                      </div>
                      <div>
                        <Label htmlFor="sharing_item_id">Item ID</Label>
                        <Input
                          id="sharing_item_id"
                          value={newSharing.item_id}
                          onChange={(e) => setNewSharing({...newSharing, item_id: e.target.value})}
                          placeholder="item-id-to-share"
                        />
                      </div>
                      <div>
                        <Label htmlFor="sharing_type">Sharing Type</Label>
                        <Select
                          value={newSharing.sharing_type}
                          onValueChange={(value) => setNewSharing({...newSharing, sharing_type: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="read_only">Read Only</SelectItem>
                            <SelectItem value="collaborative">Collaborative</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button onClick={handleShareItem} className="w-full">
                        Share Item
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Source Org</TableHead>
                    <TableHead>Target Org</TableHead>
                    <TableHead>RAG Feature</TableHead>
                    <TableHead>Item ID</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contextSharing.map((sharing) => (
                    <TableRow key={sharing.id}>
                      <TableCell>{sharing.source_organization_id}</TableCell>
                      <TableCell>{sharing.target_organization_id}</TableCell>
                      <TableCell>{sharing.rag_feature}</TableCell>
                      <TableCell>{sharing.item_id}</TableCell>
                      <TableCell>{sharing.sharing_type}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(sharing.status)}
                          {sharing.status}
                        </div>
                      </TableCell>
                      <TableCell>
                        {new Date(sharing.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {sharing.status === 'pending' && (
                            <Button variant="outline" size="sm">
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <Button variant="outline" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quotas Tab */}
        <TabsContent value="quotas" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Organization Quotas
              </CardTitle>
              <CardDescription>
                Monitor and manage organization context limits
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Organization</TableHead>
                    <TableHead>Context Items</TableHead>
                    <TableHead>Global Access</TableHead>
                    <TableHead>Sharing Requests</TableHead>
                    <TableHead>Usage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {organizationQuotas.map((quota) => (
                    <TableRow key={quota.id}>
                      <TableCell>{quota.organization_id}</TableCell>
                      <TableCell>
                        {quota.current_context_items}/{quota.max_context_items}
                      </TableCell>
                      <TableCell>
                        {quota.current_global_access}/{quota.max_global_access_features}
                      </TableCell>
                      <TableCell>
                        {quota.current_sharing_requests}/{quota.max_sharing_requests}
                      </TableCell>
                      <TableCell>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ 
                              width: `${(quota.current_context_items / quota.max_context_items) * 100}%` 
                            }}
                          ></div>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
