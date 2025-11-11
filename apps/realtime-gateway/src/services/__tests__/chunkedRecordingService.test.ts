import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChunkedRecordingManager, formatDuration, validateState } from '../chunkedRecordingService';

// Mock IndexedDB
const mockIndexedDB = {
  open: vi.fn(() => ({
    onupgradeneeded: null,
    onsuccess: null,
    onerror: null,
    result: {
      createObjectStore: vi.fn(),
      transaction: vi.fn(() => ({
        objectStore: vi.fn(() => ({
          put: vi.fn(),
          get: vi.fn(),
          delete: vi.fn(),
          openCursor: vi.fn(),
        })),
        oncomplete: null,
        onerror: null,
        onabort: null,
      })),
    },
  })),
};

// Mock MediaRecorder
global.MediaRecorder = vi.fn().mockImplementation(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  state: 'inactive',
  ondataavailable: null,
  onerror: null,
  onstart: null,
  onstop: null,
  onpause: null,
  onresume: null,
}));

// Mock getUserMedia
global.navigator = {
  ...global.navigator,
  mediaDevices: {
    getUserMedia: vi.fn(() => Promise.resolve(new MediaStream())),
    enumerateDevices: vi.fn(() => Promise.resolve([])),
  } as any,
};

describe('chunkedRecordingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock indexedDB
    (global as any).indexedDB = mockIndexedDB;
  });

  describe('formatDuration', () => {
    it('should format seconds correctly', () => {
      expect(formatDuration(0)).toBe('0:00');
      expect(formatDuration(30)).toBe('0:30');
      expect(formatDuration(60)).toBe('1:00');
      expect(formatDuration(90)).toBe('1:30');
      expect(formatDuration(3661)).toBe('1:01:01');
    });

    it('should handle negative values', () => {
      expect(formatDuration(-1)).toBe('0:00');
    });
  });

  describe('validateState', () => {
    it('should validate correct state', () => {
      const validState = {
        callRecordId: 'call-123',
        totalStartTime: Date.now(),
        isRecording: false,
        lastUpdateTime: Date.now(),
      };

      const result = validateState(validState);
      expect(result.isValid).toBe(true);
    });

    it('should reject state with missing callRecordId', () => {
      const invalidState = {
        totalStartTime: Date.now(),
        isRecording: false,
        lastUpdateTime: Date.now(),
      };

      const result = validateState(invalidState as any);
      expect(result.isValid).toBe(false);
    });

    it('should reject state with invalid timestamps', () => {
      const invalidState = {
        callRecordId: 'call-123',
        totalStartTime: -1,
        isRecording: false,
        lastUpdateTime: Date.now(),
      };

      const result = validateState(invalidState);
      expect(result.isValid).toBe(false);
    });
  });

  describe('ChunkedRecordingManager', () => {
    it('should create instance', () => {
      const progressCallback = vi.fn();
      const manager = new ChunkedRecordingManager(progressCallback);
      
      expect(manager).toBeDefined();
    });

    it('should have start method', () => {
      const progressCallback = vi.fn();
      const manager = new ChunkedRecordingManager(progressCallback);
      
      expect(typeof manager.start).toBe('function');
    });

    it('should have stop method', () => {
      const progressCallback = vi.fn();
      const manager = new ChunkedRecordingManager(progressCallback);
      
      expect(typeof manager.stop).toBe('function');
    });

    it('should have pause method', () => {
      const progressCallback = vi.fn();
      const manager = new ChunkedRecordingManager(progressCallback);
      
      expect(typeof manager.pause).toBe('function');
    });

    it('should have cleanup method', () => {
      const progressCallback = vi.fn();
      const manager = new ChunkedRecordingManager(progressCallback);
      
      expect(typeof manager.cleanup).toBe('function');
    });

    it('should handle cleanup without errors', () => {
      const progressCallback = vi.fn();
      const manager = new ChunkedRecordingManager(progressCallback);
      
      expect(() => manager.cleanup()).not.toThrow();
    });
  });
});

