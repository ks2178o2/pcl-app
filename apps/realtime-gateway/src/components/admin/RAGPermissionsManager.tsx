import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  Shield, 
  Settings, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Plus,
  Trash2,
  Edit,
  Lock,
  Unlock,
  Users
} from 'lucide-react';
import { useRAGFeatures } from '@/hooks/useRAGFeatures';
import { useOrganizationData } from '@/hooks/useOrganizationData';

// Role definitions with default RAG permissions
const ROLE_DEFAULTS = {
  'system_admin': {
    name: 'System Admin',
    description: 'Full system access',
    defaultPermissions: ['all'], // All permissions
    color: 'purple'
  },
  'org_admin': {
    name: 'Org Admin',
    description: 'Organization management',
    defaultPermissions: [
      'sales_intelligence',
      'customer_insights',
      'call_analysis',
      'lead_scoring'
    ],
    color: 'blue'
  },
  'team_leader': {
    name: 'Team Leader',
    description: 'Team management',
    defaultPermissions: [
      'sales_intelligence',
      'call_analysis'
    ],
    color: 'green'
  },
  'sales_coach': {
    name: 'Sales Coach',
    description: 'Sales coaching',
    defaultPermissions: [
      'sales_intelligence',
      'customer_insights',
      'call_analysis',
      'lead_scoring'
    ],
    color: 'teal'
  },
  'salesperson': {
    name: 'Salesperson',
    description: 'Sales execution',
    defaultPermissions: [
      'sales_intelligence',
      'customer_insights'
    ],
    color: 'orange'
  },
  'sales_doctor': {
    name: 'Sales Doctor',
    description: 'Medical sales specialist',
    defaultPermissions: [
      'sales_intelligence',
      'customer_insights',
      'call_analysis'
    ],
    color: 'red'
  }
};

interface RAGPermission {
  role_id: string;
  rag_feature: string;
  allowed: boolean;
  can_modify: boolean;
}

export const RAGPermissionsManager: React.FC = () => {
  const { organizationId } = useOrganizationData();
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [permissions, setPermissions] = useState<RAGPermission[]>([]);
  const [availableFeatures, setAvailableFeatures] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load permissions for selected role
  const loadPermissions = async () => {
    if (!selectedRole) return;
    
    setLoading(true);
    try {
      // In a real implementation, this would fetch from your backend
      // For now, we'll use default permissions
      const roleDefaults = ROLE_DEFAULTS[selectedRole as keyof typeof ROLE_DEFAULTS];
      const initialPermissions = availableFeatures.map(feature => ({
        role_id: selectedRole,
        rag_feature: feature,
        allowed: roleDefaults?.defaultPermissions.includes(feature) || roleDefaults?.defaultPermissions.includes('all'),
        can_modify: true
      }));
      
      setPermissions(initialPermissions);
      setHasChanges(false);
    } catch (error) {
      console.error('Error loading permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load available RAG features
  useEffect(() => {
    // Fetch from backend or use mock data
    setAvailableFeatures([
      'sales_intelligence',
      'customer_insights',
      'call_analysis',
      'lead_scoring'
    ]);
  }, []);

  // Load permissions when role is selected
  useEffect(() => {
    if (selectedRole) {
      loadPermissions();
    }
  }, [selectedRole]);

  // Handle permission toggle
  const handlePermissionToggle = (ragFeature: string, allowed: boolean) => {
    setPermissions(prev => 
      prev.map(p => 
        p.rag_feature === ragFeature 
          ? { ...p, allowed }
          : p
      )
    );
    setHasChanges(true);
  };

  // Save permissions
  const handleSave = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would POST to your backend
      console.log('Saving permissions:', permissions);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Reset to defaults
  const handleReset = () => {
    loadPermissions();
  };

  return (
    <div className="space-y-6">
      {/* Role Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Role-Based RAG Permissions
          </CardTitle>
          <CardDescription>
            Configure RAG feature access for each user role. Permissions are applied at the role level.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="role-select">Select Role</Label>
              <Select value={selectedRole} onValueChange={setSelectedRole}>
                <SelectTrigger id="role-select" className="mt-2">
                  <SelectValue placeholder="Choose a role to configure" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ROLE_DEFAULTS).map(([key, role]) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-2">
                        <Shield className={`h-4 w-4 text-${role.color}-500`} />
                        <span>{role.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedRole && (
                <p className="text-sm text-muted-foreground mt-2">
                  {ROLE_DEFAULTS[selectedRole as keyof typeof ROLE_DEFAULTS]?.description}
                </p>
              )}
            </div>

            {/* Selected Role Info */}
            {selectedRole && (
              <div className="bg-muted p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">
                      {ROLE_DEFAULTS[selectedRole as keyof typeof ROLE_DEFAULTS]?.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {ROLE_DEFAULTS[selectedRole as keyof typeof ROLE_DEFAULTS]?.description}
                    </p>
                  </div>
                  <Badge variant="outline" className="ml-2">
                    {permissions.filter(p => p.allowed).length} / {permissions.length} enabled
                  </Badge>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Permissions Table */}
      {selectedRole && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>RAG Feature Permissions</CardTitle>
                <CardDescription>
                  Configure which RAG features users with this role can access
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {hasChanges && (
                  <Badge variant="outline" className="text-orange-600">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Unsaved changes
                  </Badge>
                )}
                <Button variant="outline" onClick={handleReset} disabled={loading}>
                  Reset to Defaults
                </Button>
                <Button onClick={handleSave} disabled={loading || !hasChanges}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>RAG Feature</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Default</TableHead>
                  <TableHead>Permission</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {permissions.map((permission, index) => (
                  <TableRow key={permission.rag_feature}>
                    <TableCell className="font-medium">
                      {permission.rag_feature.replace(/_/g, ' ').toUpperCase()}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {permission.rag_feature === 'sales_intelligence' && 'AI-powered sales insights'}
                      {permission.rag_feature === 'customer_insights' && 'Customer behavior analysis'}
                      {permission.rag_feature === 'call_analysis' && 'Real-time call analysis'}
                      {permission.rag_feature === 'lead_scoring' && 'AI-powered lead qualification'}
                    </TableCell>
                    <TableCell>
                      {ROLE_DEFAULTS[selectedRole as keyof typeof ROLE_DEFAULTS]?.defaultPermissions.includes(permission.rag_feature) ||
                       ROLE_DEFAULTS[selectedRole as keyof typeof ROLE_DEFAULTS]?.defaultPermissions.includes('all') ? (
                        <Badge variant="default" className="text-xs">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Default: Allowed
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs">
                          <XCircle className="h-3 w-3 mr-1" />
                          Default: Restricted
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={permission.allowed}
                          onCheckedChange={(checked) => handlePermissionToggle(permission.rag_feature, checked)}
                          disabled={!permission.can_modify || loading}
                        />
                        <span className="text-sm">
                          {permission.allowed ? 'Allowed' : 'Restricted'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {permission.allowed ? (
                        <Badge className="bg-green-100 text-green-800">
                          <Unlock className="h-3 w-3 mr-1" />
                          Enabled
                        </Badge>
                      ) : (
                        <Badge variant="destructive">
                          <Lock className="h-3 w-3 mr-1" />
                          Disabled
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Quick Permissions Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Role Permissions Summary
          </CardTitle>
          <CardDescription>
            Quick overview of default permissions for each role
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(ROLE_DEFAULTS).map(([key, role]) => (
              <div key={key} className={`border-2 rounded-lg p-4 ${selectedRole === key ? 'border-primary' : 'border-muted'}`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{role.name}</h3>
                  <Badge variant="outline">{role.color}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{role.description}</p>
                <div className="space-y-1">
                  {role.defaultPermissions.includes('all') ? (
                    <Badge className="w-full justify-center">All Permissions</Badge>
                  ) : (
                    role.defaultPermissions.map(permission => (
                      <Badge key={permission} variant="secondary" className="mr-1 mb-1">
                        {permission.replace(/_/g, ' ')}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

