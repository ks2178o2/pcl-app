import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TranscriptViewer } from '@/components/TranscriptViewer';
import { AudioPlayer } from '@/components/AudioPlayer';
import { supabase } from '@/integrations/supabase/client';
import { Phone, Clock, User, Play, RefreshCw, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useCallRecords } from '@/hooks/useCallRecords';
interface CallRecord {
  id: string;
  patientName: string;
  salespersonName: string;
  duration: number;
  timestamp: Date;
  status: 'completed' | 'in-progress' | 'transcribing';
  audioBlob?: Blob;
  audioPath?: string; // Storage path for lazy loading
  transcript?: string;
  diarizationSegments?: any[];
  speakerMapping?: Record<string, string>;
  diarizationConfidence?: number;
  numSpeakers?: number;
}
interface CallsDashboardProps {
  calls: CallRecord[];
  onCallsUpdate?: () => void;
}
const CallsDashboardInner: React.FC<CallsDashboardProps> = ({
  calls,
  onCallsUpdate
}) => {
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);
  const [isPlayerOpen, setIsPlayerOpen] = useState(false);
  const navigate = useNavigate();
  const {
    updateSpeakerMapping
  } = useCallRecords();
  const handlePlayRecording = async (call: CallRecord) => {
    try {
      // Lazy-load audio if not already present
      if (!call.audioBlob && call.audioPath) {
        const { data: signedUrlData, error: signedUrlError } = await supabase.storage
          .from('call-recordings')
          .createSignedUrl(call.audioPath, 60 * 60);
        if (!signedUrlError && signedUrlData?.signedUrl) {
          const resp = await fetch(signedUrlData.signedUrl);
          if (resp.ok) {
            const blob = await resp.blob();
            const enhanced = { ...call, audioBlob: blob };
            setSelectedCall(enhanced);
            setIsPlayerOpen(true);
            return;
          }
        }
      }
      setSelectedCall(call);
      setIsPlayerOpen(true);
    } catch (e) {
      console.error('Failed to load audio for playback', e);
      setSelectedCall(call); // Fallback to open player without audio
      setIsPlayerOpen(true);
    }
  };
  const retryTranscription = async (call: CallRecord) => {
    try {
      if (call.audioBlob) {
        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64Data = reader.result as string;
          const base64Audio = base64Data.split(',')[1]; // Remove data URL prefix
          
          const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
          const { useAuth } = await import('@/hooks/useAuth');
          
          // Get user for organization_id
          const { user } = useAuth();
          
          const payload = await buildTranscriptionPayload({
            audioBase64: base64Audio,
            callId: call.id,
            salespersonName: call.salespersonName,
            customerName: call.patientName,
            organizationId: (user as any)?.organization_id,
          });
          
          const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
          const { data: sess } = await supabase.auth.getSession();
          const token = sess.session?.access_token;
          const resp = await fetch(`${API_BASE_URL}/api/transcribe/call-record/${encodeURIComponent(call.id)}?enable_diarization=true`, {
            method: 'POST',
            headers: {
              'Authorization': token ? `Bearer ${token}` : '',
            },
          });
          const data = await resp.json().catch(() => null);
          if (!resp.ok) {
            console.error('Transcription failed:', data);
          } else {
            console.log('Transcription retry successful:', data);
            setTimeout(() => window.location.reload(), 2000);
          }
        };
        reader.readAsDataURL(call.audioBlob);
        return;
      }

      if (call.audioPath) {
        const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
        const { useAuth } = await import('@/hooks/useAuth');
        
        // Get user for organization_id
        const { user } = useAuth();
        
        const payload = await buildTranscriptionPayload({
          storagePath: call.audioPath,
          callId: call.id,
          salespersonName: call.salespersonName,
          customerName: call.patientName,
          organizationId: (user as any)?.organization_id,
        });
        
        const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
        const { data: sess } = await supabase.auth.getSession();
        const token = sess.session?.access_token;
        const resp = await fetch(`${API_BASE_URL}/api/transcribe/call-record/${encodeURIComponent(call.id)}?enable_diarization=true`, {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
          },
        });
        const data = await resp.json().catch(() => null);
        if (!resp.ok) {
          console.error('Transcription (storage) failed:', data);
        } else {
          console.log('Transcription retry (storage) successful:', data);
          setTimeout(() => window.location.reload(), 2000);
        }
        return;
      }

      console.error('No audio available for transcription');
    } catch (error) {
      console.error('Error retrying transcription:', error);
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
  // Persist scroll position within page for dashboard browsing
  useEffect(() => {
    const onScroll = () => {
      try { sessionStorage.setItem('callsDashboardScroll', String(window.scrollY || 0)); } catch {}
    };
    window.addEventListener('scroll', onScroll);
    // Restore once per mount
    try {
      const saved = sessionStorage.getItem('callsDashboardScroll');
      if (saved) requestAnimationFrame(() => window.scrollTo(0, parseInt(saved, 10) || 0));
    } catch {}
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return <Card>
      
      <CardContent>
        {calls.length === 0 ? <div className="text-center py-8 text-muted-foreground">
            No sales calls recorded yet. Start recording your first call!
          </div> : <div className="space-y-4">
            {calls.map(call => <div key={call.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <button onClick={() => navigate(`/patient/${encodeURIComponent(call.patientName)}`)} className="font-medium text-primary hover:underline focus:underline">
                      {call.patientName}
                    </button>
                    <span className="text-sm text-muted-foreground">• {formatDate(call.timestamp)}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <Badge variant={call.status === 'completed' ? 'default' : call.status === 'transcribing' ? 'outline' : 'secondary'}>
                    {call.status === 'transcribing' ? 'Analyzing voices...' : call.status}
                  </Badge>
                  <div className="flex gap-2">
                    {(call.audioBlob || call.audioPath) && (
                      <Button onClick={() => handlePlayRecording(call)} variant="outline" size="sm" className="flex items-center gap-2">
                        <Play className="h-3 w-3" />
                        Play
                      </Button>
                    )}
                    {call.transcript && call.transcript !== 'Transcribing audio...'
                      ? (
                        <TranscriptViewer
                          transcript={call.transcript}
                          customerName={call.patientName}
                          salespersonName={call.salespersonName}
                          duration={call.duration}
                          timestamp={call.timestamp}
                          callId={call.id}
                          onRetryTranscription={() => retryTranscription(call)}
                        />
                      ) : (call.audioBlob || call.audioPath) ? (
                        <Button onClick={() => retryTranscription(call)} variant="outline" size="sm" className="flex items-center gap-2">
                          <RefreshCw className="h-3 w-3" />
                          Retry Transcription
                        </Button>
                      ) : null}
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(call.duration)}
                  </div>
                </div>

                {call.transcript && call.transcript !== 'Transcribing audio...' && <div className="mt-3 p-3 bg-muted rounded-md">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium">Transcript Preview:</p>
                      <span className="text-xs text-muted-foreground">Click "View Full Transcript" to see complete conversation</span>
                    </div>
                    <div className="text-sm text-muted-foreground max-h-20 overflow-hidden">
                      {call.transcript.split('\n\n').slice(0, 2).map((segment, index) => {
                // Extract speaker name for preview
                const speakerMatch = segment.match(/^\[([^\]]+)\]:\s*(.*)$/);
                if (!speakerMatch) return <span key={index}>{segment.substring(0, 80)}...</span>;
                const [, speakerName, text] = speakerMatch;
                const displayText = `${speakerName}: ${text}`.substring(0, 80) + '...';

                // Determine speaker type for styling
                const isSalesperson = speakerName.toLowerCase().includes('sales') || !speakerName.toLowerCase().includes('support') && !speakerName.toLowerCase().includes('customer');
                const isCustomerSupport = speakerName.toLowerCase().includes('support');
                return <div key={index} className="mb-1 truncate">
                            {isSalesperson ? <span className="text-blue-600 dark:text-blue-400">🎯 {displayText}</span> : isCustomerSupport ? <span className="text-purple-600 dark:text-purple-400">🤝 {displayText}</span> : <span className="text-green-600 dark:text-green-400">👤 {displayText}</span>}
                          </div>;
              })}
                    </div>
                  </div>}
              </div>)}
          </div>}

        <AudioPlayer call={selectedCall} isOpen={isPlayerOpen} onClose={() => setIsPlayerOpen(false)} onRetryTranscription={retryTranscription} onUpdateSpeakerMapping={updateSpeakerMapping} persistKey={selectedCall?.id} />
      </CardContent>
    </Card>;
};

export const CallsDashboard = React.memo(CallsDashboardInner);