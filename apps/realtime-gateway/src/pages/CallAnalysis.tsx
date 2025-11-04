import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { CallAnalysisPanel } from '@/components/CallAnalysisPanel';
import { FollowUpPlanPanel } from '@/components/FollowUpPlanPanel';
import { ContactPreferencesPanel } from '@/components/ContactPreferencesPanel';
import { CallAnalysis, transcriptAnalysisService, AnalysisEngine } from '@/services/transcriptAnalysisService';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';
import { NavigationMenu } from '@/components/NavigationMenu';
import { useCenterSession } from '@/hooks/useCenterSession';

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
  const [diarizationStatus, setDiarizationStatus] = useState<string>('');
  const [transcriptionProvider, setTranscriptionProvider] = useState(() => 
    localStorage.getItem('transcriptionProvider') || 'assemblyai'
  );
  const [analysisEngine, setAnalysisEngine] = useState<AnalysisEngine>(() => 
    (localStorage.getItem('analysisEngine') as AnalysisEngine) || 'auto'
  );
  const { availableCenters } = useCenterSession();

  // Local state for search/filters
  const [searchPatient, setSearchPatient] = useState('');
  const [searchSalesperson, setSearchSalesperson] = useState('all');
  const [searchCenter, setSearchCenter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [salespeople, setSalespeople] = useState<string[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  // Persist filters across navigation
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('analysisFilters');
      if (raw) {
        const obj = JSON.parse(raw);
        if (typeof obj.searchPatient === 'string') setSearchPatient(obj.searchPatient);
        if (typeof obj.searchSalesperson === 'string') setSearchSalesperson(obj.searchSalesperson);
        if (typeof obj.searchCenter === 'string') setSearchCenter(obj.searchCenter);
        if (typeof obj.dateFrom === 'string') setDateFrom(obj.dateFrom);
        if (typeof obj.dateTo === 'string') setDateTo(obj.dateTo);
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      const payload = {
        searchPatient,
        searchSalesperson,
        searchCenter,
        dateFrom,
        dateTo,
      };
      sessionStorage.setItem('analysisFilters', JSON.stringify(payload));
    } catch {}
  }, [searchPatient, searchSalesperson, searchCenter, dateFrom, dateTo]);

  // Hydrate from session cache on first mount to avoid refetch/re-analyze when navigating back
  useEffect(() => {
    if (!callId) return;
    try {
      const cachedCall = sessionStorage.getItem(`callData:${callId}`);
      if (cachedCall) {
        const parsed = JSON.parse(cachedCall);
        setCallData(parsed);
      }
      const cachedAudio = sessionStorage.getItem(`signedAudioUrl:${callId}`);
      if (cachedAudio) setSignedAudioUrl(cachedAudio);
      const cachedAnalysis = sessionStorage.getItem(`analysis:${callId}`);
      if (cachedAnalysis) setAnalysis(JSON.parse(cachedAnalysis));
    } catch (e) {
      // ignore cache errors
    }
  // run once per callId
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callId]);

  // Persist to session cache when data updates
  useEffect(() => {
    if (!callId) return;
    try {
      if (callData) sessionStorage.setItem(`callData:${callId}`, JSON.stringify(callData));
      if (signedAudioUrl) sessionStorage.setItem(`signedAudioUrl:${callId}`, signedAudioUrl);
    } catch {}
  }, [callId, callData, signedAudioUrl]);

  useEffect(() => {
    if (!callId) return;
    try {
      if (analysis) sessionStorage.setItem(`analysis:${callId}`, JSON.stringify(analysis));
    } catch {}
  }, [callId, analysis]);

  useEffect(() => {
    if (callId && user) {
      // If we already have cached callData, refresh in background without clearing state
      if (callData) {
        (async () => {
          await loadCallData();
        })();
      } else {
        loadCallData();
      }
    }
  }, [callId, user]);

  // Ensure analysis runs after call data is available to avoid race condition
  useEffect(() => {
    if (callId && user && callData) {
      // Avoid re-analyzing if we already have analysis in state (from cache)
      if (!analysis) {
        loadAnalysis();
      }
    }
  }, [callId, user, callData]);

  const loadCallData = async () => {
    if (!callId) {
      console.log('[CallAnalysis] loadCallData: No callId, skipping');
      return;
    }
    
    console.log('[CallAnalysis] loadCallData: Starting for callId:', callId);
    
    try {
      const { data, error } = await supabase
        .from('call_records')
        .select('*')
        .eq('id', callId)
        .single();
      
      if (error) {
        console.error('[CallAnalysis] loadCallData: Query error:', error);
        throw error;
      }
      
      if (!data) {
        console.warn('[CallAnalysis] loadCallData: No data returned from query');
        return;
      }
      
      // Log diarization status for debugging
      const hasDiarizationSegments = !!data?.diarization_segments;
      const diarizationSegmentsLength = Array.isArray(data?.diarization_segments) ? data.diarization_segments.length : 0;
      const transcriptPreview = data?.transcript?.substring(0, 100) || 'null';
      const transcriptContainsFailed = data?.transcript?.includes('failed') || false;
      
      console.log('[CallAnalysis] Loaded call data:', {
        id: data?.id,
        hasTranscript: !!data?.transcript,
        transcriptLength: data?.transcript?.length || 0,
        transcriptPreview,
        transcriptContainsFailed,
        hasDiarizationSegments,
        diarizationSegmentsType: typeof data?.diarization_segments,
        diarizationSegmentsLength,
        transcriptionProvider: data?.transcription_provider,
        status: data?.status,
        diarizationSegmentsPreview: Array.isArray(data?.diarization_segments) && data.diarization_segments.length > 0 ? 
          `First segment: ${JSON.stringify(data.diarization_segments[0]).substring(0, 100)}` : 'no segments'
      });
      
      // Also log key values directly for easier debugging
      console.log(`[CallAnalysis] KEY VALUES: hasDiarizationSegments=${hasDiarizationSegments}, diarizationSegmentsLength=${diarizationSegmentsLength}, transcriptContainsFailed=${transcriptContainsFailed}`);
      
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

  // Populate salespeople from search results to avoid permission-related 400s

  const executeSearch = async () => {
    setSearching(true);
    try {
      let query = supabase
        .from('call_records')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(25);

      if (searchPatient.trim()) {
        query = query.ilike('customer_name', `%${searchPatient.trim()}%`);
      }
      if (searchSalesperson && searchSalesperson !== 'all') {
        query = query.eq('salesperson_name', searchSalesperson);
      }
      if (searchCenter && searchCenter !== 'all') {
        query = query.eq('center_id', searchCenter);
      }
      if (dateFrom) {
        query = query.gte('created_at', new Date(dateFrom).toISOString());
      }
      if (dateTo) {
        const end = new Date(dateTo);
        end.setHours(23,59,59,999);
        query = query.lte('created_at', end.toISOString());
      }

      const { data, error } = await query;
      if (error) throw error;
      const rows = data || [];
      setResults(rows);
      // derive distinct salespeople from results
      const distinctSP = Array.from(new Set(rows.map((r: any) => r?.salesperson_name).filter((v: any) => typeof v === 'string' && v.trim().length > 0))).sort();
      setSalespeople(distinctSP);
    } catch (e) {
      setResults([]);
    } finally {
      setSearching(false);
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
    setDiarizationStatus('Checking existing audio chunks...');
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
        setDiarizationStatus('No chunks found; falling back to server-side transcription from storage path...');
        throw new Error('No audio chunks found for this call. Cannot retry transcription.');
      }

      // Get customer name from chunks if not in call_data
      const customerName = callData?.customer_name || 'Customer';

      toast.success(`Found ${chunks.length} chunks. Attempting transcription with diarization...`);
      setDiarizationStatus(`Found ${chunks.length} chunks. Requesting diarization from ${transcriptionProvider}...`);

      const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
      const { data: sess } = await supabase.auth.getSession();
      const token = sess.session?.access_token;
      const resp = await fetch(`${API_BASE_URL}/api/transcribe/call-record/${encodeURIComponent(callId)}?enable_diarization=true&provider=${encodeURIComponent(transcriptionProvider)}`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data?.success) {
        const msg = data?.detail || data?.error || resp.statusText || 'Transcription failed';
        setDiarizationStatus(`Diarization failed: ${msg}`);
        throw new Error(msg);
      }

      toast.success('Transcription + diarization successful! Reloading call data...');
      setDiarizationStatus('Saving segments and refreshing...');
      
      // Reload call data to get updated transcript
      await loadCallData();
      await loadAnalysis();
      setDiarizationStatus('Diarization complete.');
    } catch (e) {
      console.error('Failed to retry transcription from chunks:', e);
      toast.error(`Transcription retry failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
      if (e instanceof Error) setDiarizationStatus(`Diarization failed: ${e.message}`);
    } finally {
      setRegeneratingTranscript(false);
      setTimeout(() => setDiarizationStatus(''), 8000);
    }
  };

  const handleRegenerateTranscript = async () => {
    console.log('[handleRegenerateTranscript] Called with:', {
      callId,
      hasUser: !!user,
      hasAudioUrl: !!callData?.audio_file_url,
      hasCustomerName: !!callData?.customer_name,
      transcriptionProvider
    });
    
    if (!callId || !user || !callData?.audio_file_url || !callData?.customer_name) {
      console.error('[handleRegenerateTranscript] Missing required data:', {
        callId: !!callId,
        user: !!user,
        audio_file_url: !!callData?.audio_file_url,
        customer_name: !!callData?.customer_name
      });
      toast.error('Missing required data to regenerate transcript');
      return;
    }
    
    setRegeneratingTranscript(true);
    setDiarizationStatus(`Submitting audio to ${transcriptionProvider} for diarization...`);
    
    try {
      const salespersonName = (user as any).user_metadata?.salesperson_name || 'Provider';
      
      const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
      const { data: sess } = await supabase.auth.getSession();
      const token = sess.session?.access_token;
      
      const url = `${API_BASE_URL}/api/transcribe/call-record/${encodeURIComponent(callId)}?enable_diarization=true&provider=${encodeURIComponent(transcriptionProvider)}`;
      console.log('[handleRegenerateTranscript] Sending POST to:', url);
      console.log('[handleRegenerateTranscript] Headers:', { Authorization: token ? 'Bearer ***' : 'none' });
      
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      console.log('[handleRegenerateTranscript] Response status:', resp.status);
      
      const data = await resp.json().catch(() => null);
      console.log('[handleRegenerateTranscript] Response data:', JSON.stringify(data, null, 2));
      
      if (!resp.ok || !data?.success) {
        const msg = data?.detail || data?.error || resp.statusText || 'Transcription failed';
        setDiarizationStatus(`Diarization failed: ${msg}`);
        throw new Error(msg);
      }

      // Reload call data to get updated transcript
      await loadCallData();
      
      // Show success message
      toast.success(`Transcript + diarization submitted to ${transcriptionProvider}.`);
      setDiarizationStatus('Diarization complete.');
    } catch (e) {
      console.error('[handleRegenerateTranscript] Error:', e);
      toast.error(`Failed to regenerate transcript: ${e instanceof Error ? e.message : 'Unknown error'}`);
      if (e instanceof Error) setDiarizationStatus(`Diarization failed: ${e.message}`);
    } finally {
      setRegeneratingTranscript(false);
      setTimeout(() => setDiarizationStatus(''), 8000);
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
            
            {/* Regenerate Transcript with Diarization Button - always visible if we have audio */}
            {callData.audio_file_url && (
              <Button
                onClick={handleRegenerateTranscript}
                variant="outline"
                disabled={regeneratingTranscript}
                className="flex items-center gap-2"
                title="Regenerate transcript with speaker diarization"
              >
                <RefreshCw className={`h-4 w-4 ${regeneratingTranscript ? 'animate-spin' : ''}`} />
                {regeneratingTranscript ? 'Regenerating...' : 'Regenerate with Diarization'}
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

        {/* Two-pane content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left: User Details / Preferences */}
          <div className="col-span-12 lg:col-span-4 space-y-6">
            {/* Find Calls / Filters */}
            <div className="bg-card rounded-lg border p-6 space-y-4">
              <div className="text-lg font-semibold">Find Calls</div>
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Patient</Label>
                  <Input
                    placeholder="Search by patient name"
                    value={searchPatient}
                    onChange={(e) => setSearchPatient(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Salesperson</Label>
                  <Select value={searchSalesperson} onValueChange={setSearchSalesperson}>
                    <SelectTrigger>
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      {salespeople.map((sp) => (
                        <SelectItem key={sp} value={sp}>{sp}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Center</Label>
                  <Select value={searchCenter} onValueChange={setSearchCenter}>
                    <SelectTrigger>
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      {(availableCenters || []).map((c: any) => (
                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">From</Label>
                    <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">To</Label>
                    <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={executeSearch} disabled={searching}>
                    {searching ? 'Searching...' : 'Search'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSearchPatient('');
                      setSearchSalesperson('all');
                      setSearchCenter('all');
                      setDateFrom('');
                      setDateTo('');
                      setResults([]);
                    }}
                  >
                    Clear
                  </Button>
                </div>
              </div>
              {/* Results */}
              <div className="mt-4 space-y-2 max-h-64 overflow-auto">
                {results.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No results</div>
                ) : (
                  results.map((r) => (
                    <div key={r.id} className="p-2 rounded border flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">{r.customer_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatDate(r.created_at)}{r.center_id ? ` • Center: ${r.center_id}` : ''}
                        </div>
                      </div>
                      <Button size="sm" variant="outline" onClick={() => navigate(`/analysis/${r.id}`)}>Open</Button>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-card rounded-lg border p-6">
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">Customer</div>
                <div className="text-lg font-semibold">{callData.customer_name}</div>
              </div>
            </div>
            <ContactPreferencesPanel
              callRecordId={callId!}
              customerName={callData.customer_name || ''}
            />
          </div>

          {/* Right: Analysis */}
          <div className="col-span-12 lg:col-span-8 space-y-6">
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
                diarizationStatus={diarizationStatus}
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
    </div>
  );
};