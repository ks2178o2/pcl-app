import React from 'react';
import { Button } from '@/components/ui/button';
import { BarChart3 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface TranscriptViewerProps {
  transcript: string;
  customerName: string;
  salespersonName: string;
  duration: number;
  timestamp: Date;
  callId?: string;
  onRetryTranscription?: () => void;
}

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({ 
  callId
}) => {
  console.log('TranscriptViewer rendering with callId:', callId);
  const navigate = useNavigate();

  const handleViewAnalysis = () => {
    if (callId) {
      navigate(`/analysis/${callId}`);
    }
  };

  return (
    <Button 
      onClick={handleViewAnalysis}
      className="bg-primary hover:bg-primary/90 text-primary-foreground" 
      size="sm"
    >
      <BarChart3 className="h-3 w-3 mr-2" />
      View Analysis
    </Button>
  );
};