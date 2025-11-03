import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChunkedRecordingManager, RecordingProgress } from '@/services/chunkedRecordingService';

interface DebugInfo {
  callRecordId: string | null;
  isRecording: boolean;
  isComplete: boolean;
  totalDuration: number;
  currentChunk: number;
  totalChunks: number;
  chunksUploaded: number;
  chunksFailed: number;
  audioLevel?: number;
  errorMessage?: string;
  mediaRecorderState: string;
  streamActive: boolean;
  audioContextState: string;
}

export const RecordingDebug: React.FC = () => {
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const managerRef = useRef<ChunkedRecordingManager | null>(null);

  const updateDebugInfo = () => {
    if (!managerRef.current) {
      // Try to get instance from state if available
      const state = ChunkedRecordingManager.loadState();
      if (state) {
        setDebugInfo({
          callRecordId: state.callRecordId,
          isRecording: state.isRecording,
          isComplete: false,
          totalDuration: state.currentChunkNumber > 0 ? (Date.now() - state.totalStartTime) / 1000 : 0,
          currentChunk: state.currentChunkNumber,
          totalChunks: state.totalChunks,
          chunksUploaded: 0,
          chunksFailed: 0,
          mediaRecorderState: 'unknown',
          streamActive: state.isRecording,
          audioContextState: 'unknown',
          currentSliceSeq: state.currentSliceSeq || 0,
        } as DebugInfo & { currentSliceSeq?: number });
        return;
      }
      setDebugInfo(null);
      return;
    }

    const progress = managerRef.current.getProgress();
    
    // Try to access internal state (may not be accessible, so we'll use progress)
    setDebugInfo({
      callRecordId: null, // Would need to add getter to manager
      isRecording: progress.isRecording,
      isComplete: progress.isComplete,
      totalDuration: progress.totalDuration,
      currentChunk: progress.currentChunk,
      totalChunks: progress.totalChunks,
      chunksUploaded: progress.chunksUploaded,
      chunksFailed: progress.chunksFailed,
      audioLevel: progress.audioLevel,
      errorMessage: progress.errorMessage,
      mediaRecorderState: 'unknown', // Would need to add getter
      streamActive: progress.isRecording,
      audioContextState: 'unknown', // Would need to add getter
    });
  };

  useEffect(() => {
    if (isVisible) {
      // Try to get manager instance - this is a bit of a hack
      // In a real implementation, you'd want to pass the manager as a prop
      const state = ChunkedRecordingManager.loadState();
      updateDebugInfo();
      
      const interval = setInterval(updateDebugInfo, 1000);
      return () => clearInterval(interval);
    }
  }, [isVisible]);

  const clearRecordingState = () => {
    ChunkedRecordingManager.clearState();
    updateDebugInfo();
  };

  if (!isVisible) {
    return (
      <Button 
        onClick={() => setIsVisible(true)} 
        variant="outline" 
        size="sm"
        className="fixed bottom-4 left-4 z-50"
      >
        Debug Recording
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-4 left-4 w-80 z-50 max-h-96 overflow-y-auto">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex justify-between items-center">
          Recording Debug
          <Button 
            onClick={() => setIsVisible(false)} 
            variant="ghost" 
            size="sm"
          >
            ×
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {debugInfo ? (
          <div className="text-xs space-y-1">
            <div><strong>Call ID:</strong> {debugInfo.callRecordId || 'None'}</div>
            <div><strong>Recording:</strong> {debugInfo.isRecording ? 'Yes' : 'No'}</div>
            <div><strong>Complete:</strong> {debugInfo.isComplete ? 'Yes' : 'No'}</div>
            <div><strong>Duration:</strong> {debugInfo.totalDuration?.toFixed(1)}s</div>
            <div><strong>Chunk:</strong> {debugInfo.currentChunk} / {debugInfo.totalChunks}</div>
            <div><strong>Uploaded:</strong> {debugInfo.chunksUploaded}</div>
            <div><strong>Failed:</strong> {debugInfo.chunksFailed}</div>
            <div><strong>Stream Active:</strong> {debugInfo.streamActive ? 'Yes' : 'No'}</div>
            {debugInfo.audioLevel !== undefined && (
              <div><strong>Audio Level:</strong> {Math.round(debugInfo.audioLevel)}%</div>
            )}
            {debugInfo.errorMessage && (
              <div className="text-red-600"><strong>Error:</strong> {debugInfo.errorMessage}</div>
            )}
          </div>
        ) : (
          <div className="text-xs text-muted-foreground">No active recording</div>
        )}
        <div className="flex gap-2">
          <Button onClick={updateDebugInfo} size="sm" variant="outline">
            Refresh
          </Button>
          <Button onClick={clearRecordingState} size="sm" variant="destructive">
            Clear State
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

