import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';

interface VoiceProfile {
  id: string;
  user_id: string;
  profile_type: 'salesperson' | 'customer';
  speaker_name: string;
  audio_sample_url?: string;
  voice_embedding?: any;
  sample_text?: string;
  sample_duration_seconds?: number;
  confidence_score: number;
  created_at: string;
  updated_at: string;
}

export const useVoiceProfiles = () => {
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      loadProfiles();
    }
  }, [user]);

  const loadProfiles = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError(null);

      const { data, error: fetchError } = await supabase
        .from('voice_profiles')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (fetchError) throw fetchError;

      setProfiles((data || []) as VoiceProfile[]);
    } catch (err) {
      console.error('Error loading voice profiles:', err);
      setError(err instanceof Error ? err.message : 'Failed to load voice profiles');
    } finally {
      setLoading(false);
    }
  };

  const createProfile = async (
    profileType: 'salesperson' | 'customer',
    speakerName: string,
    audioBlob: Blob,
    sampleText: string,
    duration: number
  ): Promise<VoiceProfile | null> => {
    if (!user) throw new Error('User not authenticated');

    try {
      // Upload audio file to storage
      const fileName = `${user.id}/${speakerName}-${Date.now()}.webm`;
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('voice-samples')
        .upload(fileName, audioBlob, {
          contentType: 'audio/webm'
        });

      if (uploadError) throw uploadError;

      // Save voice profile to database
      const { data, error } = await supabase
        .from('voice_profiles')
        .insert({
          user_id: user.id,
          profile_type: profileType,
          speaker_name: speakerName,
          audio_sample_url: uploadData.path,
          sample_text: sampleText,
          sample_duration_seconds: duration,
          confidence_score: 0.85 // Initial confidence score
        })
        .select()
        .single();

      if (error) throw error;

      // Refresh the profiles list
      await loadProfiles();

      return data as VoiceProfile;
    } catch (err) {
      console.error('Error creating voice profile:', err);
      throw err;
    }
  };

  const deleteProfile = async (profileId: string): Promise<void> => {
    try {
      const { error } = await supabase
        .from('voice_profiles')
        .delete()
        .eq('id', profileId);

      if (error) throw error;

      // Refresh the profiles list
      await loadProfiles();
    } catch (err) {
      console.error('Error deleting voice profile:', err);
      throw err;
    }
  };

  const getProfileByName = (speakerName: string, profileType?: 'salesperson' | 'customer'): VoiceProfile | null => {
    return profiles.find(profile => 
      profile.speaker_name === speakerName && 
      (!profileType || profile.profile_type === profileType)
    ) || null;
  };

  const getSalespersonProfiles = (): VoiceProfile[] => {
    return profiles.filter(profile => profile.profile_type === 'salesperson');
  };

  const getCustomerProfiles = (): VoiceProfile[] => {
    return profiles.filter(profile => profile.profile_type === 'customer');
  };

  return {
    profiles,
    loading,
    error,
    loadProfiles,
    createProfile,
    deleteProfile,
    getProfileByName,
    getSalespersonProfiles,
    getCustomerProfiles
  };
};