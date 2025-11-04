import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/integrations/supabase/client', () => {
  const rows: any[] = [
    { analysis_data: { summary: 'older' }, created_at: '2025-01-01T00:00:00Z' },
    { analysis_data: { summary: 'newest' }, created_at: '2025-12-31T00:00:00Z' },
  ];

  const q = {
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    order: vi.fn().mockReturnThis(),
    limit: vi.fn().mockReturnThis(),
  };

  return {
    supabase: {
      from: vi.fn().mockReturnValue(q),
      auth: { getSession: vi.fn().mockResolvedValue({ session: { access_token: 't' } }) }
    },
    // for runtime dynamic import path used in service
    default: { supabase: { from: vi.fn().mockReturnValue(q) } },
  };
});

// After import-mocks
import { transcriptAnalysisService } from '@/services/transcriptAnalysisService';

// Helper to patch the chained call return value for .from('call_analyses')
function setSupabaseRows(rows: any[]) {
  const mod = require('@/integrations/supabase/client');
  const q = {
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    order: vi.fn().mockReturnThis(),
    limit: vi.fn().mockResolvedValue({ data: rows, error: null }),
  };
  mod.supabase.from = vi.fn().mockReturnValue(q);
}

describe('transcriptAnalysisService', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getStoredAnalysis returns newest row without PGRST116', async () => {
    setSupabaseRows([
      { analysis_data: { summary: 'older' }, created_at: '2025-01-01T00:00:00Z' },
      { analysis_data: { summary: 'newest' }, created_at: '2025-12-31T00:00:00Z' },
    ]);
    const result = await transcriptAnalysisService.getStoredAnalysis('call-1');
    expect(result?.summary).toBe('newest');
  });

  it('analyzeTranscript parses fenced JSON', async () => {
    // Mock backend analyze to return fenced json
    const fetchSpy = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      json: async () => ({ analysis: '```json\n{ "summary": "ok" }\n```', provider: 'gemini' })
    } as any);

    const analysis = await transcriptAnalysisService.analyzeTranscript(
      'hello', 'Customer', 'Sales', 'c1', 'u1', 'llm'
    );
    expect(analysis.summary).toBe('ok');
    fetchSpy.mockRestore();
  });

  it('analyzeTranscript extracts JSON substring when extra prose present', async () => {
    const body = 'noise before { "summary": "ok2" } noise after';
    const fetchSpy = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      json: async () => ({ analysis: body, provider: 'openai' })
    } as any);

    const analysis = await transcriptAnalysisService.analyzeTranscript(
      'hello', 'Customer', 'Sales', undefined, undefined, 'llm'
    );
    expect(analysis.summary).toBe('ok2');
    fetchSpy.mockRestore();
  });
});


