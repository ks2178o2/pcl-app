import { expect, afterEach, beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Mock navigator.mediaDevices globally for all tests
if (typeof global !== 'undefined') {
  const mockEnumerateDevices = vi.fn().mockResolvedValue([])
  const mockGetUserMedia = vi.fn().mockResolvedValue({
    getTracks: vi.fn().mockReturnValue([{ stop: vi.fn(), kind: 'audio' }])
  })

  // Ensure navigator exists
  if (!global.navigator) {
    (global as any).navigator = {}
  }

  // Set up mediaDevices with proper property descriptor
  Object.defineProperty(global.navigator, 'mediaDevices', {
    writable: true,
    configurable: true,
    enumerable: true,
    value: Object.freeze({
      getUserMedia: mockGetUserMedia,
      enumerateDevices: mockEnumerateDevices
    })
  })

  // Also set up on window for browser-like environment
  if (typeof window !== 'undefined') {
    Object.defineProperty(window, 'navigator', {
      writable: true,
      configurable: true,
      value: global.navigator
    })
  }
}

// Cleanup after each test case
afterEach(() => {
  cleanup()
})

// Mock environment variables
Object.defineProperty(import.meta, 'env', {
  value: {
    VITE_SUPABASE_URL: 'https://test.supabase.co',
    VITE_SUPABASE_ANON_KEY: 'test-anon-key',
    VITE_API_URL: 'http://localhost:8000'
  },
  writable: true
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock console methods to reduce noise in tests
const originalError = console.error
const originalWarn = console.warn

beforeEach(() => {
  console.error = vi.fn()
  console.warn = vi.fn()
})

afterEach(() => {
  console.error = originalError
  console.warn = originalWarn
})
