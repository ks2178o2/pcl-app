import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAdminManagement } from '@/hooks/useAdminManagement';
import { useOrganizations } from '@/hooks/useOrganizations';

interface Region {
  id: string;
  name: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

interface EditRegionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  region: Region | null;
  onSuccess: () => void;
}

export const EditRegionDialog = ({ open, onOpenChange, region, onSuccess }: EditRegionDialogProps) => {
  const [formData, setFormData] = useState({
    name: '',
    organization_id: ''
  });
  
  const { updateRegion, loading } = useAdminManagement();
  const { organizations } = useOrganizations();

  useEffect(() => {
    if (region) {
      setFormData({
        name: region.name,
        organization_id: region.organization_id
      });
    }
  }, [region]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!region) return;
    
    const result = await updateRegion({
      id: region.id,
      name: formData.name,
      organization_id: formData.organization_id
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
          <DialogTitle>Edit Region</DialogTitle>
          <DialogDescription>
            Update the region information below.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Region Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
            />
          </div>
          
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Updating...' : 'Update Region'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};