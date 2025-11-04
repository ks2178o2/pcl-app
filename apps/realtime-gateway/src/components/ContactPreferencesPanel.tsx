import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useContactPreferences } from '@/hooks/useContactPreferences';
import { useToast } from '@/hooks/use-toast';
import { Settings, Shield, Clock, Phone, Mail, MessageSquare, Voicemail } from 'lucide-react';

interface ContactPreferencesPanelProps {
  callRecordId: string;
  customerName: string;
}

export const ContactPreferencesPanel: React.FC<ContactPreferencesPanelProps> = ({
  callRecordId,
  customerName
}) => {
  const { preferences, loading, savePreferences } = useContactPreferences(callRecordId);
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    customer_name: customerName,
    email_allowed: true,
    sms_allowed: true,
    phone_allowed: true,
    voicemail_allowed: true,
    preferred_contact_time: '',
    timezone: 'America/New_York',
    do_not_contact: false,
    notes: ''
  });

  // Restore draft from session cache
  useEffect(() => {
    try {
      const key = `contactPrefsDraft:${callRecordId}`;
      const cached = sessionStorage.getItem(key);
      if (cached) {
        const parsed = JSON.parse(cached);
        setFormData((prev) => ({ ...prev, ...parsed }));
      }
    } catch {}
  }, [callRecordId]);

  useEffect(() => {
    if (preferences) {
      setFormData({
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
    }
  }, [preferences]);

  const handleSave = async () => {
    const { error } = await savePreferences(formData);
    
    if (error) {
      toast({
        title: "Error",
        description: "Failed to save contact preferences",
        variant: "destructive",
      });
    } else {
      toast({
        title: "Success",
        description: "Contact preferences saved successfully",
      });
      try { sessionStorage.removeItem(`contactPrefsDraft:${callRecordId}`); } catch {}
    }
  };

  const updateField = (field: string, value: any) => {
    setFormData(prev => {
      const next: any = { ...prev, [field]: value };
      try { sessionStorage.setItem(`contactPrefsDraft:${callRecordId}`, JSON.stringify(next)); } catch {}
      return next;
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Contact Preferences
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Contact Preferences
        </CardTitle>
        <CardDescription>
          Manage communication preferences and compliance settings for {customerName}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
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
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="h-4 w-4" />
              <Label className="text-sm font-medium">Allowed Channels</Label>
            </div>
            
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
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              <Label className="text-sm font-medium">Contact Timing</Label>
            </div>
            
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
          <Label className="text-sm font-medium">Notes</Label>
          <Textarea
            placeholder="Add any special instructions or notes about contacting this customer..."
            value={formData.notes}
            onChange={(e) => updateField('notes', e.target.value)}
            rows={3}
          />
        </div>

        {/* Save Button */}
        <Button onClick={handleSave} className="w-full">
          Save Preferences
        </Button>
      </CardContent>
    </Card>
  );
};