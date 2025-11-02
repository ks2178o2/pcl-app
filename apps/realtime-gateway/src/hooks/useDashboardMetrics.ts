import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface DashboardMetrics {
  newLeadsThisWeek: number;
  newLeadsChange: number;
  consultationsBooked: number;
  consultationsChange: number;
  dealsClosedThisMonth: number;
  dealsClosedChange: number;
  revenueGenerated: number;
  revenueChange: number;
}

/**
 * Custom hook to fetch and calculate dashboard metrics
 * Maps existing data to sales metrics:
 * - New Leads = New appointments this week
 * - Consultations Booked = Appointments scheduled
 * - Deals Closed = Call records this month
 * - Revenue = Mock revenue based on calls (placeholder)
 */
export const useDashboardMetrics = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    newLeadsThisWeek: 0,
    newLeadsChange: 0,
    consultationsBooked: 0,
    consultationsChange: 0,
    dealsClosedThisMonth: 0,
    dealsClosedChange: 0,
    revenueGenerated: 0,
    revenueChange: 0,
  });
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchMetrics();
    }
  }, [user]);

  const fetchMetrics = async () => {
    if (!user) return;

    setLoading(true);
    try {
      // Calculate date ranges
      const now = new Date();
      const oneWeekAgo = new Date(now);
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      
      const twoWeeksAgo = new Date(now);
      twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
      
      const oneMonthAgo = new Date(now);
      oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
      
      const twoMonthsAgo = new Date(now);
      twoMonthsAgo.setMonth(twoMonthsAgo.getMonth() - 2);

      // Fetch new patients (leads) using patients table if available, otherwise appointments
      const { data: patientsThisWeek, error: patientsError } = await (supabase as any)
        .from('patients')
        .select('created_at')
        .gte('created_at', oneWeekAgo.toISOString())
        .order('created_at', { ascending: false });

      const { data: patientsLastWeek } = await (supabase as any)
        .from('patients')
        .select('created_at')
        .gte('created_at', twoWeeksAgo.toISOString())
        .lt('created_at', oneWeekAgo.toISOString())
        .order('created_at', { ascending: false });

      // Also fetch appointments for consultations
      const { data: appointmentsThisWeek, error: appsError } = await supabase
        .from('appointments')
        .select('created_at')
        .eq('user_id', user.id)
        .gte('created_at', oneWeekAgo.toISOString());

      const { data: appointmentsLastWeek } = await supabase
        .from('appointments')
        .select('created_at')
        .eq('user_id', user.id)
        .gte('created_at', twoWeeksAgo.toISOString())
        .lt('created_at', oneWeekAgo.toISOString());

      // Fetch calls (deals closed)
      const { data: callsThisMonth, error: callsError } = await supabase
        .from('call_records')
        .select('created_at, duration_seconds')
        .eq('user_id', user.id)
        .gte('created_at', oneMonthAgo.toISOString())
        .eq('is_active', true);

      const { data: callsLastMonth } = await supabase
        .from('call_records')
        .select('created_at, duration_seconds')
        .eq('user_id', user.id)
        .gte('created_at', twoMonthsAgo.toISOString())
        .lt('created_at', oneMonthAgo.toISOString())
        .eq('is_active', true);

      if (callsError || (appsError && patientsError)) {
        console.error('Error fetching metrics:', appsError || callsError || patientsError);
        setLoading(false);
        return;
      }

      // Calculate metrics - use patients as leads if available, otherwise appointments
      const newLeadsThisWeek = (patientsThisWeek?.length || 0) + (appointmentsThisWeek?.length || 0);
      const newLeadsLastWeek = (patientsLastWeek?.length || 0) + (appointmentsLastWeek?.length || 0);
      const newLeadsChange = newLeadsLastWeek > 0 
        ? Math.round(((newLeadsThisWeek - newLeadsLastWeek) / newLeadsLastWeek) * 100)
        : 0;

      // Consultations = Total appointments (all time)
      const { data: totalAppointments } = await supabase
        .from('appointments')
        .select('created_at')
        .eq('user_id', user.id);

      const consultationsBooked = totalAppointments?.length || 0;
      
      // Get previous week's appointments for comparison
      const { data: appointmentsTwoWeeksAgo } = await supabase
        .from('appointments')
        .select('created_at')
        .eq('user_id', user.id)
        .lt('created_at', twoWeeksAgo.toISOString());

      const consultationsLastPeriod = appointmentsTwoWeeksAgo?.length || 0;
      const consultationsChange = consultationsLastPeriod > 0
        ? Math.round(((consultationsBooked - consultationsLastPeriod) / consultationsLastPeriod) * 100)
        : 0;

      // Deals closed = Call records this month
      const dealsClosedThisMonth = callsThisMonth?.length || 0;
      const dealsClosedLastMonth = callsLastMonth?.length || 0;
      const dealsClosedChange = dealsClosedLastMonth > 0
        ? Math.round(((dealsClosedThisMonth - dealsClosedLastMonth) / dealsClosedLastMonth) * 100)
        : 0;

      // Revenue = Mock calculation based on calls (placeholder for real revenue tracking)
      // Estimate $500 per call as average revenue
      const revenueGenerated = dealsClosedThisMonth * 500;
      const revenueLastMonth = dealsClosedLastMonth * 500;
      const revenueChange = revenueLastMonth > 0
        ? Math.round(((revenueGenerated - revenueLastMonth) / revenueLastMonth) * 100)
        : 0;

      setMetrics({
        newLeadsThisWeek,
        newLeadsChange,
        consultationsBooked,
        consultationsChange,
        dealsClosedThisMonth,
        dealsClosedChange,
        revenueGenerated,
        revenueChange,
      });
    } catch (error) {
      console.error('Error calculating metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  return {
    metrics,
    loading,
    refetch: fetchMetrics,
  };
};

