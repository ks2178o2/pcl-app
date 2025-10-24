import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { VoiceRecorder } from '@/components/VoiceRecorder';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { Mic, User, Clock, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { NavigationMenu } from '@/components/NavigationMenu';

interface VoiceProfile {
  id: string;
  speaker_name: string;
  profile_type: 'salesperson' | 'customer';
  audio_sample_url?: string;
  confidence_score: number;
  sample_duration_seconds?: number;
  created_at: string;
}

const SAMPLE_TEXTS = [
  "Hello, thank you for your interest in our product. I'm excited to show you how our solution can help improve your business operations and increase your team's productivity. Let me walk you through the key features and benefits that make our platform unique in the marketplace.",
  
  "Good morning! I appreciate the opportunity to discuss how we can support your company's goals. Our technology has helped hundreds of businesses streamline their processes, reduce costs, and achieve better results. I'd love to demonstrate the specific features that would be most valuable for your organization.",
  
  "Thank you for taking the time to speak with me today. I understand you're looking for a solution that can scale with your business while maintaining the quality and reliability your customers expect. Our platform is designed exactly for companies like yours, and I'm confident we can deliver the results you're looking for."
];

export const VoiceProfile = () => {
  const [voiceProfiles, setVoiceProfiles] = useState<VoiceProfile[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedText, setSelectedText] = useState(SAMPLE_TEXTS[0]);
  const [loading, setLoading] = useState(true);

  const { user } = useAuth();
  const { profile } = useProfile();
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    loadVoiceProfiles();
  }, [user]);

  const loadVoiceProfiles = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from('voice_profiles')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setVoiceProfiles((data || []) as VoiceProfile[]);
    } catch (error) {
      console.error('Error loading voice profiles:', error);
      toast({
        title: "Error loading voice profiles",
        description: "Failed to load your existing voice profiles.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRecordingComplete = async (audioBlob: Blob, duration: number) => {
    if (!user || !profile) return;

    setIsProcessing(true);
    
    try {
      // Upload audio file to storage
      const fileName = `${user.id}/${profile.salesperson_name}-${Date.now()}.webm`;
      
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
          profile_type: 'salesperson',
          speaker_name: profile.salesperson_name,
          audio_sample_url: uploadData.path,
          sample_text: selectedText,
          sample_duration_seconds: duration,
          confidence_score: 0.85 // Initial confidence score
        })
        .select()
        .single();

      if (error) throw error;

      toast({
        title: "Voice profile created successfully!",
        description: "Your voice profile will now be used to improve speaker identification in call transcripts.",
      });

      // Refresh the list
      loadVoiceProfiles();
      setIsRecording(false);

    } catch (error) {
      console.error('Error saving voice profile:', error);
      toast({
        title: "Failed to save voice profile",
        description: error instanceof Error ? error.message : "An unexpected error occurred.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const deleteVoiceProfile = async (profileId: string) => {
    try {
      const { error } = await supabase
        .from('voice_profiles')
        .delete()
        .eq('id', profileId);

      if (error) throw error;

      toast({
        title: "Voice profile deleted",
        description: "The voice profile has been removed successfully.",
      });

      loadVoiceProfiles();
    } catch (error) {
      console.error('Error deleting voice profile:', error);
      toast({
        title: "Failed to delete voice profile",
        description: "An error occurred while deleting the voice profile.",
        variant: "destructive",
      });
    }
  };

  const formatDuration = (seconds: number) => {
    return `${seconds}s`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading voice profiles...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
        <NavigationMenu />
      </div>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Mic className="h-8 w-8" />
          Voice Profile Setup
        </h1>
        <p className="text-muted-foreground">
          Create voice profiles to improve speaker identification accuracy in your call transcripts.
        </p>
      </div>

      {/* Existing Voice Profiles */}
      {voiceProfiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Your Voice Profiles
            </CardTitle>
            <CardDescription>
              Manage your existing voice profiles for improved speaker recognition.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {voiceProfiles.map((profile) => (
                <div
                  key={profile.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{profile.speaker_name}</h3>
                      <Badge variant="secondary">
                        {profile.profile_type}
                      </Badge>
                      {profile.confidence_score >= 0.8 && (
                        <Badge variant="default" className="bg-green-100 text-green-800">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          High Quality
                        </Badge>
                      )}
                      {profile.confidence_score < 0.6 && (
                        <Badge variant="destructive">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Low Quality
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {profile.sample_duration_seconds ? formatDuration(profile.sample_duration_seconds) : 'Unknown'}
                      </span>
                      <span>Created {formatDate(profile.created_at)}</span>
                      <span>Confidence: {Math.round(profile.confidence_score * 100)}%</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteVoiceProfile(profile.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    Delete
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create New Voice Profile */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Voice Profile</CardTitle>
          <CardDescription>
            Record a voice sample to improve speaker identification in your call transcripts.
            Better voice profiles lead to more accurate speaker diarization.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!isRecording ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-3">Choose a sample text to read:</h3>
                <div className="space-y-2">
                  {SAMPLE_TEXTS.map((text, index) => (
                    <button
                      key={index}
                      onClick={() => setSelectedText(text)}
                      className={`w-full p-3 text-left border rounded-lg transition-colors ${
                        selectedText === text
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <div className="font-medium mb-1">Sample {index + 1}</div>
                      <div className="text-sm text-muted-foreground line-clamp-2">
                        {text}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <Button 
                onClick={() => setIsRecording(true)}
                size="lg"
                className="w-full flex items-center gap-2"
              >
                <Mic className="h-4 w-4" />
                Start Voice Recording
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <VoiceRecorder
                sampleText={selectedText}
                onRecordingComplete={handleRecordingComplete}
                isProcessing={isProcessing}
              />
              
              <Button
                variant="outline"
                onClick={() => setIsRecording(false)}
                className="w-full"
              >
                Cancel Recording
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Benefits Section */}
      <Card>
        <CardHeader>
          <CardTitle>Why Create a Voice Profile?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h3 className="font-medium">Improved Accuracy</h3>
              <p className="text-sm text-muted-foreground">
                Voice profiles help our AI distinguish between speakers more accurately, 
                leading to better transcript quality and speaker identification.
              </p>
            </div>
            <div className="space-y-3">
              <h3 className="font-medium">Personalized Recognition</h3>
              <p className="text-sm text-muted-foreground">
                Your unique voice characteristics are analyzed to create a personalized 
                speaker model that works specifically for your voice.
              </p>
            </div>
            <div className="space-y-3">
              <h3 className="font-medium">Better Call Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Accurate speaker identification enables more precise analysis of conversation 
                flow, objections, and action items in your sales calls.
              </p>
            </div>
            <div className="space-y-3">
              <h3 className="font-medium">Privacy & Security</h3>
              <p className="text-sm text-muted-foreground">
                Voice samples are stored securely and used only for improving your 
                transcription accuracy. Data is not shared with third parties.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
