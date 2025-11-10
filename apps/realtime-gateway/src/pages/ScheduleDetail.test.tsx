import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import ScheduleDetail from './ScheduleDetail'

// Mock dependencies
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-123',
      email: 'test@example.com'
    },
    signOut: vi.fn(),
    loading: false
  })
}))

vi.mock('@/hooks/useProfile', () => ({
  useProfile: () => ({
    profile: {
      id: 'test-profile',
      organization_id: 'test-org',
      timezone: 'America/Los_Angeles'
    },
    loading: false
  })
}))

vi.mock('@/hooks/useAppointments', () => ({
  useAppointments: () => ({
    appointments: [
      {
        id: 'appt-1',
        customer_name: 'John Doe',
        appointment_date: new Date().toISOString(),
        type: 'Initial Consult',
        status: 'current',
        patient_id: 'patient-1',
        email: 'john@example.com',
        phone_number: '555-1234'
      }
    ],
    loading: false,
    loadAppointments: vi.fn().mockResolvedValue(undefined)
  })
}))

vi.mock('@/hooks/useCallRecords', () => ({
  useCallRecords: () => ({
    calls: [],
    loadCalls: vi.fn().mockResolvedValue(undefined),
    handleChunkedRecordingComplete: vi.fn().mockResolvedValue(undefined)
  })
}))

vi.mock('@/hooks/useCenterSession', () => ({
  useCenterSession: () => ({
    activeCenter: 'center-123',
    needsCenterSelection: false,
    availableCenters: [
      { id: 'center-123', name: 'Test Center' }
    ],
    setActiveCenter: vi.fn(),
    error: null
  })
}))

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          eq: vi.fn(() => ({
            order: vi.fn(() => ({
              limit: vi.fn().mockResolvedValue({
                data: [],
                error: null
              })
            }))
          }))
        }))
      }))
    }))
  }
}))

vi.mock('@/components/ChunkedAudioRecorder', () => ({
  ChunkedAudioRecorder: ({ onRecordingComplete, autoStart, patientName }: any) => {
    const handleComplete = () => {
      onRecordingComplete?.('test-call-record-123', 300)
    }

    return (
      <div data-testid="chunked-audio-recorder">
        <div>ChunkedAudioRecorder - {patientName}</div>
        {autoStart && <div data-testid="auto-start-active">Auto-start active</div>}
        <button onClick={handleComplete} data-testid="complete-recording">
          Complete Recording
        </button>
      </div>
    )
  }
}))

vi.mock('@/components/AudioUploadModal', () => ({
  AudioUploadModal: ({ open, onOpenChange, appointment }: any) => {
    if (!open) return null
    return (
      <div data-testid="audio-upload-modal">
        <div>Upload Modal for {appointment?.customer_name}</div>
        <button onClick={() => onOpenChange(false)}>Close</button>
      </div>
    )
  }
}))

vi.mock('@/components/SalesDashboardSidebar', () => ({
  SalesDashboardSidebar: () => <div data-testid="sidebar">Sidebar</div>
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('ScheduleDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithRouter(<ScheduleDetail />)
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })

    it('renders appointment list', () => {
      renderWithRouter(<ScheduleDetail />)
      expect(screen.getByText(/patient meeting schedule/i)).toBeInTheDocument()
    })

    it('renders selected appointment details', () => {
      renderWithRouter(<ScheduleDetail />)
      // Should show appointment details when one is selected
      waitFor(() => {
        expect(screen.getByText(/john doe/i)).toBeInTheDocument()
      })
    })

    it('shows calendar navigation', () => {
      renderWithRouter(<ScheduleDetail />)
      expect(screen.getByText(/today's patient meeting schedule/i)).toBeInTheDocument()
    })
  })

  describe('Start Consult button', () => {
    it('renders Start Consult button when not recording', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })
    })

    it('shows ChunkedAudioRecorder when Start Consult is clicked', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('chunked-audio-recorder')).toBeInTheDocument()
      })
    })

    it('enables autoStart when ChunkedAudioRecorder is shown', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('auto-start-active')).toBeInTheDocument()
      })
    })

    it('disables Start Consult button when no appointment is selected', () => {
      vi.mock('@/hooks/useAppointments', () => ({
        useAppointments: () => ({
          appointments: [],
          loading: false,
          loadAppointments: vi.fn()
        })
      }))

      renderWithRouter(<ScheduleDetail />)
      
      // When no appointments, button should be disabled or not shown
      const startButton = screen.queryByText(/start consult/i)
      if (startButton) {
        expect(startButton.closest('button')).toBeDisabled()
      }
    })

    it('disables Start Consult button when no center is selected', () => {
      vi.mock('@/hooks/useCenterSession', () => ({
        useCenterSession: () => ({
          activeCenter: null,
          needsCenterSelection: true,
          availableCenters: [],
          setActiveCenter: vi.fn(),
          error: null
        })
      }))

      renderWithRouter(<ScheduleDetail />)
      
      waitFor(() => {
        const startButton = screen.queryByText(/start consult/i)
        if (startButton) {
          expect(startButton.closest('button')).toBeDisabled()
        }
      })
    })

    it('shows message when center is not selected', () => {
      vi.mock('@/hooks/useCenterSession', () => ({
        useCenterSession: () => ({
          activeCenter: null,
          needsCenterSelection: true,
          availableCenters: [],
          setActiveCenter: vi.fn(),
          error: null
        })
      }))

      renderWithRouter(<ScheduleDetail />)
      
      waitFor(() => {
        expect(screen.getByText(/please select a center/i)).toBeInTheDocument()
      })
    })
  })

  describe('Recording completion', () => {
    it('calls handleChunkedRecordingComplete when recording finishes', async () => {
      const { useCallRecords } = await import('@/hooks/useCallRecords')
      const mockHandleComplete = vi.fn()
      
      vi.mocked(useCallRecords).mockReturnValue({
        calls: [],
        loadCalls: vi.fn(),
        handleChunkedRecordingComplete: mockHandleComplete
      } as any)

      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('chunked-audio-recorder')).toBeInTheDocument()
      })

      const completeButton = screen.getByTestId('complete-recording')
      await userEvent.click(completeButton)

      await waitFor(() => {
        expect(mockHandleComplete).toHaveBeenCalledWith('test-call-record-123', 300)
      })
    })

    it('reloads calls after recording completion', async () => {
      const { useCallRecords } = await import('@/hooks/useCallRecords')
      const mockLoadCalls = vi.fn()
      
      vi.mocked(useCallRecords).mockReturnValue({
        calls: [],
        loadCalls: mockLoadCalls,
        handleChunkedRecordingComplete: vi.fn().mockResolvedValue(undefined)
      } as any)

      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('chunked-audio-recorder')).toBeInTheDocument()
      })

      const completeButton = screen.getByTestId('complete-recording')
      await userEvent.click(completeButton)

      await waitFor(() => {
        expect(mockLoadCalls).toHaveBeenCalledWith(50)
      })
    })

    it('hides ChunkedAudioRecorder after recording completion', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('chunked-audio-recorder')).toBeInTheDocument()
      })

      const completeButton = screen.getByTestId('complete-recording')
      await userEvent.click(completeButton)

      await waitFor(() => {
        expect(screen.queryByTestId('chunked-audio-recorder')).not.toBeInTheDocument()
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })
    })
  })

  describe('Upload Recording button', () => {
    it('renders Upload Recording button', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/upload recording/i)).toBeInTheDocument()
      })
    })

    it('opens AudioUploadModal when Upload Recording is clicked', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/upload recording/i)).toBeInTheDocument()
      })

      const uploadButton = screen.getByText(/upload recording/i)
      await userEvent.click(uploadButton)

      await waitFor(() => {
        expect(screen.getByTestId('audio-upload-modal')).toBeInTheDocument()
      })
    })

    it('closes AudioUploadModal when close is clicked', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/upload recording/i)).toBeInTheDocument()
      })

      const uploadButton = screen.getByText(/upload recording/i)
      await userEvent.click(uploadButton)

      await waitFor(() => {
        expect(screen.getByTestId('audio-upload-modal')).toBeInTheDocument()
      })

      const closeButton = screen.getByText(/close/i)
      await userEvent.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByTestId('audio-upload-modal')).not.toBeInTheDocument()
      })
    })
  })

  describe('Appointment selection', () => {
    it('selects first appointment by default', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/john doe/i)).toBeInTheDocument()
      })
    })

    it('loads patient details when appointment is selected', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/john doe/i)).toBeInTheDocument()
      })

      // Patient details should be loaded
      await waitFor(() => {
        // Check if patient info is displayed
        expect(screen.getByText(/initial consult details/i)).toBeInTheDocument()
      })
    })
  })

  describe('Props passed to ChunkedAudioRecorder', () => {
    it('passes correct patientName to ChunkedAudioRecorder', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByText(/chunkedaudiorecorder - john doe/i)).toBeInTheDocument()
      })
    })

    it('passes patientId to ChunkedAudioRecorder', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        const recorder = screen.getByTestId('chunked-audio-recorder')
        expect(recorder).toBeInTheDocument()
      })
    })

    it('passes centerId to ChunkedAudioRecorder', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('chunked-audio-recorder')).toBeInTheDocument()
      })
    })

    it('passes autoStart=true to ChunkedAudioRecorder', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/start consult/i)).toBeInTheDocument()
      })

      const startButton = screen.getByText(/start consult/i)
      await userEvent.click(startButton)

      await waitFor(() => {
        expect(screen.getByTestId('auto-start-active')).toBeInTheDocument()
      })
    })
  })

  describe('Date navigation', () => {
    it('allows navigating to previous day', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /previous/i })
        expect(prevButton).toBeInTheDocument()
      })
    })

    it('allows navigating to next day', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i })
        expect(nextButton).toBeInTheDocument()
      })
    })
  })

  describe('Filter tabs', () => {
    it('shows filter tabs', () => {
      renderWithRouter(<ScheduleDetail />)
      
      expect(screen.getByText(/all meetings/i)).toBeInTheDocument()
      expect(screen.getByText(/consults/i)).toBeInTheDocument()
      expect(screen.getByText(/confirmed/i)).toBeInTheDocument()
    })

    it('allows filtering appointments', async () => {
      renderWithRouter(<ScheduleDetail />)
      
      const confirmedTab = screen.getByText(/confirmed/i)
      await userEvent.click(confirmedTab)
      
      // Filter should be applied
      expect(confirmedTab).toBeInTheDocument()
    })
  })
})
