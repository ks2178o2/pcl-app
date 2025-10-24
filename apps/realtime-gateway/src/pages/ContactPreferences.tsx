import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAllContactPreferences } from '@/hooks/useAllContactPreferences';
import { useToast } from '@/hooks/use-toast';
import { 
  Settings, 
  Edit3, 
  Trash2, 
  Shield, 
  Mail, 
  MessageSquare, 
  Phone, 
  Voicemail,
  Clock,
  Search,
  Filter
} from 'lucide-react';
import { NavigationMenu } from '@/components/NavigationMenu';

interface EditPreferencesDialogProps {
  preferences: any;
  onUpdate: (id: string, updates: any) => Promise<{ error: any }>;
  onDelete: (id: string) => Promise<{ error: any }>;
}

const EditPreferencesDialog: React.FC<EditPreferencesDialogProps> = ({
  preferences,
  onUpdate,
  onDelete
}) => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    customer_name: preferences.customer_name,
    email_allowed: preferences.email_allowed,
    sms_allowed: preferences.sms_allowed,
    phone_allowed: preferences.phone_allowed,
    voicemail_allowed: preferences.voicemail_allowed,
    preferred_contact_time: preferences.preferred_contact_time || '',
    timezone: preferences.timezone,
    do_not_contact: preferences.do_not_contact,
    notes: preferences.notes || ''
  });

  const handleSave = async () => {
    const { error } = await onUpdate(preferences.id, formData);
    
    if (error) {
      toast({
        title: "Error",
        description: "Failed to update contact preferences",
        variant: "destructive",
      });
    } else {
      toast({
        title: "Success",
        description: "Contact preferences updated successfully",
      });
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete these preferences?')) {
      const { error } = await onDelete(preferences.id);
      
      if (error) {
        toast({
          title: "Error", 
          description: "Failed to delete contact preferences",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Success",
          description: "Contact preferences deleted successfully",
        });
      }
    }
  };

  const updateField = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Edit Contact Preferences</DialogTitle>
        <DialogDescription>
          Update communication preferences for {preferences.customer_name}
        </DialogDescription>
      </DialogHeader>
      
      <div className="space-y-6">
        {/* Customer Name */}
        <div className="space-y-2">
          <Label htmlFor="customer_name">Customer Name</Label>
          <Input
            id="customer_name"
            value={formData.customer_name}
            onChange={(e) => updateField('customer_name', e.target.value)}
          />
        </div>

        {/* Do Not Contact Override */}
        <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-destructive" />
            <div>
              <Label className="text-sm font-medium">Do Not Contact</Label>
              <p className="text-xs text-muted-foreground">Override all communication for this customer</p>
            </div>
          </div>
          <Switch
            checked={formData.do_not_contact}
            onCheckedChange={(checked) => updateField('do_not_contact', checked)}
          />
        </div>

        {/* Communication Channels */}
        {!formData.do_not_contact && (
          <div className="space-y-4">
            <Label className="text-sm font-medium">Allowed Channels</Label>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  <Label className="text-sm">Email</Label>
                </div>
                <Switch
                  checked={formData.email_allowed}
                  onCheckedChange={(checked) => updateField('email_allowed', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  <Label className="text-sm">SMS</Label>
                </div>
                <Switch
                  checked={formData.sms_allowed}
                  onCheckedChange={(checked) => updateField('sms_allowed', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  <Label className="text-sm">Phone Call</Label>
                </div>
                <Switch
                  checked={formData.phone_allowed}
                  onCheckedChange={(checked) => updateField('phone_allowed', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Voicemail className="h-4 w-4" />
                  <Label className="text-sm">Voicemail</Label>
                </div>
                <Switch
                  checked={formData.voicemail_allowed}
                  onCheckedChange={(checked) => updateField('voicemail_allowed', checked)}
                />
              </div>
            </div>
          </div>
        )}

        {/* Timing Preferences */}
        {!formData.do_not_contact && (
          <div className="space-y-4">
            <Label className="text-sm font-medium">Contact Timing</Label>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Preferred Time</Label>
                <Select
                  value={formData.preferred_contact_time}
                  onValueChange={(value) => updateField('preferred_contact_time', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select time preference" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="no_preference">No preference</SelectItem>
                    <SelectItem value="morning">Morning (9am-12pm)</SelectItem>
                    <SelectItem value="afternoon">Afternoon (12pm-5pm)</SelectItem>
                    <SelectItem value="evening">Evening (5pm-8pm)</SelectItem>
                    <SelectItem value="weekends">Weekends only</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Timezone</Label>
                <Select
                  value={formData.timezone}
                  onValueChange={(value) => updateField('timezone', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="America/New_York">Eastern Time</SelectItem>
                    <SelectItem value="America/Chicago">Central Time</SelectItem>
                    <SelectItem value="America/Denver">Mountain Time</SelectItem>
                    <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        )}

        {/* Notes */}
        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Textarea
            id="notes"
            placeholder="Add any special instructions or notes about contacting this customer..."
            value={formData.notes}
            onChange={(e) => updateField('notes', e.target.value)}
            rows={3}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between pt-4">
          <Button variant="destructive" onClick={handleDelete} className="gap-2">
            <Trash2 className="h-4 w-4" />
            Delete
          </Button>
          
          <Button onClick={handleSave} className="gap-2">
            <Settings className="h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </div>
    </DialogContent>
  );
};

export default function ContactPreferences() {
  const { preferences, loading, updatePreferences, deletePreferences } = useAllContactPreferences();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  const filteredPreferences = preferences.filter(pref => {
    const matchesSearch = pref.customer_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterType === 'all') return matchesSearch;
    if (filterType === 'do_not_contact') return matchesSearch && pref.do_not_contact;
    if (filterType === 'email_only') return matchesSearch && pref.email_allowed && !pref.sms_allowed && !pref.phone_allowed;
    if (filterType === 'no_email') return matchesSearch && !pref.email_allowed;
    
    return matchesSearch;
  });

  const getContactChannels = (pref: any) => {
    if (pref.do_not_contact) return [<Badge key="dnc" variant="destructive" className="text-xs">Do Not Contact</Badge>];
    
    const channels = [];
    if (pref.email_allowed) channels.push(<Mail key="email" className="h-3 w-3 text-green-600" />);
    if (pref.sms_allowed) channels.push(<MessageSquare key="sms" className="h-3 w-3 text-blue-600" />);
    if (pref.phone_allowed) channels.push(<Phone key="phone" className="h-3 w-3 text-purple-600" />);
    if (pref.voicemail_allowed) channels.push(<Voicemail key="voicemail" className="h-3 w-3 text-orange-600" />);
    
    return channels.length > 0 ? channels : [<span key="none" className="text-xs text-muted-foreground">None</span>];
  };

  const getTimingInfo = (pref: any) => {
    if (pref.do_not_contact) return null;
    
    const parts = [];
    if (pref.preferred_contact_time) {
      parts.push(pref.preferred_contact_time.charAt(0).toUpperCase() + pref.preferred_contact_time.slice(1));
    }
    if (pref.timezone !== 'America/New_York') {
      const timezoneNames: { [key: string]: string } = {
        'America/Chicago': 'CT',
        'America/Denver': 'MT',
        'America/Los_Angeles': 'PT'
      };
      parts.push(timezoneNames[pref.timezone] || 'ET');
    }
    
    return parts.length > 0 ? parts.join(' • ') : 'No preference';
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pt Pref.</h1>
          <p className="text-muted-foreground">Manage patient communication preferences</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            {preferences.length} Customers
          </Badge>
          <NavigationMenu />
        </div>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search customers..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Customers</SelectItem>
                <SelectItem value="do_not_contact">Do Not Contact</SelectItem>
                <SelectItem value="email_only">Email Only</SelectItem>
                <SelectItem value="no_email">No Email</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Preferences Table */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Preferences</CardTitle>
          <CardDescription>
            View and edit communication preferences for all customers
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredPreferences.length === 0 ? (
            <div className="text-center py-8">
              <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No preferences found</h3>
              <p className="text-muted-foreground">
                {searchTerm ? 'No customers match your search.' : 'Contact preferences will appear here once customers consent to communication.'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Channels</TableHead>
                  <TableHead>Timing</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPreferences.map((pref) => (
                  <TableRow key={pref.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {pref.do_not_contact && <Shield className="h-4 w-4 text-destructive" />}
                        <span className="font-medium">{pref.customer_name}</span>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getContactChannels(pref)}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {getTimingInfo(pref)}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {pref.notes ? (pref.notes.length > 30 ? `${pref.notes.substring(0, 30)}...` : pref.notes) : '—'}
                      </span>
                    </TableCell>
                    
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {new Date(pref.updated_at).toLocaleDateString()}
                      </span>
                    </TableCell>
                    
                    <TableCell>
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="sm" className="gap-2">
                            <Edit3 className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <EditPreferencesDialog
                          preferences={pref}
                          onUpdate={updatePreferences}
                          onDelete={deletePreferences}
                        />
                      </Dialog>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}