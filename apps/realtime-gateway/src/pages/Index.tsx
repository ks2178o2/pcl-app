import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AudioRecorder } from '@/components/AudioRecorder';
import { ChunkedAudioRecorder } from '@/components/ChunkedAudioRecorder';
import { CallsDashboard } from '@/components/CallsDashboard';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart3, Mic, Zap, Upload } from 'lucide-react';
import { PatientInput } from '@/components/PatientInput';
import { NavigationMenu } from '@/components/NavigationMenu';
import { OrganizationHeader } from '@/components/OrganizationHeader';
import { useCenterSession } from '@/hooks/useCenterSession';
import { CenterSelectionModal } from '@/components/CenterSelectionModal';
import { Tabs as ViewTabs, TabsContent as ViewTabsContent, TabsList as ViewTabsList, TabsTrigger as ViewTabsTrigger } from '@/components/ui/tabs';
import { AudioControls } from '@/components/AudioControls';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
const Index = () => {
  const {
    calls,
    addCall,
    loadCalls,
    handleChunkedRecordingComplete
  } = useCallRecords();
  const {
    user,
    signOut,
    loading: authLoading
  } = useAuth();
  const {
    profile,
    loading: profileLoading
  } = useProfile();
  const [selectedPatient, setSelectedPatient] = useState<{
    id?: string;
    name: string;
  }>({
    name: ''
  });
  const [callsLimit, setCallsLimit] = useState<number>(10);
  const navigate = useNavigate();
  const { activeCenter, needsCenterSelection, availableCenters, setActiveCenter, error: centerError } = useCenterSession();

  useEffect(() => {
    loadCalls(callsLimit);
  }, [callsLimit]);
  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth');
    }
  }, [user, authLoading, navigate]);
  if (authLoading || profileLoading) {
    return <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg">Loading...</div>
        </div>
      </div>;
  }
  if (!user) {
    return null;
  }
  
  if (!profile) {
    return <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="text-lg">Loading profile...</div>
        <div className="text-sm text-muted-foreground mt-2">User: {user.email}</div>
      </div>
    </div>;
  }
  const handleRecordingComplete = async (audioBlob: Blob, duration: number) => {
    const patientName = selectedPatient.name.trim();
    if (!patientName) {
      alert('Please select or enter a patient name before recording.');
      return;
    }
    if (!activeCenter) {
      alert('Please select a center before recording.');
      return;
    }
    await addCall(audioBlob, duration, patientName, profile.salesperson_name, selectedPatient.id, activeCenter);
    setSelectedPatient({
      name: ''
    }); // Clear the patient after recording
  };
  return <div className="min-h-screen bg-background">
      <OrganizationHeader />
      
      {/* Form Factor Selector */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-3">
          <ViewTabs defaultValue="desktop" className="w-fit">
            
          </ViewTabs>
        </div>
      </div>

      <div className="p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex justify-between items-start mb-8">
            <div className="text-center flex-1">
              <h1 className="text-4xl font-bold mb-4">Sales Angel Buddy</h1>
              <p className="text-xl text-muted-foreground">Your AI-powered sales copilot system</p>
              <p className="text-sm text-muted-foreground mt-2">Welcome back, {profile.salesperson_name}</p>
            </div>
            <NavigationMenu />
          </div>

        <div className="space-y-8">
          {/* Recording Section - Front and Center */}
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row gap-4 w-full">
              <div className="flex-1">
                <PatientInput value={selectedPatient} onChange={setSelectedPatient} />
              </div>
            </div>
            
            <Tabs defaultValue="professional" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="professional" className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Professional
                </TabsTrigger>
                <TabsTrigger value="quick" className="flex items-center gap-2">
                  <Mic className="h-4 w-4" />
                  Quick
                </TabsTrigger>
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  <Upload className="h-4 w-4" />
                  Upload
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="professional" className="mt-4 space-y-4">
                <div className="bg-gradient-to-r from-primary/5 via-secondary/5 to-accent/5 p-4 rounded-lg border border-primary/10">
                  <div className="mb-3">
                    <h4 className="font-medium text-primary mb-1">💼 Professional Recording</h4>
                    <p className="text-sm text-muted-foreground">
                      Best for longer calls with real-time chunked uploads. Automatically saves as you record, preventing data loss.
                    </p>
                  </div>
                </div>
                <ChunkedAudioRecorder 
                  onRecordingComplete={(callRecordId, duration) => {
                    handleChunkedRecordingComplete(callRecordId, duration);
                    setSelectedPatient({
                      name: ''
                    }); // Clear for next recording
                  }} 
                  disabled={!selectedPatient.name.trim() || !activeCenter} 
                  patientName={selectedPatient.name} 
                  patientId={selectedPatient.id}
                  centerId={activeCenter || undefined} 
                />
                {/* User feedback for disabled button */}
                {(!selectedPatient.name.trim() || !activeCenter) && (
                  <div className="text-sm text-muted-foreground mt-2">
                    {!selectedPatient.name.trim() && !activeCenter ? (
                      "Please select a patient and center to start recording"
                    ) : !selectedPatient.name.trim() ? (
                      "Please select a patient to start recording"
                    ) : (
                      "Please select a center to start recording"
                    )}
                  </div>
                )}
              </TabsContent>
              
              <TabsContent value="quick" className="mt-4 space-y-4">
                <div className="bg-gradient-to-r from-secondary/5 via-accent/5 to-primary/5 p-4 rounded-lg border border-secondary/10">
                  <div className="mb-3">
                    <h4 className="font-medium mb-1 text-slate-950">⚡ Quick Recording</h4>
                    <p className="text-sm text-muted-foreground">
                      Perfect for short interactions and quick notes. Records in-browser and uploads when complete.
                    </p>
                  </div>
                </div>
                <AudioRecorder onRecordingComplete={handleRecordingComplete} disabled={!selectedPatient.name.trim() || !activeCenter} patientName={selectedPatient.name} />
                {/* User feedback for disabled button */}
                {(!selectedPatient.name.trim() || !activeCenter) && (
                  <div className="text-sm text-muted-foreground mt-2">
                    {!selectedPatient.name.trim() && !activeCenter ? (
                      "Please select a patient and center to start recording"
                    ) : !selectedPatient.name.trim() ? (
                      "Please select a patient to start recording"
                    ) : (
                      "Please select a center to start recording"
                    )}
                  </div>
                )}
              </TabsContent>
              
              <TabsContent value="upload" className="mt-4 space-y-4">
                <div className="bg-gradient-to-r from-accent/5 via-primary/5 to-secondary/5 p-4 rounded-lg border border-accent/10">
                  <div className="mb-3">
                    <h4 className="font-medium text-accent mb-1">📁 Upload Recording</h4>
                    <p className="text-sm text-muted-foreground">
                      Upload existing audio files from your device. Supports WAV, MP3, M4A, WebM, and OGG formats.
                    </p>
                  </div>
                </div>
                <AudioControls 
                  patientName={selectedPatient.name} 
                  patientId={selectedPatient.id} 
                  hideUpload={false} 
                  hideTest={true} 
                  centerId={activeCenter || undefined} 
                />
              </TabsContent>
            </Tabs>
          </div>

          {/* Recent Interactions Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Recent Interactions</h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Show:</span>
                <Select value={callsLimit.toString()} onValueChange={(value) => setCallsLimit(value === 'all' ? 999999 : parseInt(value))}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">Last 10</SelectItem>
                    <SelectItem value="25">Last 25</SelectItem>
                    <SelectItem value="50">Last 50</SelectItem>
                    <SelectItem value="all">All</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <CallsDashboard calls={calls} onCallsUpdate={() => loadCalls(callsLimit)} />
            
            {calls.length > 0 && <div className="bg-gradient-to-r from-primary/10 via-secondary/10 to-accent/10 p-4 rounded-lg border border-primary/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg mb-2">🚀 AI-Powered Analysis</h3>
                    <p className="text-sm text-muted-foreground">
                      Get detailed insights on your latest sales calls with advanced AI analysis
                    </p>
                  </div>
                  <Button onClick={() => navigate('/search')} className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    View Analysis
                  </Button>
                </div>
              </div>}
          </div>
        </div>
        </div>
      </div>
      
      {/* Center Selection Modal */}
      <CenterSelectionModal 
        open={needsCenterSelection}
        centers={availableCenters}
        onSelectCenter={setActiveCenter}
      />
      
      {/* Center Error */}
      {centerError && (
        <div className="fixed bottom-4 right-4 bg-destructive text-destructive-foreground p-4 rounded-lg shadow-lg">
          {centerError}
        </div>
      )}
    </div>;
};
export default Index;