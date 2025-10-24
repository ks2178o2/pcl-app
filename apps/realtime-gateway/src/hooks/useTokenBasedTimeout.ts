import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { useToast } from './use-toast';
import { supabase } from '@/integrations/supabase/client';

interface TokenTimeoutState {
  isWarningVisible: boolean;
  remainingSeconds: number;
  lastActivity: Date;
}

interface UseTokenTimeoutProps {
  onTimeout: () => Promise<void>;
  warningMinutes?: number;
  isRecording?: boolean;
}

export const useTokenBasedTimeout = ({ 
  onTimeout, 
  warningMinutes = 2,
  isRecording = false 
}: UseTokenTimeoutProps) => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [state, setState] = useState<TokenTimeoutState>({
    isWarningVisible: false,
    remainingSeconds: 0,
    lastActivity: new Date(),
  });

  const warningTimeoutRef = useRef<NodeJS.Timeout>();
  const checkIntervalRef = useRef<NodeJS.Timeout>();
  const activityTimeoutRef = useRef<NodeJS.Timeout>();
  const countdownIntervalRef = useRef<NodeJS.Timeout>();

  // Check token expiration and show warning
  const checkTokenExpiration = useCallback(async () => {
    if (!user || isRecording) return;

    // Get current session from Supabase
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error || !session?.expires_at) return;

    const expiresAt = new Date(session.expires_at * 1000);
    const now = new Date();
    const timeUntilExpiry = expiresAt.getTime() - now.getTime();
    const warningTime = warningMinutes * 60 * 1000;

    // If token expires soon, show warning
    if (timeUntilExpiry <= warningTime && timeUntilExpiry > 0) {
      const remainingSeconds = Math.floor(timeUntilExpiry / 1000);
      setState(prev => ({
        ...prev,
        isWarningVisible: true,
        remainingSeconds
      }));

      // Clear any existing countdown
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }

      // Start countdown
      countdownIntervalRef.current = setInterval(() => {
        setState(prev => {
          const newRemaining = prev.remainingSeconds - 1;
          if (newRemaining <= 0) {
            if (countdownIntervalRef.current) {
              clearInterval(countdownIntervalRef.current);
            }
            onTimeout();
            return prev;
          }
          return { ...prev, remainingSeconds: newRemaining };
        });
      }, 1000);
    }
    // If token already expired
    else if (timeUntilExpiry <= 0) {
      onTimeout();
    }
  }, [user, isRecording, warningMinutes, onTimeout]);

  // Activity handler with debouncing
  const handleActivity = useCallback(() => {
    if (isRecording) return;

    if (activityTimeoutRef.current) {
      clearTimeout(activityTimeoutRef.current);
    }

    // Debounce activity tracking (reduce from multiple events to one)
    activityTimeoutRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, lastActivity: new Date() }));
    }, 1000);
  }, [isRecording]);

  // Extend session by refreshing token
  const extendSession = useCallback(async () => {
    try {
      // Clear countdown when extending
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }

      const { data, error } = await supabase.auth.refreshSession();
      
      if (error) {
        console.error('Failed to refresh session:', error);
        toast({
          title: "Session Refresh Failed",
          description: "Please log in again.",
          variant: "destructive",
        });
        onTimeout();
        return;
      }

      // After successful refresh, check for stale recording state
      try {
        const { ChunkedRecordingManager } = await import('@/services/chunkedRecordingService');
        const existingState = ChunkedRecordingManager.loadState();
        
        if (existingState) {
          const validation = ChunkedRecordingManager.validateState(existingState);
          if (!validation.valid) {
            console.log('🧹 Clearing stale recording state after session refresh:', validation.reason);
            ChunkedRecordingManager.clearState();
            await ChunkedRecordingManager.clearAllSlices();
          }
        }
      } catch (e) {
        console.warn('Could not validate recording state:', e);
      }

      setState(prev => ({ 
        ...prev, 
        isWarningVisible: false, 
        remainingSeconds: 0,
        lastActivity: new Date()
      }));

      toast({
        title: "Session Extended",
        description: "Your session has been refreshed successfully.",
      });
    } catch (error) {
      console.error('Error refreshing session:', error);
      onTimeout();
    }
  }, [toast, onTimeout]);

  // Set up periodic token checking
  useEffect(() => {
    if (!user) return;

    // Check every 30 seconds instead of continuous monitoring
    checkIntervalRef.current = setInterval(checkTokenExpiration, 30000);
    
    // Initial check
    checkTokenExpiration();

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [user, checkTokenExpiration]);

  // Set up activity listeners (only when user is present)
  useEffect(() => {
    if (!user) return;

    const events = ['mousedown', 'keypress', 'click', 'scroll'];
    
    events.forEach(event => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
      
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
      if (activityTimeoutRef.current) clearTimeout(activityTimeoutRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, [user, handleActivity]);

  return {
    ...state,
    extendSession,
    checkTokenExpiration,
  };
};