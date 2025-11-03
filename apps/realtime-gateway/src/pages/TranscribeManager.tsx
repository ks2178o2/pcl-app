import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { NavigationMenu } from '@/components/NavigationMenu';
import { useToast } from '@/hooks/use-toast';
import { 
  ArrowLeft, 
  FileAudio, 
  Upload,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Download,
  AlertCircle
} from 'lucide-react';
import TranscribeFileUpload from '@/components/TranscribeFileUpload';
import { useAuth } from '@/hooks/useAuth';

interface Transcription {
  id: string;
  file_name: string;
  file_size: number;
  provider: string;
  status: string;
  progress?: number;
  transcript?: string;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export const TranscribeManager = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('upload');

  useEffect(() => {
    if (user) {
      loadTranscriptions();
    }
  }, [user]);

  const loadTranscriptions = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const response = await fetch('/api/transcribe/list?limit=100&offset=0', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load transcriptions');
      }

      const data = await response.json();
      setTranscriptions(data.transcriptions || []);
    } catch (error) {
      console.error('Error loading transcriptions:', error);
      toast({
        title: "Error",
        description: "Failed to load transcriptions",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (uploadId: string) => {
    if (!confirm('Are you sure you want to delete this transcription?')) {
      return;
    }

    try {
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const response = await fetch(`/api/transcribe/${uploadId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete transcription');
      }

      toast({
        title: "Deleted",
        description: "Transcription deleted successfully",
      });

      loadTranscriptions();
    } catch (error) {
      console.error('Error deleting transcription:', error);
      toast({
        title: "Error",
        description: "Failed to delete transcription",
        variant: "destructive",
      });
    }
  };

  const handleRetry = async (uploadId: string) => {
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const response = await fetch(`/api/transcribe/retry/${uploadId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to retry transcription');
      }

      toast({
        title: "Retry started",
        description: "Transcription job restarted",
      });

      loadTranscriptions();
    } catch (error) {
      console.error('Error retrying transcription:', error);
      toast({
        title: "Error",
        description: "Failed to retry transcription",
        variant: "destructive",
      });
    }
  };

  const handleRefresh = () => {
    loadTranscriptions();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <Badge variant="default" className="bg-green-100 text-green-800">Completed</Badge>;
      case 'processing':
        return <Badge variant="secondary">Processing</Badge>;
      case 'queued':
        return <Badge variant="outline">Queued</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getProviderBadge = (provider: string) => {
    return <Badge variant="outline">{provider === 'deepgram' ? 'Deepgram' : 'AssemblyAI'}</Badge>;
  };

  const handleUploadComplete = () => {
    loadTranscriptions();
    setActiveTab('transcriptions');
  };

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
          <FileAudio className="h-8 w-8" />
          Transcription Manager
        </h1>
        <p className="text-muted-foreground">
          Upload audio files for transcription and manage your transcription jobs.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="upload">
            <Upload className="h-4 w-4 mr-2" />
            Upload Audio
          </TabsTrigger>
          <TabsTrigger value="transcriptions">
            <FileAudio className="h-4 w-4 mr-2" />
            My Transcriptions
          </TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload">
          <TranscribeFileUpload onUploadComplete={handleUploadComplete} />
        </TabsContent>

        {/* Transcriptions Tab */}
        <TabsContent value="transcriptions">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <FileAudio className="h-5 w-5" />
                    Transcription History
                  </CardTitle>
                  <CardDescription>
                    View and manage your transcription jobs
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={loading}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                  <p className="text-muted-foreground">Loading transcriptions...</p>
                </div>
              ) : transcriptions.length === 0 ? (
                <div className="text-center py-8">
                  <FileAudio className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No transcriptions yet</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Upload an audio file to get started
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {transcriptions.map((transcription) => (
                    <div
                      key={transcription.id}
                      className="border rounded-lg p-4 space-y-3"
                    >
                      {/* Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <FileAudio className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">{transcription.file_name}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{formatFileSize(transcription.file_size)}</span>
                            <span>•</span>
                            <span>{formatDate(transcription.created_at)}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusBadge(transcription.status)}
                          {getProviderBadge(transcription.provider)}
                        </div>
                      </div>

                      {/* Progress */}
                      {transcription.status === 'processing' && transcription.progress !== undefined && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Processing...</span>
                            <span>{transcription.progress}%</span>
                          </div>
                          <div className="w-full bg-secondary rounded-full h-2">
                            <div
                              className="bg-primary h-2 rounded-full transition-all"
                              style={{ width: `${transcription.progress}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Transcript preview */}
                      {transcription.status === 'completed' && transcription.transcript && (
                        <div className="mt-3 p-3 bg-muted rounded-lg max-h-40 overflow-y-auto">
                          <p className="text-sm font-medium mb-1">Transcript:</p>
                          <p className="text-sm text-muted-foreground line-clamp-3">
                            {transcription.transcript}
                          </p>
                        </div>
                      )}

                      {/* Error */}
                      {transcription.status === 'failed' && transcription.error && (
                        <Alert variant="destructive">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>{transcription.error}</AlertDescription>
                        </Alert>
                      )}

                      {/* Actions */}
                      <div className="flex items-center justify-end gap-2 pt-2 border-t">
                        {transcription.status === 'failed' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRetry(transcription.id)}
                          >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Retry
                          </Button>
                        )}
                        {transcription.status === 'completed' && transcription.transcript && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const blob = new Blob([transcription.transcript!], { type: 'text/plain' });
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = `${transcription.file_name}.txt`;
                              document.body.appendChild(a);
                              a.click();
                              document.body.removeChild(a);
                              URL.revokeObjectURL(url);
                            }}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(transcription.id)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TranscribeManager;

