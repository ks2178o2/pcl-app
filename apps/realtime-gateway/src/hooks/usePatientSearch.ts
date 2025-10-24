import { useState, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import type { Patient } from './usePatients';
import { useOrganizationSecurity } from './useOrganizationSecurity';

export const usePatientSearch = () => {
  const [results, setResults] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { userOrganizationId } = useOrganizationSecurity();

  const search = useCallback(async (input: string): Promise<Patient[]> => {
    console.log('Patient search input:', input);
    
    // Handle comma-separated format "Last, First" or space-separated "First Last"
    let parts: string[];
    if (input.includes(',')) {
      parts = input.split(',').map(p => p.trim()).reverse(); // "Last, First" -> ["First", "Last"]
    } else {
      parts = input.trim().split(/\s+/);
    }
    
    console.log('Search parts:', parts);
    
    if (parts.length < 2) {
      console.log('Not enough parts for search');
      setResults([]);
      return [];
    }
    const [first, last] = parts;
    if (first.length < 3 || last.length < 3) {
      console.log('Parts too short:', { first: first.length, last: last.length });
      setResults([]);
      return [];
    }

    setLoading(true);
    setError(null);

    // Build the base query - search for names containing BOTH parts (AND logic)
    let query: any = (supabase as any)
      .from('patients')
      .select('id, full_name, email, phone, friendly_id, created_at, updated_at')
      .ilike('full_name', `%${first}%`)
      .ilike('full_name', `%${last}%`)
      .limit(20);

    console.log('Executing patient search query with:', { first, last, userOrganizationId });

    // Try org scoping if column exists (fallback gracefully if it doesn't)
    try {
      if (userOrganizationId) {
        query = query.eq('organization_id', userOrganizationId);
      }
      
      const { data, error } = await query;
      console.log('Search query result:', { data, error, count: data?.length });
      
      let finalData = data;
      let finalError = error as any;

      // Fallback: if org filter caused an error (e.g., column missing), retry without it
      if (finalError && userOrganizationId) {
        console.warn('Org-scoped search failed, retrying without org filter...', finalError);
        const { data: dataNoOrg, error: errNoOrg } = await (supabase as any)
          .from('patients')
          .select('id, full_name, email, phone, friendly_id, created_at, updated_at')
          .ilike('full_name', `%${first}%`)
          .ilike('full_name', `%${last}%`)
          .limit(20);
        finalData = dataNoOrg;
        finalError = errNoOrg as any;
        console.log('Retry (no-org) result:', { dataNoOrg, errNoOrg, count: dataNoOrg?.length });
      }
      
      if (finalError) {
        console.error('Search error (after fallback):', finalError);
        setError(finalError.message || 'Search failed');
        setResults([]);
        setLoading(false);
        return [];
      }

      const mapped: Patient[] = (finalData || []).map((p: any) => ({
        id: p.id,
        name: p.full_name,
        email: p.email ?? undefined,
        phone: p.phone ?? undefined,
        friendlyId: p.friendly_id ?? '',
        created_at: p.created_at,
        updated_at: p.updated_at,
      }));
      
      console.log('Mapped results:', mapped);
      setResults(mapped);
      setLoading(false);
      return mapped;
    } catch (e) {
      console.error('Search exception:', e);
      setError(e instanceof Error ? e.message : 'Search failed');
      setResults([]);
      setLoading(false);
      return [];
    }
  }, [userOrganizationId]);

  const clear = useCallback(() => setResults([]), []);

  return { results, loading, error, search, clear };
};
