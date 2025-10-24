import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  User, 
  Phone, 
  Mail, 
  Calendar, 
  MessageSquare, 
  Activity,
  Search,
  Filter,
  MoreVertical
} from 'lucide-react';
import { PatientSelector } from './PatientSelector';

interface Patient {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  lastContact?: Date;
  friendlyId: string;
  totalCalls?: number;
  totalAppointments?: number;
  lastAppointment?: Date;
  preferredContact?: 'email' | 'phone' | 'sms';
  notes?: string;
}

interface PatientActivity {
  id: string;
  type: 'call' | 'appointment' | 'email' | 'sms';
  date: Date;
  description: string;
  outcome?: string;
}

export const PatientManagement: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'recent' | 'high-priority'>('all');

  // Mock data - will be replaced with real database calls
  const mockPatients: Patient[] = [
    {
      id: '1',
      name: 'John Smith',
      email: 'john@example.com',
      phone: '+1-555-0123',
      lastContact: new Date('2024-01-15'),
      friendlyId: 'PT-ABC123DEF456',
      totalCalls: 3,
      totalAppointments: 2,
      lastAppointment: new Date('2024-01-20'),
      preferredContact: 'email',
      notes: 'Interested in premium package'
    },
    {
      id: '2',
      name: 'Sarah Johnson',
      email: 'sarah@example.com',
      phone: '+1-555-0124',
      lastContact: new Date('2024-01-10'),
      friendlyId: 'PT-XYZ789GHI012',
      totalCalls: 1,
      totalAppointments: 1,
      lastAppointment: new Date('2024-01-25'),
      preferredContact: 'phone'
    }
  ];

  const mockActivities: PatientActivity[] = [
    {
      id: '1',
      type: 'call',
      date: new Date('2024-01-15'),
      description: 'Initial consultation call',
      outcome: 'Scheduled follow-up'
    },
    {
      id: '2',
      type: 'appointment',
      date: new Date('2024-01-20'),
      description: 'Product demonstration',
      outcome: 'Interested in trial'
    },
    {
      id: '3',
      type: 'email',
      date: new Date('2024-01-22'),
      description: 'Follow-up email sent',
      outcome: 'Opened'
    }
  ];

  const filteredPatients = mockPatients.filter(patient => {
    const matchesSearch = patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         patient.friendlyId.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterType === 'recent') {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return matchesSearch && patient.lastContact && patient.lastContact > weekAgo;
    }
    
    return matchesSearch;
  });

  const getActivityIcon = (type: PatientActivity['type']) => {
    switch (type) {
      case 'call': return <Phone className="h-4 w-4" />;
      case 'appointment': return <Calendar className="h-4 w-4" />;
      case 'email': return <Mail className="h-4 w-4" />;
      case 'sms': return <MessageSquare className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Patient Management</h2>
          <p className="text-muted-foreground">
            Manage your patient relationships and track interactions
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          {mockPatients.length} Total Patients
        </Badge>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="details">Patient Details</TabsTrigger>
          <TabsTrigger value="activities">Activity Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Find Patient
                </CardTitle>
                <CardDescription>
                  Search for existing patients or create new ones
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PatientSelector
                  onPatientSelect={setSelectedPatient}
                  selectedPatient={selectedPatient}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Patient Statistics</CardTitle>
                <CardDescription>
                  Your patient management overview
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-primary/5 rounded-lg">
                    <div className="text-2xl font-bold">{mockPatients.length}</div>
                    <div className="text-sm text-muted-foreground">Total Patients</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold">
                      {mockPatients.filter(p => p.lastContact && 
                        p.lastContact > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length}
                    </div>
                    <div className="text-sm text-muted-foreground">Active This Week</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Avg. Calls per Patient</span>
                    <span className="font-medium">
                      {(mockPatients.reduce((sum, p) => sum + (p.totalCalls || 0), 0) / mockPatients.length || 0).toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Scheduled Appointments</span>
                    <span className="font-medium">
                      {mockPatients.reduce((sum, p) => sum + (p.totalAppointments || 0), 0)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>All Patients</span>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search patients..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredPatients.map((patient) => (
                  <div
                    key={patient.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedPatient(patient)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center">
                        <User className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h4 className="font-medium">{patient.name}</h4>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="outline" className="text-xs">
                            {patient.friendlyId}
                          </Badge>
                          {patient.email && (
                            <span className="flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {patient.email}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="text-right">
                        <div>{patient.totalCalls || 0} calls</div>
                        {patient.lastContact && (
                          <div>Last: {patient.lastContact.toLocaleDateString()}</div>
                        )}
                      </div>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="details" className="space-y-6">
          {selectedPatient ? (
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <User className="h-5 w-5" />
                      {selectedPatient.name}
                    </CardTitle>
                    <CardDescription>
                      Patient ID: {selectedPatient.friendlyId}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      {selectedPatient.email && (
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{selectedPatient.email}</span>
                        </div>
                      )}
                      {selectedPatient.phone && (
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{selectedPatient.phone}</span>
                        </div>
                      )}
                    </div>
                    
                    {selectedPatient.notes && (
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <h5 className="font-medium mb-2">Notes</h5>
                        <p className="text-sm text-muted-foreground">{selectedPatient.notes}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Quick Stats
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">Total Calls</span>
                      <Badge variant="secondary">{selectedPatient.totalCalls || 0}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Appointments</span>
                      <Badge variant="secondary">{selectedPatient.totalAppointments || 0}</Badge>
                    </div>
                    {selectedPatient.lastContact && (
                      <div className="flex justify-between">
                        <span className="text-sm">Last Contact</span>
                        <span className="text-sm text-muted-foreground">
                          {selectedPatient.lastContact.toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    {selectedPatient.preferredContact && (
                      <div className="flex justify-between">
                        <span className="text-sm">Preferred Contact</span>
                        <Badge variant="outline" className="capitalize">
                          {selectedPatient.preferredContact}
                        </Badge>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No Patient Selected</h3>
                <p className="text-muted-foreground mb-4">
                  Select a patient from the overview tab to view their details
                </p>
                <Button onClick={() => window.location.hash = '#overview'}>
                  Go to Overview
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="activities" className="space-y-6">
          {selectedPatient ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Activity Timeline for {selectedPatient.name}
                </CardTitle>
                <CardDescription>
                  Complete interaction history with this patient
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockActivities.map((activity, index) => (
                    <div key={activity.id} className="flex items-start gap-4">
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                        activity.type === 'call' ? 'bg-blue-100 text-blue-600' :
                        activity.type === 'appointment' ? 'bg-green-100 text-green-600' :
                        activity.type === 'email' ? 'bg-purple-100 text-purple-600' :
                        'bg-orange-100 text-orange-600'
                      }`}>
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium capitalize">{activity.type}</p>
                          <time className="text-sm text-muted-foreground">
                            {activity.date.toLocaleDateString()}
                          </time>
                        </div>
                        <p className="text-sm text-muted-foreground">{activity.description}</p>
                        {activity.outcome && (
                          <Badge variant="outline" className="mt-1 text-xs">
                            {activity.outcome}
                          </Badge>
                        )}
                      </div>
                      {index < mockActivities.length - 1 && (
                        <div className="absolute left-4 mt-8 h-6 w-px bg-border" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No Patient Selected</h3>
                <p className="text-muted-foreground">
                  Select a patient to view their activity timeline
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};