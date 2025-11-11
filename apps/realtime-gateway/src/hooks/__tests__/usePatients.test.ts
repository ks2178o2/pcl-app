import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePatients } from '../usePatients';

describe('usePatients', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => usePatients());
    expect(result.current).toBeDefined();
  });
});
