import { useState, useEffect } from 'react';
import { transcribeAudio } from '@/services/transcriptionService';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';

interface CallRecord {
  id: string;
  patientName: string;
  salespersonName: string;
  duration: number;
  timestamp: Date;
  status: 'completed' | 'in-progress' | 'transcribing';
  audioBlob?: Blob;
  transcript?: string;
  diarizationSegments?: any[];
  speakerMapping?: Record<string, string>;
  diarizationConfidence?: number;
  numSpeakers?: number;
  patientId?: string; // Optional for now, will be required after migration
  audioPath?: string; // Storage path to audio in bucket for lazy playback
}

export const useCallRecords = () => {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const { user } = useAuth();
  const { toast } = useToast();

  // Load calls from database on mount
  // Removed auto-load on user change - parent component now controls when to load with limit

  const loadCalls = async (limit?: number) => {
    if (!user) return;
    
    console.log('🔄 Loading calls from database for user:', user.id, limit ? `(limit: ${limit})` : '');

    try {
      console.log('🔍 Starting query for user:', user.id, limit ? `limit: ${limit}` : '');
      
      // Restore original working query pattern with proper chaining
      let query = supabase
        .from('call_records')
        .select('*')  // Try SELECT * like appointments
        .eq('user_id', user.id)
        .eq('recording_complete', true);  // Use recording_complete instead of is_active
      
      if (limit) {
        query = query.limit(limit);
      }
      
      query = query.order('start_time', { ascending: false });  // Use start_time instead of created_at

      console.log('⏳ Executing query...');
      const { data, error } = await query;
      console.log('✅ Query completed, data:', data?.length || 0, 'records');

      if (error) {
        console.error('❌ Error in loadCalls query:', error);
        throw error;
      }
      
      console.log('📊 Query returned', data?.length || 0, 'records');

      // Format the data - simplified version without expensive audio fetching
      const formattedCalls: CallRecord[] = (data || []).map(record => ({
        id: record.id,
        patientName: record.customer_name,
        salespersonName: 'You', // Will be filled by parent component
        duration: record.duration_seconds || 0,
        timestamp: new Date(record.start_time || record.created_at),
        status: 'completed' as const,
        transcript: record.transcript || undefined,
        audioPath: record.audio_file_url || undefined,
        diarizationSegments: (record as any).diarization_segments || [],
        speakerMapping: (record as any).speaker_mapping || {},
        diarizationConfidence: (record as any).diarization_confidence || 0,
        numSpeakers: (record as any).num_speakers || 2,
        patientId: (record as any).patient_id || undefined
      }));

      setCalls(formattedCalls);
    } catch (error) {
      console.error('❌ Error loading calls:', error);
    }
  };

  const addCall = async (audioBlob: Blob, duration: number, patientName: string, salespersonName: string, patientId?: string, centerId?: string) => {
    if (!user) return;

    const newCall: CallRecord = {
      id: Date.now().toString(),
      patientName,
      salespersonName,
      duration,
      timestamp: new Date(),
      status: 'transcribing',
      audioBlob,
      transcript: 'Transcribing audio...',
      patientId
    };

    setCalls(prev => [newCall, ...prev]);

    console.log('💾 Saving call to database:', {
      patient: patientName,
      duration,
      userId: user.id
    });

    try {
      // Save to database first
      const { data, error } = await supabase
        .from('call_records')
        .insert({
          user_id: user.id,
          customer_name: patientName,
          start_time: new Date().toISOString(),
          end_time: new Date(Date.now() + duration * 1000).toISOString(),
          transcript: 'Transcribing audio...',
          total_chunks: 1,
          chunks_uploaded: 0,
          recording_complete: true,
          patient_id: patientId || null,
          center_id: centerId || null
        })
        .select()
        .single();

      if (error) throw error;

      console.log('✅ Call saved to database with ID:', data.id);

      // Upload audio file to storage
      const fileName = `${user.id}/${data.id}.webm`;
      console.log('📤 Uploading audio file:', fileName);
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('call-recordings')
        .upload(fileName, audioBlob, {
          contentType: 'audio/webm',
          upsert: true,
        });

      if (uploadError) {
        console.error('❌ Audio upload failed:', uploadError);
      } else {
        console.log('✅ Audio uploaded successfully:', uploadData.path);
        
        // Update database with audio file URL and mark as ready for transcription
        const { error: updateError } = await supabase
          .from('call_records')
          .update({
            chunks_uploaded: 1,
            status: 'ready_for_transcription',
            audio_file_url: uploadData.path 
          })
          .eq('id', data.id);
          
        if (updateError) {
          console.error('❌ Failed to update audio URL:', updateError);
        } else {
          console.log('✅ Audio URL updated in database');
        }
      }

      // Update the call with the database ID
      const updatedCall = { ...newCall, id: data.id, audioPath: (typeof uploadData !== 'undefined' && uploadData?.path) ? uploadData.path : (undefined as any) };
      setCalls(prev => prev.map(call => 
        call.id === newCall.id ? updatedCall : call
      ));

      console.log('🎤 Starting transcription for call:', data.id);

      // Start transcription in the background - wrap in setTimeout to prevent stack overflow
      setTimeout(async () => {
        try {
          // Import helper
          const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
          
          const storagePath = (typeof uploadData !== 'undefined' && uploadData?.path) ? uploadData.path : undefined;
          
          let transcriptionResult: any, transcriptionError: any;
          
          if (storagePath) {
            // Prefer server-side fetch from storage to avoid large payloads
            const payload = await buildTranscriptionPayload({
              storagePath,
              callId: data.id,
              salespersonName,
              customerName: patientName,
              organizationId: (user as any)?.organization_id,
            });
            
            ({ data: transcriptionResult, error: transcriptionError } = await supabase.functions.invoke('transcribe-audio-v2', {
              body: payload,
            }));
          } else {
            // Fallback: convert blob to base64 and send directly
            const convertBlobToBase64 = async (blob: Blob) => {
              const arrayBuffer = await blob.arrayBuffer();
              const uint8Array = new Uint8Array(arrayBuffer);
              let base64String = '';
              const chunkSize = 8192;
              for (let i = 0; i < uint8Array.length; i += chunkSize) {
                const chunk = uint8Array.slice(i, i + chunkSize);
                base64String += btoa(String.fromCharCode(...chunk));
              }
              return base64String;
            };
            const audioBase64 = await convertBlobToBase64(audioBlob);
            
            const payload = await buildTranscriptionPayload({
              audioBase64,
              callId: data.id,
              salespersonName,
              customerName: patientName,
              organizationId: (user as any)?.organization_id,
            });
            
            ({ data: transcriptionResult, error: transcriptionError } = await supabase.functions.invoke('transcribe-audio-v2', {
              body: payload,
            }));
          }
          
          if (transcriptionError || !transcriptionResult?.success) {
            throw new Error(transcriptionResult?.error || 'Transcription failed');
          }
          
          const transcript = transcriptionResult.transcript;
          console.log('✅ Transcription completed, updating database for call:', data.id);
          await updateCallInDatabase(data.id, { transcript, status: 'completed' });
          
          // After successful transcription, trigger analysis in background
          console.log('🔍 Starting background analysis for call:', data.id);
          setTimeout(async () => {
            try {
              // Fetch the complete call record to get diarization_segments
              const { data: callData, error: fetchError } = await supabase
                .from('call_records')
                .select('transcript, diarization_segments, speaker_mapping')
                .eq('id', data.id)
                .single();
              
              if (fetchError || !callData) {
                throw new Error('Failed to fetch call data for analysis');
              }

              // Generate formatted transcript from diarization segments if available
              let formattedTranscript = callData.transcript;
              if (callData.diarization_segments && callData.speaker_mapping) {
                const { generateMappedTranscript } = await import('@/utils/speakerUtils');
                formattedTranscript = generateMappedTranscript(
                  callData.diarization_segments as any[],
                  callData.speaker_mapping as Record<string, string>
                );
              }

              const { transcriptAnalysisService } = await import('@/services/transcriptAnalysisService');
              await transcriptAnalysisService.analyzeTranscript(
                formattedTranscript,
                patientName,
                salespersonName,
                data.id,
                user.id
              );
              console.log('✅ Background analysis completed for call:', data.id);
            } catch (error) {
              console.error('❌ Background analysis failed for call:', data.id, error);
            }
          }, 1000); // Wait 1 second after transcription completes
        } catch (error) {
          console.error('❌ Transcription failed:', error);
          await updateCallInDatabase(data.id, { 
            transcript: 'Transcription failed', 
            status: 'completed' 
          });
        }
      }, 0);

      return updatedCall;
    } catch (error) {
      console.error('❌ Error saving call to database:', error);
      // Update local state to show error
      updateCall(newCall.id, { 
        transcript: 'Failed to save call', 
        status: 'completed' 
      });
      return newCall;
    }
  };

  const updateCallInDatabase = async (id: string, updates: { transcript?: string; status?: string }) => {
    console.log('📝 Updating transcript in database for call:', id);
    try {
      const { error } = await supabase
        .from('call_records')
        .update({
          transcript: updates.transcript
        })
        .eq('id', id);

      if (error) throw error;

      console.log('✅ Transcript updated successfully in database');

      // Update local state
      setCalls(prev => 
        prev.map(call => 
          call.id === id ? { 
            ...call, 
            transcript: updates.transcript,
            status: updates.status as any || call.status
          } : call
        )
      );
    } catch (error) {
      console.error('❌ Error updating transcript in database:', error);
    }
  };

  const updateCall = (id: string, updates: Partial<CallRecord>) => {
    setCalls(prev => 
      prev.map(call => 
        call.id === id ? { ...call, ...updates } : call
      )
    );
  };

  const updateSpeakerMapping = async (callId: string, speakerMapping: Record<string, string>) => {
    try {
      const { error } = await supabase
        .from('call_records')
        .update({ speaker_mapping: speakerMapping } as any)
        .eq('id', callId);

      if (error) throw error;

      // Update local state
      updateCall(callId, { speakerMapping });
      console.log('✅ Speaker mapping updated successfully');
    } catch (error) {
      console.error('❌ Error updating speaker mapping:', error);
    }
  };

  // New function for handling chunked recording completion
  const handleChunkedRecordingComplete = async (callRecordId: string, totalDuration: number) => {
    console.log('🎯 Handling chunked recording completion:', { callRecordId, totalDuration });

    // Update UI immediately
    setCalls(prev => prev.map(call =>
      call.id === callRecordId
        ? { ...call, duration: totalDuration, status: 'transcribing' as const }
        : call
    ));

    // Robust DB-based wait: ensure all expected chunks are visible before invoking
    const maxWaitMs = 60000; // 60s
    const pollMs = 800;
    const start = Date.now();
    let uploaded = 0;
    let expected = 0;
    let complete = false;

    for (;;) {
      try {
        const [{ data: rec }, { count }] = await Promise.all([
          supabase.from('call_records').select('total_chunks,recording_complete').eq('id', callRecordId).single(),
          supabase.from('call_chunks').select('id', { count: 'exact', head: true }).eq('call_record_id', callRecordId).eq('upload_status', 'uploaded'),
        ]);
        expected = rec?.total_chunks ?? expected;
        complete = !!rec?.recording_complete;
        uploaded = typeof count === 'number' ? count : uploaded;
        const elapsed = Date.now() - start;
        console.log(`📊 Chunk readiness: ${uploaded}/${expected}, complete=${complete}, elapsed=${elapsed}ms`);
        if (complete && expected > 0 && uploaded >= expected) break;
        if (elapsed >= maxWaitMs) break;
      } catch (e) {
        console.warn('⚠️ Chunk readiness check failed:', e);
        // still keep waiting up to max
      }
      await new Promise(r => setTimeout(r, pollMs));
    }

    // If nothing uploaded after wait, back off and retry later
    if (uploaded === 0) {
      toast({ title: 'Upload in progress', description: 'Waiting for audio chunks to finish uploading...' });
      setTimeout(() => handleChunkedRecordingComplete(callRecordId, totalDuration), 5000);
      return;
    }

    // Trigger transcription
    try {
      const { buildTranscriptionPayload } = await import('@/utils/transcriptionUtils');
      console.log('🎤 Invoking transcription for chunked recording:', { callRecordId });
      const payload = await buildTranscriptionPayload({ callId: callRecordId, useChunks: true, organizationId: (user as any)?.organization_id });
      const { data, error } = await supabase.functions.invoke('transcribe-audio-v2', { body: payload });
      if (error) {
        console.error('❌ Transcription invocation failed:', error);
        setCalls(prev => prev.map(call => call.id === callRecordId ? { ...call, status: 'in-progress' as const } : call));
        toast({ title: 'Transcription failed', description: 'Could not start transcription. You can retry from the call list.', variant: 'destructive' });
      } else {
        console.log('✅ Transcription started successfully:', data?.requestId);
        toast({ title: 'Transcription started', description: `Processing ${uploaded} audio chunks...` });
      }
    } catch (error) {
      console.error('❌ Error invoking transcription:', error);
      setCalls(prev => prev.map(call => call.id === callRecordId ? { ...call, status: 'in-progress' as const } : call));
    }
  };

  return {
    calls,
    addCall,
    updateCall,
    updateSpeakerMapping,
    loadCalls,
    handleChunkedRecordingComplete
  };
};