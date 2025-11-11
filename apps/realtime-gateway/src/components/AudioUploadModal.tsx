import React, { useRef, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, X, FileAudio, Check, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useProfile } from '@/hooks/useProfile';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useToast } from '@/hooks/use-toast';
import { shouldConvertAudio, convertAudioToWebM, formatFileSize, ConversionProgress } from '@/services/audioConversionService';

interface AppointmentWithStatus {
  id: string;
  customer_name: string;
  appointment_date: string;
  status: 'upcoming' | 'current' | 'recent' | 'past';
  timeDescription: string;
  patient_id?: string | null;
}

interface AudioUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointment: AppointmentWithStatus;
  onUploadComplete: () => void;
  centerId?: string;
}

export const AudioUploadModal: React.FC<AudioUploadModalProps> = ({
  open,
  onOpenChange,
  appointment,
  onUploadComplete,
  centerId
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string>('');
  const [conversionProgress, setConversionProgress] = useState<ConversionProgress | null>(null);
  const [compressionInfo, setCompressionInfo] = useState<{originalSize: number; convertedSize: number; ratio: number} | null>(null);
  const { profile } = useProfile();
  const { addCall } = useCallRecords();
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadError('');
    setConversionProgress(null);
    setCompressionInfo(null);

    // Validate file type
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/m4a', 'audio/webm', 'audio/ogg'];
    const fileExtension = file.name.toLowerCase().match(/\.(wav|mp3|m4a|webm|ogg)$/);
    
    if (!validTypes.includes(file.type) && !fileExtension) {
      setUploadError('Please upload a valid audio file (WAV, MP3, M4A, WebM, or OGG)');
      return;
    }

    // Check if large WAV needs conversion
    const needsConversion = shouldConvertAudio(file, file.name);
    
    // For files that don't need conversion, validate size against backend limit
    if (!needsConversion) {
      const maxSize = 100 * 1024 * 1024; // 100MB backend limit
      if (file.size > maxSize) {
        setUploadError('File size must be less than 100MB');
        return;
      }
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile || !profile) return;

    // Log file information upfront
    console.log('📁 Starting upload process:', {
      fileName: selectedFile.name,
      fileType: selectedFile.type,
      originalSize: selectedFile.size,
      originalSizeFormatted: formatFileSize(selectedFile.size),
      lastModified: new Date(selectedFile.lastModified).toISOString()
    });

    setUploading(true);
    setUploadError('');
    setConversionProgress(null);
    setCompressionInfo(null);

    try {
      // Check if file needs conversion
      const needsConversion = shouldConvertAudio(selectedFile, selectedFile.name);
      let finalBlob: Blob = selectedFile;
      let finalContentType = selectedFile.type;
      
      if (needsConversion) {
        console.log('🔄 Converting large WAV file to WebM...', {
          fileName: selectedFile.name,
          originalSize: formatFileSize(selectedFile.size),
          type: selectedFile.type
        });
        
        const conversionResult = await convertAudioToWebM(selectedFile, setConversionProgress);
        finalBlob = conversionResult.convertedBlob;
        finalContentType = 'audio/webm';
        
        setCompressionInfo({
          originalSize: conversionResult.originalSize,
          convertedSize: conversionResult.convertedSize,
          ratio: conversionResult.compressionRatio
        });
        
        console.log('✅ Conversion complete:', {
          originalSize: formatFileSize(conversionResult.originalSize),
          convertedSize: formatFileSize(conversionResult.convertedSize),
          compressionRatio: conversionResult.compressionRatio + '%'
        });

        // Validate converted file size
        const maxSize = 100 * 1024 * 1024; // 100MB backend limit
        if (finalBlob.size > maxSize) {
          setUploadError('Even after compression, file size is still too large. Please use a shorter recording.');
          setUploading(false);
          return;
        }
      }

      // Create audio element to get duration
      const audioElement = document.createElement('audio');
      const objectUrl = URL.createObjectURL(finalBlob);
      audioElement.src = objectUrl;

      // Set a timeout to handle cases where metadata doesn't load
      const metadataTimeout = setTimeout(() => {
        console.warn('⚠️ Audio metadata loading timed out after 10 seconds');
        URL.revokeObjectURL(objectUrl);
        setUploadError('Failed to load audio metadata. The file may be corrupted or in an unsupported format.');
        setUploading(false);
      }, 10000); // 10 second timeout

      audioElement.addEventListener('loadedmetadata', async () => {
        clearTimeout(metadataTimeout);
        const duration = isNaN(audioElement.duration) ? 0 : audioElement.duration;
        console.log('🎵 Audio metadata loaded:', { duration, fileName: selectedFile.name });
        
        try {
          // Create a properly typed blob with correct content type
          const typedBlob = new Blob([finalBlob], { type: finalContentType });
          
          // Log final blob details before upload
          console.log('📦 Final blob prepared for upload:', {
            size: typedBlob.size,
            sizeFormatted: formatFileSize(typedBlob.size),
            contentType: finalContentType,
            originalSize: selectedFile.size,
            originalSizeFormatted: formatFileSize(selectedFile.size),
            compressionRatio: selectedFile.size > 0 
              ? `${((1 - typedBlob.size / selectedFile.size) * 100).toFixed(1)}% reduction`
              : 'N/A'
          });
          
          // Add the call using the existing addCall function
          const patientId = appointment.patient_id || undefined;
          console.log('📞 Calling addCall with:', {
            patientName: appointment.customer_name,
            patientId,
            centerId,
            duration: `${Math.round(duration)}s (${Math.round(duration / 60)}min ${Math.round(duration % 60)}s)`,
            blobSize: typedBlob.size,
            blobSizeFormatted: formatFileSize(typedBlob.size)
          });
          
          const uploadStartTime = Date.now();
          console.log('⏱️ Upload started at:', new Date(uploadStartTime).toISOString());
          
          const callResult = await addCall(
            typedBlob,
            duration,
            appointment.customer_name,
            profile.salesperson_name,
            patientId,
            centerId
          );
          
          const uploadEndTime = Date.now();
          const uploadDuration = ((uploadEndTime - uploadStartTime) / 1000).toFixed(2);
          const uploadSpeed = uploadDuration ? formatFileSize(typedBlob.size / parseFloat(uploadDuration)) + '/s' : 'N/A';
          
          console.log('✅ Upload completed:', {
            duration: `${uploadDuration}s`,
            speed: uploadSpeed,
            totalSize: formatFileSize(typedBlob.size),
            completedAt: new Date(uploadEndTime).toISOString()
          });
          console.log('✅ addCall completed, result:', callResult);
          
          if (!callResult) {
            console.error('❌ addCall returned undefined - user may not be authenticated');
            setUploadError('Failed to upload: User not authenticated. Please refresh and try again.');
            URL.revokeObjectURL(objectUrl);
            setUploading(false);
            return;
          }
          
          console.log('🔍 Checking callResult.id:', {
            callResult,
            id: (callResult as any)?.id,
            idType: typeof (callResult as any)?.id,
            hasDash: typeof (callResult as any)?.id === 'string' ? (callResult as any).id.includes('-') : false,
            idLength: typeof (callResult as any)?.id === 'string' ? (callResult as any).id.length : 0
          });
          
          const successMessage = compressionInfo 
            ? `Recording uploaded and compressed from ${formatFileSize(compressionInfo.originalSize)} to ${formatFileSize(compressionInfo.convertedSize)} (${compressionInfo.ratio}% smaller)`
            : `Recording for ${appointment.customer_name} has been uploaded and will be transcribed`;
          
          toast({
            title: 'Audio uploaded successfully',
            description: successMessage,
          });

          URL.revokeObjectURL(objectUrl);
          clearTimeout(metadataTimeout);
          
          // Call onUploadComplete first to refresh the calls list
          onUploadComplete();
          
          // Navigate to analysis page only if we have a valid UUID id
          const newId = (callResult as any)?.id;
          console.log('🧭 Navigation check:', {
            newId,
            isString: typeof newId === 'string',
            hasDash: typeof newId === 'string' ? newId.includes('-') : false,
            length: typeof newId === 'string' ? newId.length : 0,
            willNavigate: typeof newId === 'string' && newId.includes('-') && newId.length >= 32
          });
          
          if (typeof newId === 'string' && newId.includes('-') && newId.length >= 32) {
            console.log('✅ Navigating to analysis page:', `/analysis/${newId}`);
            // Small delay to ensure state updates complete before navigation
            setTimeout(() => {
              navigate(`/analysis/${newId}`);
            }, 100);
          } else {
            console.warn('⚠️ Navigation skipped - invalid ID:', newId);
            // Calls list should already be refreshed by onUploadComplete
          }
        } catch (error) {
          console.error('❌ Error uploading audio:', error);
          setUploadError('Failed to upload audio file. Please try again.');
          URL.revokeObjectURL(objectUrl);
          clearTimeout(metadataTimeout);
        } finally {
          setUploading(false);
        }
      });

      audioElement.addEventListener('error', (e) => {
        clearTimeout(metadataTimeout);
        console.error('❌ Audio element error:', e);
        URL.revokeObjectURL(objectUrl);
        setUploadError('Invalid audio file. Please select a valid audio recording. The file may be corrupted or in an unsupported format.');
        setUploading(false);
      });

    } catch (error) {
      console.error('Error processing audio file:', error);
      setUploadError('Failed to process audio file. Please try again.');
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setUploadError('');
    setConversionProgress(null);
    setCompressionInfo(null);
    onOpenChange(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md" aria-describedby="upload-dialog-description">
        <DialogHeader>
          <DialogTitle>Upload Call Recording</DialogTitle>
        </DialogHeader>
        <div id="upload-dialog-description" className="sr-only">
          Upload an audio file for a call recording
        </div>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">Appointment Details:</div>
            <div className="bg-muted/50 p-3 rounded-lg">
              <div className="font-medium">{appointment.customer_name}</div>
              <div className="text-sm text-muted-foreground">
                {formatDateTime(appointment.appointment_date)}
              </div>
            </div>
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-1">
                <div><strong>Supported formats:</strong> WAV, MP3, M4A, WebM, OGG</div>
                <div><strong>Size limit:</strong> 100MB (WAV files accepted directly, no conversion needed)</div>
                <div className="text-xs text-muted-foreground mt-1">
                  WAV files are uploaded directly without conversion for faster uploads
                </div>
              </div>
            </AlertDescription>
          </Alert>

          {uploadError && (
            <Alert variant="destructive">
              <AlertDescription>{uploadError}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.m4a,.webm,.ogg,audio/wav,audio/mpeg,audio/mp3,audio/m4a,audio/webm,audio/ogg"
              onChange={handleFileSelect}
              className="hidden"
            />

            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="w-full"
              disabled={uploading}
            >
              <Upload className="h-4 w-4 mr-2" />
              Select Audio File
            </Button>

            {selectedFile && (
              <div className="bg-muted/50 p-3 rounded-lg">
                <div className="flex items-center gap-2">
                  <FileAudio className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{selectedFile.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatFileSize(selectedFile.size)}
                    {shouldConvertAudio(selectedFile, selectedFile.name) && 
                        <span className="ml-2 text-orange-600">• Large file - will be compressed to WebM</span>
                    }
                    </div>
                  </div>
                </div>
              </div>
            )}

            {conversionProgress && (
              <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                <div className="text-sm font-medium text-blue-900 mb-2">
                  Converting audio... ({conversionProgress.stage})
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${conversionProgress.progress}%` }}
                  />
                </div>
                <div className="text-xs text-blue-700 mt-1">
                  {conversionProgress.progress}% complete
                </div>
              </div>
            )}

            {compressionInfo && !conversionProgress && (
              <div className="bg-green-50 border border-green-200 p-3 rounded-lg">
                <div className="text-sm font-medium text-green-900">
                  Conversion Complete!
                </div>
                <div className="text-xs text-green-700 mt-1">
                  Reduced from {formatFileSize(compressionInfo.originalSize)} to {formatFileSize(compressionInfo.convertedSize)} 
                  ({compressionInfo.ratio}% smaller)
                </div>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={uploading}>
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button 
            onClick={handleUpload} 
            disabled={!selectedFile || uploading}
          >
            {uploading ? (
              'Uploading...'
            ) : (
              <>
                <Check className="h-4 w-4 mr-2" />
                Upload Recording
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};