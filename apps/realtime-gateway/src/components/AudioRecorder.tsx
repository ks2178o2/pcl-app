import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AudioControls } from '@/components/AudioControls';
import { Mic, Square, Play, Pause, Volume2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

interface PersistedAudioRecordingState {
  isRecording: boolean;
  startTime: number;
  patientName?: string;
  patientId?: string;
  timestamp: number;
}

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob, duration: number) => void;
  disabled?: boolean;
  patientName?: string;
  patientId?: string;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onRecordingComplete,
  disabled = false,
  patientName,
  patientId
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioURL, setAudioURL] = useState<string>('');
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordingAudioLevel, setRecordingAudioLevel] = useState(0);
  const [recordingCompleted, setRecordingCompleted] = useState(false);
  const [completedRecording, setCompletedRecording] = useState<{ blob: Blob; duration: number } | null>(null);
  const [showRecoveryDialog, setShowRecoveryDialog] = useState(false);
  const [recoveryState, setRecoveryState] = useState<PersistedAudioRecordingState | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationIdRef = useRef<number | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);

  const STORAGE_KEY = 'audiorecorder_state';

  const saveState = () => {
    if (isRecording) {
      const state: PersistedAudioRecordingState = {
        isRecording: true,
        startTime: recordingStartTimeRef.current || Date.now(),
        patientName,
        patientId,
        timestamp: Date.now()
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  };

  const clearState = () => {
    localStorage.removeItem(STORAGE_KEY);
  };

  const loadState = (): PersistedAudioRecordingState | null => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    
    try {
      const state = JSON.parse(stored) as PersistedAudioRecordingState;
      // Check if state is older than 24 hours
      const age = Date.now() - state.timestamp;
      if (age > 24 * 60 * 60 * 1000) {
        clearState();
        return null;
      }
      return state;
    } catch (error) {
      console.error('Failed to load persisted state:', error);
      clearState();
      return null;
    }
  };

  const startRecording = async () => {
    try {
      chunksRef.current = [];
      setRecordingCompleted(false);
      setCompletedRecording(null);
      setAudioURL('');
      setRecordingTime(0);
      setRecordingAudioLevel(0);
      recordingStartTimeRef.current = Date.now();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        chunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioURL(url);
        setDuration(recordingTime);
        setRecordingCompleted(true);
        setCompletedRecording({ blob, duration: recordingTime });
      };

      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Audio level monitoring during recording
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateAudioLevel = () => {
        if (isRecording && analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setRecordingAudioLevel(Math.min(100, (average / 128) * 100));
          animationIdRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);

      // Save state immediately
      saveState();

      // Update document title
      document.title = '🔴 Recording...';

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
        saveState(); // Save state every second
      }, 1000);

      updateAudioLevel();
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current);
      animationIdRef.current = null;
    }

    setRecordingAudioLevel(0);
    recordingStartTimeRef.current = null;
    
    // Clear persisted state
    clearState();
    
    // Reset document title
    document.title = 'Sales Angel Buddy';
  };

  const togglePlayback = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleStoreRecording = () => {
    if (completedRecording && onRecordingComplete) {
      onRecordingComplete(completedRecording.blob, completedRecording.duration);
      setRecordingCompleted(false);
      setCompletedRecording(null);
      setAudioURL('');
      setDuration(0);
    }
  };

  const handleDeleteRecording = () => {
    setRecordingCompleted(false);
    setCompletedRecording(null);
    setAudioURL('');
    setDuration(0);
    clearState();
  };

  const handleRecoverRecording = async () => {
    setShowRecoveryDialog(false);
    setRecoveryState(null);
    toast.info('Starting new recording for same patient');
    await startRecording();
  };

  const handleDiscardRecording = () => {
    clearState();
    setShowRecoveryDialog(false);
    setRecoveryState(null);
    toast.info('Previous recording discarded');
  };

  const handleFileUpload = (file: File, audioBlob: Blob, duration: number) => {
    setAudioURL(URL.createObjectURL(audioBlob));
    setDuration(duration);

    // Trigger the recording complete callback with the uploaded file
    if (onRecordingComplete) {
      onRecordingComplete(audioBlob, duration);
    }
  };

  useEffect(() => {
    // Check for existing recording on mount
    const existingState = loadState();
    if (existingState && existingState.isRecording) {
      setRecoveryState(existingState);
      setShowRecoveryDialog(true);
      toast.info('Recording was interrupted', {
        description: 'Quick recordings cannot be recovered after leaving the page. Consider using the Professional Recorder for important calls.'
      });
    }

    // Handle visibility change - save state when tab is hidden
    const handleVisibilityChange = () => {
      if (document.hidden && isRecording) {
        saveState();
      }
    };

    // Warn before page unload if recording
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isRecording) {
        saveState();
        e.preventDefault();
        e.returnValue = 'Recording in progress. Are you sure you want to leave?';
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
      
      // Only cleanup if NOT recording
      if (!isRecording) {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
        if (animationIdRef.current) {
          cancelAnimationFrame(animationIdRef.current);
        }
      }
    };
  }, [isRecording]);

  return (
    <>
      {/* Recovery Dialog */}
      <Dialog open={showRecoveryDialog} onOpenChange={setShowRecoveryDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              Recording Interrupted
            </DialogTitle>
            <DialogDescription className="space-y-3 pt-4">
              <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-amber-900 dark:text-amber-100">
                  Previous recording audio was lost when you left the page
                </p>
              </div>
              
              <div className="space-y-1">
                {recoveryState?.patientName && (
                  <p><span className="font-medium">Patient:</span> {recoveryState.patientName}</p>
                )}
                {recoveryState?.startTime && (
                  <p className="text-sm text-muted-foreground">
                    Started: {new Date(recoveryState.startTime).toLocaleString()}
                  </p>
                )}
              </div>
              
              <p className="text-sm text-muted-foreground">
                Quick recordings cannot be recovered. For important calls, consider using the Professional Recorder which auto-saves every 30 seconds.
              </p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={handleDiscardRecording}>
              Dismiss
            </Button>
            <Button onClick={handleRecoverRecording}>
              Start New Recording
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Sales Call Recorder
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
        <AudioControls patientName={patientName} patientId={patientId} hideUpload={true} />
        
        <div className="flex flex-wrap gap-2">
          {!isRecording ? (
            <Button 
              onClick={startRecording} 
              className="flex items-center gap-2"
              disabled={disabled}
            >
              <Mic className="h-4 w-4" />
              Start Recording
            </Button>
          ) : (
            <Button onClick={stopRecording} variant="destructive" className="flex items-center gap-2">
              <Square className="h-4 w-4" />
              Stop Recording
            </Button>
          )}
        </div>

        {isRecording && (
          <div className="space-y-3 p-4 rounded-lg bg-destructive/5 border border-destructive/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-destructive">
                <div className="w-3 h-3 bg-destructive rounded-full animate-pulse" />
                <span className="font-medium">Recording Call</span>
              </div>
              <div className="text-lg font-mono text-destructive">
                {Math.floor(recordingTime / 60)}:{(Math.floor(recordingTime) % 60).toString().padStart(2, '0')}
              </div>
            </div>
            
            {patientName && (
              <div className="text-sm text-muted-foreground">
                Patient: <span className="font-medium">{patientName}</span>
              </div>
            )}
            
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Volume2 className="h-3 w-3" />
                Audio Level: {Math.round(recordingAudioLevel)}%
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-destructive h-2 rounded-full transition-all duration-100"
                  style={{ width: `${recordingAudioLevel}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {recordingCompleted && completedRecording && (
          <div className="space-y-4 p-4 rounded-lg bg-secondary/20 border border-secondary">
            {/* Hidden audio element for playback */}
            <audio
              ref={audioRef}
              src={audioURL}
              onEnded={() => setIsPlaying(false)}
              className="hidden"
            />
            
            <div className="text-center">
              <h3 className="font-medium text-lg mb-2">Recording Complete!</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Duration: {Math.round(completedRecording.duration)}s
              </p>
              
              {/* Playback controls */}
              <div className="flex justify-center gap-2 mb-4">
                <Button onClick={togglePlayback} variant="outline" size="sm">
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  {isPlaying ? 'Pause' : 'Play'}
                </Button>
              </div>
              
              {/* Store or Delete options */}
              <div className="flex justify-center gap-3">
                <Button 
                  onClick={handleStoreRecording}
                  className="flex items-center gap-2"
                >
                  Store & Transcribe
                </Button>
                <Button 
                  onClick={handleDeleteRecording}
                  variant="destructive"
                  className="flex items-center gap-2"
                >
                  Delete Recording
                </Button>
              </div>
            </div>
          </div>
        )}

        {audioURL && !recordingCompleted && (
          <div className="space-y-2">
            <audio
              ref={audioRef}
              src={audioURL}
              onEnded={() => setIsPlaying(false)}
              className="hidden"
            />
            <div className="flex items-center gap-2">
              <Button onClick={togglePlayback} variant="outline" size="sm">
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <span className="text-sm text-muted-foreground">
                Uploaded file - Duration: {Math.round(duration)}s
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
    </>
  );
};