import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useRecordingState } from '../useRecordingState';

describe('useRecordingState', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useRecordingState());
    expect(result.current).toBeDefined();
  });
});
