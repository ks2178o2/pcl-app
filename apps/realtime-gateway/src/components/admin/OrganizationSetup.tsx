import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { useSystemAdmin } from '@/hooks/useSystemAdmin';
import { useOrganizations } from '@/hooks/useOrganizations';
import { useOrganizationData } from '@/hooks/useOrganizationData';

type SetupStep = 'organization' | 'region' | 'center';

export const OrganizationSetup = () => {
  const [activeStep, setActiveStep] = useState<SetupStep>('organization');
  const [selectedOrganization, setSelectedOrganization] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  
  const { 
    loading, 
    createOrganization, 
    createRegion, 
    createCenter 
  } = useSystemAdmin();
  
  const { organizations, refetch: refetchOrganizations } = useOrganizations();
  const { regions, centers, refetch: refetchOrgData } = useOrganizationData();

  const [formData, setFormData] = useState({
    organizationName: '',
    businessType: '',
    regionName: '',
    centerName: '',
    centerAddress: '',
    transcriptionProvider: 'deepgram' as 'deepgram' | 'assemblyai',
    transcriptionFallbackProvider: 'assemblyai' as 'deepgram' | 'assemblyai',
    transcriptionAllowFallback: true,
    transcriptionBakeoff: false
  });

  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await createOrganization({
      name: formData.organizationName,
      businessType: formData.businessType,
      transcriptionProvider: formData.transcriptionProvider,
      transcriptionFallbackProvider: formData.transcriptionFallbackProvider,
      transcriptionAllowFallback: formData.transcriptionAllowFallback,
      transcriptionBakeoff: formData.transcriptionBakeoff
    });
    
    if (result.data) {
      await refetchOrganizations();
      setSelectedOrganization(result.data.id);
      setActiveStep('region');
      setFormData(prev => ({ 
        ...prev, 
        organizationName: '', 
        businessType: '',
        transcriptionProvider: 'deepgram',
        transcriptionFallbackProvider: 'assemblyai',
        transcriptionAllowFallback: true,
        transcriptionBakeoff: false
      }));
    }
  };

  const handleCreateRegion = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await createRegion({
      name: formData.regionName,
      organization_id: selectedOrganization
    });
    
    if (result.data) {
      await refetchOrgData();
      setSelectedRegion(result.data.id);
      setActiveStep('center');
      setFormData(prev => ({ ...prev, regionName: '' }));
    }
  };

  const handleCreateCenter = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await createCenter({
      name: formData.centerName,
      address: formData.centerAddress,
      regionId: selectedRegion
    });
    
    if (result.data) {
      await refetchOrgData();
      setFormData(prev => ({ ...prev, centerName: '', centerAddress: '' }));
    }
  };

  // Filter regions by selected organization
  const filteredRegions = regions.filter(region => 
    selectedOrganization === '' || region.organization_id === selectedOrganization
  );

  return (
    <div className="space-y-6">
      <div className="flex space-x-2">
        {(['organization', 'region', 'center'] as SetupStep[]).map((step) => (
          <Button
            key={step}
            variant={activeStep === step ? 'default' : 'outline'}
            onClick={() => setActiveStep(step)}
            className="capitalize"
          >
            {step}
          </Button>
        ))}
      </div>

      {activeStep === 'organization' && (
        <Card>
          <CardHeader>
            <CardTitle>Create Organization</CardTitle>
            <CardDescription>Set up a new customer organization</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateOrganization} className="space-y-4">
              <div>
                <Label htmlFor="orgName">Organization Name</Label>
                <Input
                  id="orgName"
                  value={formData.organizationName}
                  onChange={(e) => setFormData(prev => ({ ...prev, organizationName: e.target.value }))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="businessType">Business Type</Label>
                <Input
                  id="businessType"
                  value={formData.businessType}
                  onChange={(e) => setFormData(prev => ({ ...prev, businessType: e.target.value }))}
                  placeholder="e.g., Healthcare, Dental, Medical"
                />
              </div>

              {/* Transcription Settings */}
              <div className="space-y-4 pt-4 border-t">
                <h3 className="text-sm font-semibold">Transcription Settings</h3>
                
                <div>
                  <Label htmlFor="transcriptionProvider">Primary Transcription Provider</Label>
                  <Select
                    value={formData.transcriptionProvider}
                    onValueChange={(value: 'deepgram' | 'assemblyai') => setFormData(prev => ({ ...prev, transcriptionProvider: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="deepgram">Deepgram (Nova-2)</SelectItem>
                      <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="transcriptionFallbackProvider">Fallback Provider</Label>
                  <Select
                    value={formData.transcriptionFallbackProvider}
                    onValueChange={(value: 'deepgram' | 'assemblyai') => setFormData(prev => ({ ...prev, transcriptionFallbackProvider: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="deepgram">Deepgram (Nova-2)</SelectItem>
                      <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="allowFallback">Enable automatic fallback</Label>
                  <Switch
                    id="allowFallback"
                    checked={formData.transcriptionAllowFallback}
                    onCheckedChange={(checked) => setFormData(prev => ({ ...prev, transcriptionAllowFallback: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="bakeoff">Enable bakeoff mode (doubles cost)</Label>
                  <Switch
                    id="bakeoff"
                    checked={formData.transcriptionBakeoff}
                    onCheckedChange={(checked) => setFormData(prev => ({ ...prev, transcriptionBakeoff: checked }))}
                  />
                </div>
              </div>

              <Button type="submit" disabled={loading}>
                Create Organization
              </Button>
            </form>
            
            {organizations.length > 0 && (
              <div className="mt-6">
                <Label>Select Existing Organization</Label>
                <Select value={selectedOrganization} onValueChange={setSelectedOrganization}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {organizations.map(org => (
                      <SelectItem key={org.id} value={org.id}>
                        {org.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedOrganization && (
                  <Button 
                    className="mt-2" 
                    onClick={() => setActiveStep('region')}
                  >
                    Continue to Regions
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeStep === 'region' && selectedOrganization && (
        <Card>
          <CardHeader>
            <CardTitle>Create Region</CardTitle>
            <CardDescription>Add regions within the selected organization</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateRegion} className="space-y-4">
              <div>
                <Label htmlFor="regionName">Region Name</Label>
                <Input
                  id="regionName"
                  value={formData.regionName}
                  onChange={(e) => setFormData(prev => ({ ...prev, regionName: e.target.value }))}
                  required
                />
              </div>
              <Button type="submit" disabled={loading}>
                Create Region
              </Button>
            </form>

            {/* Show existing regions for selected organization */}
            {filteredRegions.length > 0 && (
              <div className="mt-6">
                <Label>Existing Regions in Selected Organization</Label>
                <div className="mt-2 space-y-2">
                  {filteredRegions.map(region => (
                    <div key={region.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <span className="font-medium">{region.name}</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedRegion(region.id);
                          setActiveStep('center');
                        }}
                      >
                        Select & Continue
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeStep === 'center' && selectedRegion && (
        <Card>
          <CardHeader>
            <CardTitle>Create Center</CardTitle>
            <CardDescription>Add centers within the selected region</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateCenter} className="space-y-4">
              <div>
                <Label htmlFor="centerName">Center Name</Label>
                <Input
                  id="centerName"
                  value={formData.centerName}
                  onChange={(e) => setFormData(prev => ({ ...prev, centerName: e.target.value }))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="centerAddress">Address (Optional)</Label>
                <Input
                  id="centerAddress"
                  value={formData.centerAddress}
                  onChange={(e) => setFormData(prev => ({ ...prev, centerAddress: e.target.value }))}
                  placeholder="Street address, city, state"
                />
              </div>
              <Button type="submit" disabled={loading}>
                Create Center
              </Button>
            </form>
            
            {/* Show existing centers for selected region */}
            {selectedRegion && centers.filter(c => c.region_id === selectedRegion).length > 0 && (
              <div className="mt-6">
                <Label>Existing Centers in Selected Region</Label>
                <div className="mt-2 space-y-2">
                  {centers
                    .filter(center => center.region_id === selectedRegion)
                    .map(center => (
                      <div key={center.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <span className="font-medium">{center.name}</span>
                          {center.address && (
                            <p className="text-sm text-muted-foreground">{center.address}</p>
                          )}
                        </div>
                        <Badge variant="secondary">Created</Badge>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};