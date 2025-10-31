import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface Patient {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  friendlyId: string;
  lastContact?: string;
  created_at: string;
  updated_at: string;
}

interface CreatePatientData {
  name: string;
  email?: string;
  phone?: string;
  center_id?: string;  // Optional center assignment
}

export const usePatients = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchPatients = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const { data, error } = await (supabase as any)
        .from('patients')
        .select('id, full_name, email, phone, friendly_id, created_at, updated_at')
        .order('updated_at', { ascending: false });

      if (error) {
        console.error('Error fetching patients:', error);
        // If table doesn't exist, return empty array instead of throwing
        if (error.code === 'PGRST116' || error.message?.includes('relation "patients" does not exist')) {
          console.warn('Patients table does not exist yet. Please run the database migration.');
          setPatients([]);
          return;
        }
        throw error;
      }

      const mapped: Patient[] = (data || []).map((p: any) => ({
        id: p.id,
        name: p.full_name,
        email: p.email ?? undefined,
        phone: p.phone ?? undefined,
        friendlyId: p.friendly_id ?? '',
        created_at: p.created_at,
        updated_at: p.updated_at,
      }));

      setPatients(mapped);
    } catch (error) {
      console.error('Error fetching patients:', error);
      // Set empty array on error to prevent UI crashes
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  const generateFriendlyId = () => `P${Math.random().toString(36).substr(2, 6).toUpperCase()}`;

  const createPatient = async (patientData: CreatePatientData): Promise<Patient> => {
    if (!user) throw new Error('User not authenticated');

    try {
      const { data, error } = await (supabase as any)
        .from('patients')
        .insert([{
          full_name: patientData.name,
          email: patientData.email ?? null,
          phone: patientData.phone ?? null,
          center_id: patientData.center_id ?? null,  // Set center_id if provided
        }])
        .select('id, full_name, email, phone, friendly_id, created_at, updated_at')
        .single();

      if (error) {
        // If table doesn't exist, provide helpful error message
        if (error.code === 'PGRST116' || error.message?.includes('relation "patients" does not exist')) {
          throw new Error('Patients table does not exist. Please run the database migration first.');
        }
        throw error;
      }

      const newPatient: Patient = {
        id: data.id,
        name: data.full_name,
        email: data.email ?? undefined,
        phone: data.phone ?? undefined,
        friendlyId: data.friendly_id ?? generateFriendlyId(),
        created_at: data.created_at,
        updated_at: data.updated_at,
      };

      setPatients(prev => [newPatient, ...prev]);
      return newPatient;
    } catch (error) {
      console.error('Error creating patient:', error);
      throw error;
    }
  };

  const updatePatient = async (id: string, updates: Partial<CreatePatientData>): Promise<Patient> => {
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await (supabase as any)
      .from('patients')
      .update({
        full_name: updates.name,
        email: updates.email ?? null,
        phone: updates.phone ?? null,
        updated_at: new Date().toISOString(),
      })
      .eq('id', id)
      .select('id, full_name, email, phone, friendly_id, created_at, updated_at')
      .single();

    if (error) throw error;

    const updated: Patient = {
      id: data.id,
      name: data.full_name,
      email: data.email ?? undefined,
      phone: data.phone ?? undefined,
      friendlyId: data.friendly_id ?? '',
      created_at: data.created_at,
      updated_at: data.updated_at,
    };

    setPatients(prev => prev.map(p => (p.id === id ? updated : p)));
    return updated;
  };

  const deletePatient = async (id: string): Promise<void> => {
    if (!user) throw new Error('User not authenticated');

    const { error } = await (supabase as any).from('patients').delete().eq('id', id);
    if (error) throw error;

    setPatients(prev => prev.filter(p => p.id !== id));
  };

  useEffect(() => {
    fetchPatients();
  }, [user]);

  return {
    patients,
    loading,
    createPatient,
    updatePatient,
    deletePatient,
    refetch: fetchPatients,
  };
};