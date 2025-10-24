import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useIdleTimeoutSettings } from '@/hooks/useIdleTimeoutSettings';
import { useOrganizations } from '@/hooks/useOrganizations';
import { Plus, Edit, Trash2, Clock, Shield } from 'lucide-react';
import { Constants } from '@/integrations/supabase/types';

interface TimeoutSettingFormData {
  role: string;
  organization_id?: string;
  timeout_minutes: number;
  warning_minutes: number;
  enabled: boolean;
}

export const IdleTimeoutManagement: React.FC = () => {
  const { settings, loading, createSetting, updateSetting, deleteSetting } = useIdleTimeoutSettings();
  const { organizations } = useOrganizations();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingSetting, setEditingSetting] = useState<string | null>(null);
  const [formData, setFormData] = useState<TimeoutSettingFormData>({
    role: '',
    timeout_minutes: 15,
    warning_minutes: 2,
    enabled: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSetting) {
        await updateSetting(editingSetting, formData);
      } else {
        await createSetting(formData);
      }
      setIsDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Error saving timeout setting:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      role: '',
      timeout_minutes: 15,
      warning_minutes: 2,
      enabled: true,
    });
    setEditingSetting(null);
  };

  const handleEdit = (setting: any) => {
    setFormData({
      role: setting.role,
      organization_id: setting.organization_id || '',
      timeout_minutes: setting.timeout_minutes,
      warning_minutes: setting.warning_minutes,
      enabled: setting.enabled,
    });
    setEditingSetting(setting.id);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this timeout setting?')) {
      await deleteSetting(id);
    }
  };

  const getOrganizationName = (orgId?: string) => {
    if (!orgId) return 'Global Default';
    const org = organizations.find(o => o.id === orgId);
    return org?.name || 'Unknown Organization';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              <CardTitle>Idle Timeout Settings</CardTitle>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={resetForm}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Setting
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>
                    {editingSetting ? 'Edit' : 'Create'} Timeout Setting
                  </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="role">User Role</Label>
                    <Select
                      value={formData.role}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, role: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        {Constants.public.Enums.user_role.map(role => (
                          <SelectItem key={role} value={role}>
                            {role.charAt(0).toUpperCase() + role.slice(1).replace('_', ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="organization">Organization (Optional)</Label>
                    <Select
                      value={formData.organization_id || 'global'}
                      onValueChange={(value) => setFormData(prev => ({ 
                        ...prev, 
                        organization_id: value === 'global' ? undefined : value 
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select organization (leave empty for global)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="global">Global Default</SelectItem>
                        {organizations.map(org => (
                          <SelectItem key={org.id} value={org.id}>
                            {org.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="timeout_minutes">Timeout (Minutes)</Label>
                    <Input
                      id="timeout_minutes"
                      type="number"
                      min="5"
                      max="480"
                      value={formData.timeout_minutes}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        timeout_minutes: parseInt(e.target.value) || 15 
                      }))}
                    />
                  </div>

                  <div>
                    <Label htmlFor="warning_minutes">Warning Period (Minutes)</Label>
                    <Input
                      id="warning_minutes"
                      type="number"
                      min="1"
                      max="10"
                      value={formData.warning_minutes}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        warning_minutes: parseInt(e.target.value) || 2 
                      }))}
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="enabled"
                      checked={formData.enabled}
                      onCheckedChange={(checked) => setFormData(prev => ({ 
                        ...prev, 
                        enabled: checked 
                      }))}
                    />
                    <Label htmlFor="enabled">Enabled</Label>
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="submit" className="flex-1">
                      {editingSetting ? 'Update' : 'Create'}
                    </Button>
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setIsDialogOpen(false)}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Role</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Timeout</TableHead>
                  <TableHead>Warning</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center">Loading...</TableCell>
                  </TableRow>
                ) : settings.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center">No timeout settings configured</TableCell>
                  </TableRow>
                ) : (
                  settings.map((setting) => (
                    <TableRow key={setting.id}>
                      <TableCell className="font-medium">
                        {setting.role.charAt(0).toUpperCase() + setting.role.slice(1).replace('_', ' ')}
                      </TableCell>
                      <TableCell>
                        {getOrganizationName(setting.organization_id)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {setting.timeout_minutes}m
                        </div>
                      </TableCell>
                      <TableCell>{setting.warning_minutes}m</TableCell>
                      <TableCell>
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                          setting.enabled 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {setting.enabled ? 'Enabled' : 'Disabled'}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex gap-2 justify-end">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEdit(setting)}
                          >
                            <Edit className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(setting.id)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};