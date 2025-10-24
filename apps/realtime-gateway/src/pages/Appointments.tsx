import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { AppointmentUploadWithPreview } from '@/components/AppointmentUploadWithPreview';
import { AppointmentsList } from '@/components/AppointmentsList';
import { PatientManagement } from '@/components/PatientManagement';
import { PatientSelector } from '@/components/PatientSelector';
import { AppointmentCreationForm } from '@/components/AppointmentCreationForm';
import { NavigationMenu } from '@/components/NavigationMenu';
import { OrganizationHeader } from '@/components/OrganizationHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Calendar, Activity } from 'lucide-react';
interface Patient {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  friendlyId: string;
}
const Appointments = () => {
  const {
    user,
    signOut,
    loading: authLoading
  } = useAuth();
  const {
    profile,
    loading: profileLoading
  } = useProfile();
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const navigate = useNavigate();
  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth');
    }
  }, [user, authLoading, navigate]);
  const handleAppointmentsUploaded = () => {
    // Trigger refresh of appointments list
    setRefreshKey(prev => prev + 1);
  };
  const handleAppointmentCreated = () => {
    // Trigger refresh of appointments list
    setRefreshKey(prev => prev + 1);
  };
  if (authLoading || profileLoading) {
    return <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg">Loading...</div>
        </div>
      </div>;
  }
  if (!user || !profile) {
    return null;
  }
  return <div className="min-h-screen bg-background">
      <OrganizationHeader />
      <div className="p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex justify-between items-start mb-8">
            <div className="text-center flex-1">
              <h1 className="text-4xl font-bold mb-4">Patient-Centered Activity Management</h1>
              <p className="text-xl text-muted-foreground">Manage your patient relationships, appointments, and interactions</p>
              <p className="text-sm text-muted-foreground mt-2">Welcome back, {profile.salesperson_name}</p>
            </div>
            <NavigationMenu />
          </div>

          <Tabs defaultValue="patients" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="patients" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Patient Management
              </TabsTrigger>
              <TabsTrigger value="appointments" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Appointments
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Analytics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="patients">
              <PatientManagement />
            </TabsContent>

            <TabsContent value="appointments" className="space-y-6">
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-6">
                  <AppointmentUploadWithPreview onUploadComplete={handleAppointmentsUploaded} />
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Manual Appointment Creation</CardTitle>
                      <CardDescription>
                        Create individual appointments without file upload
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <PatientSelector onPatientSelect={setSelectedPatient} selectedPatient={selectedPatient} />
                      
                      {selectedPatient && <AppointmentCreationForm patient={selectedPatient} onAppointmentCreated={handleAppointmentCreated} />}
                    </CardContent>
                  </Card>
                </div>
                
                <div className="space-y-6">
                  <AppointmentsList key={refreshKey} />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="analytics">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Patient Analytics Dashboard
                  </CardTitle>
                  <CardDescription>
                    Insights into your patient engagement and success metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-12">
                    <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-medium mb-2">Analytics Coming Soon</h3>
                    <p className="text-muted-foreground">
                      Patient journey analytics, conversion metrics, and engagement insights will be available here
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>;
};
export default Appointments;