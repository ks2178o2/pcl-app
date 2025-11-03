import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Trash2 } from 'lucide-react';
import { useFailedUploads } from '@/hooks/useFailedUploads';
import { useToast } from '@/hooks/use-toast';
import { formatDistanceToNow } from 'date-fns';

export const FailedUploadsBanner: React.FC = () => {
  const { failedUploads, retryUpload, deleteFailedUpload } = useFailedUploads();
  const { toast } = useToast();

  if (failedUploads.length === 0) return null;

  const handleRetry = async (callRecordId: string) => {
    try {
      await retryUpload(callRecordId);
      toast({
        title: "Upload successful!",
        description: "Your recording has been saved.",
      });
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Please try again later.",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async (callRecordId: string) => {
    try {
      await deleteFailedUpload(callRecordId);
      toast({
        title: "Recording deleted",
        description: "The failed upload has been removed.",
      });
    } catch (error) {
      toast({
        title: "Delete failed",
        description: "Could not delete the recording.",
        variant: "destructive",
      });
    }
  };

  return (
    <Alert variant="destructive" className="mb-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>
        {failedUploads.length} {failedUploads.length === 1 ? 'recording needs' : 'recordings need'} attention
      </AlertTitle>
      <AlertDescription className="mt-2 space-y-2">
        {failedUploads.map((upload) => (
          <div key={upload.id} className="flex items-center justify-between bg-background/50 rounded p-2">
            <div className="flex-1">
              <div className="font-medium">{upload.customer_name}</div>
              <div className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(upload.start_time), { addSuffix: true })}
                {upload.duration_seconds && ` • ${Math.floor(upload.duration_seconds / 60)}:${String(Math.floor(upload.duration_seconds % 60)).padStart(2, '0')}`}
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleRetry(upload.id)}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Retry
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(upload.id)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        ))}
      </AlertDescription>
    </Alert>
  );
};

