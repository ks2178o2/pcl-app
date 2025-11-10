import { useState, useEffect, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

interface Region {
  id: string;
  organization_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface Center {
  id: string;
  region_id: string;
  name: string;
  address?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  region?: Region;
}

interface UserAssignment {
  id: string;
  user_id: string;
  center_id?: string;
  region_id?: string;
  organization_id?: string;
  center?: Center;
  region?: Region;
}

export const useOrganizationData = () => {
  const [regions, setRegions] = useState<Region[]>([]);
  const [centers, setCenters] = useState<Center[]>([]);
  const [assignments, setAssignments] = useState<UserAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const lastUserIdRef = useRef<string | null>(null);
  const fetchingRef = useRef(false);

  // Extract stable user ID for dependency
  const userId = user?.id;

  useEffect(() => {
    // Skip if no user
    if (!userId) {
      if (regions.length > 0 || centers.length > 0 || assignments.length > 0) {
        setRegions([]);
        setCenters([]);
        setAssignments([]);
      }
      lastUserIdRef.current = null;
      return;
    }

    // Skip if already fetching or if we've already loaded for this user
    if (fetchingRef.current || (lastUserIdRef.current === userId && !loading)) {
      return;
    }

    // Only fetch if user ID changed
    if (lastUserIdRef.current === userId) {
      return;
    }

    fetchOrganizationData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const fetchOrganizationData = async () => {
    if (!user || !userId) return;
    
    fetchingRef.current = true;
    lastUserIdRef.current = userId;
    setLoading(true);
    try {
      console.log('Fetching organization data...');
      
      // Fetch organizations - system admins see all, others see their assigned org
      let organizationsData: any[] = [];
      try {
        console.log('Fetching organizations...');
        const orgsRes = await supabase.from('organizations').select('*').order('name');
        if (orgsRes.error) {
          console.error('Organizations error:', orgsRes.error);
          organizationsData = [];
        } else {
          organizationsData = orgsRes.data || [];
        }
        console.log('Organizations fetched successfully:', organizationsData.length);
      } catch (error) {
        console.error('Organizations fetch failed:', error);
        organizationsData = [];
      }
      
      // Fetch regions with organization_id (after migration) or adapt network_id (before migration)
      let regionsData: Region[] = [];
      try {
        console.log('Fetching regions...');
        const regionsRes = await supabase.from('regions').select('*').order('name');
        if (regionsRes.error) {
          console.error('Regions error:', regionsRes.error);
          regionsData = [];
        } else {
          // Map the data to match our interface (handle both pre and post migration)
          regionsData = (regionsRes.data || []).map((region: any) => ({
            ...region,
            organization_id: region.organization_id || '00000000-0000-0000-0000-000000000001', // Default org for pre-migration data
            is_active: region.is_active ?? true // Default to true if not present
          }));
        }
        console.log('Regions fetched successfully:', regionsData.length);
      } catch (error) {
        console.error('Regions fetch failed:', error);
        regionsData = [];
      }

      // Fetch centers with regions
      let centersData: Center[] = [];
      try {
        console.log('Fetching centers...');
        const centersRes = await supabase
          .from('centers')
          .select(`
            *,
            region:regions(*)
          `)
          .order('name');
        if (centersRes.error) {
          console.error('Centers error:', centersRes.error);
          centersData = [];
        } else {
          // Map centers and their regions to match our interface
          centersData = (centersRes.data || []).map((center: any) => ({
            ...center,
            is_active: center.is_active ?? true, // Default to true if not present
            region: center.region ? {
              ...center.region,
              organization_id: center.region.organization_id || '00000000-0000-0000-0000-000000000001',
              is_active: center.region.is_active ?? true
            } : undefined
          }));
        }
        console.log('Centers fetched successfully:', centersData.length);
      } catch (error) {
        console.error('Centers fetch failed:', error);
        centersData = [];
      }

      // Fetch user assignments - system admins see all, others see their scope
      let assignmentsData: UserAssignment[] = [];
      try {
        console.log('Fetching user assignments...');
        const assignmentsRes = await supabase
          .from('user_assignments')
          .select(`
            *,
            center:centers(*),
            region:regions(*)
          `)
          .order('created_at', { ascending: false });
        
        if (assignmentsRes.error) {
          console.error('Assignments error:', assignmentsRes.error);
          assignmentsData = [];
        } else {
          // Map assignments to match our interface  
          assignmentsData = (assignmentsRes.data || []).map((assignment: any) => ({
            ...assignment,
            center: assignment.center ? {
              ...assignment.center,
              is_active: assignment.center.is_active ?? true
            } : undefined,
            region: assignment.region ? {
              ...assignment.region,
              organization_id: assignment.region.organization_id || '00000000-0000-0000-0000-000000000001',
              is_active: assignment.region.is_active ?? true
            } : undefined
          }));
        }
        console.log('Assignments fetched successfully:', assignmentsData.length);
      } catch (error) {
        console.error('Assignments fetch failed:', error);
        assignmentsData = [];
      }

      setRegions(regionsData);
      setCenters(centersData);
      setAssignments(assignmentsData);
      
    } catch (error) {
      console.error('Error fetching organization data:', error);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
    }
  };

  return {
    regions,
    centers,
    assignments,
    loading,
    refetch: fetchOrganizationData
  };
};