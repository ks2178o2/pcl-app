import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useContactPreferences } from '../useContactPreferences';

describe('useContactPreferences', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useContactPreferences());
    expect(result.current).toBeDefined();
  });
});
