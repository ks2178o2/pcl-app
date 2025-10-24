import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { TestTube, Upload } from 'lucide-react';
import { AudioUploadModal } from '@/components/AudioUploadModal';
import { useToast } from '@/hooks/use-toast';

interface AudioControlsProps {
  patientName: string;
  patientId?: string;
  hideUpload?: boolean;
  hideTest?: boolean;
  centerId?: string;
}

export const AudioControls: React.FC<AudioControlsProps> = ({ 
  patientName, 
  patientId,
  hideUpload = false,
  hideTest = false,
  centerId
}) => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const { toast } = useToast();

  const testAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      toast({
        title: "Audio test successful",
        description: "Your microphone is working properly",
      });
    } catch (error) {
      toast({
        title: "Audio test failed",
        description: "Could not access microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="flex gap-2">
      {!hideTest && (
        <Button
          variant="outline" 
          size="sm"
          onClick={testAudio}
          className="text-xs"
        >
          <TestTube className="h-3 w-3 mr-1" />
          Test Audio
        </Button>
      )}

      {!hideUpload && (
        <Button
          variant="outline" 
          size="sm"
          onClick={() => setShowUploadModal(true)}
          disabled={!patientName.trim()}
          className="text-xs"
        >
          <Upload className="h-3 w-3 mr-1" />
          Upload Audio
        </Button>
      )}

      <AudioUploadModal
        open={showUploadModal}
        onOpenChange={setShowUploadModal}
        appointment={{
          id: patientId || 'temp',
          customer_name: patientName,
          appointment_date: new Date().toISOString(),
          status: 'current' as const,
          timeDescription: 'Now'
        }}
        centerId={centerId}
        onUploadComplete={() => {
          setShowUploadModal(false);
          toast({
            title: "Success",
            description: "Audio uploaded successfully",
          });
        }}
      />
    </div>
  );
};