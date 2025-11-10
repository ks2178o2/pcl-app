import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePatientSearch } from '../usePatientSearch';

describe('usePatientSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => usePatientSearch());
    expect(result.current).toBeDefined();
  });
});
