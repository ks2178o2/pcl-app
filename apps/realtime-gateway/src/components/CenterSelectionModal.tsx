import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { MapPin, Building } from 'lucide-react';

interface CenterSelectionModalProps {
  open: boolean;
  centers: Array<{ id: string; name: string; region?: { name: string } }>;
  onSelectCenter: (centerId: string) => void;
}

export const CenterSelectionModal: React.FC<CenterSelectionModalProps> = ({
  open,
  centers,
  onSelectCenter,
}) => {
  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Select Your Center
          </DialogTitle>
          <DialogDescription>
            You have access to multiple centers. Please select which center you'll be working with today.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {centers.map((center) => (
            <Card key={center.id} className="cursor-pointer hover:bg-accent/50 transition-colors">
              <CardContent className="p-4">
                <Button 
                  variant="ghost" 
                  className="w-full h-auto p-0 justify-start"
                  onClick={() => onSelectCenter(center.id)}
                >
                  <div className="flex items-center gap-3">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <div className="text-left">
                      <div className="font-medium">{center.name}</div>
                      {center.region && (
                        <div className="text-sm text-muted-foreground">{center.region.name}</div>
                      )}
                    </div>
                  </div>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
};