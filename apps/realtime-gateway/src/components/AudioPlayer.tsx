import React, { useState, useRef, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/integrations/supabase/client';
import { SpeakerMappingEditor } from '@/components/SpeakerMappingEditor';
import { generateMappedTranscript, swapSpeakers, normalizeDiarizationSegments } from '@/utils/speakerUtils';
import { Play, Pause, Square, Volume2, Clock, FileText, RefreshCw, Zap, Users, Edit3, RotateCcw } from 'lucide-react';

interface CallRecord {
  id: string;
  patientName: string;
  salespersonName: string;
  duration: number;
  timestamp: Date;
  status: 'completed' | 'in-progress' | 'transcribing';
  audioBlob?: Blob;
  transcript?: string;
  diarizationSegments?: any[];
  speakerMapping?: Record<string, string>;
  diarizationConfidence?: number;
  numSpeakers?: number;
}

interface AudioPlayerProps {
  call: CallRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onRetryTranscription?: (call: CallRecord) => void;
  onUpdateSpeakerMapping?: (callId: string, mapping: Record<string, string>) => void;
  // Optional key to persist/restore UI state across navigations
  persistKey?: string;
}

interface TranscriptSegment {
  speaker: string;
  text: string;
  startTime: number; // estimated start time in seconds
  isActive: boolean;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ call, isOpen, onClose, onRetryTranscription, onUpdateSpeakerMapping, persistKey }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState([100]);
  const [playbackSpeed, setPlaybackSpeed] = useState('1');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [transcriptSegments, setTranscriptSegments] = useState<TranscriptSegment[]>([]);
  const [retryingTranscription, setRetryingTranscription] = useState(false);
  const [retryingAnalysis, setRetryingAnalysis] = useState(false);
  const [showSpeakerEditor, setShowSpeakerEditor] = useState(false);
  const [displayTranscript, setDisplayTranscript] = useState<string>('');

  // Restore persisted state
  useEffect(() => {
    if (!persistKey) return;
    try {
      const raw = sessionStorage.getItem(`audioplayer:${persistKey}`);
      if (raw) {
        const st = JSON.parse(raw);
        if (typeof st.time === 'number') setCurrentTime(st.time);
        if (typeof st.speed === 'string') setPlaybackSpeed(st.speed);
        if (Array.isArray(st.volume)) setVolume(st.volume);
      }
    } catch {}
  }, [persistKey]);

  useEffect(() => {
    if (call?.audioBlob) {
      const url = URL.createObjectURL(call.audioBlob);
      setAudioUrl(url);
      
      // Set initial duration from call data
      if (call.duration && !isNaN(call.duration) && isFinite(call.duration)) {
        setDuration(call.duration);
      }
      
      // Generate display transcript with speaker mapping
      if (call.transcript && call.diarizationSegments && call.speakerMapping) {
        const mappedTranscript = generateMappedTranscript(call.diarizationSegments, call.speakerMapping);
        setDisplayTranscript(mappedTranscript);
        parseTranscriptWithTimestamps(mappedTranscript, call.duration);
      } else if (call.transcript) {
        setDisplayTranscript(call.transcript);
        parseTranscriptWithTimestamps(call.transcript, call.duration);
      }
      
      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [call]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => {
      const audioDuration = audio.duration;
      if (audioDuration && !isNaN(audioDuration) && isFinite(audioDuration)) {
        setDuration(audioDuration);
      } else if (call?.duration) {
        // Fallback to call duration if audio duration is not available
        setDuration(call.duration);
      }
    };
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('durationchange', updateDuration);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('durationchange', updateDuration);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioUrl, call?.duration]);

  // Persist on changes
  useEffect(() => {
    if (!persistKey) return;
    try {
      sessionStorage.setItem(`audioplayer:${persistKey}`, JSON.stringify({
        time: currentTime,
        speed: playbackSpeed,
        volume
      }));
    } catch {}
  }, [persistKey, currentTime, playbackSpeed, volume]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume[0] / 100;
    }
  }, [volume]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = parseFloat(playbackSpeed);
    }
  }, [playbackSpeed]);

  const parseTranscriptWithTimestamps = (transcript: string, totalDuration: number) => {
    const segments = transcript.split('\n\n').filter(s => s.trim());
    const segmentDuration = totalDuration / segments.length;
    
    const parsedSegments: TranscriptSegment[] = segments.map((segment, index) => {
      const speakerMatch = segment.match(/^\[([^\]]+)\]:\s*(.*)$/);
      const speaker = speakerMatch ? speakerMatch[1] : 'Unknown';
      const text = speakerMatch ? speakerMatch[2] : segment;
      
      return {
        speaker,
        text,
        startTime: index * segmentDuration,
        isActive: false
      };
    });
    
    setTranscriptSegments(parsedSegments);
  };

  // Update active segment based on current time
  useEffect(() => {
    setTranscriptSegments(prev => 
      prev.map(segment => ({
        ...segment,
        isActive: currentTime >= segment.startTime && 
                 currentTime < segment.startTime + (duration / prev.length)
      }))
    );
  }, [currentTime, duration]);

  const togglePlayback = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const stopPlayback = () => {
    if (!audioRef.current) return;
    
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleSeek = (value: number[]) => {
    if (!audioRef.current || !duration || isNaN(duration) || !isFinite(duration)) return;
    
    const newTime = (value[0] / 100) * duration;
    if (isNaN(newTime) || !isFinite(newTime)) return;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleProgressBarClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !duration || isNaN(duration) || !isFinite(duration)) return;
    
    const rect = event.currentTarget.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    
    if (isNaN(newTime) || !isFinite(newTime)) return;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const jumpToSegment = (startTime: number) => {
    if (!audioRef.current) return;
    
    audioRef.current.currentTime = startTime;
    setCurrentTime(startTime);
  };

  const handleRetryTranscription = async () => {
    if (!call || !onRetryTranscription) return;
    
    setRetryingTranscription(true);
    try {
      await onRetryTranscription(call);
    } catch (error) {
      console.error('Failed to retry transcription:', error);
    } finally {
      setRetryingTranscription(false);
    }
  };

  const handleRetryAnalysis = async () => {
    if (!call || !call.transcript) return;
    
    setRetryingAnalysis(true);
    try {
      const { data, error } = await supabase.functions.invoke('analyze-transcript', {
        body: {
          transcript: call.transcript,
          callId: call.id,
          customerName: call.patientName,
          salespersonName: call.salespersonName
        }
      });

      if (error) {
        console.error('Analysis failed:', error);
        alert('Analysis failed. Please check the console for details.');
      } else {
        console.log('Analysis retry successful:', data);
        // Auto-refresh to show updated analysis
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      }
    } catch (error) {
      console.error('Error retrying analysis:', error);
    } finally {
      setRetryingAnalysis(false);
    }
  };

  const handleSpeakerSwap = async () => {
    if (!call || !call.diarizationSegments || !call.speakerMapping || !onUpdateSpeakerMapping) return;

    const expandedSegments = normalizeDiarizationSegments(call.diarizationSegments);

    // Find the two most active speakers
    const uniqueSpeakers = Array.from(new Set(expandedSegments.map(s => s.speaker))).sort();
    if (uniqueSpeakers.length >= 2) {
      const swappedMapping = swapSpeakers(call.speakerMapping, uniqueSpeakers[0], uniqueSpeakers[1]);
      await onUpdateSpeakerMapping(call.id, swappedMapping);
      
      // Update display transcript
      const newTranscript = generateMappedTranscript(call.diarizationSegments, swappedMapping);
      setDisplayTranscript(newTranscript);
      parseTranscriptWithTimestamps(newTranscript, call.duration);
    }
  };

  const handleSpeakerMappingSave = async (newMapping: Record<string, string>) => {
    if (!call || !call.diarizationSegments || !onUpdateSpeakerMapping) return;
    
    await onUpdateSpeakerMapping(call.id, newMapping);
    
    // Update display transcript
    const newTranscript = generateMappedTranscript(call.diarizationSegments, newMapping);
    setDisplayTranscript(newTranscript);
    parseTranscriptWithTimestamps(newTranscript, call.duration);
  };

  const formatTime = (seconds: number) => {
    if (!seconds || isNaN(seconds) || !isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderTranscriptSegment = (segment: TranscriptSegment, index: number) => {
    const isSalesperson = segment.speaker.toLowerCase().includes('sales') || 
                         (!segment.speaker.toLowerCase().includes('support') && 
                          !segment.speaker.toLowerCase().includes('customer'));
    const isCustomerSupport = segment.speaker.toLowerCase().includes('support');
    
    const baseClasses = "mb-3 p-3 rounded-lg border cursor-pointer transition-all duration-200";
    const activeClasses = segment.isActive 
      ? "ring-2 ring-primary shadow-md transform scale-[1.02]" 
      : "hover:shadow-sm";
    
    let colorClasses = "";
    let icon = "";
    
    if (isSalesperson) {
      colorClasses = segment.isActive 
        ? "bg-blue-100 dark:bg-blue-900/30 border-blue-500" 
        : "bg-blue-50 dark:bg-blue-950/20 border-blue-200 hover:bg-blue-100 dark:hover:bg-blue-900/20";
      icon = "🎯";
    } else if (isCustomerSupport) {
      colorClasses = segment.isActive 
        ? "bg-purple-100 dark:bg-purple-900/30 border-purple-500" 
        : "bg-purple-50 dark:bg-purple-950/20 border-purple-200 hover:bg-purple-100 dark:hover:bg-purple-900/20";
      icon = "🤝";
    } else {
      colorClasses = segment.isActive 
        ? "bg-green-100 dark:bg-green-900/30 border-green-500" 
        : "bg-green-50 dark:bg-green-950/20 border-green-200 hover:bg-green-100 dark:hover:bg-green-900/20";
      icon = "👤";
    }

    return (
      <div 
        key={index} 
        className={`${baseClasses} ${activeClasses} ${colorClasses}`}
        onClick={() => jumpToSegment(segment.startTime)}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="font-semibold flex items-center gap-2">
            {icon} {segment.speaker}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatTime(segment.startTime)}
          </span>
        </div>
        <p className="text-sm leading-relaxed">{segment.text}</p>
      </div>
    );
  };

  if (!call) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] p-0">
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Audio Player - {call.patientName}
          </DialogTitle>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>Recorded: {call.timestamp.toLocaleString()}</span>
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Duration: {formatTime(call.duration)}
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex gap-2 mt-2 flex-wrap">
              {onRetryTranscription && call.transcript && (call.transcript.includes('failed') || call.transcript.includes('Transcription failed')) && (
                <Button
                  onClick={handleRetryTranscription}
                  variant="outline"
                  size="sm"
                  disabled={retryingTranscription}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className={`h-4 w-4 ${retryingTranscription ? 'animate-spin' : ''}`} />
                  {retryingTranscription ? 'Retrying...' : 'Retry Transcription'}
                </Button>
              )}
              
              {call.transcript && !call.transcript.includes('failed') && (
                <Button
                  onClick={handleRetryAnalysis}
                  variant="outline"
                  size="sm"
                  disabled={retryingAnalysis}
                  className="flex items-center gap-2"
                >
                  <Zap className={`h-4 w-4 ${retryingAnalysis ? 'animate-spin' : ''}`} />
                  {retryingAnalysis ? 'Analyzing...' : 'Retry Analysis'}
                </Button>
              )}

              {/* Speaker mapping controls */}
              {call.diarizationSegments && call.speakerMapping && call.numSpeakers === 2 && (
                <Button
                  onClick={handleSpeakerSwap}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  Swap Speakers
                </Button>
              )}

              {call.diarizationSegments && call.speakerMapping && (
                <Button
                  onClick={() => setShowSpeakerEditor(true)}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <Edit3 className="h-4 w-4" />
                  Edit Labels
                </Button>
              )}
            </div>

            {/* Confidence indicator */}
            {call.diarizationConfidence && call.diarizationConfidence > 0 && (
              <div className="mt-2">
                <Badge 
                  variant="outline" 
                  className={`text-xs ${
                    call.diarizationConfidence >= 0.9 ? 'text-green-600 dark:text-green-400' :
                    call.diarizationConfidence >= 0.75 ? 'text-yellow-600 dark:text-yellow-400' :
                    'text-red-600 dark:text-red-400'
                  }`}
                >
                  <Users className="h-3 w-3 mr-1" />
                  {Math.round(call.diarizationConfidence * 100)}% speaker confidence
                </Badge>
                {call.diarizationConfidence < 0.75 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Low confidence - consider reviewing speaker labels
                  </p>
                )}
              </div>
            )}
        </DialogHeader>

        <div className="flex flex-col lg:flex-row h-[70vh]">
          {/* Audio Controls Panel */}
          <div className="lg:w-1/3 p-6 border-b lg:border-b-0 lg:border-r">
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Audio Controls</h3>
              
              {/* Audio Element */}
              {audioUrl && (
                <audio ref={audioRef} src={audioUrl} preload="metadata" />
              )}

              {/* Playback Controls */}
              <div className="flex items-center justify-center gap-2 mb-6">
                <Button onClick={togglePlayback} size="lg" className="w-12 h-12">
                  {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                </Button>
                <Button onClick={stopPlayback} variant="outline" size="lg" className="w-12 h-12">
                  <Square className="h-5 w-5" />
                </Button>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
                <div 
                  className="w-full cursor-pointer" 
                  onClick={handleProgressBarClick}
                >
                  <Slider
                    value={[duration > 0 && !isNaN(duration) ? (currentTime / duration) * 100 : 0]}
                    onValueChange={handleSeek}
                    max={100}
                    step={0.1}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Playback Speed Control */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-4 w-4" />
                  <span className="text-sm font-medium">Speed</span>
                </div>
                <Select value={playbackSpeed} onValueChange={setPlaybackSpeed}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.5">0.5x</SelectItem>
                    <SelectItem value="0.75">0.75x</SelectItem>
                    <SelectItem value="1">1x</SelectItem>
                    <SelectItem value="1.25">1.25x</SelectItem>
                    <SelectItem value="1.5">1.5x</SelectItem>
                    <SelectItem value="2">2x</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Volume Control */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Volume2 className="h-4 w-4" />
                  <span className="text-sm font-medium">Volume</span>
                </div>
                <Slider
                  value={volume}
                  onValueChange={setVolume}
                  max={100}
                  step={1}
                  className="w-full"
                />
              </div>

              {/* Audio Info */}
              <div className="text-xs text-muted-foreground space-y-1">
                <p>Click any transcript segment to jump to that part of the audio.</p>
                <p>The currently playing segment is highlighted.</p>
                {onRetryTranscription && call && call.transcript && (call.transcript.includes('failed') || call.transcript.includes('Transcription failed')) && (
                  <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                    <p className="text-yellow-800 dark:text-yellow-200 text-sm font-medium mb-2">Transcription failed</p>
                    <Button
                      onClick={handleRetryTranscription}
                      variant="outline"
                      size="sm"
                      disabled={retryingTranscription}
                      className="flex items-center gap-2"
                    >
                      <RefreshCw className={`h-4 w-4 ${retryingTranscription ? 'animate-spin' : ''}`} />
                      {retryingTranscription ? 'Retrying...' : 'Retry Transcription'}
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Transcript Panel */}
          <div className="lg:w-2/3 p-6">
            <h3 className="font-semibold mb-4">Interactive Transcript</h3>
            <ScrollArea className="h-full">
              <div className="pr-4">
                {transcriptSegments.length > 0 ? (
                  transcriptSegments.map((segment, index) => 
                    renderTranscriptSegment(segment, index)
                  )
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No transcript available
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* Speaker Mapping Editor */}
        {call && (
          <SpeakerMappingEditor
            isOpen={showSpeakerEditor}
            onClose={() => setShowSpeakerEditor(false)}
            speakerMapping={call.speakerMapping || {}}
            onSave={handleSpeakerMappingSave}
            diarizationSegments={call.diarizationSegments || []}
            confidence={call.diarizationConfidence || 0}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};