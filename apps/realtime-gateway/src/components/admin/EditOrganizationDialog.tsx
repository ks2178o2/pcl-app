import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface Organization {
  id: string;
  name: string;
  business_address?: string;
  business_type?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface EditOrganizationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  organization: Organization | null;
  onSuccess: () => void;
}

const businessTypes = [
  'Healthcare',
  'Technology',
  'Manufacturing',
  'Retail',
  'Finance',
  'Education',
  'Non-profit',
  'Government',
  'Other'
];

export const EditOrganizationDialog = ({ open, onOpenChange, organization, onSuccess }: EditOrganizationDialogProps) => {
  const [formData, setFormData] = useState({
    name: '',
    business_address: '',
    business_type: '',
    transcription_provider: 'deepgram' as 'deepgram' | 'assemblyai',
    transcription_fallback_provider: 'assemblyai' as 'deepgram' | 'assemblyai',
    transcription_allow_fallback: true,
    transcription_bakeoff: false
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (organization) {
      setFormData({
        name: organization.name || '',
        business_address: organization.business_address || '',
        business_type: organization.business_type || '',
        transcription_provider: (organization as any).transcription_provider || 'deepgram',
        transcription_fallback_provider: (organization as any).transcription_fallback_provider || 'assemblyai',
        transcription_allow_fallback: (organization as any).transcription_allow_fallback ?? true,
        transcription_bakeoff: (organization as any).transcription_bakeoff ?? false
      });
    }
  }, [organization]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!organization) return;
    
    setLoading(true);
    try {
      const { error } = await supabase
        .from('organizations')
        .update({
          name: formData.name,
          business_address: formData.business_address || null,
          business_type: formData.business_type || null,
          transcription_provider: formData.transcription_provider,
          transcription_fallback_provider: formData.transcription_fallback_provider,
          transcription_allow_fallback: formData.transcription_allow_fallback,
          transcription_bakeoff: formData.transcription_bakeoff
        } as any)
        .eq('id', organization.id);

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Organization updated successfully"
      });
      
      onSuccess();
      onOpenChange(false);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Organization</DialogTitle>
          <DialogDescription>
            Update the organization information below.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Organization Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
            />
          </div>
          
          <div>
            <Label htmlFor="business_address">Business Address</Label>
            <Textarea
              id="business_address"
              value={formData.business_address}
              onChange={(e) => setFormData(prev => ({ ...prev, business_address: e.target.value }))}
              placeholder="Enter business address (optional)"
              rows={3}
            />
          </div>
          
          <div>
            <Label htmlFor="business_type">Business Type</Label>
            <Select 
              value={formData.business_type} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, business_type: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select business type (optional)" />
              </SelectTrigger>
              <SelectContent>
                {businessTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Transcription Settings */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="text-sm font-semibold">Transcription Settings</h3>
            
            <div>
              <Label htmlFor="transcription_provider">Primary Transcription Provider</Label>
              <Select
                value={formData.transcription_provider}
                onValueChange={(value: 'deepgram' | 'assemblyai') => setFormData(prev => ({ ...prev, transcription_provider: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="deepgram">Deepgram (Nova-2)</SelectItem>
                  <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Primary provider for all transcriptions in this organization
              </p>
            </div>

            <div>
              <Label htmlFor="transcription_fallback_provider">Fallback Provider</Label>
              <Select
                value={formData.transcription_fallback_provider}
                onValueChange={(value: 'deepgram' | 'assemblyai') => setFormData(prev => ({ ...prev, transcription_fallback_provider: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select fallback" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="deepgram">Deepgram (Nova-2)</SelectItem>
                  <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Used if primary provider fails
              </p>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="allow_fallback">Enable automatic fallback</Label>
                <p className="text-xs text-muted-foreground">
                  Automatically use fallback provider if primary fails
                </p>
              </div>
              <Switch
                id="allow_fallback"
                checked={formData.transcription_allow_fallback}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, transcription_allow_fallback: checked }))}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="bakeoff">Enable bakeoff mode</Label>
                <p className="text-xs text-muted-foreground text-yellow-600">
                  ⚠️ Run both providers to compare (doubles cost)
                </p>
              </div>
              <Switch
                id="bakeoff"
                checked={formData.transcription_bakeoff}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, transcription_bakeoff: checked }))}
              />
            </div>
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Updating...' : 'Update Organization'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};