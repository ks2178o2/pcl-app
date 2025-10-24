import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from './useAuth';
import { useToast } from './use-toast';

export interface IdleTimeoutConfig {
  role: string;
  timeout_minutes: number;
  warning_minutes: number;
  enabled: boolean;
}

export interface IdleTimeoutState {
  isWarningVisible: boolean;
  remainingSeconds: number;
  isRecording: boolean;
  lastActivity: Date;
  timeoutConfig: IdleTimeoutConfig | null;
}

interface UseIdleTimeoutProps {
  onTimeout: () => Promise<void>;
  isRecording?: boolean;
}

export const useIdleTimeout = ({ onTimeout, isRecording = false }: UseIdleTimeoutProps) => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [state, setState] = useState<IdleTimeoutState>({
    isWarningVisible: false,
    remainingSeconds: 0,
    isRecording: false,
    lastActivity: new Date(),
    timeoutConfig: null,
  });

  const timeoutRef = useRef<NodeJS.Timeout>();
  const warningTimeoutRef = useRef<NodeJS.Timeout>();
  const activityTimeoutRef = useRef<NodeJS.Timeout>();
  const lastActivityRef = useRef<Date>(new Date());

  // Get default timeout configuration based on user type
  const getDefaultTimeoutConfig = useCallback((): IdleTimeoutConfig => {
    // Default configuration for PHI compliance
    return {
      role: 'default',
      timeout_minutes: 15, // 15 minutes default for PHI security
      warning_minutes: 2,  // 2 minute warning
      enabled: true,
    };
  }, []);

  // Use refs to avoid circular dependencies
  const timeoutConfigRef = useRef<IdleTimeoutConfig | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout>();

  // Reset activity timer - removed from useCallback to break circular dependency
  const resetActivity = () => {
    if (isRecording) return; // Don't reset during recording

    const now = new Date();
    lastActivityRef.current = now;
    setState(prev => ({ ...prev, lastActivity: now }));

    // Clear existing timeouts
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    if (countdownIntervalRef.current) clearTimeout(countdownIntervalRef.current);

    const config = timeoutConfigRef.current;
    if (!config || !config.enabled) return;

    const timeoutMs = config.timeout_minutes * 60 * 1000;
    const warningMs = (config.timeout_minutes - config.warning_minutes) * 60 * 1000;

    // Set warning timeout
    warningTimeoutRef.current = setTimeout(() => {
      setState(prev => ({ 
        ...prev, 
        isWarningVisible: true,
        remainingSeconds: config.warning_minutes * 60
      }));

      // Start countdown with reduced frequency for better performance
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
    }, warningMs);

    // Set actual timeout
    timeoutRef.current = setTimeout(() => {
      onTimeout();
    }, timeoutMs);
  };

  // Activity event handlers with increased debounce for better performance
  const handleActivity = useCallback(() => {
    if (activityTimeoutRef.current) {
      clearTimeout(activityTimeoutRef.current);
    }
    
    // Increased debounce from 1000ms to 2000ms to reduce CPU usage
    activityTimeoutRef.current = setTimeout(() => {
      resetActivity();
    }, 2000);
  }, []); // Empty dependency array to prevent circular references

  // Extend session (when user clicks "Stay Logged In")
  const extendSession = useCallback(() => {
    setState(prev => ({ ...prev, isWarningVisible: false, remainingSeconds: 0 }));
    resetActivity();
    toast({
      title: "Session Extended",
      description: "Your session has been extended for security.",
    });
  }, [toast]);

  // Update recording state
  useEffect(() => {
    setState(prev => ({ ...prev, isRecording }));
    
    if (isRecording) {
      // Pause timeouts during recording
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    } else {
      // Resume timeouts when recording stops
      resetActivity();
    }
  }, [isRecording]); // Removed resetActivity from dependencies

  // Load timeout configuration
  useEffect(() => {
    if (user) {
      const config = getDefaultTimeoutConfig();
      timeoutConfigRef.current = config;
      setState(prev => ({ ...prev, timeoutConfig: config }));
    }
  }, [user, getDefaultTimeoutConfig]);

  // Set up activity listeners
  useEffect(() => {
    const config = timeoutConfigRef.current;
    if (!config?.enabled) return;

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    // Initialize activity timer only once
    const now = new Date();
    lastActivityRef.current = now;
    setState(prev => ({ ...prev, lastActivity: now }));

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
      
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
      if (activityTimeoutRef.current) clearTimeout(activityTimeoutRef.current);
      if (countdownIntervalRef.current) clearTimeout(countdownIntervalRef.current);
    };
  }, [handleActivity]); // Removed resetActivity and state.timeoutConfig from dependencies

  return {
    ...state,
    extendSession,
    resetActivity,
  };
};