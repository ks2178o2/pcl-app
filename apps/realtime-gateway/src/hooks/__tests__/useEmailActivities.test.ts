import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useEmailActivities } from '../useEmailActivities';

describe('useEmailActivities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useEmailActivities());
    expect(result.current).toBeDefined();
  });
});
