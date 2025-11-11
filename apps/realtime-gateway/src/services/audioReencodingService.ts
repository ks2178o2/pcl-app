/**
 * Audio Re-encoding Service
 * 
 * Properly concatenates multiple WebM audio blobs by:
 * 1. Decoding each blob to raw audio (AudioBuffer)
 * 2. Concatenating the raw audio data
 * 3. Re-encoding into a single valid WebM file
 * 
 * This avoids the "Invalid data" error from Deepgram that occurs
 * when directly concatenating WebM blobs (which creates malformed files
 * with multiple headers and incomplete clusters).
 */

/**
 * Combines WebM slices from the same MediaRecorder session into a single Blob
 * Filters out zero-size slices
 */
function combineWebMSlices(slices: Blob[]): Blob {
  const nonEmpty = slices.filter(s => s.size > 0);
  if (nonEmpty.length === 0) {
    throw new Error("All slices are empty");
  }
  const type = nonEmpty[0].type || 'audio/webm;codecs=opus';
  return new Blob(nonEmpty, { type });
}

/**
 * Re-encodes multiple audio slices into a single valid WebM file
 * 
 * Strategy:
 * 1. First attempts fast-path: direct concatenation (works for slices from same MediaRecorder session)
 * 2. Validates the concatenated blob with lightweight decode check
 * 3. Falls back to decode+re-encode if validation fails
 * 
 * @param slices Array of audio Blobs to concatenate
 * @returns A single properly formatted WebM Blob
 */
export async function reencodeAudioSlices(slices: Blob[]): Promise<Blob> {
  if (slices.length === 0) {
    throw new Error("No slices to re-encode");
  }

  if (slices.length === 1) {
    // Single slice doesn't need re-encoding
    return slices[0];
  }

  const startTime = Date.now();
  console.log(`[AudioReencoding] Processing ${slices.length} slices`);

  // Step 1: Try fast-path - direct concatenation
  try {
    const combined = combineWebMSlices(slices);
    console.log(`[AudioReencoding] Trying direct concatenation fast-path: ${(combined.size / 1024 / 1024).toFixed(2)}MB`);
    
    // Validate the combined blob by attempting to decode it
    const audioContext = new AudioContext();
    const arrayBuffer = await combined.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    await audioContext.close();
    
    const elapsed = Date.now() - startTime;
    console.log(`[AudioReencoding] ✓ Direct concatenation validated: ${audioBuffer.duration.toFixed(2)}s in ${elapsed}ms`);
    
    return combined;
  } catch (error) {
    console.warn("[AudioReencoding] Direct concatenation validation failed, falling back to re-encode:", error);
  }

  // Step 2: Fallback - decode each slice and re-encode
  console.log(`[AudioReencoding] Starting fallback re-encoding of ${slices.length} slices`);

  try {
    // Decode all slices to AudioBuffers
    const audioContext = new AudioContext();
    const audioBuffers: AudioBuffer[] = [];
    
    for (let i = 0; i < slices.length; i++) {
      const arrayBuffer = await slices[i].arrayBuffer();
      try {
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        audioBuffers.push(audioBuffer);
        console.log(`[AudioReencoding] ✓ Decoded slice ${i + 1}/${slices.length}: ${audioBuffer.duration.toFixed(2)}s`);
      } catch (err) {
        console.error(`[AudioReencoding] ✗ Failed to decode slice ${i + 1}/${slices.length}:`, err);
        // Don't throw - skip corrupted slices and try to salvage what we can
      }
    }

    if (audioBuffers.length === 0) {
      throw new Error("No valid audio data could be decoded from any slice");
    }

    console.log(`[AudioReencoding] Successfully decoded ${audioBuffers.length}/${slices.length} slices`);

    // Concatenate AudioBuffers
    const sampleRate = audioBuffers[0].sampleRate;
    const numberOfChannels = audioBuffers[0].numberOfChannels;
    const totalLength = audioBuffers.reduce((sum, buf) => sum + buf.length, 0);
    
    console.log(`[AudioReencoding] Concatenating ${audioBuffers.length} buffers: ${totalLength} samples, ${sampleRate}Hz, ${numberOfChannels} channels`);
    
    const combinedBuffer = audioContext.createBuffer(
      numberOfChannels,
      totalLength,
      sampleRate
    );

    let offset = 0;
    for (const buffer of audioBuffers) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const channelData = buffer.getChannelData(channel);
        combinedBuffer.getChannelData(channel).set(channelData, offset);
      }
      offset += buffer.length;
    }

    const totalDuration = combinedBuffer.duration;
    console.log(`[AudioReencoding] Combined buffer duration: ${totalDuration.toFixed(2)}s`);

    // Re-encode using MediaRecorder
    const recodedBlob = await encodeAudioBuffer(combinedBuffer, audioContext);
    
    await audioContext.close();
    
    const elapsed = Date.now() - startTime;
    console.log(`[AudioReencoding] Fallback re-encoding complete: ${(recodedBlob.size / 1024 / 1024).toFixed(2)}MB in ${elapsed}ms`);
    
    return recodedBlob;
  } catch (error) {
    console.error("[AudioReencoding] Re-encoding failed:", error);
    throw error;
  }
}

/**
 * Encodes an AudioBuffer into a WebM blob using MediaRecorder
 */
async function encodeAudioBuffer(
  audioBuffer: AudioBuffer,
  audioContext: AudioContext
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    // Create a buffer source to play the audio
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;

    // Create a destination to capture the audio
    const destination = audioContext.createMediaStreamDestination();
    source.connect(destination);

    // Set up MediaRecorder to capture the stream
    const mediaRecorder = new MediaRecorder(destination.stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 128000
    });

    const chunks: Blob[] = [];
    let startTime: number;

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'audio/webm' });
      const elapsed = Date.now() - startTime;
      console.log(`[AudioReencoding] MediaRecorder captured ${chunks.length} chunks in ${elapsed}ms`);
      resolve(blob);
    };

    mediaRecorder.onerror = (event) => {
      console.error("[AudioReencoding] MediaRecorder error:", event);
      reject(new Error("MediaRecorder encoding failed"));
    };

    // Start recording
    mediaRecorder.start();
    startTime = Date.now();
    
    // Play the audio through (this triggers the recording)
    source.start(0);

    // Stop recording when playback completes
    source.onended = () => {
      // Give MediaRecorder a moment to finish
      setTimeout(() => {
        if (mediaRecorder.state !== 'inactive') {
          mediaRecorder.stop();
        }
      }, 100);
    };
  });
}

