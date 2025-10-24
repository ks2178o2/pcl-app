import { supabase } from '@/integrations/supabase/client';

interface TranscriptionPayload {
  callId?: string;
  audioBase64?: string;
  audioUrl?: string;
  storagePath?: string;
  provider: 'deepgram' | 'assemblyai';
  fallback_provider: 'deepgram' | 'assemblyai';
  allow_fallback: boolean;
  bakeoff: boolean;
  language?: string;
  useChunks?: boolean;
  salespersonName?: string;
  customerName?: string;
  clientTraceId?: string;
}

interface BuildPayloadOptions {
  callId?: string;
  audioBase64?: string;
  audioUrl?: string;
  storagePath?: string;
  useChunks?: boolean;
  salespersonName?: string;
  customerName?: string;
  organizationId?: string; // Used to lookup org-specific provider settings
  overrideProvider?: 'deepgram' | 'assemblyai';
  overrideFallback?: 'deepgram' | 'assemblyai';
  overrideAllowFallback?: boolean;
  overrideBakeoff?: boolean;
  language?: string;
}

/**
 * Build standardized transcription payload with organization-specific settings
 * 
 * Priority order for provider settings:
 * 1. Explicit override parameters
 * 2. Organization-level settings from database
 * 3. localStorage (legacy support)
 * 4. Hardcoded defaults
 * 
 * @param options - Configuration options for transcription payload
 * @returns Promise<TranscriptionPayload> - Standardized payload for transcribe-audio-v2
 */
export async function buildTranscriptionPayload(
  options: BuildPayloadOptions
): Promise<TranscriptionPayload> {
  // Start with default values
  let orgProvider: 'deepgram' | 'assemblyai' = 'deepgram';
  let orgFallback: 'deepgram' | 'assemblyai' = 'assemblyai';
  let orgAllowFallback = true;
  let orgBakeoff = false;

  // 1. Fetch organization-specific settings if organizationId provided
  if (options.organizationId) {
    try {
      const { data: org, error } = await supabase
        .from('organizations')
        .select('transcription_provider, transcription_fallback_provider, transcription_allow_fallback, transcription_bakeoff')
        .eq('id', options.organizationId)
        .maybeSingle();

      if (!error && org) {
        // Type assertion needed since columns might not exist yet in older databases
        const orgData = org as any;
        orgProvider = (orgData.transcription_provider as 'deepgram' | 'assemblyai') || 'deepgram';
        orgFallback = (orgData.transcription_fallback_provider as 'deepgram' | 'assemblyai') || 'assemblyai';
        orgAllowFallback = orgData.transcription_allow_fallback ?? true;
        orgBakeoff = orgData.transcription_bakeoff ?? false;
        console.log('📊 Using organization transcription settings:', {
          provider: orgProvider,
          fallback: orgFallback,
          allowFallback: orgAllowFallback,
          bakeoff: orgBakeoff
        });
      }
    } catch (err) {
      console.warn('⚠️ Could not fetch organization transcription settings, using defaults:', err);
    }
  }

  // 2. Check localStorage for user override (legacy support)
  const localProvider = localStorage.getItem('transcriptionProvider') as 'deepgram' | 'assemblyai' | null;

  // 3. Build payload with priority: explicit override > org settings > localStorage > defaults
  const provider = options.overrideProvider || orgProvider || localProvider || 'deepgram';
  
  // Ensure fallback is different from primary provider
  const fallbackProvider = options.overrideFallback || orgFallback || 
    (provider === 'deepgram' ? 'assemblyai' : 'deepgram');

  const payload: TranscriptionPayload = {
    callId: options.callId,
    audioBase64: options.audioBase64,
    audioUrl: options.audioUrl,
    storagePath: options.storagePath,
    provider,
    fallback_provider: fallbackProvider,
    allow_fallback: options.overrideAllowFallback ?? orgAllowFallback,
    bakeoff: options.overrideBakeoff ?? orgBakeoff,
    useChunks: options.useChunks,
    salespersonName: options.salespersonName,
    customerName: options.customerName,
    clientTraceId: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
  };

  // Only include language if explicitly provided
  if (options.language) {
    payload.language = options.language;
  }

  console.log('🎤 Built transcription payload:', {
    callId: payload.callId,
    provider: payload.provider,
    fallback: payload.fallback_provider,
    allowFallback: payload.allow_fallback,
    bakeoff: payload.bakeoff,
    hasAudio: !!(payload.audioBase64 || payload.audioUrl || payload.storagePath),
    useChunks: payload.useChunks
  });

  return payload;
}
