import React, { useState, useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { SalesDashboardSidebar } from '@/components/SalesDashboardSidebar';
import { 
  Plus,
  Search,
  TrendingUp,
  TrendingDown,
  MoreVertical,
  Calendar as CalendarIcon,
  Phone,
  UserPlus,
  Mail,
  CheckCircle2,
  Pencil
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useAppointments } from '@/hooks/useAppointments';
import { useDashboardMetrics } from '@/hooks/useDashboardMetrics';
import { supabase } from '@/integrations/supabase/client';
import { cn } from '@/lib/utils';

interface RecentActivity {
  message: string;
  timestamp: string;
  icon: React.ReactNode;
  sortKey?: number; // Internal use for sorting
}

const SalesDashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut } = useAuth();
  const { profile } = useProfile();
  const { calls, loadCalls } = useCallRecords();
  const { appointments: dbAppointments, loading: appointmentsLoading, loadAppointments } = useAppointments();
  const { metrics, loading: metricsLoading } = useDashboardMetrics();
  
  // Simple, bulletproof approach: track last pathname and always reload when it matches
  const lastPathnameRef = useRef<string>('');
  
  // BULLETPROOF: Always reload when pathname is /dashboard
  // Use useLayoutEffect to run synchronously before paint
  useLayoutEffect(() => {
    if (!user || !profile) return;
    
    // Only proceed if we're actually on the dashboard route
    if (location.pathname !== '/dashboard') {
      lastPathnameRef.current = location.pathname;
      return;
    }
    
    const pathnameChanged = lastPathnameRef.current !== '/dashboard';
    const isEmpty = dbAppointments.length === 0 && calls.length === 0;
    
    // ALWAYS reload if pathname changed TO /dashboard OR data is empty
    if (pathnameChanged || isEmpty) {
      lastPathnameRef.current = '/dashboard';
      // Don't load here - let the useEffect below handle it when user/profile are ready
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, profile, location.pathname, dbAppointments.length, calls.length]);
  
  // Reload when user/profile are ready AND we're on dashboard route
  // This ensures hooks have the latest user/profile before calling load functions
  useEffect(() => {
    if (!user || !profile || location.pathname !== '/dashboard') return;
    
    const pathnameChanged = lastPathnameRef.current !== '/dashboard';
    const isEmpty = dbAppointments.length === 0 && calls.length === 0;
    
    // Reload if pathname changed to dashboard OR data is empty
    if (pathnameChanged || isEmpty) {
      lastPathnameRef.current = '/dashboard';
      
      // Wait a bit to ensure hooks have updated their refs with the latest user
      const timer = setTimeout(() => {
        loadCalls(10);
        loadAppointments(new Date());
      }, 100);
      
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, profile, location.pathname, dbAppointments.length, calls.length]);
  
  // Also reload when component becomes visible (handles tab switching)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && user && profile && location.pathname === '/dashboard') {
        // Tab became visible - reload data
        loadCalls(10);
        loadAppointments(new Date());
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, profile, location.pathname]);

  // Generate activity feed from calls and appointments (memoized)
  const activities = useMemo(() => {
    const activitiesList: RecentActivity[] = [];
    
    // Add recent calls as activities
    if (calls && calls.length > 0) {
      calls.forEach((call) => {
        if (!call.timestamp) return; // Skip if no timestamp
        
        const timeDiff = Date.now() - call.timestamp.getTime();
        const minutesAgo = Math.floor(timeDiff / 60000);
        const hoursAgo = Math.floor(minutesAgo / 60);
        
        let timestamp: string;
        if (minutesAgo < 60) {
          timestamp = `${minutesAgo} ${minutesAgo === 1 ? 'min' : 'mins'} ago`;
        } else if (hoursAgo < 24) {
          timestamp = `${hoursAgo} ${hoursAgo === 1 ? 'hour' : 'hours'} ago`;
        } else {
          timestamp = `${Math.floor(hoursAgo / 24)} days ago`;
        }

        activitiesList.push({
          message: `Call logged with ${call.patientName}. Duration: ${Math.floor(call.duration / 60)}m ${call.duration % 60}s.`,
          timestamp,
          icon: <Phone className="h-4 w-4" />,
          sortKey: call.timestamp.getTime()
        });
      });
    }

    // Add recent appointments as activities (show all appointments, not just today's)
    // We need to load all recent appointments, not just today's
    // For now, we'll use today's appointments but show them in Recent Activity too
    if (dbAppointments && dbAppointments.length > 0) {
      dbAppointments.forEach((apt) => {
        const aptDate = new Date(apt.created_at || apt.appointment_date);
        const timeDiff = Date.now() - aptDate.getTime();
        const minutesAgo = Math.floor(timeDiff / 60000);
        const hoursAgo = Math.floor(minutesAgo / 60);
        
        let timestamp: string;
        if (minutesAgo < 60) {
          timestamp = `${minutesAgo} ${minutesAgo === 1 ? 'min' : 'mins'} ago`;
        } else if (hoursAgo < 24) {
          timestamp = `${hoursAgo} ${hoursAgo === 1 ? 'hour' : 'hours'} ago`;
        } else {
          timestamp = `${Math.floor(hoursAgo / 24)} days ago`;
        }

        activitiesList.push({
          message: `Appointment scheduled: ${apt.customer_name}`,
          timestamp,
          icon: <CalendarIcon className="h-4 w-4" />,
          sortKey: aptDate.getTime()
        });
      });
    }

    // Sort by timestamp (most recent first) and limit to 5 most recent
    return activitiesList
      .sort((a, b) => (b.sortKey || 0) - (a.sortKey || 0))
      .slice(0, 5)
      .map(({ sortKey, ...activity }) => activity); // Remove sortKey before returning
  }, [calls, dbAppointments]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Debug loading state
  if (!user || !profile) {
    console.log('⏳ SalesDashboard: Waiting for user or profile - user:', !!user, 'profile:', !!profile);
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg">Loading...</div>
          <div className="text-sm text-gray-500 mt-2">Waiting for authentication...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 flex">
      {/* Left Sidebar */}
      <SalesDashboardSidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-gray-50/50 to-white">
        {/* Top Header Bar */}
        <div className="h-16 bg-white/80 backdrop-blur-sm border-b border-border/50 flex items-center justify-between px-6 shadow-sm">
          <div className="flex-1 max-w-lg relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Search leads, tasks..." 
              className="w-full pl-10 bg-white/90 border-border/50 focus:bg-white focus:border-primary/30 transition-colors"
            />
          </div>
          <Button className="bg-primary hover:bg-primary/90 text-white shadow-sm hover:shadow-md transition-all">
            <Plus className="h-4 w-4 mr-2" />
            New Lead
          </Button>
        </div>

        {/* Dashboard Content */}
        <ScrollArea className="flex-1">
          <div className="p-8 max-w-7xl mx-auto">
            {/* Greeting */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground mb-2">
                {getGreeting()}, {profile.salesperson_name || 'Alex'}
              </h1>
              <p className="text-muted-foreground text-base">
                Here's your sales overview for today.
              </p>
            </div>

            {/* KPI Cards - Hidden for now */}
            {false && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <MetricCard
                  title="New Leads This Week"
                  value={metrics.newLeadsThisWeek}
                  change={metrics.newLeadsChange}
                  isPositive={metrics.newLeadsChange >= 0}
                  icon={<TrendingUp className="h-4 w-4" />}
                />
                <MetricCard
                  title="Consultations Booked"
                  value={metrics.consultationsBooked}
                  change={metrics.consultationsChange}
                  isPositive={metrics.consultationsChange >= 0}
                  icon={<TrendingUp className="h-4 w-4" />}
                />
                <MetricCard
                  title="Deals Closed (Month)"
                  value={metrics.dealsClosedThisMonth}
                  change={metrics.dealsClosedChange}
                  isPositive={metrics.dealsClosedChange >= 0}
                  icon={<TrendingUp className="h-4 w-4" />}
                />
                <MetricCard
                  title="Revenue Generated"
                  value={formatCurrency(metrics.revenueGenerated)}
                  change={metrics.revenueChange}
                  isPositive={metrics.revenueChange >= 0}
                  icon={<TrendingUp className="h-4 w-4" />}
                  editable
                />
              </div>
            )}

            {/* Today's Focus and Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Today's Focus */}
              <Card className="bg-white border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-foreground">Today's Focus</CardTitle>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-primary hover:text-primary/80 hover:bg-accent/50 transition-colors"
                      onClick={() => navigate('/schedule')}
                    >
                      View All
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Scheduled Appointments */}
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-4 uppercase tracking-wide">Scheduled Appointments</h4>
                    <div className="space-y-3">
                      {appointmentsLoading ? (
                        <div className="text-center py-8">
                          <CalendarIcon className="h-12 w-12 text-muted-foreground/30 mx-auto mb-3 animate-pulse" />
                          <p className="text-sm text-muted-foreground">Loading appointments...</p>
                        </div>
                      ) : (() => {
                        // Filter appointments to only show today's appointments
                        const today = new Date();
                        const todayStr = today.toDateString();
                        const userTimezone = profile?.timezone || 'America/Los_Angeles';
                        
                        const todayAppointments = (dbAppointments || []).filter((apt) => {
                          const aptDate = new Date(apt.appointment_date);
                          // Convert to user's timezone for comparison
                          const aptDateInUserTZ = new Date(aptDate.toLocaleString('en-US', { timeZone: userTimezone }));
                          const todayInUserTZ = new Date(today.toLocaleString('en-US', { timeZone: userTimezone }));
                          return aptDateInUserTZ.toDateString() === todayInUserTZ.toDateString();
                        }).sort((a, b) => {
                          // Sort by appointment time
                          return new Date(a.appointment_date).getTime() - new Date(b.appointment_date).getTime();
                        });

                        return todayAppointments.length > 0 ? (
                          todayAppointments.map((apt, idx) => {
                            const aptDate = new Date(apt.appointment_date);
                            // Use user's timezone if available, otherwise default to America/Los_Angeles for business hours
                            // This ensures appointments created in Pacific time display correctly
                            const displayTimezone = profile?.timezone || 'America/Los_Angeles';
                            const timeStr = aptDate.toLocaleTimeString('en-US', { 
                              hour: 'numeric', 
                              minute: '2-digit',
                              timeZone: displayTimezone
                            });
                            
                            return (
                              <div 
                                key={apt.id} 
                                className="flex items-start justify-between group p-3 rounded-lg hover:bg-accent/30 transition-colors cursor-pointer border border-transparent hover:border-primary/20"
                                onClick={() => navigate('/schedule')}
                              >
                                <div className="flex items-start space-x-3 flex-1">
                                  <div className="mt-0.5 p-1.5 rounded-md bg-primary/10">
                                    <CalendarIcon className="h-4 w-4 text-primary" />
                                  </div>
                                  <div className="flex-1">
                                    <p className="font-semibold text-foreground">{timeStr} - {apt.customer_name}</p>
                                    <p className="text-sm text-muted-foreground mt-0.5">
                                      Today
                                    </p>
                                  </div>
                                </div>
                                <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 h-8 w-8 p-0">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </div>
                            );
                          })
                        ) : (
                          <div className="text-center py-8">
                            <CalendarIcon className="h-12 w-12 text-muted-foreground/30 mx-auto mb-3" />
                            <p className="text-sm text-muted-foreground">No appointments scheduled for today</p>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card className="bg-white border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-primary hover:text-primary/80 hover:bg-accent/50 transition-colors"
                      onClick={() => navigate('/activity')}
                    >
                      View All
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {activities.length > 0 ? (
                      activities.map((activity, idx) => (
                        <div 
                          key={idx} 
                          className="flex items-start space-x-3 p-2 rounded-lg hover:bg-accent/30 transition-colors"
                        >
                          <div className="mt-0.5 p-1.5 rounded-md bg-primary/10 text-primary flex-shrink-0">
                            {activity.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-foreground leading-relaxed">{activity.message}</p>
                            <p className="text-xs text-muted-foreground mt-1">{activity.timestamp}</p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8">
                        <Phone className="h-12 w-12 text-muted-foreground/30 mx-auto mb-3" />
                        <p className="text-sm text-muted-foreground">No recent activity</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string | number;
  change: number;
  isPositive?: boolean; // Always true now, but kept for backward compatibility
  icon: React.ReactNode;
  editable?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  change, 
  isPositive,
  icon,
  editable 
}) => {
  return (
    <Card className="bg-white/90 backdrop-blur-sm border-border/50 shadow-sm hover:shadow-md hover:border-primary/20 transition-all group">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">{title}</CardTitle>
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-primary/10 text-primary opacity-70 group-hover:opacity-100 transition-opacity">
            {icon}
          </div>
          {editable && (
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-primary hover:bg-accent/50 opacity-0 group-hover:opacity-100 transition-all">
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="text-3xl font-bold text-foreground mb-3">{value}</div>
        <div className="flex items-center space-x-1.5">
          {isPositive ? (
            <>
              <div className="flex items-center space-x-1 px-2 py-1 rounded-md bg-primary/10">
                <TrendingUp className="h-3.5 w-3.5 text-primary" />
                <span className="text-sm text-primary font-semibold">+{change}%</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center space-x-1 px-2 py-1 rounded-md bg-destructive/10">
                <TrendingDown className="h-3.5 w-3.5 text-destructive" />
                <span className="text-sm text-destructive font-semibold">{change}%</span>
              </div>
            </>
          )}
          <span className="text-xs text-muted-foreground">
            vs last period
          </span>
        </div>
      </CardContent>
    </Card>
  );
};

export default SalesDashboard;

