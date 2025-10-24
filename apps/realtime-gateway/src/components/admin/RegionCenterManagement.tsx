import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Edit, Trash2, Search, Building, MapPin } from 'lucide-react';
import { useOrganizations } from '@/hooks/useOrganizations';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { useAdminManagement } from '@/hooks/useAdminManagement';
import { EditRegionDialog } from './EditRegionDialog';
import { EditCenterDialog } from './EditCenterDialog';

export const RegionCenterManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [editRegionOpen, setEditRegionOpen] = useState(false);
  const [editCenterOpen, setEditCenterOpen] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<any>(null);
  const [selectedCenter, setSelectedCenter] = useState<any>(null);

  const { organizations } = useOrganizations();
  const { regions, centers, loading, refetch } = useOrganizationData();
  const { deleteRegion, deleteCenter, loading: deleteLoading } = useAdminManagement();

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

  // Filter data based on search term
  const filteredRegions = regions.filter(region =>
    region.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    getOrganizationName(region.organization_id).toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredCenters = centers.filter(center =>
    center.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (center.address && center.address.toLowerCase().includes(searchTerm.toLowerCase())) ||
    getRegionName(center.region_id).toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEditRegion = (region: any) => {
    setSelectedRegion(region);
    setEditRegionOpen(true);
  };

  const handleEditCenter = (center: any) => {
    setSelectedCenter(center);
    setEditCenterOpen(true);
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

  const handleSuccess = () => {
    refetch();
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading management data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="flex items-center space-x-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search regions and centers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <Tabs defaultValue="regions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="regions" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            Regions ({filteredRegions.length})
          </TabsTrigger>
          <TabsTrigger value="centers" className="flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            Centers ({filteredCenters.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="regions">
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
                      <TableCell colSpan={4} className="text-center text-muted-foreground">
                        No regions found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="centers">
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
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        No centers found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
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
    </div>
  );
};