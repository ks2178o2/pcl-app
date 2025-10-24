export interface ConversionResult {
  convertedBlob: Blob;
  originalSize: number;
  convertedSize: number;
  compressionRatio: number;
}

export interface ConversionProgress {
  stage: 'analyzing' | 'converting' | 'complete';
  progress: number;
}

const WAV_SIZE_THRESHOLD = 5 * 1024 * 1024; // 5MB threshold for conversion

export const shouldConvertAudio = (file: Blob, fileName: string): boolean => {
  const isWav = fileName.toLowerCase().endsWith('.wav') || file.type === 'audio/wav';
  const isLarge = file.size > WAV_SIZE_THRESHOLD;
  return isWav && isLarge;
};

export const convertAudioToWebM = async (
  audioBlob: Blob,
  onProgress?: (progress: ConversionProgress) => void
): Promise<ConversionResult> => {
  const originalSize = audioBlob.size;
  
  try {
    onProgress?.({ stage: 'analyzing', progress: 10 });

    // Create audio context
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    onProgress?.({ stage: 'analyzing', progress: 30 });

    // Decode audio data
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    onProgress?.({ stage: 'converting', progress: 50 });

    // Set up MediaRecorder with WebM format
    const stream = new MediaStream();
    const source = audioContext.createMediaStreamSource(
      new MediaStream([await createAudioTrackFromBuffer(audioBuffer, audioContext)])
    );
    
    // Create a destination that we can connect to a MediaStream
    const destination = audioContext.createMediaStreamDestination();
    source.connect(destination);
    
    onProgress?.({ stage: 'converting', progress: 70 });

    // Record with WebM format
    const mediaRecorder = new MediaRecorder(destination.stream, {
      mimeType: 'audio/webm;codecs=opus'
    });

    const chunks: BlobPart[] = [];
    
    return new Promise((resolve, reject) => {
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        onProgress?.({ stage: 'complete', progress: 100 });
        
        const convertedBlob = new Blob(chunks, { type: 'audio/webm' });
        const convertedSize = convertedBlob.size;
        const compressionRatio = Math.round(((originalSize - convertedSize) / originalSize) * 100);

        audioContext.close();
        
        resolve({
          convertedBlob,
          originalSize,
          convertedSize,
          compressionRatio
        });
      };

      mediaRecorder.onerror = (event) => {
        audioContext.close();
        reject(new Error('Conversion failed'));
      };

      onProgress?.({ stage: 'converting', progress: 90 });
      mediaRecorder.start();
      
      // Stop recording after the audio duration
      setTimeout(() => {
        mediaRecorder.stop();
      }, (audioBuffer.duration * 1000) + 100);
    });

  } catch (error) {
    console.error('Audio conversion failed:', error);
    throw new Error('Failed to convert audio format');
  }
};

// Helper function to create audio track from buffer
async function createAudioTrackFromBuffer(
  audioBuffer: AudioBuffer, 
  audioContext: AudioContext
): Promise<MediaStreamTrack> {
  // Create an offline context to render the audio
  const offlineContext = new OfflineAudioContext(
    audioBuffer.numberOfChannels,
    audioBuffer.length,
    audioBuffer.sampleRate
  );
  
  const source = offlineContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineContext.destination);
  source.start();
  
  const renderedBuffer = await offlineContext.startRendering();
  
  // Create a MediaStream from the rendered buffer
  const stream = audioContext.createMediaStreamDestination().stream;
  return stream.getAudioTracks()[0];
}

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};