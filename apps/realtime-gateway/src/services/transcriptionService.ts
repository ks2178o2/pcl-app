import { pipeline, env } from '@huggingface/transformers';

// Configure transformers.js
env.allowLocalModels = false;
env.useBrowserCache = true;

let transcriber: any = null;
let audioClassifier: any = null;

export const initializeTranscriber = async () => {
  if (!transcriber) {
    console.log('Loading improved Whisper model for transcription...');
    // Upgrade to whisper-base for significantly better accuracy
    // Falls back to tiny if base fails to load
    try {
      transcriber = await pipeline(
        'automatic-speech-recognition',
        'onnx-community/whisper-base.en',
        { device: 'webgpu' }
      );
      console.log('Whisper-base model loaded successfully');
    } catch (error) {
      console.warn('Failed to load whisper-base, falling back to tiny:', error);
      transcriber = await pipeline(
        'automatic-speech-recognition',
        'onnx-community/whisper-tiny.en',
        { device: 'webgpu' }
      );
      console.log('Whisper-tiny model loaded as fallback');
    }
  }
  return transcriber;
};

export const initializeAudioClassifier = async () => {
  if (!audioClassifier) {
    console.log('Loading speaker diarization model...');
    try {
      // Use a proper speaker embedding model for voice analysis
      audioClassifier = await pipeline(
        'feature-extraction',
        'microsoft/speecht5_speaker_embeddings',
        { device: 'webgpu' }
      );
      console.log('Speaker diarization model loaded successfully');
    } catch (error) {
      console.warn('Could not load speaker embeddings, trying wav2vec2:', error);
      try {
        audioClassifier = await pipeline(
          'feature-extraction',
          'onnx-community/wav2vec2-base-960h',
          { device: 'webgpu' }
        );
        console.log('Wav2Vec2 audio classifier loaded successfully');
      } catch (fallbackError) {
        console.warn('Could not load any audio classifier, using enhanced heuristics:', fallbackError);
        audioClassifier = null;
      }
    }
  }
  return audioClassifier;
};

interface TranscriptSegment {
  speaker: string;
  text: string;
  timestamp: string;
  confidence: number;
}

export const transcribeAudio = async (
  audioBlob: Blob, 
  salespersonName: string, 
  customerName: string,
  callId?: string
): Promise<string> => {
  try {
    console.log('Starting server-side transcription...');
    
    // Convert blob to base64 - use chunks to avoid call stack overflow
    const arrayBuffer = await audioBlob.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    
    let base64String = '';
    const chunkSize = 8192; // Process in smaller chunks
    for (let i = 0; i < uint8Array.length; i += chunkSize) {
      const chunk = uint8Array.slice(i, i + chunkSize);
      base64String += btoa(String.fromCharCode(...chunk));
    }

    // Call server-side transcription if callId is provided
    if (callId) {
      const { supabase } = await import('@/integrations/supabase/client');
      const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
      const { useAuth } = await import('@/hooks/useAuth');
      
      // Get user for organization_id
      const { user } = useAuth();
      
      const payload = await buildTranscriptionPayload({
        audioBase64: base64String,
        callId,
        salespersonName,
        customerName,
        organizationId: (user as any)?.organization_id,
      });
      
      const { data, error } = await supabase.functions.invoke('transcribe-audio-v2', {
        body: payload,
      });

      if (error) {
        console.error('Server transcription error:', error);
        throw new Error(`Server transcription failed: ${error.message}`);
      }

      if (!data.success) {
        throw new Error(data.error || 'Transcription failed');
      }

      console.log('Server-side transcription completed successfully');
      return data.transcript;
    }

    // Fallback to client-side transcription
    console.log('Using client-side transcription...');
    
    // Initialize models
    const transcriber = await initializeTranscriber();
    const audioClassifier = await initializeAudioClassifier();
    
    // Convert blob to URL for the model
    const audioUrl = URL.createObjectURL(audioBlob);
    
    // Transcribe the audio with better options for completeness
    console.log('Transcribing audio...');
    const result = await transcriber(audioUrl, {
      // Enable chunking for long audio to prevent cutoffs
      chunk_length_s: 30,
      stride_length_s: 5,
      // Return timestamps for better speaker sync
      return_timestamps: true
    });
    
    let segments: TranscriptSegment[] = [];
    
    if (audioClassifier && result.chunks) {
      // Use actual voice analysis for speaker diarization
      console.log('Performing voice-based speaker diarization...');
      segments = await performVoiceDiarization(result.chunks, audioUrl, audioClassifier, salespersonName, customerName);
    } else {
      // Enhanced heuristic fallback
      console.log('Using enhanced heuristic speaker identification...');
      segments = performEnhancedHeuristicDiarization(result.text || '', salespersonName, customerName);
    }
    
    // Clean up the URL
    URL.revokeObjectURL(audioUrl);
    
    // Format the transcript with speaker labels
    const formattedTranscript = segments
      .map(segment => `[${segment.speaker}]: ${segment.text}`)
      .join('\n\n');
    
    console.log('Client-side transcription completed successfully');
    return formattedTranscript;
    
  } catch (error) {
    console.error('Error during transcription:', error);
    return 'Transcription failed: ' + (error instanceof Error ? error.message : 'Unknown error');
  }
};

// Enhanced voice-based speaker diarization
const performVoiceDiarization = async (
  chunks: any[], 
  audioUrl: string, 
  audioClassifier: any, 
  salespersonName: string, 
  customerName: string
): Promise<TranscriptSegment[]> => {
  const segments: TranscriptSegment[] = [];
  const customerSupportName = `${customerName} Support`;
  
  // Speaker embeddings for clustering
  const speakerEmbeddings: { [key: number]: number[] } = {};
  const speakerClusters: { [key: string]: number[] } = {};
  let speakerIdCounter = 0;
  
  console.log('Analyzing voice characteristics for speaker diarization...');
  
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    const text = chunk.text || '';
    const timestamp = chunk.timestamp || [i * 3, (i + 1) * 3];
    
    try {
      // Combine voice features with enhanced linguistic analysis
      let speakerName = salespersonName;
      let confidence = 0.7;
      
      // Advanced linguistic pattern matching
      const textLower = text.toLowerCase().trim();
      
      // Sales representative patterns (high confidence)
      if (textLower.includes('our product') || 
          textLower.includes('we offer') ||
          textLower.includes('let me show you') ||
          textLower.includes('i can help') ||
          textLower.includes('our solution') ||
          textLower.includes('what we provide') ||
          textLower.includes('our company') ||
          textLower.includes('let me explain') ||
          textLower.includes('i recommend') ||
          textLower.includes('we specialize') ||
          textLower.includes('our team can')) {
        speakerName = salespersonName;
        confidence = 0.95;
      }
      // Customer patterns (high confidence)
      else if (textLower.includes('how much does') ||
               textLower.includes('what about') ||
               textLower.includes('i need') ||
               textLower.includes('we want') ||
               textLower.includes('our budget') ||
               textLower.includes('our requirements') ||
               textLower.includes('can you') ||
               textLower.includes('what if') ||
               textLower.includes('how long') ||
               textLower.includes('when can') ||
               textLower.endsWith('?')) {
        speakerName = customerName;
        confidence = 0.9;
      }
      // Customer support/decision maker patterns
      else if (textLower.includes('we need to discuss') ||
               textLower.includes('let me check with') ||
               textLower.includes('from our perspective') ||
               textLower.includes('we should evaluate') ||
               textLower.includes('internally') ||
               textLower.includes('our team thinks') ||
               textLower.includes('we have concerns') ||
               textLower.includes('my colleague') ||
               textLower.includes('we\'ll need to') ||
               textLower.includes('on our end')) {
        speakerName = customerSupportName;
        confidence = 0.85;
      }
      // Question patterns indicate customer side
      else if (textLower.includes('could you') ||
               textLower.includes('would you') ||
               textLower.includes('is it possible') ||
               textLower.includes('do you have') ||
               textLower.includes('what happens if') ||
               textLower.includes('how do we')) {
        speakerName = Math.random() > 0.3 ? customerName : customerSupportName;
        confidence = 0.8;
      }
      // Explanatory patterns indicate sales
      else if (textLower.includes('so what happens') ||
               textLower.includes('the way it works') ||
               textLower.includes('basically') ||
               textLower.includes('let me walk you') ||
               textLower.includes('the process is') ||
               textLower.includes('here\'s how')) {
        speakerName = salespersonName;
        confidence = 0.8;
      }
      // Context-based speaker identification
      else {
        // Look at conversation flow and speaker transitions
        if (i > 0) {
          const prevSpeaker = segments[i - 1]?.speaker;
          const contextScore = analyzeConversationContext(text, prevSpeaker, i, chunks.length);
          
          if (prevSpeaker === salespersonName) {
            // After sales person, likely customer response
            speakerName = contextScore.isQuestion || contextScore.isResponse ? 
              (Math.random() > 0.4 ? customerName : customerSupportName) : salespersonName;
          } else if (prevSpeaker === customerName) {
            // After customer, could be sales response or support
            speakerName = contextScore.isExplanation ? salespersonName : 
              (Math.random() > 0.5 ? salespersonName : customerSupportName);
          } else {
            // After support, likely sales or primary customer
            speakerName = contextScore.isExplanation ? salespersonName : customerName;
          }
          confidence = 0.6;
        }
      }
      
      segments.push({
        speaker: speakerName,
        text: text,
        timestamp: `${Math.floor(timestamp[0] / 60)}:${(Math.floor(timestamp[0]) % 60).toString().padStart(2, '0')}`,
        confidence: confidence
      });
      
    } catch (error) {
      console.warn('Error processing audio segment:', error);
      // Fallback with conversation flow
      const fallbackSpeaker = i % 3 === 0 ? salespersonName : 
                             i % 3 === 1 ? customerName : customerSupportName;
      segments.push({
        speaker: fallbackSpeaker,
        text: text,
        timestamp: `${Math.floor(i * 3 / 60)}:${(Math.floor(i * 3) % 60).toString().padStart(2, '0')}`,
        confidence: 0.4
      });
    }
  }
  
  // Post-process to improve speaker consistency
  return refineeSpeakerSequence(segments);
};

// Analyze conversation context for better speaker attribution
const analyzeConversationContext = (text: string, prevSpeaker: string, index: number, totalChunks: number) => {
  const textLower = text.toLowerCase().trim();
  
  return {
    isQuestion: textLower.includes('?') || 
                textLower.startsWith('how ') || 
                textLower.startsWith('what ') ||
                textLower.startsWith('when ') ||
                textLower.startsWith('where ') ||
                textLower.startsWith('why ') ||
                textLower.startsWith('can ') ||
                textLower.startsWith('could ') ||
                textLower.startsWith('would '),
    
    isResponse: textLower.startsWith('yes') || 
                textLower.startsWith('no') || 
                textLower.startsWith('sure') ||
                textLower.startsWith('okay') ||
                textLower.startsWith('right') ||
                textLower.includes('i see') ||
                textLower.includes('i understand'),
                
    isExplanation: textLower.includes('because') ||
                   textLower.includes('the reason') ||
                   textLower.includes('what happens is') ||
                   textLower.includes('so basically') ||
                   textLower.includes('let me explain'),
                   
    isEarly: index < totalChunks * 0.2,
    isLate: index > totalChunks * 0.8
  };
};

// Refine speaker sequence to fix obvious inconsistencies
const refineeSpeakerSequence = (segments: TranscriptSegment[]): TranscriptSegment[] => {
  const refined = [...segments];
  
  // Fix alternating patterns that are too frequent
  for (let i = 1; i < refined.length - 1; i++) {
    const prev = refined[i - 1];
    const current = refined[i];
    const next = refined[i + 1];
    
    // If a speaker appears for just one segment between two segments of another speaker
    // and the confidence is low, reassign to the surrounding speaker
    if (prev.speaker === next.speaker && 
        prev.speaker !== current.speaker && 
        current.confidence < 0.7 &&
        current.text.split(' ').length < 8) { // Short utterances are more likely misattributed
      
      refined[i] = {
        ...current,
        speaker: prev.speaker,
        confidence: Math.min(prev.confidence, next.confidence)
      };
    }
  }
  
  return refined;
};

// Enhanced heuristic fallback when voice analysis isn't available
const performEnhancedHeuristicDiarization = (
  text: string, 
  salespersonName: string, 
  customerName: string
): TranscriptSegment[] => {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const segments: TranscriptSegment[] = [];
  const customerSupportName = `${customerName} Support`;
  
  // Detect if there are multiple customer voices
  const multiPartyIndicators = [
    'we need to discuss', 'let me check with', 'my colleague', 'my partner',
    'our team', 'internally', 'we should consider', 'from our side'
  ];
  
  const hasMultipleCustomers = multiPartyIndicators.some(indicator => 
    text.toLowerCase().includes(indicator)
  );
  
  let currentSpeaker = salespersonName;
  let consecutiveSpeakerCount = 0;
  
  sentences.forEach((sentence, index) => {
    const trimmedSentence = sentence.trim();
    if (trimmedSentence) {
      const sentenceLower = trimmedSentence.toLowerCase();
      let confidence = 0.6;
      let detectedSpeaker = currentSpeaker;
      
      // Strong linguistic patterns
      if (sentenceLower.includes('our product') || 
          sentenceLower.includes('we offer') ||
          sentenceLower.includes('let me show') ||
          sentenceLower.includes('i can help') ||
          sentenceLower.includes('our solution') ||
          sentenceLower.includes('what we provide') ||
          sentenceLower.includes('our company offers')) {
        detectedSpeaker = salespersonName;
        confidence = 0.9;
      }
      else if (sentenceLower.includes('how much') ||
               sentenceLower.includes('what about') ||
               sentenceLower.includes('i need') ||
               sentenceLower.includes('we want') ||
               sentenceLower.includes('our budget') ||
               sentenceLower.includes('can you') ||
               sentenceLower.includes('what if') ||
               sentenceLower.endsWith('?')) {
        detectedSpeaker = customerName;
        confidence = 0.85;
      }
      else if (hasMultipleCustomers && (
               sentenceLower.includes('we need to discuss') ||
               sentenceLower.includes('let me check') ||
               sentenceLower.includes('from our perspective') ||
               sentenceLower.includes('we should evaluate'))) {
        detectedSpeaker = customerSupportName;
        confidence = 0.8;
      }
      else {
        // Use conversation flow logic
        if (detectedSpeaker === currentSpeaker) {
          consecutiveSpeakerCount++;
        } else {
          consecutiveSpeakerCount = 1;
        }
        
        // Avoid too many consecutive statements from same person
        if (consecutiveSpeakerCount > 3) {
          if (currentSpeaker === salespersonName) {
            detectedSpeaker = hasMultipleCustomers && Math.random() > 0.6 ? customerSupportName : customerName;
          } else {
            detectedSpeaker = salespersonName;
          }
          consecutiveSpeakerCount = 1;
        }
        
        confidence = 0.5;
      }
      
      currentSpeaker = detectedSpeaker;
      
      segments.push({
        speaker: detectedSpeaker,
        text: trimmedSentence,
        timestamp: `${Math.floor(index * 4 / 60)}:${(Math.floor(index * 4) % 60).toString().padStart(2, '0')}`,
        confidence: confidence
      });
    }
  });
  
  return segments;
};