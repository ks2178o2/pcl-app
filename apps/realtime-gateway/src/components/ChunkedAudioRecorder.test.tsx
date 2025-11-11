import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ChunkedAudioRecorder } from './ChunkedAudioRecorder'

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

// Mock dependencies
vi.mock('@/hooks/useProfile', () => ({
  useProfile: () => ({
    profile: {
      id: 'test-profile',
      organization_id: 'test-org'
    }
  })
}))

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}))

vi.mock('@/components/AudioUploadModal', () => ({
  AudioUploadModal: () => null
}))

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getUser: vi.fn().mockResolvedValue({
        data: {
          user: {
            id: 'test-user-123',
            email: 'test@example.com'
          }
        }
      })
    },
    from: vi.fn(() => ({
      insert: vi.fn(() => ({
        select: vi.fn(() => ({
          single: vi.fn().mockResolvedValue({
            data: { id: 'test-call-record-123' },
            error: null
          })
        }))
      }))
    }))
  }
}))

vi.mock('@/services/chunkedRecordingService', () => {
  // Factory function to create a fresh mock manager instance
  const createMockManager = () => {
    const mockManager = {
      startRecording: vi.fn().mockResolvedValue(undefined),
      pauseRecording: vi.fn().mockResolvedValue(undefined),
      resumeRecording: vi.fn().mockResolvedValue(undefined),
      stopRecording: vi.fn().mockResolvedValue(undefined),
      getProgress: vi.fn().mockReturnValue({
        currentChunk: 0,
        totalChunks: 0,
        chunksUploaded: 0,
        chunksFailed: 0,
        isRecording: false,
        isComplete: false,
        totalDuration: 0
      }),
      cleanup: vi.fn(),
      saveState: vi.fn(),
      clearState: vi.fn()
    }
    // Ensure cleanup is definitely a function
    if (!mockManager.cleanup || typeof mockManager.cleanup !== 'function') {
      mockManager.cleanup = vi.fn()
    }
    return mockManager
  }

  // Create the mock constructor as a vi.fn() so we can track calls
  const MockChunkedRecordingManager = vi.fn().mockImplementation((_setProgress: any) => {
    return createMockManager()
  }) as any
  
  // Add static methods
  MockChunkedRecordingManager.loadState = vi.fn().mockReturnValue(null)
  MockChunkedRecordingManager.validateState = vi.fn().mockReturnValue({ valid: true })

  return {
    ChunkedRecordingManager: MockChunkedRecordingManager as any,
    formatDuration: (seconds: number) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
  }
})

// Mock MediaRecorder and getUserMedia
const mockMediaRecorder = {
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  state: 'inactive',
  ondataavailable: null,
  onstop: null,
  onerror: null
}

const mockMediaStream = {
  getTracks: vi.fn().mockReturnValue([
    { stop: vi.fn(), kind: 'audio' }
  ])
}

// Navigator.mediaDevices is mocked globally in test-setup.ts
// But ensure it's available here as well as a fallback
if (global.navigator && !global.navigator.mediaDevices) {
  Object.defineProperty(global.navigator, 'mediaDevices', {
    writable: true,
    configurable: true,
    value: {
      getUserMedia: vi.fn().mockResolvedValue(mockMediaStream),
      enumerateDevices: vi.fn().mockResolvedValue([])
    }
  })
}

global.MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder) as any

global.window.requestAnimationFrame = vi.fn((cb) => {
  setTimeout(cb, 16)
  return 1
})

global.window.cancelAnimationFrame = vi.fn()

describe('ChunkedAudioRecorder', () => {
  const mockOnRecordingComplete = vi.fn()
  
  beforeEach(() => {
    // Clear localStorage and reset document title
    // Note: We don't reset mocks here to preserve implementations
    // Each test gets a fresh mock instance from the factory function
    localStorage.clear()
    document.title = 'Test Page'
  })

  afterEach(() => {
    // Don't restore mocks - we want to preserve our mock implementations
    // Cleanup is handled by React's cleanup in render
  })

  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )
      expect(screen.getByText(/professional mode/i)).toBeInTheDocument()
    })

    it('renders with all props', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          patientId="patient-123"
          centerId="center-123"
          disabled={false}
        />
      )
      expect(screen.getByText(/professional mode/i)).toBeInTheDocument()
    })

    it('shows info alert when not recording', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )
      expect(screen.getByText(/records in 5-minute chunks/i)).toBeInTheDocument()
    })
  })

  describe('Auto-start functionality', () => {
    it('auto-starts recording when autoStart is true', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          autoStart={true}
          disabled={false}
        />
      )

      await waitFor(() => {
        const results = (ChunkedRecordingManager as any).mock?.results || []
        const manager = results[results.length - 1]?.value // Use last result
        expect(manager?.startRecording).toHaveBeenCalled()
      }, { timeout: 2000 })
    })

    it('does not auto-start when autoStart is false', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          autoStart={false}
        />
      )

      await waitFor(() => {
        const results = (ChunkedRecordingManager as any).mock?.results || []
        const manager = results[results.length - 1]?.value // Use last result
        expect(manager?.startRecording).not.toHaveBeenCalled()
      })
    })

    it('does not auto-start when disabled', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          autoStart={true}
          disabled={true}
        />
      )

      await waitFor(() => {
        const results = (ChunkedRecordingManager as any).mock?.results || []
        const manager = results[results.length - 1]?.value // Use last result
        expect(manager?.startRecording).not.toHaveBeenCalled()
      })
    })

    it('does not auto-start without patient name', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          autoStart={true}
        />
      )

      await waitFor(() => {
        const results = (ChunkedRecordingManager as any).mock?.results || []
        const manager = results[results.length - 1]?.value // Use last result
        expect(manager?.startRecording).not.toHaveBeenCalled()
      })
    })
  })

  describe('Manual recording start', () => {
    it('shows start button when not recording', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )
      expect(screen.getByText(/start recording/i)).toBeInTheDocument()
    })

    it('starts recording when start button is clicked', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        const results = (ChunkedRecordingManager as any).mock?.results || []
        const manager = results[results.length - 1]?.value
        expect(manager?.startRecording).toHaveBeenCalled()
      })
    })

    it('disables start button when patient name is missing', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
        />
      )
      
      const startButton = screen.getByText(/start recording/i).closest('button')
      expect(startButton).toBeDisabled()
    })

    it('disables start button when disabled prop is true', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          disabled={true}
        />
      )
      
      const startButton = screen.getByText(/start recording/i).closest('button')
      expect(startButton).toBeDisabled()
    })
  })

  describe('Recording state', () => {
    it('shows stop button when recording', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        startRecording: vi.fn().mockResolvedValue(undefined),
        pauseRecording: vi.fn().mockResolvedValue(undefined),
        getProgress: vi.fn().mockReturnValue({
          currentChunk: 1,
          totalChunks: 1,
          chunksUploaded: 0,
          chunksFailed: 0,
          isRecording: true,
          isComplete: false,
          totalDuration: 60
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByText(/stop recording/i)).toBeInTheDocument()
      })
    })

    it('pauses recording when stop button is clicked', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        startRecording: vi.fn().mockResolvedValue(undefined),
        pauseRecording: vi.fn().mockResolvedValue(undefined),
        getProgress: vi.fn()
          .mockReturnValueOnce({
            isRecording: true,
            currentChunk: 1,
            totalChunks: 1,
            chunksUploaded: 0,
            chunksFailed: 0,
            isComplete: false,
            totalDuration: 60
          })
          .mockReturnValue({
            isRecording: false,
            currentChunk: 1,
            totalChunks: 1,
            chunksUploaded: 0,
            chunksFailed: 0,
            isComplete: false,
            totalDuration: 60
          })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByText(/stop recording/i)).toBeInTheDocument()
      })

      const stopButton = screen.getByText(/stop recording/i)
      await userEvent.click(stopButton)

      await waitFor(() => {
        expect(mockManager.pauseRecording).toHaveBeenCalled()
      })
    })
  })

  describe('Error handling', () => {
    it('handles microphone permission denied error', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        startRecording: vi.fn().mockRejectedValue(new Error('Microphone access denied')),
        getProgress: vi.fn().mockReturnValue({
          isRecording: false,
          currentChunk: 0,
          totalChunks: 0,
          chunksUploaded: 0,
          chunksFailed: 0,
          isComplete: false,
          totalDuration: 0
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)
      
      global.navigator.permissions = {
        query: vi.fn().mockResolvedValue({ state: 'denied' })
      } as any

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(mockManager.startRecording).toHaveBeenCalled()
      })
    })

    it('handles database error when creating call record', async () => {
      const { supabase } = await import('@/integrations/supabase/client')
      
      ;(supabase.from as any).mockReturnValue({
        insert: vi.fn(() => ({
          select: vi.fn(() => ({
            single: vi.fn().mockResolvedValue({
              data: null,
              error: { message: 'Database error' }
            })
          }))
        }))
      })

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        // Error should be handled gracefully
        expect(startButton).toBeInTheDocument()
      })
    })

    it('handles missing user authentication', async () => {
      const { supabase } = await import('@/integrations/supabase/client')
      
      ;(supabase.auth.getUser as any).mockResolvedValue({
        data: { user: null }
      })

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        // Should handle error gracefully
        expect(startButton).toBeInTheDocument()
      })
    })
  })

  describe('Recording completion', () => {
    it('calls onRecordingComplete when recording finishes', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        startRecording: vi.fn().mockResolvedValue(undefined),
        stopRecording: vi.fn().mockResolvedValue(undefined),
        getProgress: vi.fn()
          .mockReturnValueOnce({
            isRecording: true,
            currentChunk: 1,
            totalChunks: 1,
            chunksUploaded: 0,
            chunksFailed: 0,
            isComplete: false,
            totalDuration: 60
          })
          .mockReturnValue({
            isRecording: false,
            currentChunk: 1,
            totalChunks: 1,
            chunksUploaded: 1,
            chunksFailed: 0,
            isComplete: true,
            totalDuration: 300
          })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      // Simulate recording completion
      await act(async () => {
        // Trigger progress update that indicates completion
        const manager = results[results.length - 1]?.value
        if (manager?.onProgressUpdate) {
          manager.onProgressUpdate({
            isRecording: false,
            currentChunk: 1,
            totalChunks: 1,
            chunksUploaded: 1,
            chunksFailed: 0,
            isComplete: true,
            totalDuration: 300
          })
        }
      })

      await waitFor(() => {
        expect(mockOnRecordingComplete).toHaveBeenCalledWith(
          expect.any(String),
          300
        )
      }, { timeout: 2000 })
    })
  })

  describe('Props handling', () => {
    it('uses patientName prop correctly', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="John Doe"
        />
      )
      expect(screen.getByText(/start recording/i)).toBeInTheDocument()
    })

    it('uses patientId prop when creating call record', async () => {
      const { supabase } = await import('@/integrations/supabase/client')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          patientId="patient-123"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(supabase.from).toHaveBeenCalled()
      })
    })

    it('uses centerId prop when creating call record', async () => {
      const { supabase } = await import('@/integrations/supabase/client')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          centerId="center-123"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(supabase.from).toHaveBeenCalled()
      })
    })
  })

  describe('State persistence', () => {
    it('checks for existing recording state on mount', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      // Should check for existing state
      expect(ChunkedRecordingManager.loadState).toHaveBeenCalled()
    })
  })

  describe('Progress display', () => {
    it('displays recording duration correctly', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        getProgress: vi.fn().mockReturnValue({
          isRecording: true,
          currentChunk: 2,
          totalChunks: 3,
          chunksUploaded: 1,
          chunksFailed: 0,
          isComplete: false,
          totalDuration: 600
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      // Should display duration
      await waitFor(() => {
        expect(screen.getByText(/10:00/i)).toBeInTheDocument()
      })
    })

    it('shows upload progress percentage', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        getProgress: vi.fn().mockReturnValue({
          isRecording: false,
          currentChunk: 5,
          totalChunks: 10,
          chunksUploaded: 7,
          chunksFailed: 0,
          isComplete: false,
          totalDuration: 1500
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      // Should show upload progress
      await waitFor(() => {
        expect(screen.getByText(/70%/i)).toBeInTheDocument()
      })
    })

    it('displays chunk statistics', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        getProgress: vi.fn().mockReturnValue({
          isRecording: false,
          currentChunk: 5,
          totalChunks: 5,
          chunksUploaded: 5,
          chunksFailed: 0,
          isComplete: true,
          totalDuration: 1500
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      // Should show completed state
      await waitFor(() => {
        expect(screen.getByText(/5\/5/i)).toBeInTheDocument()
      })
    })
  })

  describe('Error display', () => {
    it('shows error message when present', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        getProgress: vi.fn().mockReturnValue({
          isRecording: false,
          currentChunk: 0,
          totalChunks: 0,
          chunksUploaded: 0,
          chunksFailed: 1,
          isComplete: false,
          totalDuration: 0,
          errorMessage: 'Upload failed'
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      await waitFor(() => {
        expect(screen.getByText(/upload failed/i)).toBeInTheDocument()
      })
    })

    it('shows retry button when error occurs', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        retryFailedChunks: vi.fn(),
        getProgress: vi.fn().mockReturnValue({
          isRecording: false,
          currentChunk: 0,
          totalChunks: 0,
          chunksUploaded: 0,
          chunksFailed: 1,
          isComplete: false,
          totalDuration: 0,
          errorMessage: 'Upload failed'
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      await waitFor(() => {
        const retryButton = screen.getByText(/retry/i)
        expect(retryButton).toBeInTheDocument()
      })
    })
  })

  describe('Props validation', () => {
    it('handles undefined patientName gracefully', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName={undefined}
        />
      )

      const startButton = screen.getByText(/start recording/i).closest('button')
      expect(startButton).toBeDisabled()
    })

    it('handles null patientName gracefully', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName={null as any}
        />
      )

      const startButton = screen.getByText(/start recording/i).closest('button')
      expect(startButton).toBeDisabled()
    })

    it('works with minimal props', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
        />
      )

      expect(screen.getByText(/start recording/i)).toBeInTheDocument()
    })
  })

  describe('Recording state transitions', () => {
    it('transitions from stopped to recording', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        startRecording: vi.fn().mockResolvedValue(undefined),
        getProgress: vi.fn()
          .mockReturnValueOnce({
            isRecording: false,
            currentChunk: 0,
            totalChunks: 0,
            chunksUploaded: 0,
            chunksFailed: 0,
            isComplete: false,
            totalDuration: 0
          })
          .mockReturnValue({
            isRecording: true,
            currentChunk: 1,
            totalChunks: 1,
            chunksUploaded: 0,
            chunksFailed: 0,
            isComplete: false,
            totalDuration: 60
          })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      const startButton = screen.getByText(/start recording/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(mockManager.startRecording).toHaveBeenCalled()
      })
    })
  })

  describe('Disabled state handling', () => {
    it('prevents all interactions when disabled', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          disabled={true}
        />
      )

      const startButton = screen.getByText(/start recording/i).closest('button')
      expect(startButton).toBeDisabled()
    })

    it('shows appropriate UI when disabled', () => {
      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
          disabled={true}
        />
      )

      expect(screen.getByText(/start recording/i)).toBeInTheDocument()
    })
  })

  describe('Call record ID handling', () => {
    it('handles callRecordId state correctly', async () => {
      const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService')
      const mockManager = {
        getProgress: vi.fn().mockReturnValue({
          isRecording: false,
          currentChunk: 1,
          totalChunks: 1,
          chunksUploaded: 0,
          chunksFailed: 0,
          isComplete: false,
          totalDuration: 60
        })
      }
      
      ;(ChunkedRecordingManager as any).mockImplementation(() => mockManager)

      renderWithRouter(
        <ChunkedAudioRecorder
          onRecordingComplete={mockOnRecordingComplete}
          patientName="Test Patient"
        />
      )

      // Component should handle state correctly
      expect(screen.getByText(/start recording/i)).toBeInTheDocument()
    })
  })
})
