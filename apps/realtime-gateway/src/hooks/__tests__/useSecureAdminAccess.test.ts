import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSecureAdminAccess } from '../useSecureAdminAccess';

describe('useSecureAdminAccess', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useSecureAdminAccess());
    expect(result.current).toBeDefined();
  });
});
