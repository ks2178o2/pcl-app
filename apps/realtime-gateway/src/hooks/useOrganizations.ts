import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface Organization {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export const useOrganizations = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('organizations')
        .select('*')
        .order('name');

      if (error) {
        console.error('Error fetching organizations:', error);
      } else {
        // Handle migration - add is_active default if not present
        const organizationsWithActive = (data || []).map((org: any) => ({
          ...org,
          is_active: org.is_active ?? true // Default to true if not present
        }));
        setOrganizations(organizationsWithActive);
      }
    } catch (error) {
      console.error('Error fetching organizations:', error);
    } finally {
      setLoading(false);
    }
  };

  return {
    organizations,
    loading,
    refetch: fetchOrganizations
  };
};