import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Phone, Mail, MessageSquare, Clock, User, Calendar, Save } from 'lucide-react';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useAllContactPreferences } from '@/hooks/useAllContactPreferences';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';

interface PatientContact {
  email?: string;
  phone?: string;
}

export const PatientDetails: React.FC = () => {
  const { patientName } = useParams<{ patientName: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const decodedPatientName = patientName ? decodeURIComponent(patientName) : '';
  
  const { calls } = useCallRecords();
  const { preferences: allPreferences, updatePreferences, loading: prefsLoading } = useAllContactPreferences();
  
  const [contactInfo, setContactInfo] = useState<PatientContact>({});
  const [editingContact, setEditingContact] = useState(false);
  const [editingPreferences, setEditingPreferences] = useState(false);
  const [localContactInfo, setLocalContactInfo] = useState<PatientContact>({});
  const [localPreferences, setLocalPreferences] = useState({
    email_allowed: true,
    sms_allowed: true,
    phone_allowed: true,
    voicemail_allowed: true,
    do_not_contact: false,
    preferred_contact_time: '',
    timezone: 'America/New_York',
    notes: ''
  });

  // Filter calls for this patient
  const patientCalls = calls.filter(call => 
    call.patientName?.toLowerCase() === decodedPatientName.toLowerCase()
  );

  // Get existing preferences for this patient
  const existingPreferences = allPreferences.find(pref => 
    pref.customer_name?.toLowerCase() === decodedPatientName.toLowerCase()
  );

  useEffect(() => {
    if (existingPreferences) {
      setLocalPreferences({
        email_allowed: existingPreferences.email_allowed,
        sms_allowed: existingPreferences.sms_allowed,
        phone_allowed: existingPreferences.phone_allowed,
        voicemail_allowed: existingPreferences.voicemail_allowed,
        do_not_contact: existingPreferences.do_not_contact,
        preferred_contact_time: existingPreferences.preferred_contact_time || '',
        timezone: existingPreferences.timezone || 'America/New_York',
        notes: existingPreferences.notes || ''
      });
    }
  }, [existingPreferences]);

  useEffect(() => {
    setLocalContactInfo(contactInfo);
  }, [contactInfo]);

  useEffect(() => {
    // Load contact info from appointments or any available source
    const loadContactInfo = async () => {
      if (!user) return;

      try {
        const { data: appointments } = await supabase
          .from('appointments')
          .select('email, phone_number')
          .eq('user_id', user.id)
          .eq('customer_name', decodedPatientName)
          .order('created_at', { ascending: false })
          .limit(1);

        if (appointments && appointments.length > 0) {
          setContactInfo({
            email: appointments[0].email || undefined,
            phone: appointments[0].phone_number || undefined
          });
        }
      } catch (error) {
        console.error('Error loading contact info:', error);
      }
    };

    loadContactInfo();
  }, [user, decodedPatientName]);

  const handleSaveContact = async () => {
    if (!user) return;

    try {
      // Update the most recent appointment record with new contact info
      const { data: appointments } = await supabase
        .from('appointments')
        .select('id')
        .eq('user_id', user.id)
        .eq('customer_name', decodedPatientName)
        .order('created_at', { ascending: false })
        .limit(1);

      if (appointments && appointments.length > 0) {
        const { error } = await supabase
          .from('appointments')
          .update({
            email: localContactInfo.email || null,
            phone_number: localContactInfo.phone || null
          })
          .eq('id', appointments[0].id);

        if (error) throw error;
      } else {
        // Create new appointment record if none exists
        const { error } = await supabase
          .from('appointments')
          .insert({
            user_id: user.id,
            customer_name: decodedPatientName,
            appointment_date: new Date().toISOString(),
            email: localContactInfo.email || null,
            phone_number: localContactInfo.phone || null
          });

        if (error) throw error;
      }

      setContactInfo(localContactInfo);
      setEditingContact(false);
      toast({
        title: "Contact Updated",
        description: "Contact information has been saved successfully"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save contact information",
        variant: "destructive"
      });
    }
  };

  const handleSavePreferences = async () => {
    if (!user) return;

    try {
      if (existingPreferences?.id) {
        // Update existing preferences
        await updatePreferences(existingPreferences.id, localPreferences);
      } else {
        // Create new preferences - we need a call record ID, so use the most recent call
        const mostRecentCall = patientCalls[0];
        if (!mostRecentCall) {
          toast({
            title: "Error",
            description: "Cannot create preferences without a call record",
            variant: "destructive"
          });
          return;
        }

        const { error } = await supabase
          .from('contact_preferences')
          .insert({
            call_record_id: mostRecentCall.id,
            user_id: user.id,
            customer_name: decodedPatientName,
            email_allowed: localPreferences.email_allowed,
            sms_allowed: localPreferences.sms_allowed,
            phone_allowed: localPreferences.phone_allowed,
            voicemail_allowed: localPreferences.voicemail_allowed,
            do_not_contact: localPreferences.do_not_contact,
            preferred_contact_time: localPreferences.preferred_contact_time || null,
            timezone: localPreferences.timezone,
            notes: localPreferences.notes || null
          });

        if (error) throw error;
      }

      setEditingPreferences(false);
      toast({
        title: "Preferences Updated",
        description: "Contact preferences have been saved successfully"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save preferences",
        variant: "destructive"
      });
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (date: Date) => {
    return date.toLocaleString();
  };

  if (!patientName) {
    return <div>Patient not found</div>;
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        <div className="flex items-center gap-3">
          <User className="h-6 w-6" />
          <h1 className="text-2xl font-bold">{decodedPatientName}</h1>
        </div>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Contact Information
              </div>
              <Button
                variant={editingContact ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  if (editingContact) {
                    handleSaveContact();
                  } else {
                    setEditingContact(true);
                  }
                }}
                className="flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                {editingContact ? 'Save Contact' : 'Edit Contact'}
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label>Email</Label>
                {editingContact ? (
                  <Input
                    type="email"
                    value={localContactInfo.email || ''}
                    onChange={(e) => setLocalContactInfo(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="patient@example.com"
                    className="mt-1"
                  />
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{contactInfo.email || 'No email on file'}</span>
                  </div>
                )}
              </div>
              
              <div>
                <Label>Phone Number</Label>
                {editingContact ? (
                  <Input
                    type="tel"
                    value={localContactInfo.phone || ''}
                    onChange={(e) => setLocalContactInfo(prev => ({ ...prev, phone: e.target.value }))}
                    placeholder="(555) 123-4567"
                    className="mt-1"
                  />
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{contactInfo.phone || 'No phone number on file'}</span>
                  </div>
                )}
              </div>
            </div>

            {editingContact && (
              <div className="flex gap-2 mt-4">
                <Button onClick={handleSaveContact}>Save Contact</Button>
                <Button variant="outline" onClick={() => {
                  setEditingContact(false);
                  setLocalContactInfo(contactInfo);
                }}>
                  Cancel
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Communication Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Communication Preferences
              </div>
              <Button
                variant={editingPreferences ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  if (editingPreferences) {
                    handleSavePreferences();
                  } else {
                    setEditingPreferences(true);
                  }
                }}
                className="flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                {editingPreferences ? 'Save Changes' : 'Edit Preferences'}
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {existingPreferences ? (
              <>
                {/* Do Not Contact Toggle */}
                <div className="flex items-center justify-between">
                  <Label htmlFor="do-not-contact" className="text-base">
                    Do Not Contact
                  </Label>
                  <Switch
                    id="do-not-contact"
                    checked={localPreferences.do_not_contact}
                    onCheckedChange={(checked) => 
                      editingPreferences && setLocalPreferences(prev => ({ ...prev, do_not_contact: checked }))
                    }
                    disabled={!editingPreferences}
                  />
                </div>

                <Separator />

                {/* Contact Method Preferences */}
                <div className="space-y-4">
                  <h4 className="font-medium">Allowed Contact Methods</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center justify-between">
                      <Label>Email</Label>
                      <Switch
                        checked={localPreferences.email_allowed}
                        onCheckedChange={(checked) => 
                          editingPreferences && setLocalPreferences(prev => ({ ...prev, email_allowed: checked }))
                        }
                        disabled={!editingPreferences || localPreferences.do_not_contact}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>SMS</Label>
                      <Switch
                        checked={localPreferences.sms_allowed}
                        onCheckedChange={(checked) => 
                          editingPreferences && setLocalPreferences(prev => ({ ...prev, sms_allowed: checked }))
                        }
                        disabled={!editingPreferences || localPreferences.do_not_contact}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Phone Call</Label>
                      <Switch
                        checked={localPreferences.phone_allowed}
                        onCheckedChange={(checked) => 
                          editingPreferences && setLocalPreferences(prev => ({ ...prev, phone_allowed: checked }))
                        }
                        disabled={!editingPreferences || localPreferences.do_not_contact}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Voicemail</Label>
                      <Switch
                        checked={localPreferences.voicemail_allowed}
                        onCheckedChange={(checked) => 
                          editingPreferences && setLocalPreferences(prev => ({ ...prev, voicemail_allowed: checked }))
                        }
                        disabled={!editingPreferences || localPreferences.do_not_contact}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Contact Timing */}
                <div className="space-y-4">
                  <h4 className="font-medium">Contact Timing</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Preferred Contact Time</Label>
                      <Select
                        value={localPreferences.preferred_contact_time}
                        onValueChange={(value) => 
                          editingPreferences && setLocalPreferences(prev => ({ ...prev, preferred_contact_time: value }))
                        }
                        disabled={!editingPreferences}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select time" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="morning">Morning (8AM - 12PM)</SelectItem>
                          <SelectItem value="afternoon">Afternoon (12PM - 5PM)</SelectItem>
                          <SelectItem value="evening">Evening (5PM - 8PM)</SelectItem>
                          <SelectItem value="anytime">Anytime</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Timezone</Label>
                      <Select
                        value={localPreferences.timezone}
                        onValueChange={(value) => 
                          editingPreferences && setLocalPreferences(prev => ({ ...prev, timezone: value }))
                        }
                        disabled={!editingPreferences}
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

                {/* Notes */}
                <div>
                  <Label>Notes</Label>
                  <Textarea
                    value={localPreferences.notes}
                    onChange={(e) => 
                      editingPreferences && setLocalPreferences(prev => ({ ...prev, notes: e.target.value }))
                    }
                    placeholder="Any additional notes about contact preferences..."
                    disabled={!editingPreferences}
                    className="mt-1"
                  />
                </div>

                {editingPreferences && (
                  <div className="flex gap-2">
                    <Button onClick={handleSavePreferences}>Save Changes</Button>
                    <Button variant="outline" onClick={() => setEditingPreferences(false)}>
                      Cancel
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <>
                {/* Show default form for creating new preferences */}
                <div className="space-y-6">
                  {/* Do Not Contact Toggle */}
                  <div className="flex items-center justify-between">
                    <Label htmlFor="do-not-contact" className="text-base">
                      Do Not Contact
                    </Label>
                    <Switch
                      id="do-not-contact"
                      checked={localPreferences.do_not_contact}
                      onCheckedChange={(checked) => 
                        editingPreferences && setLocalPreferences(prev => ({ ...prev, do_not_contact: checked }))
                      }
                      disabled={!editingPreferences}
                    />
                  </div>

                  <Separator />

                  {/* Contact Method Preferences */}
                  <div className="space-y-4">
                    <h4 className="font-medium">Allowed Contact Methods</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center justify-between">
                        <Label>Email</Label>
                        <Switch
                          checked={localPreferences.email_allowed}
                          onCheckedChange={(checked) => 
                            editingPreferences && setLocalPreferences(prev => ({ ...prev, email_allowed: checked }))
                          }
                          disabled={!editingPreferences || localPreferences.do_not_contact}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>SMS</Label>
                        <Switch
                          checked={localPreferences.sms_allowed}
                          onCheckedChange={(checked) => 
                            editingPreferences && setLocalPreferences(prev => ({ ...prev, sms_allowed: checked }))
                          }
                          disabled={!editingPreferences || localPreferences.do_not_contact}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Phone Call</Label>
                        <Switch
                          checked={localPreferences.phone_allowed}
                          onCheckedChange={(checked) => 
                            editingPreferences && setLocalPreferences(prev => ({ ...prev, phone_allowed: checked }))
                          }
                          disabled={!editingPreferences || localPreferences.do_not_contact}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Voicemail</Label>
                        <Switch
                          checked={localPreferences.voicemail_allowed}
                          onCheckedChange={(checked) => 
                            editingPreferences && setLocalPreferences(prev => ({ ...prev, voicemail_allowed: checked }))
                          }
                          disabled={!editingPreferences || localPreferences.do_not_contact}
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Contact Timing */}
                  <div className="space-y-4">
                    <h4 className="font-medium">Contact Timing</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Preferred Contact Time</Label>
                        <Select
                          value={localPreferences.preferred_contact_time}
                          onValueChange={(value) => 
                            editingPreferences && setLocalPreferences(prev => ({ ...prev, preferred_contact_time: value }))
                          }
                          disabled={!editingPreferences}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select time" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="morning">Morning (8AM - 12PM)</SelectItem>
                            <SelectItem value="afternoon">Afternoon (12PM - 5PM)</SelectItem>
                            <SelectItem value="evening">Evening (5PM - 8PM)</SelectItem>
                            <SelectItem value="anytime">Anytime</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Timezone</Label>
                        <Select
                          value={localPreferences.timezone}
                          onValueChange={(value) => 
                            editingPreferences && setLocalPreferences(prev => ({ ...prev, timezone: value }))
                          }
                          disabled={!editingPreferences}
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

                  {/* Notes */}
                  <div>
                    <Label>Notes</Label>
                    <Textarea
                      value={localPreferences.notes}
                      onChange={(e) => 
                        editingPreferences && setLocalPreferences(prev => ({ ...prev, notes: e.target.value }))
                      }
                      placeholder="Any additional notes about contact preferences..."
                      disabled={!editingPreferences}
                      className="mt-1"
                    />
                  </div>

                  {editingPreferences && (
                    <div className="flex gap-2">
                      <Button onClick={handleSavePreferences}>Create Preferences</Button>
                      <Button variant="outline" onClick={() => setEditingPreferences(false)}>
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Call History */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Call History ({patientCalls.length} calls)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {patientCalls.length === 0 ? (
              <p className="text-muted-foreground">No calls recorded for this patient yet.</p>
            ) : (
              <div className="space-y-4">
                {patientCalls.map((call) => (
                  <div key={call.id} className="border rounded-lg p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={
                          call.status === 'completed' ? 'default' : 
                          call.status === 'transcribing' ? 'outline' : 'secondary'
                        }>
                          {call.status === 'transcribing' ? 'Analyzing voices...' : call.status}
                        </Badge>
                        <span className="text-sm text-muted-foreground">{formatDate(call.timestamp)}</span>
                      </div>
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatDuration(call.duration)}
                      </div>
                    </div>
                    
                    {call.transcript && call.transcript !== 'Transcribing audio...' && (
                      <div className="mt-2 p-3 bg-muted rounded-md">
                        <p className="text-sm font-medium mb-1">Transcript Preview:</p>
                        <div className="text-sm text-muted-foreground max-h-20 overflow-hidden">
                          {call.transcript.substring(0, 150)}...
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};