import React, { useState, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Users, Check, X, Edit3 } from 'lucide-react';
import { expandDiarizationSegments } from '@/utils/speakerUtils';

interface SpeakerMappingEditorProps {
  isOpen: boolean;
  onClose: () => void;
  speakerMapping: Record<string, string>;
  onSave: (mapping: Record<string, string>) => void;
  diarizationSegments?: any[];
  confidence?: number;
}

export const SpeakerMappingEditor: React.FC<SpeakerMappingEditorProps> = ({
  isOpen,
  onClose,
  speakerMapping,
  onSave,
  diarizationSegments = [],
  confidence = 0
}) => {
  const [editedMapping, setEditedMapping] = useState<Record<string, string>>(speakerMapping);

  const handleMappingChange = (originalSpeaker: string, newName: string) => {
    setEditedMapping(prev => ({
      ...prev,
      [originalSpeaker]: newName
    }));
  };

  const handleSave = () => {
    onSave(editedMapping);
    onClose();
  };

  const handleCancel = () => {
    setEditedMapping(speakerMapping);
    onClose();
  };

  // Normalize segments (handles both compact and standard formats)
  const normalizedSegments = useMemo(() => {
    if (!diarizationSegments || diarizationSegments.length === 0) return [];
    // Check if compact format (has 'sp' property)
    if (diarizationSegments[0]?.sp) {
      return expandDiarizationSegments(diarizationSegments);
    }
    return diarizationSegments;
  }, [diarizationSegments]);

  const uniqueSpeakers = Array.from(new Set(normalizedSegments.map(seg => seg.speaker))).sort();
  const speakerStats = uniqueSpeakers.map(speaker => {
    const segments = normalizedSegments.filter(seg => seg.speaker === speaker);
    const totalDuration = segments.reduce((sum, seg) => sum + (seg.endTime - seg.startTime), 0);
    const avgConfidence = segments.reduce((sum, seg) => sum + (seg.confidence || 0.85), 0) / segments.length;
    
    return {
      speaker,
      segmentCount: segments.length,
      totalDuration,
      avgConfidence
    };
  });

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.75) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit3 className="h-5 w-5" />
            Edit Speaker Labels
          </DialogTitle>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              {uniqueSpeakers.length} speakers detected
            </div>
            {confidence > 0 && (
              <Badge variant="outline" className={getConfidenceColor(confidence)}>
                {Math.round(confidence * 100)}% confidence
              </Badge>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-4">
          {/* Speaker mapping form */}
          <div className="space-y-3">
            {speakerStats.map(({ speaker, segmentCount, totalDuration, avgConfidence }) => (
              <Card key={speaker}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex-1">
                      <Label htmlFor={`speaker-${speaker}`} className="text-sm font-medium">
                        Speaker {speaker}
                      </Label>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{segmentCount} segments</span>
                        <span>•</span>
                        <span>{formatTime(totalDuration)} speaking</span>
                        <span>•</span>
                        <Badge variant="outline" className={`text-xs ${getConfidenceColor(avgConfidence)}`}>
                          {Math.round(avgConfidence * 100)}%
                        </Badge>
                      </div>
                    </div>
                    <div className="flex-1">
                      <Input
                        id={`speaker-${speaker}`}
                        value={editedMapping[speaker] || `Speaker ${speaker}`}
                        onChange={(e) => handleMappingChange(speaker, e.target.value)}
                        placeholder={`Enter name for Speaker ${speaker}`}
                        className="w-full"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {confidence < 0.75 && (
            <div className="p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                <strong>Low confidence detection:</strong> The speaker identification confidence is below 75%. 
                Please review and adjust the speaker labels as needed.
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={handleCancel}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button onClick={handleSave}>
              <Check className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};