import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAllContactPreferences } from '../useAllContactPreferences';

describe('useAllContactPreferences', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useAllContactPreferences());
    expect(result.current).toBeDefined();
  });
});
