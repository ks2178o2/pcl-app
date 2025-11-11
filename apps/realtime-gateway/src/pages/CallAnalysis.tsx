import React, { useState, useEffect, useRef } from 'react';
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
import { getApiUrl } from '@/utils/apiConfig';

export const CallAnalysisPage: React.FC = () => {
  const { callId } = useParams<{ callId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [analysis, setAnalysis] = useState<CallAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [retryingAnalysis, setRetryingAnalysis] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<{
    stage: 'waiting-transcript' | 'analyzing' | 'generating-insights' | 'complete' | 'error';
    message: string;
    progress: number; // 0-100
  } | null>(null);
  const [callData, setCallData] = useState<any>(null);
  const transcriptPollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const transcriptionTriggeredRef = useRef<boolean>(false); // Track if transcription has been triggered for this call
  const loadAnalysisTriggeredRef = useRef<string>(''); // Track if loadAnalysis has been triggered for this callId+analysis combo
  const isLoadingAnalysisRef = useRef<boolean>(false); // Track loading state to prevent concurrent calls
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
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

  // Use stable user ID to prevent re-running on user object reference changes
  const userId = user?.id;
  useEffect(() => {
    if (callId && userId) {
      // If we already have cached callData, refresh in background without clearing state
      if (callData && callData.id === callId) {
        // Already loaded for this callId, skip
        return;
      }
      if (callData) {
        (async () => {
          await loadCallData();
        })();
      } else {
        loadCallData();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callId, userId]);

  // Cleanup polling intervals on unmount
  useEffect(() => {
    return () => {
      if (transcriptPollIntervalRef.current) {
        clearInterval(transcriptPollIntervalRef.current);
        transcriptPollIntervalRef.current = null;
      }
    };
  }, []);

  // Reset trigger flags when callId changes
  useEffect(() => {
    transcriptionTriggeredRef.current = false;
    loadAnalysisTriggeredRef.current = '';
  }, [callId]);

  // Ensure analysis runs after call data is available to avoid race condition
  // Use stable user ID to prevent re-running on user object reference changes
  useEffect(() => {
    // Create a unique key for this callId+analysis state to prevent duplicate triggers
    const triggerKey = `${callId}-${!!analysis}-${!!isLoadingAnalysis}`;
    
    if (callId && userId && callData && !analysis && !isLoadingAnalysis && loadAnalysisTriggeredRef.current !== triggerKey) {
      loadAnalysisTriggeredRef.current = triggerKey;
      loadAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callId, userId, callData?.id, analysis, isLoadingAnalysis]);

  // Poll for analysis completion when analyzing
  useEffect(() => {
    if (!isAnalyzing || !callId || analysis) return;

    const pollInterval = setInterval(async () => {
      try {
        const storedAnalysis = await transcriptAnalysisService.getStoredAnalysis(callId);
        if (storedAnalysis) {
          console.log('✅ Analysis completed - found in database');
          setAnalysis(storedAnalysis);
          setAnalysisStatus({
            stage: 'complete',
            message: 'Analysis complete!',
            progress: 100
          });
          setIsAnalyzing(false);
        }
      } catch (error) {
        console.error('Error polling for analysis:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [isAnalyzing, callId, analysis]);

  const loadCallData = async () => {
    if (!callId) {
      return;
    }
    
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
      
      // Loaded call data successfully
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
    
    // Prevent multiple simultaneous calls using ref (more reliable than state)
    if (isLoadingAnalysisRef.current) {
      return;
    }
    
    isLoadingAnalysisRef.current = true;
    setIsLoadingAnalysis(true);
    
    // Clean up any existing polling interval
    if (transcriptPollIntervalRef.current) {
      clearInterval(transcriptPollIntervalRef.current);
      transcriptPollIntervalRef.current = null;
    }
    
    // First, ensure we have callData - if not, load it first
    if (!callData) {
      await loadCallData();
      isLoadingAnalysisRef.current = false;
      setIsLoadingAnalysis(false);
      // Wait a moment for state to update, then retry only if not already triggered
      const triggerKey = `${callId}-${false}-${false}`;
      if (loadAnalysisTriggeredRef.current !== triggerKey) {
        setTimeout(() => {
          if (!isLoadingAnalysisRef.current) {
            loadAnalysis();
          }
        }, 500);
      }
      return;
    }
    
    // Check transcript status - fetch fresh from DB to be sure
    
    try {
      // Check transcription status - fetch vendor_insights to get uploadId
      // Note: vendor_insights is JSONB, so it should be queryable
      const { data: freshData, error: freshDataError } = await supabase
        .from('call_records')
        .select('transcript, audio_file_url, recording_complete, vendor_insights')
        .eq('id', callId)
        .single();
      
      if (freshDataError) {
        console.error('[loadAnalysis] Error fetching transcript status:', freshDataError);
        // Fall back to callData if query fails
        if (!callData) {
          throw freshDataError;
        }
      }
      
      const transcript = freshData?.transcript || callData?.transcript;
      const hasAudioFile = !!freshData?.audio_file_url;
      const recordingComplete = freshData?.recording_complete;
      const vendorInsights = freshData?.vendor_insights || callData?.vendor_insights;
      const uploadId = typeof vendorInsights === 'object' && vendorInsights !== null ? (vendorInsights as any)?.transcription_upload_id : null;
      
      // If no uploadId but transcript is still placeholder, trigger transcription
      // Note: We trigger even if audio_file_url is missing, as the backend may handle it differently
      // IMPORTANT: Only trigger once per call to prevent infinite loops
      const shouldTriggerTranscription = !uploadId && 
                                        transcript === 'Transcribing audio...' && 
                                        user && 
                                        !isLoadingAnalysis &&
                                        !transcriptionTriggeredRef.current &&
                                        callId;
      
      if (shouldTriggerTranscription) {
        transcriptionTriggeredRef.current = true; // Mark as triggered to prevent retries
        try {
          setIsLoadingAnalysis(true);
          const { data: sessionData } = await supabase.auth.getSession();
          const token = sessionData?.session?.access_token;
          if (token) {
            const resp = await fetch(getApiUrl(`/api/transcribe/call-record/${callId}?enable_diarization=true`), {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
            });
            if (resp.ok) {
              const respJson = await resp.json();
              const newUploadId = respJson?.upload_id || respJson?.transcript_job_id;
              
              // Store uploadId in vendor_insights
              if (newUploadId) {
                const updatedInsights = {
                  ...(typeof vendorInsights === 'object' && vendorInsights !== null ? vendorInsights : {}),
                  transcription_upload_id: newUploadId
                };
                await supabase
                  .from('call_records')
                  .update({ vendor_insights: updatedInsights })
                  .eq('id', callId);
                
                // Reload fresh data to get the uploadId
                await loadCallData();
              }
            } else {
              // Transcription trigger failed - reset flag so it can be retried later
              transcriptionTriggeredRef.current = false;
              const errorText = await resp.text().catch(() => 'Unknown error');
              console.error('[loadAnalysis] Failed to trigger transcription:', resp.status, errorText);
            }
          }
        } catch (triggerError) {
          // Transcription trigger failed - reset flag so it can be retried later
          transcriptionTriggeredRef.current = false;
          console.error('[loadAnalysis] Error triggering transcription:', triggerError);
        } finally {
          isLoadingAnalysisRef.current = false;
          setIsLoadingAnalysis(false);
        }
      }
      
      // Check if transcription is already in progress
      const isTranscriptionInProgress = transcript === 'Transcribing audio...' && 
                                       (transcriptionProvider || hasAudioFile);
      
      // Check if transcript is ready - must not be placeholder text
      // "Transcribing audio..." is exactly 21 characters, so we check for > 21 to ensure it's not placeholder
      const isTranscriptReady = transcript && 
                                typeof transcript === 'string' &&
                                transcript.trim() !== '' &&
                                transcript.trim() !== 'Transcribing audio...' &&
                                !transcript.toLowerCase().includes('failed') &&
                                transcript.trim().length > 21; // Must be longer than placeholder text (21 chars)
      
      // Check if transcript is ready
      
      if (!isTranscriptReady) {
        // Transcript not ready, starting polling
        const initialStatus = {
          stage: 'waiting-transcript' as const,
          message: 'Waiting for transcript to be ready...',
          progress: 10
        };
        setAnalysisStatus(initialStatus);
        setIsAnalyzing(true);
        
        // Start polling for transcript - use reasonable polling interval
        let pollCount = 0;
        const pollIntervalMs = 5000; // Poll every 5 seconds instead of 2 seconds
        const maxPolls = 60; // 5 minutes max (60 * 5 seconds = 300 seconds)
        
        // Clear any existing interval first
        if (transcriptPollIntervalRef.current) {
          clearInterval(transcriptPollIntervalRef.current);
        }
        
        transcriptPollIntervalRef.current = setInterval(async () => {
          pollCount++;
          try {
            // Fetch transcript from database
            const { data: pollData, error: pollError } = await supabase
              .from('call_records')
              .select('transcript')
              .eq('id', callId)
              .single();
            
            if (pollError) {
              console.error('[loadAnalysis] Error polling transcript:', pollError);
              // Continue with status endpoint check even if DB query fails
            }
            
            // If we have uploadId, query the status endpoint for actual progress
            let actualProgress: number | null = null;
            let statusMessage = 'Waiting for transcript to be ready...';
            let statusTranscript: string | null = null; // Transcript from status endpoint
            if (uploadId && user) {
              try {
                const { data: sessionData } = await supabase.auth.getSession();
                const token = sessionData?.session?.access_token;
                if (token) {
                  const statusResp = await fetch(getApiUrl(`/api/transcribe/status/${uploadId}`), {
                    headers: { Authorization: `Bearer ${token}` },
                  });
                  if (statusResp.ok) {
                    const statusJson = await statusResp.json();
                    actualProgress = statusJson?.progress !== null && statusJson?.progress !== undefined ? statusJson.progress : null;
                    statusTranscript = statusJson?.transcript || null;
                    
                    if (statusJson?.status === 'processing' && actualProgress !== null) {
                      statusMessage = `Transcribing audio... ${Math.round(actualProgress)}% complete`;
                    } else if (statusJson?.status === 'completed') {
                      statusMessage = 'Transcription complete!';
                      actualProgress = 100;
                      // If we have a transcript from the status endpoint, update the database immediately
                      if (statusTranscript && statusTranscript.trim() && statusTranscript.trim() !== 'Transcribing audio...') {
                        // Got completed transcript from status endpoint, updating database
                        try {
                          await supabase
                            .from('call_records')
                            .update({ transcript: statusTranscript })
                            .eq('id', callId);
                          // Database updated with transcript from status endpoint
                        } catch (updateError) {
                          console.error('[loadAnalysis] Failed to update database with transcript:', updateError);
                        }
                      }
                    } else if (statusJson?.status === 'failed') {
                      statusMessage = `Transcription failed: ${statusJson?.error || 'Unknown error'}`;
                      actualProgress = 0;
                    }
                  }
                }
              } catch (statusError) {
                // If status endpoint fails, fall back to estimated progress
                console.warn('[loadAnalysis] Failed to fetch transcription status:', statusError);
              }
            }
            
            // Determine if we have real progress from backend or need to show waiting state
            // NOTE: Backend only provides stage markers (5=starting, 50=processing, 100=done), 
            // NOT real incremental transcription progress. The transcription services (Deepgram/AssemblyAI)
            // don't provide real-time progress updates in our current implementation.
            const hasBackendProgress = actualProgress !== null && actualProgress >= 0;
            
            // Use backend progress if available, otherwise show minimal progress to indicate waiting
            // Don't fake progress by incrementing - be honest that we're waiting
            let displayProgress: number;
            let progressType: 'real' | 'waiting' = 'waiting';
            
            if (hasBackendProgress) {
              displayProgress = actualProgress;
              // Backend provides stage markers: 5 (starting), 50 (processing), 100 (done)
              // These are not real transcription progress, just status stages
              progressType = 'real';
              if (pollCount === 1 || pollCount % 6 === 0) {
                // Backend progress update
              }
            } else {
              // No progress from backend - show fixed minimal progress to indicate we're waiting
              // Don't increment it - that would be misleading
              displayProgress = 10; // Fixed at 10% to show activity, not fake progress
              progressType = 'waiting';
            }
            
            // Check if transcript is ready - prefer status endpoint transcript, then database
            const pollTranscript = statusTranscript || pollData?.transcript;
            const isPollTranscriptReady = pollTranscript && 
                                         typeof pollTranscript === 'string' &&
                                         pollTranscript.trim() !== '' &&
                                         pollTranscript.trim() !== 'Transcribing audio...' &&
                                         !pollTranscript.toLowerCase().includes('failed') &&
                                         pollTranscript.trim().length > 21; // Must be longer than placeholder (21 chars)
            
            // Polling for transcript (verbose logging disabled to reduce console spam)
            // Only log every 30 seconds (every 6th poll) for minimal feedback
            if (pollCount % 6 === 0) {
              console.log(`[loadAnalysis] Polling for transcript... (${pollCount}/${maxPolls})`);
            }
            
            // Update progress bar periodically to show we're still working
            if (pollCount % 3 === 0 || actualProgress !== null) {
              let finalMessage: string;
              
              if (hasBackendProgress) {
                // Use accurate message based on real backend progress
                if (actualProgress === 100) {
                  finalMessage = 'Transcription complete!';
                } else if (actualProgress >= 90) {
                  finalMessage = 'Finishing transcription...';
                } else if (actualProgress >= 70) {
                  finalMessage = 'Processing audio with transcription service...';
                } else if (actualProgress >= 50) {
                  finalMessage = 'Transcribing audio... (in progress)';
                } else if (actualProgress >= 30) {
                  finalMessage = 'Transcribing audio... (processing)';
                } else if (actualProgress >= 20) {
                  finalMessage = 'Transcription queued, starting soon...';
                } else if (actualProgress >= 10) {
                  finalMessage = 'Starting transcription...';
                } else {
                  finalMessage = statusMessage || 'Initializing transcription...';
                }
              } else if (uploadId) {
                // We have uploadId but no progress - backend may not be reporting incremental progress
                finalMessage = pollCount < 12  // First minute
                  ? 'Transcription in progress... (processing audio)' 
                  : pollCount < 24  // Second minute
                  ? 'Transcription is taking longer than usual. Still processing...'
                  : 'Transcription is still processing. This may take a few minutes for long recordings...';
              } else {
                // No uploadId - transcription started via direct endpoint (no progress tracking available)
                // Can only poll database for transcript completion
                finalMessage = pollCount < 12  // First minute
                  ? 'Transcription in progress... (no progress tracking available)' 
                  : pollCount < 24  // Second minute
                  ? 'Transcription is taking longer than usual. Still processing...'
                  : 'Transcription is still processing. This may take a few minutes for long recordings...';
              }
              
              if (pollCount === 1 || pollCount % 6 === 0) {
                // Progress update (verbose logging disabled)
              }
              
              setAnalysisStatus({
                stage: 'waiting-transcript',
                progress: displayProgress,
                message: finalMessage
              });
            }
            
            // Also check if status endpoint says completed (even if transcript not in DB yet)
            const statusSaysComplete = actualProgress === 100 && statusTranscript && statusTranscript.trim().length > 21;
            
            // Log detailed state for debugging (verbose logging disabled)
            
            if (isPollTranscriptReady || statusSaysComplete) {
              // Transcript ready, clearing interval and proceeding
              if (transcriptPollIntervalRef.current) {
                clearInterval(transcriptPollIntervalRef.current);
                transcriptPollIntervalRef.current = null;
              }
              isLoadingAnalysisRef.current = false;
              setIsLoadingAnalysis(false);
              
              // If we got transcript from status endpoint but DB doesn't have it yet, ensure DB is updated
              if (statusTranscript && (!pollData?.transcript || pollData.transcript === 'Transcribing audio...')) {
                try {
                  await supabase
                    .from('call_records')
                    .update({ transcript: statusTranscript })
                    .eq('id', callId);
                } catch (updateError) {
                  console.error('[loadAnalysis] Failed to update database:', updateError);
                }
              }
              
              // Reload call data and start analysis
              await loadCallData();
              // Continue with analysis after a brief delay, but only if not already loading
              setTimeout(() => {
                if (!isLoadingAnalysisRef.current) {
                  loadAnalysis();
                }
              }, 500);
            } else if (pollCount >= maxPolls) {
              console.warn('[loadAnalysis] Max polls reached, stopping...');
              if (transcriptPollIntervalRef.current) {
                clearInterval(transcriptPollIntervalRef.current);
                transcriptPollIntervalRef.current = null;
              }
              isLoadingAnalysisRef.current = false;
              setIsLoadingAnalysis(false);
              setAnalysisStatus({
                stage: 'error',
                message: 'Transcript is taking longer than expected. The transcription may have failed. Please try refreshing or retrying transcription from the call list.',
                progress: 0
              });
            }
          } catch (error) {
              console.error('[loadAnalysis] Error polling for transcript:', error);
              if (pollCount >= maxPolls) {
                if (transcriptPollIntervalRef.current) {
                  clearInterval(transcriptPollIntervalRef.current);
                  transcriptPollIntervalRef.current = null;
                }
                isLoadingAnalysisRef.current = false;
                setIsLoadingAnalysis(false);
              }
            }
        }, pollIntervalMs);
        
        return;
      }
    } catch (error) {
      console.error('[loadAnalysis] Error checking transcript:', error);
      isLoadingAnalysisRef.current = false;
      setIsLoadingAnalysis(false);
      // Fall through to try with existing callData
      return;
    }
    
    // Transcript is ready, proceeding with analysis
    setIsAnalyzing(true);
    setAnalysisStatus({
      stage: 'analyzing',
      message: 'Checking for existing analysis...',
      progress: 20
    });
    
    try {
      // First try to get stored analysis
      const storedAnalysis = await transcriptAnalysisService.getStoredAnalysis(callId);
      
      if (storedAnalysis) {
        console.log('Loading stored analysis for', callId);
        setAnalysis(storedAnalysis);
        setAnalysisStatus({
          stage: 'complete',
          message: 'Analysis loaded!',
          progress: 100
        });
        setIsAnalyzing(false);
        setIsLoadingAnalysis(false);
      } else if (callData?.transcript && callData.transcript !== 'Transcribing audio...' && !callData.transcript.includes('failed')) {
        console.log('No stored analysis found, calling LLM for', callId);
        setAnalysisStatus({
          stage: 'generating-insights',
          message: 'Generating analysis with AI... This may take 30-60 seconds.',
          progress: 40
        });
        
        // If no stored analysis, trigger new analysis
        // Note: This is async and may take time, so we'll poll for completion
        transcriptAnalysisService.analyzeTranscript(
          callData.transcript,
          callData.customer_name,
          (user as any).user_metadata?.salesperson_name || 'Provider',
          callId,
          user.id,
          analysisEngine,
          callData.vendor_insights
        ).then((result) => {
          setAnalysis(result);
          setAnalysisStatus({
            stage: 'complete',
            message: 'Analysis complete!',
            progress: 100
          });
          setIsAnalyzing(false);
          isLoadingAnalysisRef.current = false;
          setIsLoadingAnalysis(false);
        }).catch((error) => {
          console.error('Failed to analyze transcript:', error);
          setAnalysisStatus({
            stage: 'error',
            message: 'Analysis failed. Please try again.',
            progress: 0
          });
          setIsAnalyzing(false);
          isLoadingAnalysisRef.current = false;
          setIsLoadingAnalysis(false);
        });
        
        // Update progress while waiting - use functional updates to avoid stale closures
        setTimeout(() => {
          setAnalysisStatus(prev => {
            if (prev && prev.stage === 'generating-insights') {
              return {
                ...prev,
                message: 'Still generating analysis... This may take up to 60 seconds.',
                progress: 60
              };
            }
            return prev;
          });
        }, 15000);
        
        setTimeout(() => {
          setAnalysisStatus(prev => {
            if (prev && prev.stage === 'generating-insights') {
              return {
                ...prev,
                message: 'Almost done... Finalizing insights.',
                progress: 80
              };
            }
            return prev;
          });
        }, 30000);
      }
    } catch (error) {
      console.error('Failed to analyze transcript:', error);
      setAnalysisStatus({
        stage: 'error',
        message: 'Analysis failed. Please try again.',
        progress: 0
      });
      setIsAnalyzing(false);
      isLoadingAnalysisRef.current = false;
      setIsLoadingAnalysis(false);
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
        // No chunks found - use the call record's audio_file_url directly via the new endpoint
        setDiarizationStatus('No chunks found; using call record audio file directly...');
        
        if (!callData?.audio_file_url) {
          throw new Error('No audio file URL found for this call record. Cannot retry transcription.');
        }
        
        // Use the new endpoint that works with call_record_id
        const { data: sess } = await supabase.auth.getSession();
        const token = sess.session?.access_token;
        
        const resp = await fetch(getApiUrl(`/api/transcribe/call-record/${encodeURIComponent(callId)}?enable_diarization=true&provider=${encodeURIComponent(transcriptionProvider)}`), {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
          },
        });
        
        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.success) {
          const msg = data?.detail || data?.error || resp.statusText || 'Transcription failed';
          throw new Error(msg);
        }
        
        toast.success('Transcription started successfully! Reloading call data...');
        setDiarizationStatus('Transcription queued. Reloading...');
        
        // Reload call data to get updated transcript
        await loadCallData();
        await loadAnalysis();
        setDiarizationStatus('Transcription complete.');
        return;
      }

      // Get customer name from chunks if not in call_data
      const customerName = callData?.customer_name || 'Customer';

      toast.success(`Found ${chunks.length} chunks. Attempting transcription with diarization...`);
      setDiarizationStatus(`Found ${chunks.length} chunks. Requesting diarization from ${transcriptionProvider}...`);

      const { data: sess } = await supabase.auth.getSession();
      const token = sess.session?.access_token;
      const resp = await fetch(getApiUrl(`/api/transcribe/call-record/${encodeURIComponent(callId)}?enable_diarization=true&provider=${encodeURIComponent(transcriptionProvider)}`), {
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
      
      const { data: sess } = await supabase.auth.getSession();
      const token = sess.session?.access_token;
      
      const url = getApiUrl(`/api/transcribe/call-record/${encodeURIComponent(callId)}?enable_diarization=true&provider=${encodeURIComponent(transcriptionProvider)}`);
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
                analysisStatus={analysisStatus}
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