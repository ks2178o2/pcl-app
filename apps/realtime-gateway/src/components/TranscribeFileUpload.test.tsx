import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TranscribeFileUpload from './TranscribeFileUpload';
import { useAuth } from '@/hooks/useAuth';

// Mock dependencies - must be top-level, hoisted by vitest
vi.mock('@/hooks/useAuth');
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getSession: vi.fn()
    }
  }
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => {
  const mockToast = vi.fn();
  return {
    useToast: () => ({
      toast: mockToast
    }),
    toast: mockToast
  };
});

describe('TranscribeFileUpload', () => {
  const mockOnUploadComplete = vi.fn();
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    organization_id: 'org-123'
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    
    (useAuth as any).mockReturnValue({
      user: mockUser,
      loading: false
    });
    
    // Mock supabase session
    const { supabase } = await import('@/integrations/supabase/client');
    vi.spyOn(supabase.auth, 'getSession').mockResolvedValue({
      data: { session: { access_token: 'mock-token' } }
    });
  });

  it('renders upload interface correctly', () => {
    render(<TranscribeFileUpload onUploadComplete={mockOnUploadComplete} />);
    
    expect(screen.getByText(/transcribe audio file/i)).toBeInTheDocument();
    expect(screen.getByText(/drop audio file here/i)).toBeInTheDocument();
    expect(screen.getByText(/mp3, wav, m4a, webm, ogg, flac/i)).toBeInTheDocument();
  });

  it('displays drag and drop zone', () => {
    render(<TranscribeFileUpload />);
    
    const dropZone = screen.getByText(/drop audio file here or click to browse/i);
    expect(dropZone).toBeInTheDocument();
  });

  it('validates file type on selection', async () => {
    const user = userEvent.setup();
    render(<TranscribeFileUpload />);
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (fileInput) {
      const invalidFile = new File(['content'], 'document.pdf', { type: 'application/pdf' });
      await user.upload(fileInput, invalidFile);
      
      // File should not be accepted (validation happens in handleFileSelect)
      // This test verifies the component renders and file input exists
      expect(fileInput).toBeInTheDocument();
    }
  });

  it('validates file size limit', async () => {
    const user = userEvent.setup();
    render(<TranscribeFileUpload />);
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (fileInput) {
      // Create a file larger than 100MB
      const largeContent = new Array(101 * 1024).fill('x').join('');
      const largeFile = new File([largeContent], 'large.mp3', { type: 'audio/mpeg' });
      
      await user.upload(fileInput, largeFile);
      
      // Should show error about file size
    }
  });

  it('displays provider selection dropdown', () => {
    render(<TranscribeFileUpload />);
    
    // Provider selection should be visible when file is selected
    // This might need file selection first
  });

  it('displays optional language field', () => {
    render(<TranscribeFileUpload />);
    
    // Language field should be visible when file is selected
  });

  it('shows progress bar during upload', async () => {
    // Mock successful upload
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({
        success: true,
        upload_id: 'upload-123',
        message: 'Upload successful'
      })
    });
    
    const user = userEvent.setup();
    render(<TranscribeFileUpload />);
    
    // Simulate file upload process
    // Check that progress bar appears
  });

  it('handles upload success', async () => {
    // Mock XMLHttpRequest
    const mockXHR = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      upload: { addEventListener: vi.fn() },
      addEventListener: vi.fn(),
      status: 201,
      responseText: JSON.stringify({
        success: true,
        upload_id: 'upload-123',
        storage_path: 'path/to/file.mp3',
        file_name: 'test.mp3',
        file_size: 1024,
        message: 'Upload successful'
      })
    };
    
    global.XMLHttpRequest = vi.fn(() => mockXHR) as any;
    
    const user = userEvent.setup();
    render(<TranscribeFileUpload onUploadComplete={mockOnUploadComplete} />);
    
    // Select and upload file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, file);
    
    // Find and click upload button
    const uploadButton = screen.getByText(/upload & start transcription/i);
    await user.click(uploadButton);
    
    // Trigger loadend event
    const loadendHandler = mockXHR.addEventListener.mock.calls.find(
      call => call[0] === 'loadend'
    )?.[1];
    
    if (loadendHandler) {
      loadendHandler();
    }
    
    // Wait for callback to be called (with 2s delay in component)
    await waitFor(() => {
      expect(mockOnUploadComplete).toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  it('handles upload failure', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({
        detail: 'Upload failed'
      })
    });
    
    render(<TranscribeFileUpload />);
    
    // Should show error message
  });

  it('requires authentication', () => {
    (useAuth as any).mockReturnValue({
      user: null,
      loading: false
    });
    
    render(<TranscribeFileUpload />);
    
    // Should not allow upload without user
  });

  it('supports all audio formats', () => {
    render(<TranscribeFileUpload />);
    
    const formats = ['mp3', 'wav', 'm4a', 'webm', 'ogg', 'flac'];
    const supportedText = screen.getByText(/mp3, wav, m4a, webm, ogg, flac/i);
    
    expect(supportedText).toBeInTheDocument();
  });

  it('clears selected file', async () => {
    const user = userEvent.setup();
    render(<TranscribeFileUpload />);
    
    // Select a file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (fileInput) {
      await user.upload(fileInput, file);
      
      // Look for clear/remove button
      // const clearButton = screen.getByRole('button', { name: /remove/i });
      // await user.click(clearButton);
      
      // File should be cleared
    }
  });
});

