import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { CallAnalysisPanel } from '@/components/CallAnalysisPanel';
import { FollowUpPlanPanel } from '@/components/FollowUpPlanPanel';
import { CallAnalysis, transcriptAnalysisService, AnalysisEngine } from '@/services/transcriptAnalysisService';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';
import { NavigationMenu } from '@/components/NavigationMenu';

export const CallAnalysisPage: React.FC = () => {
  const { callId } = useParams<{ callId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [analysis, setAnalysis] = useState<CallAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [retryingAnalysis, setRetryingAnalysis] = useState(false);
  const [callData, setCallData] = useState<any>(null);
  const [signedAudioUrl, setSignedAudioUrl] = useState<string | null>(null);
  const [regeneratingTranscript, setRegeneratingTranscript] = useState(false);
  const [transcriptionProvider, setTranscriptionProvider] = useState(() => 
    localStorage.getItem('transcriptionProvider') || 'assemblyai'
  );
  const [analysisEngine, setAnalysisEngine] = useState<AnalysisEngine>(() => 
    (localStorage.getItem('analysisEngine') as AnalysisEngine) || 'auto'
  );

  useEffect(() => {
    if (callId && user) {
      loadCallData();
    }
  }, [callId, user]);

  // Ensure analysis runs after call data is available to avoid race condition
  useEffect(() => {
    if (callId && user && callData) {
      loadAnalysis();
    }
  }, [callId, user, callData]);

  const loadCallData = async () => {
    if (!callId) return;
    
    try {
      const { data, error } = await supabase
        .from('call_records')
        .select('*')
        .eq('id', callId)
        .single();
      
      if (error) throw error;
      setCallData(data);

      // Create signed URL for audio playback if available
      if (data.audio_file_url) {
        try {
          const { data: signed, error: signError } = await supabase.storage
            .from('call-recordings')
            .createSignedUrl(data.audio_file_url, 60 * 60);
          if (signError) throw signError;
          setSignedAudioUrl(signed?.signedUrl || null);
        } catch (e) {
          console.warn('Failed to create signed audio URL:', e);
          setSignedAudioUrl(null);
        }
      } else {
        setSignedAudioUrl(null);
      }
    } catch (error) {
      console.error('Failed to load call data:', error);
    }
  };

  const loadAnalysis = async () => {
    if (!callId || !user) return;
    
    setIsAnalyzing(true);
    try {
      // First try to get stored analysis
      const storedAnalysis = await transcriptAnalysisService.getStoredAnalysis(callId);
      
      if (storedAnalysis) {
        console.log('Loading stored analysis for', callId);
        setAnalysis(storedAnalysis);
      } else if (callData?.transcript && callData.transcript !== 'Transcribing audio...' && !callData.transcript.includes('failed')) {
        console.log('No stored analysis found, calling LLM for', callId);
        // If no stored analysis, trigger new analysis
        const result = await transcriptAnalysisService.analyzeTranscript(
          callData.transcript,
          callData.customer_name,
          (user as any).user_metadata?.salesperson_name || 'Provider',
          callId,
          user.id,
          analysisEngine,
          callData.vendor_insights
        );
        setAnalysis(result);
      }
    } catch (error) {
      console.error('Failed to analyze transcript:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRetryAnalysis = async () => {
    if (!callId || !callData?.transcript || !user) return;
    
    setRetryingAnalysis(true);
    try {
      // Force new analysis by bypassing stored analysis
      const result = await transcriptAnalysisService.analyzeTranscript(
        callData.transcript,
        callData.customer_name,
        (user as any).user_metadata?.salesperson_name || 'Provider',
        callId,
        user.id,
        analysisEngine,
        callData.vendor_insights
      );
      setAnalysis(result);
    } catch (error) {
      console.error('Failed to retry analysis:', error);
    } finally {
      setRetryingAnalysis(false);
    }
  };

  const convertBlobToBase64 = async (blob: Blob) => {
    const arrayBuffer = await blob.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    let base64String = '';
    const chunkSize = 8192;
    for (let i = 0; i < uint8Array.length; i += chunkSize) {
      const chunk = uint8Array.slice(i, i + chunkSize);
      base64String += btoa(String.fromCharCode(...chunk));
    }
    return base64String;
  };

  const handleRetryTranscriptionFromChunks = async () => {
    if (!callId || !user) return;
    setRegeneratingTranscript(true);
    try {
      const salespersonName = (user as any).user_metadata?.salesperson_name || 'Provider';
      
      // Check if chunks exist
      const { data: chunks, error: chunksError } = await supabase
        .from('call_chunks')
        .select('*')
        .eq('call_record_id', callId)
        .order('chunk_number');

      if (chunksError) throw chunksError;
      if (!chunks || chunks.length === 0) {
        throw new Error('No audio chunks found for this call. Cannot retry transcription.');
      }

      // Get customer name from chunks if not in call_data
      const customerName = callData?.customer_name || 'Customer';

      toast.success(`Found ${chunks.length} chunks. Attempting transcription...`);

      const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
      
      const payload = await buildTranscriptionPayload({
        callId,
        salespersonName,
        customerName,
        organizationId: (user as any)?.organization_id,
        overrideProvider: transcriptionProvider as 'deepgram' | 'assemblyai', // Use selected provider as override
      });

      // Invoke edge function with callId - it will assemble chunks on backend
      const { data, error } = await supabase.functions.invoke('transcribe-audio-v2', {
        body: payload,
      });

      if (error) throw error;
      if (!data?.success) throw new Error(data?.error || 'Transcription failed');

      toast.success('Transcription successful! Reloading call data...');
      
      // Reload call data to get updated transcript
      await loadCallData();
      await loadAnalysis();
    } catch (e) {
      console.error('Failed to retry transcription from chunks:', e);
      toast.error(`Transcription retry failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setRegeneratingTranscript(false);
    }
  };

  const handleRegenerateTranscript = async () => {
    if (!callId || !user || !callData?.audio_file_url || !callData?.customer_name) return;
    setRegeneratingTranscript(true);
    try {
      const salespersonName = (user as any).user_metadata?.salesperson_name || 'Provider';
      
      const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
      
      const payload = await buildTranscriptionPayload({
        storagePath: callData.audio_file_url,
        callId,
        salespersonName,
        customerName: callData.customer_name,
        organizationId: (user as any)?.organization_id,
        overrideProvider: transcriptionProvider as 'deepgram' | 'assemblyai', // Use selected provider as override
      });
      
      // Send storage path directly to the edge function for server-side download
      const { data, error } = await supabase.functions.invoke('transcribe-audio-v2', {
        body: payload,
      });

      if (error) throw error;
      if (!data?.success) throw new Error(data?.error || 'Transcription failed');

      // Reload call data to get updated transcript
      await loadCallData();
      
      // Show success message
      toast.success(`Transcript successfully regenerated using ${transcriptionProvider.charAt(0).toUpperCase() + transcriptionProvider.slice(1)}`);
    } catch (e) {
      console.error('Failed to regenerate transcript:', e);
      toast.error(`Failed to regenerate transcript: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setRegeneratingTranscript(false);
    }
  };

  const handleTranscriptionProviderChange = (provider: string) => {
    setTranscriptionProvider(provider);
    localStorage.setItem('transcriptionProvider', provider);
  };

  const handleAnalysisEngineChange = (engine: AnalysisEngine) => {
    setAnalysisEngine(engine);
    localStorage.setItem('analysisEngine', engine);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  if (!callData) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <Button variant="ghost" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <NavigationMenu />
          </div>
          <div className="text-center py-8">Loading call data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Call Analysis - {callData.customer_name}</h1>
              <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                <span>Duration: {formatDuration(callData.duration_seconds || 0)}</span>
                <span>•</span>
                <span>Recorded: {formatDate(callData.created_at)}</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Transcription Provider Selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Transcription:</span>
              <Select value={transcriptionProvider} onValueChange={handleTranscriptionProviderChange}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                  <SelectItem value="deepgram">Deepgram</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Analysis Engine Selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Analysis:</span>
              <Select value={analysisEngine} onValueChange={handleAnalysisEngineChange}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto (Vendor + LLM)</SelectItem>
                  <SelectItem value="vendor">Vendor Only</SelectItem>
                  <SelectItem value="llm">LLM Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Retry Transcription Button - shown when transcript failed or is missing */}
            {(!callData.transcript || 
              callData.transcript.includes('failed') || 
              callData.transcript === 'Transcribing audio...' ||
              callData.transcript === 'Recording in progress...') && (
              <Button
                onClick={handleRetryTranscriptionFromChunks}
                variant="default"
                disabled={regeneratingTranscript}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${regeneratingTranscript ? 'animate-spin' : ''}`} />
                {regeneratingTranscript ? 'Retrying...' : 'Retry Transcription'}
              </Button>
            )}

            {/* Retry Analysis Button */}
            {callData.transcript && 
             !callData.transcript.includes('failed') && 
             callData.transcript !== 'Transcribing audio...' && 
             callData.transcript !== 'Recording in progress...' && (
              <Button
                onClick={handleRetryAnalysis}
                variant="outline"
                disabled={retryingAnalysis}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${retryingAnalysis ? 'animate-spin' : ''}`} />
                {retryingAnalysis ? 'Retrying Analysis...' : 'Retry Analysis'}
              </Button>
            )}
            <NavigationMenu />
          </div>
        </div>

        {/* Analysis Content */}
        <div className="space-y-6">
          <div className="bg-card rounded-lg border p-6">
            <CallAnalysisPanel 
              analysis={analysis} 
              isLoading={isAnalyzing} 
              transcript={callData?.transcript} 
              audioUrl={signedAudioUrl || undefined} 
              onRegenerateTranscript={handleRegenerateTranscript} 
              regeneratingTranscript={regeneratingTranscript}
              callDuration={callData?.duration_seconds || 0}
              diarizationSegments={callData?.diarization_segments}
              speakerMapping={callData?.speaker_mapping}
              callRecordId={callId}
              customerName={callData?.customer_name}
              onSpeakerMappingUpdate={async (newMapping) => {
                try {
                  const { error } = await supabase
                    .from('call_records')
                    .update({ speaker_mapping: newMapping })
                    .eq('id', callId);
                  
                  if (error) throw error;
                  
                  // Update local state
                  setCallData(prev => prev ? { ...prev, speaker_mapping: newMapping } : null);
                  toast.success('Speaker mapping updated successfully');
                } catch (error) {
                  console.error('Failed to update speaker mapping:', error);
                  toast.error('Failed to update speaker mapping');
                }
              }}
            />
          </div>
          
          <FollowUpPlanPanel
            callId={callId!}
            transcript={callData?.transcript || ''}
            analysisData={analysis}
            customerName={callData?.customer_name || ''}
            salespersonName={(user as any)?.user_metadata?.salesperson_name || 'Salesperson'}
          />
        </div>
      </div>
    </div>
  );
};