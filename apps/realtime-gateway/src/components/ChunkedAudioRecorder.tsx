import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { AudioControls } from '@/components/AudioControls';
import { Mic, Square, RefreshCw, CheckCircle, AlertCircle, Clock, Trash2, Play, Pause, Volume2, Upload as UploadIcon } from 'lucide-react';
import { ChunkedRecordingManager, RecordingProgress, formatDuration } from '@/services/chunkedRecordingService';
import { useToast } from '@/components/ui/use-toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { useProfile } from '@/hooks/useProfile';

interface ChunkedAudioRecorderProps {
  onRecordingComplete: (callRecordId: string, totalDuration: number) => void;
  disabled?: boolean;
  patientName?: string;
  patientId?: string;
  centerId?: string;
  autoStart?: boolean;
}

export const ChunkedAudioRecorder: React.FC<ChunkedAudioRecorderProps> = ({
  onRecordingComplete,
  disabled = false,
  patientName,
  patientId,
  centerId,
  autoStart = false
}) => {
  const [progress, setProgress] = useState<RecordingProgress>({
    currentChunk: 0,
    totalChunks: 0,
    chunksUploaded: 0,
    chunksFailed: 0,
    isRecording: false,
    isComplete: false,
    totalDuration: 0
  });
  const [callRecordId, setCallRecordId] = useState<string>('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showOptionsDialog, setShowOptionsDialog] = useState(false);
  const [showRecoveryDialog, setShowRecoveryDialog] = useState(false);
  const [recoveryState, setRecoveryState] = useState<any>(null);
  const recordingManagerRef = useRef<ChunkedRecordingManager | null>(null);
  const { toast } = useToast();
  const { profile } = useProfile();

  useEffect(() => {
    // Initialize recording manager
    recordingManagerRef.current = new ChunkedRecordingManager(setProgress);

    // PHASE 4: Force cleanup of any orphaned streams from previous sessions
    // This prevents phantom recording indicators in Chrome
    console.log('🧹 Checking for orphaned media streams on mount');
    
    // Stop any existing media streams that might be lingering
    // Defensive check for test environments where navigator.mediaDevices might not be available
    if (navigator?.mediaDevices?.enumerateDevices) {
      try {
        // Call enumerateDevices directly on mediaDevices to avoid "Illegal invocation" error
        // The method must be called with the correct 'this' context
        const result = navigator.mediaDevices.enumerateDevices();
        if (result && typeof result.then === 'function') {
          result.then(() => {
            // This triggers cleanup of any getUserMedia streams that are still active
            if (recordingManagerRef.current) {
              recordingManagerRef.current.cleanup(true);
              console.log('✅ Pre-mount cleanup completed');
            }
          }).catch((err: any) => console.warn('Could not enumerate devices:', err));
        } else {
          // Result is not a promise, do cleanup immediately
          if (recordingManagerRef.current) {
            recordingManagerRef.current.cleanup(true);
            console.log('✅ Pre-mount cleanup completed');
          }
        }
      } catch (err) {
        console.warn('Error enumerating devices:', err);
        // Fall through to cleanup
        if (recordingManagerRef.current) {
          recordingManagerRef.current.cleanup(true);
        }
      }
    } else {
      // In test environments or when mediaDevices is not available, still try cleanup
      if (recordingManagerRef.current) {
        recordingManagerRef.current.cleanup(true);
        console.log('✅ Pre-mount cleanup completed (no mediaDevices available)');
      }
    }

    // Check for existing recording state and auto-resume
    const existingState = ChunkedRecordingManager.loadState();
    if (existingState && existingState.isRecording) {
      console.log('🔄 Found existing recording state');
      
      // PHASE 3: Validate state before attempting recovery
      const validation = ChunkedRecordingManager.validateState(existingState);
      
      if (!validation.valid) {
        console.warn('⚠️ Stale recording state detected:', validation.reason);
        // PHASE 1: Aggressive cleanup - stop any streams first
        recordingManagerRef.current?.cleanup(true);
        ChunkedRecordingManager.clearState();
        ChunkedRecordingManager.clearAllSlices();
        toast({
          title: "Previous recording cleaned up",
          description: validation.reason || "Recording state was too old to recover",
        });
        return;
      }
      
      // Check if we already have an active recording manager with ongoing recording
      const currentProgress = recordingManagerRef.current?.getProgress();
      const isAlreadyRecording = currentProgress?.isRecording === true;
      
      if (isAlreadyRecording) {
        // Scenario A: Tab visibility change - recording never stopped, just update UI
        console.log('✅ Recording already active in memory, no restore needed');
        setCallRecordId(existingState.callRecordId);
        setRecoveryState(existingState);
        // Just show a toast to inform user
        toast({
          title: "Recording continues",
          description: "Your recording has continued in the background",
        });
      } else {
        // Scenario B: Page reload - need to restore everything
        console.log('🔄 Recording not in memory, restoring from state');
        setRecoveryState(existingState);
        setCallRecordId(existingState.callRecordId);
        handleRecoverRecording(existingState);
      }
    } else if (existingState && !existingState.isRecording) {
      // PHASE 3: State exists but says not recording - cleanup stale data
      console.log('🧹 Found stale recording state (not recording), cleaning up');
      recordingManagerRef.current?.cleanup(true);
      ChunkedRecordingManager.clearState();
      ChunkedRecordingManager.clearAllSlices();
    }

    // Add Page Visibility API listener
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab hidden - persist state
        recordingManagerRef.current?.saveState();
        console.log('👁️ Tab hidden, state persisted');
      } else {
        // Tab visible - update UI
        console.log('👁️ Tab visible again');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Add beforeunload warning
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      const currentProgress = recordingManagerRef.current?.getProgress();
      if (currentProgress?.isRecording) {
        e.preventDefault();
        recordingManagerRef.current?.saveState();
        // Update browser tab title
        document.title = '🔴 Recording in progress...';
        return (e.returnValue = 'Recording in progress. Are you sure you want to leave?');
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      // Only cleanup if not recording
      const currentProgress = recordingManagerRef.current?.getProgress();
      if (!currentProgress?.isRecording) {
        recordingManagerRef.current?.cleanup(true);
      } else {
        console.log('⚠️ Component unmounting but recording active - state preserved');
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // Monitor for upload errors and show toast notification
  useEffect(() => {
    if (progress.errorMessage) {
      toast({
        title: "Upload Error",
        description: progress.errorMessage,
        variant: "destructive",
      });
    }
  }, [progress.errorMessage, toast]);

  // Auto-start recording if autoStart prop is true
  useEffect(() => {
    if (autoStart && !disabled && patientName?.trim() && !progress.isRecording && !callRecordId) {
      // Small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        startRecording();
      }, 100);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart, disabled, patientName]);

  const startRecording = async () => {
    if (!patientName?.trim()) {
      toast({
        title: "Patient name required",
        description: "Please enter a patient name before starting the recording.",
        variant: "destructive",
      });
      return;
    }

    // Check for microphone permissions first
    try {
      const permissionStatus = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      if (permissionStatus.state === 'denied') {
        toast({
          title: "Microphone access denied",
          description: "Please enable microphone access in your browser settings and try again.",
          variant: "destructive",
        });
        return;
      }
    } catch (permissionError) {
      console.warn('Permission check failed:', permissionError);
      // Continue anyway as some browsers don't support permission query
    }

    try {
      // Create call record first
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        throw new Error('User not authenticated');
      }

      const { data, error } = await supabase
        .from('call_records')
        .insert({
          user_id: user.id,
          customer_name: patientName.trim(),
          start_time: new Date().toISOString(),
          transcript: 'Recording in progress...',
          total_chunks: 0,
          chunks_uploaded: 0,
          recording_complete: false,
          patient_id: patientId || null,
          center_id: centerId || null
        })
        .select()
        .single();

      if (error) {
        console.error('Failed to create call_record:', error);
        throw new Error(`Database error: ${error.message}`);
      }

      if (!data || !data.id) {
        throw new Error('Call record was not created - no ID returned');
      }

      console.log('Created call_record:', data.id);

      const newCallRecordId = data.id;
      setCallRecordId(newCallRecordId);

      await recordingManagerRef.current?.startRecording(newCallRecordId);
      
      // Update browser tab title
      document.title = '🔴 Recording...';
      
      toast({
        title: "Recording started",
        description: "Your call is being recorded in 5-minute chunks.",
      });
    } catch (error) {
      console.error('Failed to start recording:', error);
      toast({
        title: "Recording failed",
        description: error instanceof Error ? error.message : 'Failed to start recording',
        variant: "destructive",
      });
    }
  };

  const handleRecoverRecording = async (state?: any) => {
    const stateToRestore = state || recoveryState;
    if (!stateToRestore || !recordingManagerRef.current) return;

    try {
      const restored = await recordingManagerRef.current.restoreFromState(stateToRestore);
      
      if (restored) {
        // Calculate background duration
        const backgroundSeconds = stateToRestore.lastSaveTime 
          ? Math.floor((Date.now() - stateToRestore.lastSaveTime) / 1000)
          : 0;
        
        document.title = '🔴 Recording...';
        
        // Show non-blocking success toast
        toast({
          title: "Recording resumed",
          description: backgroundSeconds > 0 
            ? `Captured ${backgroundSeconds} seconds while in background. Recording continues...`
            : "Your recording has resumed and continues...",
        });
      } else {
        // Only show dialog if restoration FAILS
        setShowRecoveryDialog(true);
      }
    } catch (error) {
      console.error('Failed to auto-recover, showing dialog:', error);
      // Only show dialog on error
      setShowRecoveryDialog(true);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const isAccessError = errorMessage.includes('not found') || errorMessage.includes('access denied');
      
      toast({
        title: "Cannot restore recording",
        description: isAccessError 
          ? "The previous recording is no longer accessible."
          : "Failed to restore recording automatically.",
        variant: "destructive",
      });
    }
  };

  const handleDiscardRecording = async () => {
    try {
      if (recoveryState?.callRecordId) {
        // Delete the incomplete recording
        const { supabase } = await import('@/integrations/supabase/client');
        await supabase.from('call_records').delete().eq('id', recoveryState.callRecordId);
      }
      
      ChunkedRecordingManager.clearState();
      setShowRecoveryDialog(false);
      setRecoveryState(null);
      setCallRecordId('');
      
      toast({
        title: "Recording discarded",
        description: "Previous recording has been deleted.",
      });
    } catch (error) {
      console.error('Failed to discard recording:', error);
      toast({
        title: "Discard failed",
        description: "Could not delete previous recording.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = async () => {
    try {
      await recordingManagerRef.current?.stopRecording();
      
      // Reset browser tab title
      document.title = document.title.replace('🔴 ', '');
      
      // Wait for all chunks to finish uploading before triggering transcription
      const maxWaitMs = 30000; // 30 seconds
      const startWait = Date.now();
      let allUploaded = false;
      
      while (Date.now() - startWait < maxWaitMs) {
        const currentProgress = recordingManagerRef.current?.getProgress();
        const expectedChunks = currentProgress?.totalChunks || 0;
        const uploadedChunks = currentProgress?.chunksUploaded || 0;
        
        console.log(`⏳ Waiting for uploads: ${uploadedChunks}/${expectedChunks} chunks uploaded`);
        
        if (uploadedChunks >= expectedChunks && expectedChunks > 0) {
          allUploaded = true;
          console.log('✅ All chunks uploaded, triggering transcription');
          break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 500)); // Check every 500ms
      }
      
      if (!allUploaded) {
        console.warn('⚠️ Timeout waiting for all chunks to upload');
        toast({
          title: "Upload in progress",
          description: "Some chunks are still uploading. Transcription will start with available chunks.",
          variant: "default",
        });
      }
      
      toast({
        title: "Recording stopped",
        description: "Processing uploaded chunks for transcription.",
      });

      // Show delete confirmation dialog if recording was stopped but has issues or user wants to delete
      if (callRecordId && (progress.chunksFailed > 0 || progress.totalDuration > 5)) {
        setShowDeleteConfirm(true);
      }

      // Call completion callback if successful
      if (callRecordId && progress.totalDuration > 0 && progress.chunksFailed === 0) {
        onRecordingComplete(callRecordId, progress.totalDuration);
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      toast({
        title: "Error stopping recording",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    }
  };

  const handleResumeRecording = async () => {
    try {
      await recordingManagerRef.current?.resumeRecording();
      setShowOptionsDialog(false);
      toast({ title: 'Recording resumed' });
    } catch (error) {
      console.error('Failed to resume recording:', error);
      toast({ title: 'Could not resume', variant: 'destructive' });
    }
  };

  const handleUploadRecording = async () => {
    if (!callRecordId || !patientName?.trim()) {
      toast({ title: 'Missing info', description: 'No recording to upload or patient name missing.', variant: 'destructive' });
      return;
    }
    const { supabase } = await import('@/integrations/supabase/client');
    try {
      // Finalize recording (marks recording_complete and stops input)
      await recordingManagerRef.current?.stopRecording();

      let provider = localStorage.getItem('transcriptionProvider') || 'deepgram';
      const salespersonName = profile?.salesperson_name || 'Salesperson';
      console.log('Starting transcription with provider:', provider);

      // Ensure all chunks are uploaded before invoking transcription
      toast({ title: 'Finalizing uploads', description: 'Waiting for all chunks to finish uploading…' });
      const waitForAllChunks = async (timeoutMs = 60000) => {
        const start = Date.now();
        while (Date.now() - start < timeoutMs) {
          // Read expected total chunks from call_records
          const { data: record } = await supabase
            .from('call_records')
            .select('total_chunks')
            .eq('id', callRecordId)
            .single();
          const expected = (record?.total_chunks && record.total_chunks > 0) ? record.total_chunks : progress.totalChunks;

          // Count uploaded chunks
          const { count } = await supabase
            .from('call_chunks')
            .select('id', { count: 'exact', head: true })
            .eq('call_record_id', callRecordId)
            .eq('upload_status', 'uploaded');

          if (typeof count === 'number' && expected > 0 && count >= expected) {
            return true;
          }
          await new Promise(r => setTimeout(r, 1500));
        }
        return false;
      };

      const allUploaded = await waitForAllChunks();
      if (!allUploaded) {
        throw new Error('Not all chunks finished uploading. Please wait a moment and try again (or use Retry above).');
      }

      const invoke = async (prov: string) => {
        const { getApiUrl } = await import('@/utils/apiConfig');
        const { data: sess } = await supabase.auth.getSession();
        const token = sess.session?.access_token;
        const resp = await fetch(getApiUrl(`/api/transcribe/call-record/${encodeURIComponent(callRecordId)}?enable_diarization=true&provider=${encodeURIComponent(prov)}`),
          {
            method: 'POST',
            headers: {
              'Authorization': token ? `Bearer ${token}` : '',
            },
          }
        );
        const data = await resp.json().catch(() => null);
        const error = resp.ok ? null : new Error(data?.detail || resp.statusText);
        return { data, error } as any;
      };

      // Retry helper for 409 not_ready
      const invokeWithRetry = async (prov: string, maxRetries = 3) => {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
          const { data, error } = await invoke(prov);
          
          // If not ready, wait and retry
          if (data?.not_ready === true && attempt < maxRetries) {
            console.log(`⏳ Attempt ${attempt}: Not ready yet, retrying in 2s...`);
            toast({ 
              title: 'Finalizing recording', 
              description: `Waiting for all chunks... (attempt ${attempt}/${maxRetries})` 
            });
            await new Promise(r => setTimeout(r, 2000));
            continue;
          }
          
          return { data, error };
        }
        
        // Max retries exceeded
        throw new Error('Recording not ready after multiple attempts');
      };

      toast({ title: 'Starting transcription', description: `Using ${provider === 'deepgram' ? 'Deepgram' : 'AssemblyAI'}` });
      let { data, error } = await invokeWithRetry(provider);

      // Check for 404 - function not deployed
      if (error?.message?.includes('404') || error?.message?.includes('not found')) {
        console.error('❌ transcribe-audio-v2 function not deployed');
        toast({ 
          title: 'Transcription service unavailable', 
          description: 'The transcription function is not deployed. Please contact support.',
          variant: 'destructive',
          duration: 10000
        });
        throw new Error('Transcription function not deployed');
      }

      // Display requestId for debugging
      if (data?.requestId) {
        console.log(`📋 Transcription request ID: ${data.requestId}, Function version: ${data.functionVersion || 'unknown'}`);
        toast({ 
          title: 'Transcription started', 
          description: `Request ID: ${data.requestId.slice(0, 8)}...`,
          duration: 3000
        });
      }

      console.log('Transcription attempt 1:', { provider, success: data?.success, error: error?.message });

      // Fallback to AssemblyAI if Deepgram is selected but not configured
      if ((error || !data?.success) && provider === 'deepgram') {
        console.log('Deepgram failed, trying AssemblyAI...');
        toast({ title: 'Deepgram unavailable', description: 'Falling back to AssemblyAI…' });
        provider = 'assemblyai';
        ({ data, error } = await invoke(provider));
        console.log('Transcription attempt 2 (AssemblyAI):', { success: data?.success, error: error?.message });
      }

      // If the API call failed, attempt local fallback transcription
      if (error || !data?.success) {
        console.log('Server transcription failed, trying local transcription fallback...');
        toast({ title: 'Trying alternative approach', description: 'Assembling audio locally...' });
        
        try {
          // Get all chunks for this call (uploaded only), ordered by chunk number
          const { data: chunks, error: chunksError } = await supabase
            .from('call_chunks')
            .select('*')
            .eq('call_record_id', callRecordId)
            .eq('upload_status', 'uploaded')
            .order('chunk_number');

          if (chunksError) {
            console.error('Failed to fetch chunks for fallback:', chunksError);
            throw chunksError;
          }

          if (!chunks || chunks.length === 0) {
            throw new Error('No audio chunks found');
          }

          // Download and combine chunks
          const audioBlobs: Blob[] = [];
          for (const chunk of chunks) {
            const { data: audioData, error: dlErr } = await supabase.storage
              .from('call-recordings')
              .download(chunk.file_path);
            if (dlErr) {
              console.error('Chunk download failed:', dlErr, 'path:', chunk.file_path);
            }
            if (audioData) {
              audioBlobs.push(audioData);
            }
          }

          // Combine all chunks into single blob using proper re-encoding
          const { reencodeAudioSlices } = await import('@/services/audioReencodingService');
          const combinedBlob = await reencodeAudioSlices(audioBlobs);
          
          // Convert to base64
          const base64Audio = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
              const result = reader.result as string;
              resolve(result.split(',')[1]); // Remove data:audio/webm;base64, prefix
            };
            reader.onerror = reject;
            reader.readAsDataURL(combinedBlob);
          });

          try {
              const { transcribeAudio } = await import('@/services/transcriptionService');
              const localTranscript = await transcribeAudio(
                combinedBlob,
                salespersonName,
                patientName.trim()
              );

              if (localTranscript && !localTranscript.toLowerCase().startsWith('transcription failed')) {
                // Save transcript directly to database
                const { error: updateErr } = await supabase
                  .from('call_records')
                  .update({ transcript: localTranscript, status: 'completed' })
                  .eq('id', callRecordId);
                if (updateErr) {
                  console.error('Failed to update DB with local transcript:', updateErr);
                }
                data = { success: true, transcript: localTranscript, provider: 'local' } as any;
                error = null;
              }
            } catch (localErr) {
              console.error('Local transcription fallback failed:', localErr);
              throw new Error(
                `Both chunked and direct transcription failed, and local fallback also failed: ${localErr instanceof Error ? localErr.message : 'Unknown error'}`
              );
            }
        } catch (fallbackError) {
          console.error('Fallback transcription failed:', fallbackError);
          throw new Error(`Both chunked and direct transcription failed. Last error: ${fallbackError instanceof Error ? fallbackError.message : 'Unknown error'}`);
        }
      }

      if (error || !data?.success) {
        const errorMsg = data?.error || error?.message || 'Transcription failed';
        console.error('Final transcription error:', errorMsg);
        throw new Error(errorMsg);
      }

      console.log('Transcription successful!');
      toast({ title: 'Transcription started', description: 'We will update the analysis shortly.' });
      
      // Notify parent to refresh dashboards/state
      onRecordingComplete(callRecordId, progress.totalDuration);
      
      // Reset the recorder to ready state after successful upload
      setProgress({
        currentChunk: 0,
        totalChunks: 0,
        chunksUploaded: 0,
        chunksFailed: 0,
        isRecording: false,
        isComplete: false,
        totalDuration: 0
      });
      setCallRecordId('');
      
    } catch (err) {
      console.error('Upload/transcription error:', err);
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast({ 
        title: 'Upload failed', 
        description: `${message}. Call ID: ${callRecordId}. You can retry transcription from the analysis page.`,
        variant: 'destructive',
        duration: 10000
      });
    } finally {
      // Close the options dialog regardless to avoid it feeling stuck
      setShowOptionsDialog(false);
    }
  };

  const retryFailedChunks = async () => {
    try {
      await recordingManagerRef.current?.retryFailedChunks();
      toast({
        title: "Retrying uploads",
        description: "Attempting to upload failed chunks again.",
      });
    } catch (error) {
      console.error('Failed to retry chunks:', error);
      toast({
        title: "Retry failed",
        description: "Could not retry failed uploads",
        variant: "destructive",
      });
    }
  };
  const deleteRecording = async () => {
    try {
      await recordingManagerRef.current?.deleteRecording();
      
      // Reset state
      setProgress({
        currentChunk: 0,
        totalChunks: 0,
        chunksUploaded: 0,
        chunksFailed: 0,
        isRecording: false,
        isComplete: false,
        totalDuration: 0
      });
      setCallRecordId('');
      setShowDeleteConfirm(false);
      
      // Reset browser tab title
      document.title = document.title.replace('🔴 ', '');
      
      toast({
        title: "Recording deleted",
        description: "The recording has been permanently deleted.",
      });
    } catch (error) {
      console.error('Failed to delete recording:', error);
      toast({
        title: "Delete failed",
        description: error instanceof Error ? error.message : 'Could not delete recording',
        variant: "destructive",
      });
    }
  };

  const getUploadProgress = () => {
    if (progress.totalChunks === 0) return 0;
    return (progress.chunksUploaded / progress.totalChunks) * 100;
  };

  const getStatusColor = () => {
    if (progress.chunksFailed > 0) return 'destructive';
    if (progress.isRecording) return 'default';
    if (progress.isComplete) return 'secondary';
    return 'outline';
  };

  const getStatusText = () => {
    const permanentlyFailed = progress.chunksFailed > 0; // chunksFailed only counts chunks with retryCount >= 5
    const retrying = progress.totalChunks > progress.chunksUploaded && !permanentlyFailed;
    
    if (permanentlyFailed) return 'Upload Failed';
    if (retrying && progress.isRecording) return 'Recording & Uploading';
    if (progress.isRecording) return 'Recording';
    if (progress.isComplete) return 'Complete';
    if (progress.chunksUploaded > 0 && progress.totalChunks > progress.chunksUploaded) return 'Uploading';
    return 'Ready';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mic className="h-5 w-5" />
          Professional Call Recorder
          <Badge variant={getStatusColor()}>
            {getStatusText()}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <AudioControls 
          patientName={patientName || ''}
          patientId={patientId}
          hideUpload={true}
        />
        
        {/* Recording Info */}
        {(progress.isRecording || progress.totalDuration > 0) && (
          <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {formatDuration(progress.totalDuration)}
              </div>
              <div className="text-sm text-muted-foreground">Total Duration</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {progress.currentChunk + 1}
              </div>
              <div className="text-sm text-muted-foreground">Current Chunk</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {progress.chunksUploaded}/{progress.totalChunks}
              </div>
              <div className="text-sm text-muted-foreground">Uploaded</div>
            </div>
          </div>
        )}

        {/* Live Audio Level */}
        {progress.isRecording && (
          <div className="space-y-2 p-4 rounded-lg bg-secondary/20">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Volume2 className="h-4 w-4" />
              <span>Audio level: {Math.round(progress.audioLevel ?? 0)}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-100"
                style={{ width: `${Math.round(progress.audioLevel ?? 0)}%` }}
              />
            </div>
          </div>
        )}

        {/* Upload Progress */}
        {progress.totalChunks > 0 && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Upload Progress</span>
              <span>{Math.round(getUploadProgress())}%</span>
            </div>
            <Progress value={getUploadProgress()} className="h-2" />
          </div>
        )}

        {/* Error Alert */}
        {progress.errorMessage && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>{progress.errorMessage}</span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={retryFailedChunks}
                className="ml-2"
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Success Alert */}
        {progress.isComplete && progress.chunksFailed === 0 && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Recording completed successfully! All {progress.totalChunks} chunks uploaded.
            </AlertDescription>
          </Alert>
        )}

        {/* Info About Chunked Recording */}
        {!progress.isRecording && progress.totalChunks === 0 && (
          <Alert>
            <Clock className="h-4 w-4" />
            <AlertDescription>
              <strong>Professional Mode:</strong> Records in 5-minute chunks with automatic upload. 
              Perfect for long consultations up to 90+ minutes. Each chunk is saved immediately for reliability.
            </AlertDescription>
          </Alert>
        )}

        {/* Controls */}
        <div className="flex gap-2 flex-wrap">
          {progress.isRecording ? (
            <Button 
              onClick={() => {
                recordingManagerRef.current?.pauseRecording().then(() => setShowOptionsDialog(true));
              }}
              variant="destructive"
              className="flex-1"
              size="lg"
            >
              <Square className="h-4 w-4 mr-2" />
              Stop Recording
            </Button>
          ) : callRecordId ? (
            <>
              <Button 
                onClick={handleResumeRecording}
                variant="secondary"
                className="flex-1"
                size="lg"
              >
                <Play className="h-4 w-4 mr-2" />
                Resume Recording
              </Button>
              <Button 
                onClick={handleUploadRecording}
                className="flex-1"
                size="lg"
              >
                <UploadIcon className="h-4 w-4 mr-2" />
                Upload Recording
              </Button>
              <Button 
                onClick={() => setShowDeleteConfirm(true)}
                variant="outline"
                size="lg"
                className="text-destructive hover:bg-destructive hover:text-destructive-foreground"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Recording
              </Button>
            </>
          ) : (
            <Button 
              onClick={startRecording}
              disabled={disabled || !patientName?.trim()}
              className="flex-1"
              size="lg"
            >
              <Mic className="h-4 w-4 mr-2" />
              Start Professional Recording
            </Button>
          )}
        </div>

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-3">
                <div>
                  <p className="font-medium">Delete this recording?</p>
                  <p className="text-sm">
                    {progress.chunksFailed > 0 
                      ? `${progress.chunksFailed} chunks failed to upload. Deleting will remove all uploaded chunks and the recording.`
                      : `This will permanently delete the ${formatDuration(progress.totalDuration)} recording and all ${progress.totalChunks} chunks.`
                    }
                  </p>
                  <p className="text-xs mt-1 opacity-75">This action cannot be undone.</p>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setShowDeleteConfirm(false)}
                    className="flex-1"
                  >
                    Keep Recording
                  </Button>
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={deleteRecording}
                    className="flex-1"
                  >
                    Delete Permanently
                  </Button>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Chunk Status Details */}
        {progress.totalChunks > 0 && (
          <div className="text-xs text-muted-foreground space-y-1">
            <div>• Recording in 5-minute chunks for optimal reliability</div>
            <div>• Each chunk uploads automatically in the background</div>
            <div>• You can continue recording even if some uploads are pending</div>
            {progress.chunksFailed > 0 && (
              <div className="text-destructive">• Some uploads failed - use retry button above</div>
            )}
          </div>
        )}

        {/* Options Dialog after stopping */}
        <Dialog open={showOptionsDialog} onOpenChange={setShowOptionsDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Finish recording?</DialogTitle>
              <DialogDescription>Choose what to do with this recording.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div className="flex gap-2">
                <Button onClick={handleResumeRecording} variant="secondary" className="flex-1">
                  <Play className="h-4 w-4 mr-2" /> Resume recording
                </Button>
                <Button onClick={handleUploadRecording} className="flex-1">
                  <UploadIcon className="h-4 w-4 mr-2" /> Upload recording
                </Button>
              </div>
              <Button onClick={() => setShowDeleteConfirm(true)} variant="outline" className="w-full text-destructive">
                <Trash2 className="h-4 w-4 mr-2" /> Delete recording
              </Button>
            </div>
            <DialogFooter />
          </DialogContent>
        </Dialog>

        {/* Recovery Dialog */}
        <Dialog open={showRecoveryDialog} onOpenChange={setShowRecoveryDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Resume Previous Recording?</DialogTitle>
              <DialogDescription>
                We couldn't automatically resume your recording. Would you like to try again or start fresh?
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  We couldn't automatically resume your recording. Would you like to try again or start fresh?
                </AlertDescription>
              </Alert>
              
              {recoveryState && (
                <div className="text-sm text-muted-foreground space-y-1">
                  <div>• Call ID: {recoveryState.callRecordId.slice(0, 8)}...</div>
                  <div>• Chunks recorded: {recoveryState.totalChunks}</div>
                  <div>• Last updated: {new Date(recoveryState.lastUpdateTime).toLocaleString()}</div>
                </div>
              )}
              
              <div className="flex gap-2">
                <Button onClick={handleRecoverRecording} className="flex-1">
                  <Play className="h-4 w-4 mr-2" />
                  Resume Recording
                </Button>
                <Button onClick={handleDiscardRecording} variant="outline" className="flex-1">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Discard & Start Fresh
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};
