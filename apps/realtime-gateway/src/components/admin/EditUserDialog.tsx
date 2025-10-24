import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { UserRole } from "@/hooks/useUserRoles";
import { useOrganizationData } from "@/hooks/useOrganizationData";

interface EditUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: any;
  onSuccess: () => void;
}

const AVAILABLE_ROLES: UserRole[] = ['doctor', 'salesperson', 'coach', 'leader', 'system_admin'];

export const EditUserDialog = ({ open, onOpenChange, user, onSuccess }: EditUserDialogProps) => {
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<UserRole[]>([]);
  const [selectedRegionId, setSelectedRegionId] = useState<string>('');
  const [selectedCenterId, setSelectedCenterId] = useState<string>('');
  const { toast } = useToast();
  const { regions, centers } = useOrganizationData();

  // Filter regions and centers based on user's organization
  const userOrganizationRegions = regions.filter(region => 
    region.organization_id === user?.organization_id
  );
  
  const userOrganizationCenters = centers.filter(center => 
    center.region && center.region.organization_id === user?.organization_id
  );

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setSelectedRoles(user.roles || []);
      setSelectedRegionId(user.region_id || 'none');
      setSelectedCenterId(user.center_id || 'none');
    }
  }, [user]);

  const handleSave = async () => {
    if (!user) return;

    setLoading(true);
    try {
      // Update profile name only (profiles table doesn't have region_id/center_id)
      const { error: profileError } = await supabase
        .from('profiles')
        .update({ salesperson_name: name })
        .eq('id', user.id);

      if (profileError) throw profileError;

      // Handle user assignments separately
      // First, delete existing assignments for this user
      const { error: deleteAssignmentsError } = await supabase
        .from('user_assignments')
        .delete()
        .eq('user_id', user.id);

      if (deleteAssignmentsError) throw deleteAssignmentsError;

      // Create new assignment if center or region is selected
      if (selectedCenterId !== 'none' || selectedRegionId !== 'none') {
        const assignmentData: any = {
          user_id: user.id,
          center_id: selectedCenterId === 'none' ? null : selectedCenterId,
          region_id: selectedRegionId === 'none' ? null : selectedRegionId
        };

        const { error: assignmentError } = await supabase
          .from('user_assignments')
          .insert([assignmentData]);

        if (assignmentError) throw assignmentError;
      }

      // Update roles - first delete existing roles
      const { error: deleteRolesError } = await supabase
        .from('user_roles')
        .delete()
        .eq('user_id', user.id);

      if (deleteRolesError) throw deleteRolesError;

      // Insert new roles - filter out org_admin for now since database schema doesn't support it yet
      const validRoles = selectedRoles.filter(role => role !== 'org_admin');
      if (validRoles.length > 0) {
        const roleInserts = validRoles.map(role => ({
          user_id: user.id,
          role: role as 'doctor' | 'salesperson' | 'coach' | 'leader' | 'system_admin'
        }));

        const { error: insertRolesError } = await supabase
          .from('user_roles')
          .insert(roleInserts);

        if (insertRolesError) throw insertRolesError;
      }

      toast({
        title: "Success",
        description: "User updated successfully"
      });

      onSuccess();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error updating user:', error);
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = (role: UserRole, checked: boolean) => {
    if (checked) {
      setSelectedRoles(prev => [...prev, role]);
    } else {
      setSelectedRoles(prev => prev.filter(r => r !== role));
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
          <DialogDescription>
            Update user information and roles for {user.email}
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="email" className="text-right">
              Email
            </Label>
            <div className="col-span-3">
              <Input
                id="email"
                value={user.email}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground mt-1">Email cannot be changed</p>
            </div>
          </div>
          
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="col-span-3"
              placeholder="Enter user name"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="organization" className="text-right">
              Organization
            </Label>
            <div className="col-span-3">
              <Input
                id="organization"
                value={user.organization?.name || 'Not assigned'}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground mt-1">Organization cannot be changed here</p>
            </div>
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="region" className="text-right">
              Region
            </Label>
            <Select value={selectedRegionId} onValueChange={setSelectedRegionId}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a region" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No region assigned</SelectItem>
                {userOrganizationRegions.map((region) => (
                  <SelectItem key={region.id} value={region.id}>
                    {region.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="center" className="text-right">
              Center
            </Label>
            <Select value={selectedCenterId} onValueChange={setSelectedCenterId}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a center" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No center assigned</SelectItem>
                {userOrganizationCenters
                  .filter(center => selectedRegionId === 'none' || !selectedRegionId || center.region_id === selectedRegionId)
                  .map((center) => (
                    <SelectItem key={center.id} value={center.id}>
                      {center.name} {center.region && `(${center.region.name})`}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-4 items-start gap-4">
            <Label className="text-right mt-2">
              Roles
            </Label>
            <div className="col-span-3 space-y-2">
              {AVAILABLE_ROLES.map((role) => (
                <div key={role} className="flex items-center space-x-2">
                  <Checkbox
                    id={role}
                    checked={selectedRoles.includes(role)}
                    onCheckedChange={(checked) => handleRoleChange(role, checked as boolean)}
                  />
                  <Label htmlFor={role} className="text-sm font-normal">
                    {role.replace('_', ' ').charAt(0).toUpperCase() + role.replace('_', ' ').slice(1)}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};