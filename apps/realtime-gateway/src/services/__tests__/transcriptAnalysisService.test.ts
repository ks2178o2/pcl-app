import { describe, it, expect, vi, beforeEach } from 'vitest';
import { transcriptAnalysisService, AnalysisEngine } from '../transcriptAnalysisService';

// Mock fetch
global.fetch = vi.fn();

describe('transcriptAnalysisService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('analyzeTranscript', () => {
    it('should be a function', () => {
      expect(typeof transcriptAnalysisService.analyzeTranscript).toBe('function');
    });

    it('should handle empty transcript', async () => {
      const result = await transcriptAnalysisService.analyzeTranscript('', 'auto');
      expect(result).toBeDefined();
    });
  });

  describe('AnalysisEngine enum', () => {
    it('should have expected values', () => {
      expect(AnalysisEngine.AUTO).toBeDefined();
      expect(AnalysisEngine.OPENAI).toBeDefined();
      expect(AnalysisEngine.HEURISTIC).toBeDefined();
    });
  });
});

