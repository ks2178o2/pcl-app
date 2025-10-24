import React, { createContext, useContext, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useTokenBasedTimeout } from '@/hooks/useTokenBasedTimeout';
import { useRecordingState } from '@/hooks/useRecordingState';
import { IdleTimeoutWarning } from '@/components/IdleTimeoutWarning';
import { useToast } from '@/hooks/use-toast';
import { useNavigate } from 'react-router-dom';

interface IdleTimeoutContextType {
  isRecording: boolean;
  setIsRecording: (recording: boolean) => void;
  resetActivity: () => void;
}

const IdleTimeoutContext = createContext<IdleTimeoutContextType | undefined>(undefined);

export const useIdleTimeoutContext = () => {
  const context = useContext(IdleTimeoutContext);
  if (!context) {
    throw new Error('useIdleTimeoutContext must be used within IdleTimeoutProvider');
  }
  return context;
};

interface IdleTimeoutProviderProps {
  children: React.ReactNode;
}

export const IdleTimeoutProvider: React.FC<IdleTimeoutProviderProps> = ({ 
  children
}) => {
  const { signOut } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { isRecording } = useRecordingState();

  const handleTimeout = useCallback(async () => {
    try {
      // CLEANUP RECORDING STATE BEFORE LOGOUT
      console.log('🧹 Cleaning up recording state due to timeout');
      
      // Clear localStorage recording states
      localStorage.removeItem('chunked_recording_state');
      localStorage.removeItem('audiorecorder_state');
      
      // Clear IndexedDB slices
      try {
        const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService');
        await ChunkedRecordingManager.clearAllSlices();
      } catch (e) {
        console.warn('Could not clear recording slices:', e);
      }
      
      // Clear any sensitive data from localStorage/sessionStorage
      localStorage.removeItem('lastActivity');
      sessionStorage.clear();
      
      // Show timeout notification
      toast({
        title: "Session Expired",
        description: "You have been logged out due to inactivity for security.",
        variant: "destructive",
      });

      // Sign out and redirect
      await signOut();
      navigate('/auth');
    } catch (error) {
      console.error('Error during timeout logout:', error);
      // Force redirect even if signOut fails
      navigate('/auth');
    }
  }, [signOut, toast, navigate]);

  const timeoutState = useTokenBasedTimeout({
    onTimeout: handleTimeout,
    warningMinutes: 2,
    isRecording,
  });

  const handleLogoutNow = useCallback(async () => {
    try {
      await signOut();
      navigate('/auth');
    } catch (error) {
      console.error('Error during manual logout:', error);
      navigate('/auth');
    }
  }, [signOut, navigate]);

  const contextValue: IdleTimeoutContextType = {
    isRecording,
    setIsRecording: () => {}, // This will be managed by parent components
    resetActivity: timeoutState.checkTokenExpiration,
  };

  return (
    <IdleTimeoutContext.Provider value={contextValue}>
      {children}
      <IdleTimeoutWarning
        isOpen={timeoutState.isWarningVisible}
        remainingSeconds={timeoutState.remainingSeconds}
        onExtend={timeoutState.extendSession}
        onLogout={handleLogoutNow}
      />
    </IdleTimeoutContext.Provider>
  );
};