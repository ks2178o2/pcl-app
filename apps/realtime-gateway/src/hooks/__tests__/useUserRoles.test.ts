import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useUserRoles } from '../useUserRoles';

describe('useUserRoles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useUserRoles());
    expect(result.current).toBeDefined();
  });
});
