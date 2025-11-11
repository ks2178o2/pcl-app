import { Trash2, RefreshCw, Clock, BarChart3 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface CallRecord {
  id: string;
  customer_name: string;
  patientName?: string;
  timestamp: string | Date;
  duration?: number | null;
  audioPath?: string | null;
  audioBlob?: Blob | null;
  transcript?: string | null;
  salespersonName?: string;
}

export interface RecordingAction {
  action: 'delete' | 'retry-transcription' | 'view-analysis' | 'wait';
  label: string;
  icon: LucideIcon;
  variant: 'default' | 'secondary' | 'outline' | 'destructive';
  reason: string;
  disabled: boolean;
}

// Helper function to determine transcript status
const getTranscriptStatus = (transcript?: string | null): 'not-started' | 'in-progress' | 'failed' | 'complete' => {
  if (!transcript) return 'not-started';
  if (transcript === 'Transcribing audio...') return 'in-progress';
  if (transcript.includes('failed') || transcript.includes('Transcription failed')) return 'failed';
  if (transcript.length > 50) return 'complete'; // Has actual content
  return 'in-progress';
};

// Helper function to determine recording state and appropriate action
export const getRecordingAction = (call: CallRecord): RecordingAction => {
  const now = new Date();
  const recordingTime = new Date(call.timestamp);
  const timeSinceRecording = now.getTime() - recordingTime.getTime();
  const RECENT_THRESHOLD = 2 * 60 * 1000; // 2 minutes ago
  
  // Check if recording has zero or very short duration
  const isZeroDuration = !call.duration || call.duration < 1; // Less than 1 second
  
  // Check if audio file exists
  const hasAudioFile = !!(call.audioPath || call.audioBlob);
  
  // Check transcription status
  const transcriptStatus = getTranscriptStatus(call.transcript);
  
  // Determine action based on state
  if (isZeroDuration) {
    return {
      action: 'delete',
      label: 'Delete',
      icon: Trash2,
      variant: 'destructive',
      reason: 'Recording has no audio content (0:00 duration)',
      disabled: false
    };
  }
  
  if (!hasAudioFile) {
    return {
      action: 'delete',
      label: 'Delete',
      icon: Trash2,
      variant: 'destructive',
      reason: 'No audio file found',
      disabled: false
    };
  }
  
  if (transcriptStatus === 'failed' || 
      (transcriptStatus === 'in-progress' && timeSinceRecording > RECENT_THRESHOLD)) {
    return {
      action: 'retry-transcription',
      label: 'Retry Transcription',
      icon: RefreshCw,
      variant: 'outline',
      reason: 'Transcription failed or stuck',
      disabled: false
    };
  }
  
  if (transcriptStatus === 'complete' && hasAudioFile) {
    return {
      action: 'view-analysis',
      label: 'View Analysis',
      icon: BarChart3,
      variant: 'default',
      reason: 'Ready to view analysis',
      disabled: false
    };
  }
  
  // Default case - still processing
  return {
    action: 'wait',
    label: 'Processing...',
    icon: Clock,
    variant: 'secondary',
    reason: 'Recording is still being processed',
    disabled: true
  };
};

// Status color coding helper
export const getStatusColor = (action: string): string => {
  switch (action) {
    case 'delete': return 'text-red-600 bg-red-50 border-red-200';
    case 'retry-transcription': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'view-analysis': return 'text-green-600 bg-green-50 border-green-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

