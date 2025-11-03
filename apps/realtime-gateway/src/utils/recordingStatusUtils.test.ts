import { describe, it, expect } from 'vitest';
import { getRecordingAction, getStatusColor } from './recordingStatusUtils';
import type { CallRecord } from './recordingStatusUtils';
import { Trash2, RefreshCw, Clock, BarChart3 } from 'lucide-react';

describe('recordingStatusUtils', () => {
  describe('getRecordingAction', () => {
    it('detects zero-duration recordings for deletion', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(),
        duration: 0
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('delete');
      expect(action.icon).toBe(Trash2);
      expect(action.variant).toBe('destructive');
      expect(action.reason).toContain('0:00');
    });

    it('detects missing audio files for deletion', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(),
        duration: 120,
        audioPath: null,
        audioBlob: null
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('delete');
      expect(action.icon).toBe(Trash2);
      expect(action.variant).toBe('destructive');
      expect(action.reason).toContain('No audio file');
    });

    it('detects failed transcriptions for retry', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: 'failed'
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('retry-transcription');
      expect(action.icon).toBe(RefreshCw);
      expect(action.variant).toBe('outline');
    });

    it('detects stuck transcriptions for retry', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: 'Transcribing audio...'
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('retry-transcription');
      expect(action.icon).toBe(RefreshCw);
    });

    it('identifies completed transcriptions for analysis', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(),
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: 'This is a complete transcription with enough content to be considered valid and ready for analysis.'
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('view-analysis');
      expect(action.icon).toBe(BarChart3);
      expect(action.variant).toBe('default');
      expect(action.reason).toContain('Ready to view');
    });

    it('shows wait state for processing', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(),
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: 'Transcribing audio...'
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('wait');
      expect(action.icon).toBe(Clock);
      expect(action.disabled).toBe(true);
    });

    it('handles recordings with audio blob', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(Date.now() - 3 * 60 * 1000), // 3 minutes ago (not too recent)
        duration: 120,
        audioBlob: new Blob(),
        transcript: 'Complete transcription with enough content to be considered complete'
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('view-analysis');
    });

    it('handles very recent transcriptions', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(Date.now() - 30 * 1000), // 30 seconds ago
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: 'Transcribing audio...'
      };

      const action = getRecordingAction(call);

      // Should wait if very recent
      expect(action.action).toBe('wait');
      expect(action.disabled).toBe(true);
    });

    it('handles recordings without timestamp', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(),
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: null
      };

      const action = getRecordingAction(call);

      expect(action.action).toBeDefined();
    });

    it('handles partial transcripts', () => {
      const call: CallRecord = {
        id: 'call-1',
        customer_name: 'Test Customer',
        timestamp: new Date(),
        duration: 120,
        audioPath: 'path/to/audio.mp3',
        transcript: 'Incomplete'  // Too short to be complete
      };

      const action = getRecordingAction(call);

      expect(action.action).toBe('wait');
    });
  });

  describe('getStatusColor', () => {
    it('returns red color for delete action', () => {
      const color = getStatusColor('delete');
      expect(color).toContain('red');
    });

    it('returns yellow color for retry action', () => {
      const color = getStatusColor('retry-transcription');
      expect(color).toContain('yellow');
    });

    it('returns green color for view analysis action', () => {
      const color = getStatusColor('view-analysis');
      expect(color).toContain('green');
    });

    it('returns gray color for other actions', () => {
      const color = getStatusColor('wait');
      expect(color).toContain('gray');
    });

    it('handles unknown action', () => {
      const color = getStatusColor('unknown-action');
      expect(color).toContain('gray');
    });
  });
});

