import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useFailedUploads } from '@/hooks/useFailedUploads';
import { NavigationMenu } from '@/components/NavigationMenu';
import { OrganizationHeader } from '@/components/OrganizationHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CallsDashboard } from '@/components/CallsDashboard';
import { FailedUploadsBanner } from '@/components/FailedUploadsBanner';
import { 
  Mic, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Trash2, 
  BarChart3,
  Calendar,
  User
} from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { getRecordingAction, getStatusColor } from '@/utils/recordingStatusUtils';
import type { CallRecord } from '@/utils/recordingStatusUtils';

export const Recordings = () => {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { profile, loading: profileLoading } = useProfile();
  const { calls, loadCalls } = useCallRecords();
  const { failedUploads, retryUpload, deleteFailedUpload, loading: failedUploadsLoading } = useFailedUploads();
  const { toast } = useToast();
  
  const [activeTab, setActiveTab] = useState('recent');
  const [callsLimit, setCallsLimit] = useState<number>(10);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  useEffect(() => {
    if (user && !authLoading) {
      // Load recent calls based on selected limit
      loadCalls(callsLimit);
    }
  }, [callsLimit, user, authLoading, loadCalls]);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth');
    }
  }, [user, authLoading, navigate]);

  if (authLoading || profileLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg">Loading...</div>
        </div>
      </div>
    );
  }

  if (!user || !profile) {
    return null;
  }

  const handleRetryUpload = async (callRecordId: string) => {
    try {
      await retryUpload(callRecordId);
      toast({
        title: "Upload successful!",
        description: "Your recording has been saved.",
      });
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Please try again later.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteUpload = async (callRecordId: string) => {
    try {
      await deleteFailedUpload(callRecordId);
      toast({
        title: "Recording deleted",
        description: "The failed upload has been removed.",
      });
    } catch (error) {
      toast({
        title: "Delete failed",
        description: "Could not delete the recording.",
        variant: "destructive",
      });
    }
  };

  const handleViewAnalysis = (callId: string) => {
    navigate(`/analysis/${callId}`);
  };

  // Action handlers for smart recording actions
  const handleRecordingAction = async (callRecordId: string, action: string) => {
    setActionInProgress(callRecordId);
    
    try {
      const call = calls.find(c => c.id === callRecordId);
      if (!call) {
        throw new Error('Call record not found');
      }
      
      switch (action) {
        case 'delete':
          await handleDeleteRecording(callRecordId);
          break;
          
        case 'retry-transcription':
          await handleRetryTranscription(callRecordId, call as CallRecord);
          break;
          
        case 'view-analysis':
          handleViewAnalysis(callRecordId);
          break;
          
        default:
          console.warn('Unknown action:', action);
      }
    } catch (error) {
      console.error('Action failed:', error);
      toast({
        title: "Action failed",
        description: error instanceof Error ? error.message : "Could not complete action",
        variant: "destructive",
      });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDeleteRecording = async (callRecordId: string) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      'Are you sure you want to delete this recording? This action cannot be undone.'
    );
    
    if (!confirmed) return;
    
    try {
      // Delete from database
      const { error } = await supabase
        .from('call_records')
        .update({ is_active: false })
        .eq('id', callRecordId);
      
      if (error) throw error;
      
      toast({
        title: "Recording deleted",
        description: "The recording has been removed.",
      });
      
      // Reload calls
      await loadCalls(callsLimit);
    } catch (error) {
      throw new Error('Failed to delete recording');
    }
  };

  const handleRetryTranscription = async (callRecordId: string, call: CallRecord) => {
    try {
      const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
      
      let payload;
      
      if (call.audioBlob) {
        // Convert blob to base64
        const reader = new FileReader();
        const base64Promise = new Promise<string>((resolve, reject) => {
          reader.onloadend = () => {
            const base64Data = reader.result as string;
            const base64Audio = base64Data.split(',')[1];
            resolve(base64Audio);
          };
          reader.onerror = reject;
        });
        reader.readAsDataURL(call.audioBlob);
        const base64Audio = await base64Promise;
        
        payload = await buildTranscriptionPayload({
          audioBase64: base64Audio,
          callId: callRecordId,
          salespersonName: call.salespersonName || profile.salesperson_name,
          customerName: call.patientName || call.customer_name,
          organizationId: (user as any)?.organization_id,
        });
      } else if (call.audioPath) {
        payload = await buildTranscriptionPayload({
          storagePath: call.audioPath,
          callId: callRecordId,
          salespersonName: call.salespersonName || profile.salesperson_name,
          customerName: call.patientName || call.customer_name,
          organizationId: (user as any)?.organization_id,
        });
      } else {
        throw new Error('No audio data available for transcription');
      }
      
      const { data, error } = await supabase.functions.invoke('transcribe-audio-v2', {
        body: payload,
      });
      
      if (error) throw error;
      
      toast({
        title: "Transcription retry started",
        description: "Your recording is being transcribed again. This may take a few minutes.",
      });
      
      // Refresh after delay
      setTimeout(() => {
        loadCalls(callsLimit);
      }, 3000);
    } catch (error) {
      console.error('Failed to retry transcription:', error);
      throw error;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <OrganizationHeader />
      
      <div className="p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex justify-between items-start mb-8">
            <div className="text-center flex-1">
              <h1 className="text-4xl font-bold mb-4">Recording Management</h1>
              <p className="text-xl text-muted-foreground">Manage your call recordings, uploads, and transcriptions</p>
              <p className="text-sm text-muted-foreground mt-2">Welcome back, {profile.salesperson_name}</p>
            </div>
            <NavigationMenu />
          </div>

          <FailedUploadsBanner />

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="recent" className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Recent Recordings
                {calls.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {calls.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="failed" className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Failed Uploads
                {failedUploads.length > 0 && (
                  <Badge variant="destructive" className="ml-2">
                    {failedUploads.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="all" className="flex items-center gap-2">
                <Mic className="h-4 w-4" />
                All Recordings
              </TabsTrigger>
            </TabsList>

            <TabsContent value="recent" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Recent Recordings
                      </CardTitle>
                      <CardDescription>
                        Your recent call recordings with quick access to analysis and playback
                      </CardDescription>
                    </div>
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
                </CardHeader>
                <CardContent>
                  {calls.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Mic className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No recent recordings found.</p>
                      <p className="text-sm">Start recording to see your calls here.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {calls.map((call) => {
                        const recordingAction = getRecordingAction(call as CallRecord);
                        const ActionIcon = recordingAction.icon;
                        
                        return (
                          <Card key={call.id} className="border rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="font-medium">{call.patientName || call.customer_name}</div>
                                <div className="text-sm text-muted-foreground">
                                  {formatDistanceToNow(new Date(call.timestamp), { addSuffix: true })}
                                  {call.duration && call.duration > 0 && (
                                    ` • ${Math.floor(call.duration / 60)}:${String(Math.floor(call.duration % 60)).padStart(2, '0')}`
                                  )}
                                  {(!call.duration || call.duration < 1) && (
                                    <span className="text-red-500"> • 0:00 (No audio)</span>
                                  )}
                                </div>
                                
                                {/* Status indicator */}
                                <div className="mt-2 flex items-center gap-2">
                                  <div className={`w-2 h-2 rounded-full ${
                                    recordingAction.action === 'delete' ? 'bg-red-500' :
                                    recordingAction.action === 'retry-transcription' ? 'bg-yellow-500' :
                                    recordingAction.action === 'view-analysis' ? 'bg-green-500' :
                                    'bg-gray-400'
                                  }`}></div>
                                  <span className={`text-sm ${
                                    recordingAction.action === 'delete' ? 'text-red-600' :
                                    recordingAction.action === 'retry-transcription' ? 'text-yellow-600' :
                                    recordingAction.action === 'view-analysis' ? 'text-green-600' :
                                    'text-gray-600'
                                  }`}>
                                    {recordingAction.reason}
                                  </span>
                                </div>
                              </div>
                              
                              <div className="flex gap-2">
                                {/* Primary Action Button */}
                                <Button
                                  size="sm"
                                  variant={recordingAction.variant}
                                  onClick={() => handleRecordingAction(call.id, recordingAction.action)}
                                  disabled={recordingAction.disabled || actionInProgress === call.id}
                                  className="flex items-center gap-2"
                                >
                                  <ActionIcon className="h-3 w-3" />
                                  {actionInProgress === call.id ? 'Processing...' : recordingAction.label}
                                </Button>
                              </div>
                            </div>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="failed" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Failed Uploads
                  </CardTitle>
                  <CardDescription>
                    Recordings that failed to upload and need your attention
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {failedUploadsLoading ? (
                    <div className="text-center py-8">
                      <div className="text-muted-foreground">Loading failed uploads...</div>
                    </div>
                  ) : failedUploads.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No failed uploads found.</p>
                      <p className="text-sm">All your recordings have been successfully uploaded.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>
                          {failedUploads.length} {failedUploads.length === 1 ? 'recording needs' : 'recordings need'} attention
                        </AlertTitle>
                        <AlertDescription>
                          These recordings failed to upload and need to be retried or deleted.
                        </AlertDescription>
                      </Alert>
                      
                      <div className="space-y-3">
                        {failedUploads.map((upload) => (
                          <Card key={upload.id} className="border-destructive/20">
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-2">
                                    <User className="h-4 w-4 text-muted-foreground" />
                                    <span className="font-medium">{upload.customer_name}</span>
                                    <Badge variant="destructive" className="text-xs">
                                      Upload Failed
                                    </Badge>
                                  </div>
                                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                      <Calendar className="h-3 w-3" />
                                      {formatDistanceToNow(new Date(upload.start_time), { addSuffix: true })}
                                    </div>
                                    {upload.duration_seconds && (
                                      <div className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        {Math.floor(upload.duration_seconds / 60)}:
                                        {String(Math.floor(upload.duration_seconds % 60)).padStart(2, '0')}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleRetryUpload(upload.id)}
                                    className="flex items-center gap-1"
                                  >
                                    <RefreshCw className="h-3 w-3" />
                                    Retry Upload
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleDeleteUpload(upload.id)}
                                    className="text-destructive hover:text-destructive"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="all" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mic className="h-5 w-5" />
                    All Recordings
                  </CardTitle>
                  <CardDescription>
                    Complete list of all your call recordings with search and filter options
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <CallsDashboard calls={calls} onCallsUpdate={loadCalls} />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Recordings;

