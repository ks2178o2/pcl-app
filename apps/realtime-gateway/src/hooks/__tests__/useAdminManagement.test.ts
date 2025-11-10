import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAdminManagement } from '../useAdminManagement';

describe('useAdminManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useAdminManagement());
    expect(result.current).toBeDefined();
  });
});
