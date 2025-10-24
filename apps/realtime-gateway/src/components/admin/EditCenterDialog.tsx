import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useAdminManagement } from '@/hooks/useAdminManagement';
import { useOrganizationData } from '@/hooks/useOrganizationData';

interface Center {
  id: string;
  name: string;
  address?: string;
  region_id: string;
  created_at: string;
  updated_at: string;
  region?: {
    id: string;
    name: string;
    organization_id: string;
  };
}

interface EditCenterDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  center: Center | null;
  onSuccess: () => void;
}

export const EditCenterDialog = ({ open, onOpenChange, center, onSuccess }: EditCenterDialogProps) => {
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    region_id: ''
  });
  
  const { updateCenter, loading } = useAdminManagement();
  const { regions } = useOrganizationData();

  useEffect(() => {
    if (center) {
      setFormData({
        name: center.name,
        address: center.address || '',
        region_id: center.region_id
      });
    }
  }, [center]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!center) return;
    
    const result = await updateCenter({
      id: center.id,
      name: formData.name,
      address: formData.address || undefined,
      region_id: formData.region_id
    });
    
    if (result.data) {
      onSuccess();
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Center</DialogTitle>
          <DialogDescription>
            Update the center information below.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Center Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
            />
          </div>
          
          <div>
            <Label htmlFor="address">Address</Label>
            <Textarea
              id="address"
              value={formData.address}
              onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
              placeholder="Enter center address (optional)"
              rows={3}
            />
          </div>
          
          <div>
            <Label htmlFor="region">Region</Label>
            <Select 
              value={formData.region_id} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, region_id: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select region" />
              </SelectTrigger>
              <SelectContent>
                {regions.map(region => (
                  <SelectItem key={region.id} value={region.id}>
                    {region.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Updating...' : 'Update Center'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};