import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSMSActivities } from '../useSMSActivities';

describe('useSMSActivities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useSMSActivities());
    expect(result.current).toBeDefined();
  });
});
