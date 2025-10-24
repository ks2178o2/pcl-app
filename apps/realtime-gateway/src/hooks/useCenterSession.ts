import { useState, useEffect } from 'react';
import { useAuth } from './useAuth';
import { useOrganizationData } from './useOrganizationData';
import { useProfile } from './useProfile';

interface CenterSessionState {
  activeCenter: string | null;
  availableCenters: Array<{ id: string; name: string; region?: { name: string } }>;
  loading: boolean;
  error: string | null;
  hasShownInitialSelection: boolean;
}

export const useCenterSession = () => {
  const { user } = useAuth();
  const { profile } = useProfile();
  const { centers, assignments, loading: orgLoading } = useOrganizationData();
  const [sessionState, setSessionState] = useState<CenterSessionState>({
    activeCenter: null,
    availableCenters: [],
    loading: true,
    error: null,
    hasShownInitialSelection: false,
  });

  useEffect(() => {
    if (user && profile && !orgLoading && centers.length > 0) {
      initializeCenterSession();
    }
  }, [user, profile, centers, assignments, orgLoading]);

  const initializeCenterSession = () => {
    try {
      console.log('Initializing center session for user:', user?.id);
      console.log('Available centers:', centers);
      console.log('User assignments:', assignments);
      
      // Get user's assigned centers
      const userAssignments = assignments.filter(assignment => assignment.user_id === user?.id);
      console.log('User assignments for this user:', userAssignments);
      
      let availableCenters;
      
      if (userAssignments.length === 0) {
        // No assignments = access to all centers in user's organization
        console.log('No assignments found - granting access to all centers in organization');
        console.log('User organization_id:', profile?.organization_id);
        availableCenters = centers.filter(center => 
          center.region?.organization_id === profile?.organization_id
        );
        console.log('Available centers (all in org):', availableCenters);
      } else {
        // Has assignments = restricted to assigned centers only
        console.log('Assignments found - restricting to assigned centers');
        const assignedCenterIds = userAssignments.map(assignment => assignment.center_id).filter(Boolean);
        console.log('Assigned center IDs:', assignedCenterIds);
        
        availableCenters = centers.filter(center => 
          assignedCenterIds.includes(center.id)
        );
        console.log('Available centers (assigned only):', availableCenters);
      }

      // Check if there's a stored active center and if user has made initial selection
      const storedActiveCenter = localStorage.getItem('activeCenter');
      const hasShownInitialSelection = localStorage.getItem('hasShownInitialSelection') === 'true';
      let activeCenter: string | null = null;

      if (availableCenters.length === 0) {
        setSessionState({
          activeCenter: null,
          availableCenters: [],
          loading: false,
          error: 'No centers available. Please contact your administrator.',
          hasShownInitialSelection: false,
        });
        return;
      }

      if (availableCenters.length === 1) {
        // Auto-select if only one center
        activeCenter = availableCenters[0].id;
      } else if (hasShownInitialSelection && storedActiveCenter && availableCenters.some(c => c.id === storedActiveCenter)) {
        // Use stored center if user has already made initial selection and it's still valid
        activeCenter = storedActiveCenter;
      }
      // If multiple centers and no initial selection made, leave null for modal selection

      setSessionState({
        activeCenter,
        availableCenters,
        loading: false,
        error: null,
        hasShownInitialSelection,
      });

      // Store the active center and mark initial selection as completed
      if (activeCenter) {
        localStorage.setItem('activeCenter', activeCenter);
        if (availableCenters.length === 1) {
          localStorage.setItem('hasShownInitialSelection', 'true');
        }
      }
    } catch (error) {
      console.error('Error initializing center session:', error);
      setSessionState({
        activeCenter: null,
        availableCenters: [],
        loading: false,
        error: 'Failed to load center information.',
        hasShownInitialSelection: false,
      });
    }
  };

  const setActiveCenter = (centerId: string) => {
    const isValidCenter = sessionState.availableCenters.some(c => c.id === centerId);
    if (!isValidCenter) {
      console.error('Invalid center selection:', centerId);
      return;
    }

    setSessionState(prev => ({
      ...prev,
      activeCenter: centerId,
      hasShownInitialSelection: true,
    }));

    localStorage.setItem('activeCenter', centerId);
    localStorage.setItem('hasShownInitialSelection', 'true');
  };

  const getActiveCenterInfo = () => {
    if (!sessionState.activeCenter) return null;
    return sessionState.availableCenters.find(c => c.id === sessionState.activeCenter) || null;
  };

  const clearSession = () => {
    localStorage.removeItem('activeCenter');
    localStorage.removeItem('hasShownInitialSelection');
    setSessionState(prev => ({
      ...prev,
      activeCenter: null,
      hasShownInitialSelection: false,
    }));
  };

  return {
    activeCenter: sessionState.activeCenter,
    availableCenters: sessionState.availableCenters,
    loading: sessionState.loading,
    error: sessionState.error,
    setActiveCenter,
    getActiveCenterInfo,
    clearSession,
    needsCenterSelection: sessionState.availableCenters.length > 1 && !sessionState.activeCenter && !sessionState.hasShownInitialSelection,
  };
};