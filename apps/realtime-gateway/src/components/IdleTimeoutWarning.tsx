import React from 'react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Clock, Shield } from 'lucide-react';

interface IdleTimeoutWarningProps {
  isOpen: boolean;
  remainingSeconds: number;
  onExtend: () => void;
  onLogout: () => void;
}

export const IdleTimeoutWarning: React.FC<IdleTimeoutWarningProps> = ({
  isOpen,
  remainingSeconds,
  onExtend,
  onLogout,
}) => {
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <AlertDialog open={isOpen}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-warning" />
            <AlertDialogTitle>Session Timeout Warning</AlertDialogTitle>
          </div>
          <AlertDialogDescription asChild>
            <div className="space-y-3">
              <p>
                For security and PHI protection, your session will automatically 
                logout due to inactivity.
              </p>
              <div className="flex items-center gap-2 p-3 bg-warning/10 rounded-lg">
                <Clock className="h-4 w-4 text-warning" />
                <span className="font-medium text-warning">
                  Time remaining: {formatTime(remainingSeconds)}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Click "Stay Logged In" to extend your session, or "Logout" to 
                securely end your session now.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onLogout}>
            Logout Now
          </AlertDialogCancel>
          <AlertDialogAction onClick={onExtend} className="bg-primary hover:bg-primary/90">
            Stay Logged In
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};