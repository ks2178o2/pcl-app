import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  Square, 
  Volume2, 
  Clock,
  Users,
  Zap,
  MessageSquare
} from 'lucide-react';
import { normalizeDiarizationSegments } from '@/utils/speakerUtils';

interface TranscriptSegment {
  id: string;
  speaker: string;
  text: string;
  startTime: number;
  endTime: number;
  confidence?: number;
}

interface SpeakerTrack {
  speaker: string;
  color: string;
  segments: TranscriptSegment[];
}

interface SpeakerDiarizationPlayerProps {
  audioUrl?: string;
  transcript?: string;
  diarizationSegments?: any[];
  speakerMapping?: Record<string, string>;
  duration: number;
  onTimeUpdate?: (currentTime: number) => void;
}

export const SpeakerDiarizationPlayer: React.FC<SpeakerDiarizationPlayerProps> = ({
  audioUrl,
  transcript,
  diarizationSegments,
  speakerMapping,
  duration,
  onTimeUpdate
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState('1');
  const [volume, setVolume] = useState(100);
  const [speakerTracks, setSpeakerTracks] = useState<SpeakerTrack[]>([]);
  const [activeSegment, setActiveSegment] = useState<string | null>(null);
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 }); // Show 50 segments at a time

  // Speaker colors for visualization
  const speakerColors = [
    '#3B82F6', // Blue
    '#10B981', // Green  
    '#F59E0B', // Amber
    '#EF4444', // Red
    '#8B5CF6', // Violet
    '#06B6D4', // Cyan
    '#F97316', // Orange
    '#EC4899'  // Pink
  ];

  // Helper to normalize segments from any input format
  const normalizeSegments = useCallback((segments: any[]): TranscriptSegment[] => {
    return normalizeDiarizationSegments(segments);
  }, []);

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !duration || speakerTracks.length === 0) {
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    // Optimize: Sample segments for very large datasets
    const MAX_SEGMENTS_TO_DRAW = 5000;
    
    speakerTracks.forEach((track, trackIndex) => {
      const trackHeight = height / speakerTracks.length;
      const trackY = trackIndex * trackHeight;
      
      // Sample segments if too many
      const segments = track.segments.length > MAX_SEGMENTS_TO_DRAW
        ? track.segments.filter((_, i) => i % Math.ceil(track.segments.length / MAX_SEGMENTS_TO_DRAW) === 0)
        : track.segments;
      
      segments.forEach(segment => {
        const startX = (segment.startTime / duration) * width;
        const endX = (segment.endTime / duration) * width;
        
        // Skip tiny segments (< 1px wide) for performance
        if (endX - startX < 1) return;
        
        ctx.fillStyle = segment.id === activeSegment ? track.color : `${track.color}66`;
        
        // Simplified waveform pattern for better performance
        const step = Math.max(2, Math.floor((endX - startX) / 50));
        for (let x = startX; x < endX; x += step) {
          const amplitude = (Math.sin((x - startX) * 0.1) + 1) * 0.5;
          const barHeight = amplitude * (trackHeight * 0.6);
          const barY = trackY + (trackHeight - barHeight) / 2;
          
          ctx.fillRect(x, barY, Math.min(step, 2), barHeight);
        }
      });
    });

    // Draw current time indicator
    const currentX = (currentTime / duration) * width;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(currentX, 0);
    ctx.lineTo(currentX, height);
    ctx.stroke();
  }, [speakerTracks, currentTime, duration, activeSegment]);

  // Parse diarization data into speaker tracks
  useEffect(() => {
    console.log('Processing diarization data:', { 
      hasDiarizationSegments: !!diarizationSegments, 
      segmentsLength: diarizationSegments?.length,
      hasTranscript: !!transcript,
      duration 
    });
    // If we have structured diarization segments, use those
    if (diarizationSegments && diarizationSegments.length > 0) {
      console.log('Using structured diarization segments:', diarizationSegments.length);
      
      // Normalize segments (handles both compact and standard formats)
      const normalizedSegs = normalizeSegments(diarizationSegments);
      
      const segments: TranscriptSegment[] = normalizedSegs.map((segment) => ({
        id: segment.id,
        speaker: speakerMapping?.[segment.speaker] || segment.speaker,
        text: segment.text,
        startTime: segment.startTime,
        endTime: segment.endTime,
        confidence: segment.confidence
      }));

      // Group segments by speaker
      const speakerMap = new Map<string, TranscriptSegment[]>();
      segments.forEach(segment => {
        if (!speakerMap.has(segment.speaker)) {
          speakerMap.set(segment.speaker, []);
        }
        speakerMap.get(segment.speaker)!.push(segment);
      });

      // Create speaker tracks with colors
      const tracks: SpeakerTrack[] = [];
      let colorIndex = 0;
      
      speakerMap.forEach((segments, speaker) => {
        tracks.push({
          speaker,
          color: speakerColors[colorIndex % speakerColors.length],
          segments: segments.sort((a, b) => a.startTime - b.startTime)
        });
        colorIndex++;
      });

      setSpeakerTracks(tracks);
      console.log('Created speaker tracks:', tracks.map(t => ({ 
        speaker: t.speaker, 
        segmentCount: t.segments.length,
        color: t.color 
      })));
      return;
    }

    // Fallback to parsing transcript string if no structured data
    if (!transcript || transcript.trim() === '') {
      // Create a fallback track if no transcript is available
      setSpeakerTracks([{
        speaker: 'No transcript available',
        color: speakerColors[0],
        segments: [{
          id: 'fallback-segment',
          speaker: 'System',
          text: 'Transcript is not available. Please regenerate the transcript to see speaker diarization.',
          startTime: 0,
          endTime: duration,
          confidence: 1.0
        }]
      }]);
      return;
    }

    const parseTranscriptToSegments = (text: string): TranscriptSegment[] => {
      const segments: TranscriptSegment[] = [];
      const lines = text.split('\n').filter(line => line.trim());
      
      console.log('Parsing transcript with', lines.length, 'lines');
      
      // Calculate total words for better timing
      const totalWords = text.split(/\s+/).length;
      const averageWordsPerMinute = 150; // Typical speaking rate
      const estimatedDuration = (totalWords / averageWordsPerMinute) * 60;
      const actualDuration = Math.max(duration, estimatedDuration);
      
      let cumulativeTime = 0;
      
      lines.forEach((line, index) => {
        // Support multiple transcript formats
        let speakerMatch = line.match(/^\[([^\]]+)\]:\s*(.*)$/); // [Speaker]: text
        if (!speakerMatch) {
          speakerMatch = line.match(/^([^:]+):\s*(.*)$/); // Speaker: text
        }
        if (!speakerMatch) {
          speakerMatch = line.match(/^([^-]+)-\s*(.*)$/); // Speaker- text
        }
        
        if (speakerMatch) {
          const speaker = speakerMatch[1].trim();
          const content = speakerMatch[2].trim();
          
          if (content) { // Only process non-empty content
            // Calculate segment duration based on word count
            const wordsInSegment = content.split(/\s+/).length;
            const segmentDurationSeconds = Math.max(2, (wordsInSegment / averageWordsPerMinute) * 60);
            
            const startTime = cumulativeTime;
            const endTime = Math.min(actualDuration, cumulativeTime + segmentDurationSeconds);
            
            segments.push({
              id: `segment-${index}`,
              speaker,
              text: content,
              startTime,
              endTime,
              confidence: 0.85 + Math.random() * 0.15 // Simulated confidence
            });
            
            cumulativeTime = endTime + 0.5; // Small gap between segments
          }
        }
      });
      
      console.log('Parsed', segments.length, 'segments from transcript');
      return segments;
    };

    const segments = parseTranscriptToSegments(transcript);
    
    // Group segments by speaker
    const speakerMap = new Map<string, TranscriptSegment[]>();
    segments.forEach(segment => {
      if (!speakerMap.has(segment.speaker)) {
        speakerMap.set(segment.speaker, []);
      }
      speakerMap.get(segment.speaker)!.push(segment);
    });

    // Create speaker tracks with colors
    const tracks: SpeakerTrack[] = [];
    let colorIndex = 0;
    
    speakerMap.forEach((segments, speaker) => {
      tracks.push({
        speaker,
        color: speakerColors[colorIndex % speakerColors.length],
        segments: segments.sort((a, b) => a.startTime - b.startTime)
      });
      colorIndex++;
    });

    setSpeakerTracks(tracks);
  }, [transcript, diarizationSegments, speakerMapping, duration, normalizeSegments]);

  // Draw waveform when speaker tracks change (debounced for performance)
  useEffect(() => {
    if (speakerTracks.length === 0) return;
    
    const timeoutId = setTimeout(() => {
      requestAnimationFrame(() => {
        drawWaveform();
      });
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [speakerTracks, drawWaveform]);

  // Update active segment based on current time
  useEffect(() => {
    const currentSegment = speakerTracks
      .flatMap(track => track.segments)
      .find(segment => currentTime >= segment.startTime && currentTime < segment.endTime);
    
    setActiveSegment(currentSegment?.id || null);
  }, [currentTime, speakerTracks]);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      const time = audio.currentTime;
      setCurrentTime(time);
      onTimeUpdate?.(time);
      // Throttle waveform updates during playback
      requestAnimationFrame(() => {
        drawWaveform();
      });
    };

    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [onTimeUpdate]);

  // Playback rate control
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = parseFloat(playbackSpeed);
    }
  }, [playbackSpeed]);

  // Volume control
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume / 100;
    }
  }, [volume]);

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

  const handleWaveformClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!audioRef.current || !duration) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;

    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const jumpToSegment = (segment: TranscriptSegment) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = segment.startTime;
    setCurrentTime(segment.startTime);
  };

  const formatTime = (seconds: number) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeakerIcon = (speaker: string) => {
    const lower = speaker.toLowerCase();
    if (lower.includes('sales') || lower.includes('provider')) return '🎯';
    if (lower.includes('support')) return '🤝';
    return '👤';
  };

  // Memoize sorted segments for efficient rendering
  const sortedSegments = useMemo(() => {
    const allSegments = speakerTracks.flatMap(track => 
      track.segments.map(segment => ({
        ...segment,
        trackColor: track.color,
        trackSpeaker: track.speaker
      }))
    );
    return allSegments.sort((a, b) => a.startTime - b.startTime);
  }, [speakerTracks]);

  // Render only visible segments for performance
  const visibleSegments = useMemo(() => {
    return sortedSegments.slice(visibleRange.start, visibleRange.end);
  }, [sortedSegments, visibleRange]);

  // Update visible range on scroll
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const scrollTop = target.scrollTop;
    const itemHeight = 130; // Approximate height per segment
    const visibleCount = Math.ceil(target.clientHeight / itemHeight);
    const bufferCount = 10; // Extra items to render above/below viewport
    
    const start = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferCount);
    const end = Math.min(sortedSegments.length, start + visibleCount + bufferCount * 2);
    
    setVisibleRange({ start, end });
  }, [sortedSegments.length]);

  return (
    <div className="space-y-6">
      {/* Audio Element */}
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} preload="metadata" />
      )}

      {/* Main Controls */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <Button onClick={togglePlayback} size="lg" className="w-12 h-12">
                {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
              </Button>
              <Button onClick={stopPlayback} variant="outline" size="lg" className="w-12 h-12">
                <Square className="h-5 w-5" />
              </Button>
              
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4" />
                <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Speed Control */}
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                <Select value={playbackSpeed} onValueChange={setPlaybackSpeed}>
                  <SelectTrigger className="w-20">
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
              <div className="flex items-center gap-2">
                <Volume2 className="h-4 w-4" />
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={volume}
                  onChange={(e) => setVolume(Number(e.target.value))}
                  className="w-20"
                />
              </div>
            </div>
          </div>

          {/* Speaker Tracks Visualization */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Users className="h-4 w-4" />
              Speaker Tracks
            </div>
            
            {/* Waveform Canvas */}
            <div className="relative border rounded-lg overflow-hidden bg-muted/30">
              <canvas
                ref={canvasRef}
                width={800}
                height={speakerTracks.length * 60}
                className="w-full h-auto cursor-pointer"
                onClick={handleWaveformClick}
              />
              
              {/* Speaker Labels */}
              <div className="absolute left-0 top-0 bottom-0 w-24 bg-background/90 border-r">
                {speakerTracks.map((track, index) => (
                  <div 
                    key={track.speaker}
                    className="flex items-center justify-center h-[60px] text-xs font-medium border-b"
                    style={{ 
                      color: track.color,
                      height: `${100 / speakerTracks.length}%` 
                    }}
                  >
                    <div className="text-center">
                      <div>{getSpeakerIcon(track.speaker)}</div>
                      <div className="truncate max-w-20">{track.speaker}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Time markers */}
            <div className="relative h-6 border-t pt-2">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0:00</span>
                <span>{formatTime(duration / 4)}</span>
                <span>{formatTime(duration / 2)}</span>
                <span>{formatTime((duration * 3) / 4)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transcript Panel */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-4 w-4" />
            <h3 className="font-semibold">Interactive Transcript</h3>
            <Badge variant="secondary" className="text-xs">
              Click to jump to time
            </Badge>
            {sortedSegments.length > 100 && (
              <Badge variant="outline" className="text-xs ml-auto">
                {sortedSegments.length.toLocaleString()} segments (optimized)
              </Badge>
            )}
          </div>
          
          {!transcript || transcript.trim() === '' ? (
            <div className="text-center py-8 text-muted-foreground">
              <div className="mb-4">
                <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <h4 className="font-medium">No Transcript Available</h4>
                <p className="text-sm">The transcript failed to generate. Please try regenerating it.</p>
              </div>
            </div>
          ) : (
            <ScrollArea className="h-[400px]" onScroll={handleScroll}>
              <div className="space-y-3 pr-4" style={{ minHeight: `${sortedSegments.length * 130}px` }}>
                <div style={{ paddingTop: `${visibleRange.start * 130}px` }}>
                  {visibleSegments.map((segment) => {
                    const track = speakerTracks.find(t => t.speaker === segment.trackSpeaker);
                    if (!track) return null;

                    return (
                      <div
                        key={segment.id}
                        className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 mb-3 ${
                          segment.id === activeSegment
                            ? 'ring-2 shadow-md transform scale-[1.02]'
                            : 'hover:shadow-sm'
                        }`}
                        style={{
                          backgroundColor: segment.id === activeSegment 
                            ? `${track.color}15` 
                            : `${track.color}05`,
                          borderColor: segment.id === activeSegment 
                            ? track.color 
                            : `${track.color}40`
                        }}
                        onClick={() => jumpToSegment(segment)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span style={{ color: track.color }}>
                              {getSpeakerIcon(segment.speaker)}
                            </span>
                            <span className="font-semibold" style={{ color: track.color }}>
                              {segment.speaker}
                            </span>
                            {segment.confidence && (
                              <Badge variant="outline" className="text-xs">
                                {Math.round(segment.confidence * 100)}%
                              </Badge>
                            )}
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatTime(segment.startTime)}
                          </span>
                        </div>
                        <p className="text-sm leading-relaxed">{segment.text}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};