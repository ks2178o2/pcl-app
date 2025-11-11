import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useVoiceProfiles } from '../useVoiceProfiles';

describe('useVoiceProfiles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useVoiceProfiles());
    expect(result.current).toBeDefined();
  });
});
