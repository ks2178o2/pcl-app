import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useInvitations } from '@/hooks/useInvitations';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { toast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';

interface InviteUserDialogProps {
  organizationId: string;
  onSuccess?: () => void;
}

export const InviteUserDialog = ({ organizationId, onSuccess }: InviteUserDialogProps) => {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('salesperson');
  const [centerIds, setCenterIds] = useState<string[]>([]);
  const [regionId, setRegionId] = useState('');
  const [expiresInDays, setExpiresInDays] = useState(7);

  const { loading, createInvitation } = useInvitations();
  const { regions, centers } = useOrganizationData();
  const { user } = useAuth();

  // Filter regions and centers by organization
  const filteredRegions = regions.filter(r => r.organization_id === organizationId);
  const filteredCenters = centers.filter(c => 
    filteredRegions.some(r => r.id === c.region_id)
  );

  const handleCenterChange = (centerId: string, checked: boolean) => {
    setCenterIds(prev => 
      checked 
        ? [...prev, centerId]
        : prev.filter(id => id !== centerId)
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !email.includes('@')) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid email address",
        variant: "destructive",
      });
      return;
    }

    try {
      const invitationData = {
        email,
        organization_id: organizationId,
        role,
        center_ids: centerIds.length > 0 ? centerIds : undefined,
        region_id: regionId || undefined,
        expires_in_days: expiresInDays,
      };

      const result = await createInvitation(invitationData);

      toast({
        title: "Invitation Sent",
        description: `Invitation email sent to ${email}`,
      });

      // TODO: Send email notification
      // supabase.functions.invoke('send-invitation-email', {...})

      setOpen(false);
      setEmail('');
      setRole('salesperson');
      setCenterIds([]);
      setRegionId('');
      
      onSuccess?.();
    } catch (error: any) {
      toast({
        title: "Failed to Send Invitation",
        description: error.message || "An error occurred",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default">
          Invite User
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Invite User to Organization</DialogTitle>
          <DialogDescription>
            Send an email invitation to join your organization
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <Label htmlFor="invite-email">Email Address</Label>
            <Input
              id="invite-email"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {/* Role */}
          <div>
            <Label htmlFor="invite-role">Role</Label>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger id="invite-role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="salesperson">Salesperson</SelectItem>
                <SelectItem value="coach">Coach</SelectItem>
                <SelectItem value="leader">Leader</SelectItem>
                <SelectItem value="doctor">Doctor</SelectItem>
                <SelectItem value="org_admin">Organization Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Regional Access */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium">Regional Access (Optional)</h3>
            
            {/* Regions */}
            <div>
              <Label className="text-sm">Region</Label>
              <Select value={regionId} onValueChange={setRegionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select region" />
                </SelectTrigger>
                <SelectContent>
                  {filteredRegions.map(region => (
                    <SelectItem key={region.id} value={region.id}>
                      {region.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Centers */}
            <div>
              <Label className="text-sm">Centers</Label>
              <div className="mt-2 space-y-2 max-h-40 overflow-y-auto border rounded p-2">
                {filteredCenters.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    {regionId ? 'No centers available' : 'Select a region first'}
                  </p>
                ) : (
                  filteredCenters
                    .filter(c => !regionId || c.region_id === regionId)
                    .map(center => (
                      <div key={center.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={`center-${center.id}`}
                          checked={centerIds.includes(center.id)}
                          onCheckedChange={(checked) => handleCenterChange(center.id, checked as boolean)}
                        />
                        <Label htmlFor={`center-${center.id}`} className="text-sm">
                          {center.name}
                        </Label>
                      </div>
                    ))
                )}
              </div>
            </div>
          </div>

          {/* Expiry */}
          <div>
            <Label htmlFor="expires-in">Invitation Expires In (days)</Label>
            <Input
              id="expires-in"
              type="number"
              min="1"
              max="30"
              value={expiresInDays}
              onChange={(e) => setExpiresInDays(parseInt(e.target.value) || 7)}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Sending...' : 'Send Invitation'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

