import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { SalesDashboardSidebar } from '@/components/SalesDashboardSidebar';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useAppointments } from '@/hooks/useAppointments';
import {
  Phone,
  Mail,
  Calendar,
  FileText,
  Search,
  Filter
} from 'lucide-react';

interface Activity {
  id: string;
  type: 'call' | 'email' | 'appointment' | 'note';
  title: string;
  description: string;
  timestamp: Date;
  customerName?: string;
  icon: React.ReactNode;
}

const ActivityLog = () => {
  const { user } = useAuth();
  const { profile } = useProfile();
  const { calls, loadCalls } = useCallRecords();
  const { appointments, loading: appointmentsLoading } = useAppointments();
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (user && profile) {
      loadCalls(100);
    }
  }, [user, profile]);

  const activities = useMemo(() => {
    const activitiesList: Activity[] = [];

    // Add calls
    if (calls && calls.length > 0) {
      calls.forEach(call => {
        activitiesList.push({
          id: `call-${call.id}`,
          type: 'call',
          title: `Call with ${call.patientName}`,
          description: `Duration: ${Math.floor(call.duration / 60)}m ${call.duration % 60}s`,
          timestamp: call.timestamp,
          customerName: call.patientName,
          icon: <Phone className="h-4 w-4" />
        });
      });
    }

    // Add appointments
    if (appointments && appointments.length > 0) {
      appointments.forEach(apt => {
        const aptDate = new Date(apt.appointment_date);
        activitiesList.push({
          id: `apt-${apt.id}`,
          type: 'appointment',
          title: `Appointment: ${apt.customer_name}`,
          description: `Scheduled for ${aptDate.toLocaleDateString()} at ${aptDate.toLocaleTimeString()}`,
          timestamp: new Date(apt.created_at),
          customerName: apt.customer_name,
          icon: <Calendar className="h-4 w-4" />
        });
      });
    }

    // Sort by timestamp (newest first)
    activitiesList.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    return activitiesList;
  }, [calls, appointments]);

  const filteredActivities = searchTerm
    ? activities.filter(activity =>
        activity.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.customerName?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : activities;

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
      <SalesDashboardSidebar />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div className="flex-1 max-w-lg relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search activity..."
              className="w-full pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-3xl font-bold text-gray-900">Activity Log</h1>
              <div className="text-sm text-gray-600">
                {filteredActivities.length} {filteredActivities.length === 1 ? 'activity' : 'activities'}
              </div>
            </div>

            {filteredActivities.length === 0 ? (
              <Card className="p-12 text-center">
                <p className="text-gray-500">No activities found</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredActivities.map((activity) => {
                  const timeAgo = getTimeAgo(activity.timestamp);
                  
                  return (
                    <Card key={activity.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-4">
                          <div className="flex-shrink-0 p-2 bg-gray-100 rounded-lg">
                            {activity.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <h3 className="font-semibold text-gray-900">{activity.title}</h3>
                              <span className="text-sm text-gray-500">{timeAgo}</span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{activity.description}</p>
                            <div className="flex items-center space-x-4">
                              <Badge variant="outline" className="text-xs">
                                {activity.type.charAt(0).toUpperCase() + activity.type.slice(1)}
                              </Badge>
                              {activity.customerName && (
                                <span className="text-xs text-gray-500">
                                  {activity.customerName}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? 'min' : 'mins'} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
  } else {
    return date.toLocaleDateString();
  }
}

export default ActivityLog;
