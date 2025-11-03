import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
}

const SalesDashboard = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { profile } = useProfile();
  const { calls, loadCalls } = useCallRecords();
  const { appointments: dbAppointments, loading: appointmentsLoading } = useAppointments();
  const { metrics, loading: metricsLoading } = useDashboardMetrics();
  
  // Load calls on mount
  useEffect(() => {
    if (user && profile) {
      loadCalls(10);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, profile]);

  // Generate activity feed from calls and appointments (memoized)
  const activities = useMemo(() => {
    const activitiesList: RecentActivity[] = [];
    
    // Add recent calls as activities
    if (calls && calls.length > 0) {
      const recentCalls = calls.slice(0, 3);
      recentCalls.forEach((call) => {
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
          icon: <Phone className="h-4 w-4" />
        });
      });
    }

    // Add recent appointments as activities
    if (dbAppointments && dbAppointments.length > 0) {
      const recentApps = dbAppointments.slice(0, 2);
      recentApps.forEach((apt) => {
        const timeDiff = Date.now() - new Date(apt.created_at).getTime();
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
          message: `New appointment scheduled: ${apt.customer_name}`,
          timestamp,
          icon: <CalendarIcon className="h-4 w-4" />
        });
      });
    }

    return activitiesList;
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

            {/* KPI Cards */}
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
                      {dbAppointments && dbAppointments.length > 0 ? (
                        dbAppointments.map((apt, idx) => {
                          const aptDate = new Date(apt.appointment_date);
                          // Use user's timezone if available, otherwise default to America/Los_Angeles for business hours
                          // This ensures appointments created in Pacific time display correctly
                          const displayTimezone = profile?.timezone || 'America/Los_Angeles';
                          const timeStr = aptDate.toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit',
                            timeZone: displayTimezone
                          });
                          const today = new Date();
                          const isToday = aptDate.toDateString() === today.toDateString();
                          
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
                                    {isToday ? 'Today' : aptDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
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
                      )}
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

