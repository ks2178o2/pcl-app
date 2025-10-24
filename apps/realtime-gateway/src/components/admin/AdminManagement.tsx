import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Edit, Trash2, Search, Building, MapPin, Users } from 'lucide-react';
import { useOrganizations } from '@/hooks/useOrganizations';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { useAdminManagement } from '@/hooks/useAdminManagement';
import { useAdminUsers } from '@/hooks/useAdminUsers';
import { EditRegionDialog } from './EditRegionDialog';
import { EditCenterDialog } from './EditCenterDialog';
import { EditUserDialog } from './EditUserDialog';
import { EditOrganizationDialog } from './EditOrganizationDialog';

export const AdminManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOrgFilter, setSelectedOrgFilter] = useState<string>('all');
  const [editRegionOpen, setEditRegionOpen] = useState(false);
  const [editCenterOpen, setEditCenterOpen] = useState(false);
  const [editUserOpen, setEditUserOpen] = useState(false);
  const [editOrganizationOpen, setEditOrganizationOpen] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<any>(null);
  const [selectedCenter, setSelectedCenter] = useState<any>(null);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [selectedOrganization, setSelectedOrganization] = useState<any>(null);

  const { organizations, refetch: refetchOrganizations } = useOrganizations();
  const { regions, centers, loading, refetch } = useOrganizationData();
  const { users, loading: usersLoading, refetch: refetchUsers, toggleUserStatus } = useAdminUsers();
  const { 
    deleteRegion, 
    deleteCenter, 
    toggleOrganizationStatus,
    toggleRegionStatus,
    toggleCenterStatus,
    loading: deleteLoading 
  } = useAdminManagement();

  // Get organization name by ID
  const getOrganizationName = (orgId: string) => {
    const org = organizations.find(o => o.id === orgId);
    return org?.name || 'Unknown Organization';
  };

  // Get region name by ID
  const getRegionName = (regionId: string) => {
    const region = regions.find(r => r.id === regionId);
    return region?.name || 'Unknown Region';
  };

  // Filter data based on search term and organization
  const filteredRegions = regions.filter(region => {
    const matchesSearch = region.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      getOrganizationName(region.organization_id).toLowerCase().includes(searchTerm.toLowerCase());
    const matchesOrg = selectedOrgFilter === 'all' || region.organization_id === selectedOrgFilter;
    return matchesSearch && matchesOrg;
  });

  const filteredCenters = centers.filter(center => {
    const matchesSearch = center.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (center.address && center.address.toLowerCase().includes(searchTerm.toLowerCase())) ||
      getRegionName(center.region_id).toLowerCase().includes(searchTerm.toLowerCase());
    
    const centerRegion = regions.find(r => r.id === center.region_id);
    const matchesOrg = selectedOrgFilter === 'all' || (centerRegion && centerRegion.organization_id === selectedOrgFilter);
    return matchesSearch && matchesOrg;
  });

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesOrg = selectedOrgFilter === 'all' || user.organization_id === selectedOrgFilter;
    return matchesSearch && matchesOrg;
  });

  const filteredOrganizations = organizations.filter(org =>
    org.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEditRegion = (region: any) => {
    setSelectedRegion(region);
    setEditRegionOpen(true);
  };

  const handleEditCenter = (center: any) => {
    setSelectedCenter(center);
    setEditCenterOpen(true);
  };

  const handleEditUser = (user: any) => {
    setSelectedUser(user);
    setEditUserOpen(true);
  };

  const handleEditOrganization = (organization: any) => {
    setSelectedOrganization(organization);
    setEditOrganizationOpen(true);
  };

  const handleDeleteRegion = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete the region "${name}"? This action cannot be undone.`)) {
      const result = await deleteRegion(id);
      if (!result.error) {
        refetch();
      }
    }
  };

  const handleDeleteCenter = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete the center "${name}"? This action cannot be undone.`)) {
      const result = await deleteCenter(id);
      if (!result.error) {
        refetch();
      }
    }
  };

  const handleToggleOrganizationStatus = async (id: string, isActive: boolean) => {
    const result = await toggleOrganizationStatus(id, isActive);
    if (!result.error) {
      refetchOrganizations();
      refetch();
    }
  };

  const handleToggleRegionStatus = async (id: string, isActive: boolean) => {
    const result = await toggleRegionStatus(id, isActive);
    if (!result.error) {
      refetch();
    }
  };

  const handleToggleCenterStatus = async (id: string, isActive: boolean) => {
    const result = await toggleCenterStatus(id, isActive);
    if (!result.error) {
      refetch();
    }
  };

  const handleToggleUserStatus = async (id: string, isActive: boolean) => {
    const result = await toggleUserStatus(id, isActive);
    if (!result.error) {
      refetchUsers();
    }
  };

  const handleSuccess = () => {
    refetch();
  };

  if (loading || usersLoading) {
    return <div className="flex justify-center items-center h-64">Loading management data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Global Search */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <Tabs defaultValue="organizations" className="space-y-4">
        <TabsList>
          <TabsTrigger value="organizations" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            Organizations ({filteredOrganizations.length})
          </TabsTrigger>
          <TabsTrigger value="regions" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            Regions ({filteredRegions.length})
          </TabsTrigger>
          <TabsTrigger value="centers" className="flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            Centers ({filteredCenters.length})
          </TabsTrigger>
          <TabsTrigger value="users" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Users ({filteredUsers.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="organizations">
          <Card>
            <CardHeader>
              <CardTitle>Organization Management</CardTitle>
              <CardDescription>
                View and manage all organizations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Organization Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOrganizations.map((org) => (
                    <TableRow key={org.id}>
                      <TableCell className="font-medium">{org.name}</TableCell>
                      <TableCell>
                        <Switch
                          checked={org.is_active}
                          onCheckedChange={(checked) => handleToggleOrganizationStatus(org.id, checked)}
                          disabled={deleteLoading}
                          className={org.is_active ? "data-[state=checked]:bg-green-500" : ""}
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(org.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditOrganization(org)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredOrganizations.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground">
                        No organizations found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regions">
          <div className="space-y-4">
            {/* Organization Filter for Regions */}
            <div className="flex items-center space-x-4">
              <Select value={selectedOrgFilter} onValueChange={setSelectedOrgFilter}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by organization" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Organizations</SelectItem>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle>Region Management</CardTitle>
                <CardDescription>
                  View and manage all regions across organizations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Region Name</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRegions.map((region) => (
                      <TableRow key={region.id}>
                        <TableCell className="font-medium">{region.name}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">
                            {getOrganizationName(region.organization_id)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={region.is_active}
                            onCheckedChange={(checked) => handleToggleRegionStatus(region.id, checked)}
                            disabled={deleteLoading}
                            className={region.is_active ? "data-[state=checked]:bg-green-500" : ""}
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(region.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditRegion(region)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteRegion(region.id, region.name)}
                              disabled={deleteLoading}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredRegions.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground">
                          No regions found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="centers">
          <div className="space-y-4">
            {/* Organization Filter for Centers */}
            <div className="flex items-center space-x-4">
              <Select value={selectedOrgFilter} onValueChange={setSelectedOrgFilter}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by organization" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Organizations</SelectItem>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle>Center Management</CardTitle>
                <CardDescription>
                  View and manage all centers across regions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Center Name</TableHead>
                      <TableHead>Region</TableHead>
                      <TableHead>Address</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredCenters.map((center) => (
                      <TableRow key={center.id}>
                        <TableCell className="font-medium">{center.name}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">
                            {getRegionName(center.region_id)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {center.address ? (
                            <span className="text-sm text-muted-foreground">
                              {center.address}
                            </span>
                          ) : (
                            <span className="text-sm text-muted-foreground italic">
                              No address
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={center.is_active}
                            onCheckedChange={(checked) => handleToggleCenterStatus(center.id, checked)}
                            disabled={deleteLoading}
                            className={center.is_active ? "data-[state=checked]:bg-green-500" : ""}
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(center.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditCenter(center)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteCenter(center.id, center.name)}
                              disabled={deleteLoading}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredCenters.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No centers found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users">
          <div className="space-y-4">
            {/* Organization Filter for Users */}
            <div className="flex items-center space-x-4">
              <Select value={selectedOrgFilter} onValueChange={setSelectedOrgFilter}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by organization" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Organizations</SelectItem>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>
                  View and manage all user accounts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Roles</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>Region</TableHead>
                      <TableHead>Center</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{user.email}</TableCell>
                        <TableCell>
                          {user.name ? (
                            <span className="text-sm">{user.name}</span>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {user.roles.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {user.roles.map((role) => (
                                <Badge key={role} variant="outline" className="text-xs">
                                  {role.replace('_', ' ')}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-sm text-muted-foreground">No roles</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {user.organization ? (
                            <Badge variant="secondary">{user.organization.name}</Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {user.region ? (
                            <Badge variant="outline">{user.region.name}</Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {user.center ? (
                            <Badge variant="outline">{user.center.name}</Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={user.is_active}
                            onCheckedChange={(checked) => handleToggleUserStatus(user.id, checked)}
                            disabled={deleteLoading}
                            className={user.is_active ? "data-[state=checked]:bg-green-500" : ""}
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditUser(user)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredUsers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center text-muted-foreground">
                          No users found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Edit Dialogs */}
      <EditRegionDialog
        open={editRegionOpen}
        onOpenChange={setEditRegionOpen}
        region={selectedRegion}
        onSuccess={handleSuccess}
      />
      
      <EditCenterDialog
        open={editCenterOpen}
        onOpenChange={setEditCenterOpen}
        center={selectedCenter}
        onSuccess={handleSuccess}
      />
      
      <EditUserDialog
        open={editUserOpen}
        onOpenChange={setEditUserOpen}
        user={selectedUser}
        onSuccess={handleSuccess}
      />
      
      <EditOrganizationDialog
        open={editOrganizationOpen}
        onOpenChange={setEditOrganizationOpen}
        organization={selectedOrganization}
        onSuccess={() => { refetchOrganizations(); handleSuccess(); }}
      />
    </div>
  );
};