import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Mic, Square, Play, Pause, RefreshCw } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface VoiceRecorderProps {
  sampleText: string;
  onRecordingComplete: (audioBlob: Blob, duration: number) => void;
  isProcessing?: boolean;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  sampleText,
  onRecordingComplete,
  isProcessing = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationFrameRef = useRef<number>();
  const streamRef = useRef<MediaStream | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const stopMonitoringRef = useRef<(() => void) | null>(null);

  const { toast } = useToast();

  const minRecordingTime = 10; // minimum 10 seconds
  const maxRecordingTime = 60; // maximum 60 seconds

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      streamRef.current = stream;

      // Set up audio analysis for visual feedback
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyzer = audioContext.createAnalyser();
      analyzer.fftSize = 256;
      source.connect(analyzer);
      analyzerRef.current = analyzer;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          if (newTime >= maxRecordingTime) {
            stopRecording();
            return maxRecordingTime;
          }
          return newTime;
        });
      }, 1000);

      // Start audio level monitoring
      stopMonitoringRef.current = monitorAudioLevel();

      toast({
        title: "Recording started",
        description: `Please read the text clearly. Minimum ${minRecordingTime}s required.`,
      });

    } catch (error) {
      console.error('Error starting recording:', error);
      toast({
        title: "Recording failed",
        description: "Could not access microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  const monitorAudioLevel = () => {
    if (!analyzerRef.current) return;

    const dataArray = new Uint8Array(analyzerRef.current.frequencyBinCount);
    let isMonitoring = true; // Use local variable instead of state
    
    const updateLevel = () => {
      if (!analyzerRef.current || !isMonitoring) return;
      
      analyzerRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(Math.min(100, (average / 255) * 100));
      
      // Use setTimeout with increased frequency for better performance
      setTimeout(() => {
        if (isMonitoring) updateLevel();
      }, 200); // Increased from 100ms to 200ms
    };
    
    updateLevel();
    
    // Return function to stop monitoring
    return () => {
      isMonitoring = false;
    };
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = undefined;
      }

      if (stopMonitoringRef.current) {
        stopMonitoringRef.current();
        stopMonitoringRef.current = null;
      }

      if (recordingTime < minRecordingTime) {
        toast({
          title: "Recording too short",
          description: `Please record for at least ${minRecordingTime} seconds for better voice analysis.`,
          variant: "destructive",
        });
        return;
      }

      toast({
        title: "Recording completed",
        description: "You can now play back your recording or submit it.",
      });
    }
  };

  const playRecording = async () => {
    if (!audioBlob) return;

    if (isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      return;
    }

    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.onended = () => {
      setIsPlaying(false);
      URL.revokeObjectURL(audioUrl);
    };

    audio.play();
    setIsPlaying(true);
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setIsPlaying(false);
    setAudioLevel(0);
    
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  };

  const handleSubmit = () => {
    if (audioBlob && recordingTime >= minRecordingTime) {
      onRecordingComplete(audioBlob, recordingTime);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mic className="h-5 w-5" />
          Voice Sample Recording
        </CardTitle>
        <CardDescription>
          Record yourself reading the provided text to create your voice profile for better speaker identification.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Sample text to read */}
        <div className="p-4 bg-muted rounded-lg">
          <h3 className="font-medium mb-2">Please read this text clearly:</h3>
          <p className="text-sm leading-relaxed italic">
            "{sampleText}"
          </p>
        </div>

        {/* Recording controls */}
        <div className="space-y-4">
          {/* Timer and progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>Recording time: {recordingTime}s</span>
              <span>{minRecordingTime}s - {maxRecordingTime}s required</span>
            </div>
            <Progress 
              value={(recordingTime / maxRecordingTime) * 100} 
              className="w-full"
            />
          </div>

          {/* Audio level indicator */}
          {isRecording && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Audio level:</span>
                <span>{Math.round(audioLevel)}%</span>
              </div>
              <Progress 
                value={audioLevel} 
                className="w-full h-2"
              />
            </div>
          )}

          {/* Control buttons */}
          <div className="flex justify-center gap-4">
            {!isRecording && !audioBlob && (
              <Button 
                onClick={startRecording} 
                size="lg"
                className="flex items-center gap-2"
              >
                <Mic className="h-4 w-4" />
                Start Recording
              </Button>
            )}

            {isRecording && (
              <Button 
                onClick={stopRecording} 
                variant="destructive" 
                size="lg"
                className="flex items-center gap-2"
              >
                <Square className="h-4 w-4" />
                Stop Recording ({recordingTime}s)
              </Button>
            )}

            {audioBlob && !isRecording && (
              <div className="flex gap-2">
                <Button 
                  onClick={playRecording} 
                  variant="outline" 
                  size="lg"
                  className="flex items-center gap-2"
                >
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  {isPlaying ? 'Pause' : 'Play'} Recording
                </Button>
                
                <Button 
                  onClick={resetRecording} 
                  variant="outline" 
                  size="lg"
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Re-record
                </Button>
                
                <Button 
                  onClick={handleSubmit} 
                  size="lg"
                  disabled={isProcessing || recordingTime < minRecordingTime}
                  className="flex items-center gap-2"
                >
                  {isProcessing ? 'Processing...' : 'Save Voice Profile'}
                </Button>
              </div>
            )}
          </div>

          {/* Recording requirements */}
          <div className="text-xs text-muted-foreground text-center space-y-1">
            <p>• Speak clearly and at normal pace</p>
            <p>• Ensure good audio quality (minimal background noise)</p>
            <p>• Recording must be between {minRecordingTime}-{maxRecordingTime} seconds</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};