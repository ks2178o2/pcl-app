import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { useProfile } from './useProfile';

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
  const { profile } = useProfile();

  useEffect(() => {
    if (user && profile) {
      fetchMetrics();
    }
  }, [user, profile]);

  const fetchMetrics = async () => {
    if (!user || !profile) return;

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
      let patientsThisWeekQuery = (supabase as any)
        .from('patients')
        .select('created_at')
        .gte('created_at', oneWeekAgo.toISOString())
        .order('created_at', { ascending: false });
      
      let patientsLastWeekQuery = (supabase as any)
        .from('patients')
        .select('created_at')
        .gte('created_at', twoWeeksAgo.toISOString())
        .lt('created_at', oneWeekAgo.toISOString())
        .order('created_at', { ascending: false });
      
      // Only add organization filter if we have a valid organization_id
      if (profile?.organization_id) {
        patientsThisWeekQuery = patientsThisWeekQuery.eq('organization_id', profile.organization_id);
        patientsLastWeekQuery = patientsLastWeekQuery.eq('organization_id', profile.organization_id);
      }
      
      const { data: patientsThisWeek, error: patientsError } = await patientsThisWeekQuery;
      const { data: patientsLastWeek } = await patientsLastWeekQuery;

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
        .select('start_time, duration_seconds')
        .eq('user_id', user.id)
        .gte('start_time', oneMonthAgo.toISOString())
        .eq('recording_complete', true);

      const { data: callsLastMonth } = await supabase
        .from('call_records')
        .select('start_time, duration_seconds')
        .eq('user_id', user.id)
        .gte('start_time', twoMonthsAgo.toISOString())
        .lt('start_time', oneMonthAgo.toISOString())
        .eq('recording_complete', true);

      if (callsError || (appsError && patientsError)) {
        console.error('Error fetching metrics:', appsError || callsError || patientsError);
        setLoading(false);
        return;
      }

      // Calculate metrics - use patients as leads if available, otherwise appointments
      const newLeadsThisWeek = (patientsThisWeek?.length || 0) + (appointmentsThisWeek?.length || 0);
      const newLeadsLastWeek = (patientsLastWeek?.length || 0) + (appointmentsLastWeek?.length || 0);
      
      // Calculate actual percentage change (truthful from database)
      // Only show percentage when we have both periods for comparison
      const newLeadsChange = newLeadsLastWeek > 0 
        ? Math.round(((newLeadsThisWeek - newLeadsLastWeek) / newLeadsLastWeek) * 100)
        : 0; // No baseline to compare - show 0% (no change calculated)

      // Consultations = Active pipeline (recent appointments + upcoming)
      const { data: totalAppointments } = await supabase
        .from('appointments')
        .select('created_at, appointment_date')
        .eq('user_id', user.id);

      const consultationsBooked = totalAppointments?.length || 0;
      
      // Show growth based on recent momentum (last 30 days vs previous 30 days)
      const thirtyDaysAgo = new Date(now);
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      const sixtyDaysAgo = new Date(now);
      sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60);
      
      const { data: appointmentsLast30Days } = await supabase
        .from('appointments')
        .select('created_at')
        .eq('user_id', user.id)
        .gte('created_at', thirtyDaysAgo.toISOString());

      const { data: appointmentsPrevious30Days } = await supabase
        .from('appointments')
        .select('created_at')
        .eq('user_id', user.id)
        .gte('created_at', sixtyDaysAgo.toISOString())
        .lt('created_at', thirtyDaysAgo.toISOString());

      const recent30Days = appointmentsLast30Days?.length || 0;
      const previous30Days = appointmentsPrevious30Days?.length || 0;
      
      // Calculate actual percentage change (truthful from database)
      // Only show percentage when we have both periods for comparison
      const consultationsChange = previous30Days > 0
        ? Math.round(((recent30Days - previous30Days) / previous30Days) * 100)
        : 0; // No baseline to compare - show 0% (no change calculated)

      // Deals closed = Call records this month
      const dealsClosedThisMonth = callsThisMonth?.length || 0;
      const dealsClosedLastMonth = callsLastMonth?.length || 0;
      
      // Calculate actual percentage change (truthful from database)
      // Only show percentage when we have both periods for comparison
      const dealsClosedChange = dealsClosedLastMonth > 0
        ? Math.round(((dealsClosedThisMonth - dealsClosedLastMonth) / dealsClosedLastMonth) * 100)
        : 0; // No baseline to compare - show 0% (no change calculated)

      // Revenue = Mock calculation based on calls (placeholder for real revenue tracking)
      // Use $100 per call as average revenue, multiplied by 100
      const revenueGenerated = dealsClosedThisMonth * 100 * 100;
      const revenueLastMonth = dealsClosedLastMonth * 100 * 100;
      
      // Calculate actual percentage change (truthful from database)
      // Only show percentage when we have both periods for comparison
      const revenueChange = revenueLastMonth > 0
        ? Math.round(((revenueGenerated - revenueLastMonth) / revenueLastMonth) * 100)
        : 0; // No baseline to compare - show 0% (no change calculated)

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

