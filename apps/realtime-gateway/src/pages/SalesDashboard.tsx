import React, { useState, useEffect } from 'react';
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
import { supabase } from '@/integrations/supabase/client';
import { cn } from '@/lib/utils';

interface DashboardMetrics {
  newLeadsThisWeek: number;
  newLeadsChange: number;
  consultationsBooked: number;
  consultationsChange: number;
  dealsClosedThisMonth: number;
  dealsClosedChange: number;
  revenueGenerated: number;
  revenueChange: number;
}

interface ScheduledAppointment {
  time: string;
  name: string;
  type: string;
}

interface ManualFollowup {
  action: string;
  lastContact: string;
}

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
  
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    newLeadsThisWeek: 42,
    newLeadsChange: 15,
    consultationsBooked: 18,
    consultationsChange: 5,
    dealsClosedThisMonth: 7,
    dealsClosedChange: -10,
    revenueGenerated: 84000,
    revenueChange: 20
  });
  
  const [appointments, setAppointments] = useState<ScheduledAppointment[]>([
    { time: '10:00 AM', name: 'Sarah Connor', type: 'Initial Consult' },
    { time: '11:30 AM', name: 'Barbara K.', type: 'Follow-up Call' },
    { time: '2:00 PM', name: 'John Kyle', type: 'Initial Consult' }
  ]);
  
  const [followups, setFollowups] = useState<ManualFollowup[]>([
    { action: 'Follow up with Mike P.', lastContact: 'Last contact: 3 hours ago' }
  ]);
  
  const [activities, setActivities] = useState<RecentActivity[]>([
    { 
      message: 'New lead assigned from web form: Sarah Connor.', 
      timestamp: '2 mins ago',
      icon: <UserPlus className="h-4 w-4" />
    },
    { 
      message: 'Jane Doe opened your follow-up email.', 
      timestamp: '15 mins ago',
      icon: <Mail className="h-4 w-4" />
    },
    { 
      message: 'Task completed: Send quote to Dental Associates Clinic.', 
      timestamp: '1 hour ago',
      icon: <CheckCircle2 className="h-4 w-4" />
    },
    { 
      message: 'Call logged with Mike P. Duration: 12m 34s.', 
      timestamp: '3 hours ago',
      icon: <Phone className="h-4 w-4" />
    }
  ]);

  useEffect(() => {
    if (user && profile) {
      loadCalls(10);
      // TODO: Fetch real metrics from backend
      fetchDashboardMetrics();
    }
  }, [user, profile]);

  const fetchDashboardMetrics = async () => {
    // TODO: Implement real API calls to fetch:
    // - New leads this week
    // - Consultations booked
    // - Deals closed this month
    // - Revenue generated
    // For now, using mock data
  };

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

  if (!user || !profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Sidebar */}
      <SalesDashboardSidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Bar */}
        <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div className="flex-1 max-w-lg relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input 
              placeholder="Search leads, tasks..." 
              className="w-full pl-10"
            />
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            New Lead
          </Button>
        </div>

        {/* Dashboard Content */}
        <ScrollArea className="flex-1">
          <div className="p-8 max-w-7xl mx-auto">
            {/* Greeting */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">
                {getGreeting()}, {profile.salesperson_name || 'Alex'}
              </h1>
              <p className="text-gray-600 mt-2">
                Here's your sales overview for today.
              </p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="New Leads This Week"
                value={metrics.newLeadsThisWeek}
                change={metrics.newLeadsChange}
                isPositive={metrics.newLeadsChange > 0}
                icon={<TrendingUp className="h-4 w-4" />}
              />
              <MetricCard
                title="Consultations Booked"
                value={metrics.consultationsBooked}
                change={metrics.consultationsChange}
                isPositive={metrics.consultationsChange > 0}
                icon={<TrendingUp className="h-4 w-4" />}
              />
              <MetricCard
                title="Deals Closed (Month)"
                value={metrics.dealsClosedThisMonth}
                change={metrics.dealsClosedChange}
                isPositive={metrics.dealsClosedChange > 0}
                icon={<TrendingDown className="h-4 w-4" />}
              />
              <MetricCard
                title="Revenue Generated"
                value={formatCurrency(metrics.revenueGenerated)}
                change={metrics.revenueChange}
                isPositive={metrics.revenueChange > 0}
                icon={<TrendingUp className="h-4 w-4" />}
                editable
              />
            </div>

            {/* Today's Focus and Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Today's Focus */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Today's Focus</CardTitle>
                    <Button variant="ghost" size="sm" className="text-blue-600">
                      View All
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Scheduled Appointments */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-4">Scheduled Appointments</h4>
                    <div className="space-y-4">
                      {appointments.map((apt, idx) => (
                        <div key={idx} className="flex items-start justify-between group">
                          <div className="flex items-start space-x-3 flex-1">
                            <CalendarIcon className="h-5 w-5 text-gray-400 mt-0.5" />
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{apt.time} - {apt.name}</p>
                              <p className="text-sm text-gray-600">{apt.type}</p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Manual Follow-ups */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-4">Manual Follow-ups</h4>
                    <div className="space-y-4">
                      {followups.map((followup, idx) => (
                        <div key={idx} className="flex items-start justify-between group">
                          <div className="flex items-start space-x-3 flex-1">
                            <Phone className="h-5 w-5 text-gray-400 mt-0.5" />
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{followup.action}</p>
                              <p className="text-sm text-gray-600">{followup.lastContact}</p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Recent Activity</CardTitle>
                    <Button variant="ghost" size="sm" className="text-blue-600">
                      View All
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {activities.map((activity, idx) => (
                      <div key={idx} className="flex items-start space-x-3">
                        <div className="mt-0.5">{activity.icon}</div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">{activity.message}</p>
                          <p className="text-xs text-gray-500 mt-1">{activity.timestamp}</p>
                        </div>
                      </div>
                    ))}
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
  isPositive: boolean;
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
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        {editable && (
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
            <Pencil className="h-4 w-4" />
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center space-x-1 mt-2">
          {isPositive ? (
            <>
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="text-sm text-green-600">{Math.abs(change)}%</span>
            </>
          ) : (
            <>
              <TrendingDown className="h-4 w-4 text-red-600" />
              <span className="text-sm text-red-600">{Math.abs(change)}%</span>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default SalesDashboard;

