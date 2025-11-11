import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { useAuth } from '@/hooks/useAuth';
import { toast } from '@/hooks/use-toast';
import { 
  Upload, 
  FileAudio, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Loader2,
  X
} from 'lucide-react';

interface TranscribeFileUploadProps {
  onUploadComplete?: () => void;
}

interface UploadState {
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  message: string;
}

export const TranscribeFileUpload: React.FC<TranscribeFileUploadProps> = ({ 
  onUploadComplete 
}) => {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>({
    progress: 0,
    status: 'idle',
    message: ''
  });
  const [provider, setProvider] = useState<'deepgram' | 'assemblyai'>('assemblyai');
  const [language, setLanguage] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    // Validate file type
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/webm', 'audio/ogg', 'audio/flac', 'audio/mp3'];
    const validExtensions = ['.mp3', '.wav', '.m4a', '.webm', '.ogg', '.flac'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
      toast({
        title: "Invalid file type",
        description: "Please upload an audio file (MP3, WAV, M4A, WebM, OGG, FLAC)",
        variant: "destructive",
      });
      return;
    }

    // Validate file size (100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "File size must be less than 100MB",
        variant: "destructive",
      });
      return;
    }

    setSelectedFile(file);
    setUploadState({ progress: 0, status: 'idle', message: '' });
  }, []);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => prev + 1);
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => {
      const newCounter = prev - 1;
      if (newCounter === 0) {
        setIsDragging(false);
      }
      return newCounter;
    });
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setDragCounter(0);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  // Upload handler
  const handleUpload = async () => {
    if (!selectedFile || !user) return;

    setUploadState({
      progress: 0,
      status: 'uploading',
      message: 'Uploading file...'
    });

    try {
      // Get session for auth token
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error('Not authenticated');
      }

      // Create FormData
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('provider', provider);
      if (language) {
        formData.append('language', language);
      }

      // Upload with progress tracking
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 50); // First 50% for upload
          setUploadState(prev => ({ ...prev, progress }));
        }
      });

      xhr.addEventListener('loadend', () => {
        console.log('[Transcribe Upload] loadend status:', xhr.status, xhr.statusText);
        let parsed: any = undefined;
        try {
          parsed = xhr.responseText ? JSON.parse(xhr.responseText) : undefined;
        } catch (e) {
          // ignore parse error; we'll fall back to raw text
        }
        if (xhr.status === 201) {
          const response = JSON.parse(xhr.responseText);
          setUploadState({
            progress: 100,
            status: 'success',
            message: 'Upload successful! Transcription queued.'
          });
          
          toast({
            title: "Upload successful",
            description: "Your file has been uploaded and transcription is in progress.",
          });
          
          // Reset and trigger callback
          setTimeout(() => {
            setSelectedFile(null);
            setUploadState({ progress: 0, status: 'idle', message: '' });
            if (fileInputRef.current) {
              fileInputRef.current.value = '';
            }
            onUploadComplete?.();
          }, 2000);
        } else {
          const errorData = parsed || {};
          const detail = (errorData && (errorData.detail || errorData.message)) || xhr.statusText || 'Upload failed';
          console.error('[Transcribe Upload] Error response:', {
            status: xhr.status,
            statusText: xhr.statusText,
            responseText: xhr.responseText
          });
          setUploadState({
            progress: 0,
            status: 'error',
            message: detail
          });
          
          toast({
            title: "Upload failed",
            description: detail,
            variant: "destructive",
          });
        }
      });

      xhr.addEventListener('error', () => {
        setUploadState({
          progress: 0,
          status: 'error',
          message: 'Network error occurred'
        });
        
        toast({
          title: "Network error",
          description: "Could not connect to the server",
          variant: "destructive",
        });
      });

      const { getApiUrl } = await import('@/utils/apiConfig');
      xhr.open('POST', getApiUrl('/api/transcribe/upload'));
      xhr.setRequestHeader('Authorization', `Bearer ${session.access_token}`);
      xhr.send(formData);

      // Simulate processing after upload
      setUploadState(prev => ({
        ...prev,
        progress: 60,
        status: 'processing',
        message: 'Processing file...'
      }));

    } catch (error) {
      console.error('Upload error:', error);
      setUploadState({
        progress: 0,
        status: 'error',
        message: error instanceof Error ? error.message : 'Upload failed'
      });
      
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: "destructive",
      });
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusIcon = () => {
    switch (uploadState.status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-16 w-16 animate-spin text-primary" />;
      case 'success':
        return <CheckCircle className="h-16 w-16 text-green-500" />;
      case 'error':
        return <XCircle className="h-16 w-16 text-red-500" />;
      default:
        return <FileAudio className="h-16 w-16 text-muted-foreground" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Transcribe Audio File
        </CardTitle>
        <CardDescription>
          Upload an audio file for transcription using AssemblyAI or Deepgram
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Drag and Drop Zone */}
        <div
          ref={dropZoneRef}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all
            ${isDragging 
              ? 'border-primary bg-primary/10 scale-105' 
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
            }
            ${uploadState.status === 'uploading' || uploadState.status === 'processing' 
              ? 'pointer-events-none opacity-50' 
              : ''
            }
          `}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="flex flex-col items-center justify-center space-y-4">
            {getStatusIcon()}
            
            {uploadState.status === 'idle' && !selectedFile && (
              <div>
                <p className="text-lg font-medium mb-1">
                  Drop audio file here or click to browse
                </p>
                <p className="text-sm text-muted-foreground">
                  MP3, WAV, M4A, WebM, OGG, FLAC (max 100MB)
                </p>
              </div>
            )}

            {selectedFile && uploadState.status === 'idle' && (
              <div>
                <p className="text-lg font-medium mb-1">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            )}

            {uploadState.status !== 'idle' && uploadState.message && (
              <div>
                <p className="text-lg font-medium">{uploadState.message}</p>
              </div>
            )}

            {uploadState.status === 'success' && (
              <p className="text-sm text-green-600">Transcription queued successfully!</p>
            )}

            {uploadState.status === 'error' && (
              <div className="space-y-2">
                <p className="text-sm text-red-600">{uploadState.message}</p>
                <p className="text-xs text-muted-foreground">Please try again</p>
              </div>
            )}

            {(uploadState.status === 'uploading' || uploadState.status === 'processing') && (
              <div className="w-full max-w-xs space-y-2">
                <Progress value={uploadState.progress} />
                <p className="text-xs text-muted-foreground">
                  {uploadState.progress}% complete
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileSelect(file);
          }}
        />

        {/* File info and options */}
        {selectedFile && uploadState.status === 'idle' && (
          <div className="space-y-4">
            {/* Remove file button */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <FileAudio className="h-4 w-4" />
                <span className="text-sm font-medium">{selectedFile.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({formatFileSize(selectedFile.size)})
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedFile(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Provider selection */}
            <div className="space-y-2">
              <Label htmlFor="provider">Transcription Provider</Label>
              <Select value={provider} onValueChange={(value: 'deepgram' | 'assemblyai') => setProvider(value)}>
                <SelectTrigger id="provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="deepgram">Deepgram</SelectItem>
                  <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Choose your preferred transcription provider
              </p>
            </div>

            {/* Language (optional) */}
            <div className="space-y-2">
              <Label htmlFor="language">Language (optional)</Label>
              <Input
                id="language"
                placeholder="en, es, fr, etc."
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Leave empty for automatic detection
              </p>
            </div>

            {/* Upload button */}
            <Button
              onClick={handleUpload}
              disabled={!selectedFile}
              className="w-full"
              size="lg"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload & Start Transcription
            </Button>
          </div>
        )}

        {/* Instructions */}
        {!selectedFile && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              <strong>Note:</strong> Uploaded files will be transcribed asynchronously. 
              You can check transcription status and download results once processing is complete.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default TranscribeFileUpload;

