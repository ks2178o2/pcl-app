import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useSystemAdmin } from '@/hooks/useSystemAdmin';
import { useOrganizations } from '@/hooks/useOrganizations';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { UserRole } from '@/hooks/useUserRoles';
import { InviteUserDialog } from './InviteUserDialog';

interface UserFormData {
  email: string;
  password: string;
  name: string;
  organizationId: string;
  roles: UserRole[];
  centerIds: string[];
  regionIds: string[];
}

export const UserManagement = () => {
  const { loading, createUserWithRoles } = useSystemAdmin();
  const { organizations } = useOrganizations();
  const { regions, centers } = useOrganizationData();

  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    password: '',
    name: '',
    organizationId: '',
    roles: [],
    centerIds: [],
    regionIds: []
  });

  const handleRoleChange = (role: UserRole, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      roles: checked 
        ? [...prev.roles, role]
        : prev.roles.filter(r => r !== role)
    }));
  };

  const handleAssignmentChange = (type: 'center' | 'region', id: string, checked: boolean) => {
    const key = `${type}Ids` as keyof Pick<UserFormData, 'centerIds' | 'regionIds'>;
    setFormData(prev => ({
      ...prev,
      [key]: checked 
        ? [...prev[key], id]
        : prev[key].filter(assignId => assignId !== id)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const userData = {
      email: formData.email,
      password: formData.password,
      name: formData.name,
      roles: formData.roles as ('doctor' | 'salesperson' | 'coach' | 'leader' | 'org_admin' | 'system_admin')[],
      center_ids: formData.centerIds.length > 0 ? formData.centerIds : undefined,
      region_id: formData.regionIds.length > 0 ? formData.regionIds[0] : undefined,
      organization_id: formData.organizationId || undefined,
    };

    const result = await createUserWithRoles(userData);
    
    if (result.data) {
      // Reset form
      setFormData({
        email: '',
        password: '',
        name: '',
        organizationId: '',
        roles: [],
        centerIds: [],
        regionIds: []
      });
    }
  };

  const availableRoles: UserRole[] = ['doctor', 'salesperson', 'coach', 'leader', 'system_admin'];

  // Filter regions and centers by selected organization
  const filteredRegions = regions.filter(region => 
    !formData.organizationId || region.organization_id === formData.organizationId
  );
  
  const filteredCenters = centers.filter(center => {
    if (formData.regionIds.length === 0) return true;
    return formData.regionIds.includes(center.region_id);
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Create New User</CardTitle>
            <CardDescription>Add users and assign roles and organizational access</CardDescription>
          </div>
          {formData.organizationId && (
            <InviteUserDialog organizationId={formData.organizationId} />
          )}
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="organization">Organization</Label>
                <Select 
                  value={formData.organizationId} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, organizationId: value, regionIds: [], centerIds: [] }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {organizations.map(org => (
                      <SelectItem key={org.id} value={org.id}>
                        {org.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Roles */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Roles</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {availableRoles.map(role => (
                <div key={role} className="flex items-center space-x-2">
                  <Checkbox
                    id={role}
                    checked={formData.roles.includes(role)}
                    onCheckedChange={(checked) => handleRoleChange(role, !!checked)}
                  />
                  <Label htmlFor={role} className="capitalize">
                    {role.replace('_', ' ')}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Regional Access */}
          {formData.organizationId && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Regional Access</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Regions */}
                <div>
                  <Label className="text-sm font-medium">Regions</Label>
                  <div className="mt-2 space-y-2 max-h-40 overflow-y-auto border rounded p-2">
                    {filteredRegions.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No regions available</p>
                    ) : (
                      filteredRegions.map(region => (
                        <div key={region.id} className="flex items-center space-x-2">
                          <Checkbox
                            id={`region-${region.id}`}
                            checked={formData.regionIds.includes(region.id)}
                            onCheckedChange={(checked) => handleAssignmentChange('region', region.id, !!checked)}
                          />
                          <Label htmlFor={`region-${region.id}`} className="text-sm">
                            {region.name}
                          </Label>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Centers */}
                <div>
                  <Label className="text-sm font-medium">Centers</Label>
                  <div className="mt-2 space-y-2 max-h-40 overflow-y-auto border rounded p-2">
                    {filteredCenters.length === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        {formData.regionIds.length === 0 ? 'Select regions first' : 'No centers available'}
                      </p>
                    ) : (
                      filteredCenters.map(center => (
                        <div key={center.id} className="flex items-center space-x-2">
                          <Checkbox
                            id={`center-${center.id}`}
                            checked={formData.centerIds.includes(center.id)}
                            onCheckedChange={(checked) => handleAssignmentChange('center', center.id, !!checked)}
                          />
                          <Label htmlFor={`center-${center.id}`} className="text-sm">
                            {center.name}
                            {center.address && (
                              <span className="text-muted-foreground"> - {center.address}</span>
                            )}
                          </Label>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <Button type="submit" disabled={loading || formData.roles.length === 0}>
            {loading ? 'Creating User...' : 'Create User'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};