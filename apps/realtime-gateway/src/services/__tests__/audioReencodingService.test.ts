import { describe, it, expect, vi, beforeEach } from 'vitest';
import { reencodeAudioSlices } from '../audioReencodingService';

// Mock AudioContext
global.AudioContext = vi.fn().mockImplementation(() => ({
  decodeAudioData: vi.fn(() => Promise.resolve({
    duration: 10,
    sampleRate: 44100,
    numberOfChannels: 2,
    length: 441000,
    getChannelData: vi.fn(() => new Float32Array(441000)),
    copyFromChannel: vi.fn(),
  })),
  createMediaStreamDestination: vi.fn(() => ({
    stream: new MediaStream(),
  })),
  close: vi.fn(),
}));

// Mock MediaRecorder
global.MediaRecorder = vi.fn().mockImplementation(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  state: 'inactive',
  ondataavailable: null,
  onstop: null,
}));

describe('audioReencodingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('reencodeAudioSlices', () => {
    it('should throw error for empty array', async () => {
      await expect(reencodeAudioSlices([])).rejects.toThrow('No slices to re-encode');
    });

    it('should return single slice without processing', async () => {
      const singleBlob = new Blob(['test'], { type: 'audio/webm' });
      const result = await reencodeAudioSlices([singleBlob]);
      expect(result).toBe(singleBlob);
    });

    it('should be a function', () => {
      expect(typeof reencodeAudioSlices).toBe('function');
    });

    // Note: Full re-encoding test would require complex mocking
    // This verifies the function exists and handles edge cases
  });
});

