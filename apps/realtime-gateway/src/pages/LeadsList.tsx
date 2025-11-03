import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { SalesDashboardSidebar } from '@/components/SalesDashboardSidebar';
import { useAppointments } from '@/hooks/useAppointments';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import {
  Plus,
  Search,
  Phone,
  Mail,
  Calendar,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign,
  HeartPulse
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { supabase } from '@/integrations/supabase/client';

interface Lead {
  id: string;
  name: string;
  email: string;
  phone: string;
  status: 'cold' | 'warm' | 'hot';
  lastContact?: string;
  appointmentsCount: number;
  callsCount: number;
  objections?: string[];
  motivation?: string;
}

const LeadsList = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { profile } = useProfile();
  const { appointments } = useAppointments();
  const { calls } = useCallRecords();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (user) {
      loadLeads();
    }
  }, [user]);

  const loadLeads = async () => {
    if (!user) return;

    setLoading(true);
    try {
      // First, try to get all patients from the patients table
      let query = supabase
        .from('patients')
        .select('*');
      
      // Only add organization filter if we have a valid organization_id
      if (profile?.organization_id) {
        query = query.eq('organization_id', profile.organization_id);
      }
      
      const { data: patients, error: patientsError } = await query;

      const patientMap = new Map<string, Lead>();

      // If we have patients, use them as the base
      if (patients && patients.length > 0) {
        patients.forEach(patient => {
          const key = patient.full_name?.toLowerCase().trim() || '';
          if (key) {
            const lead: Lead = {
              id: patient.id,
              name: patient.full_name,
              email: patient.email || '',
              phone: patient.phone || '',
              status: 'warm' as const,
              lastContact: patient.created_at,
              appointmentsCount: 0,
              callsCount: 0,
              objections: [],
              motivation: ''
            };
            patientMap.set(key, lead);
          }
        });
      }

      // Then add/update from appointments
      if (appointments) {
        appointments.forEach(apt => {
          const key = apt.customer_name.toLowerCase().trim();
          if (!patientMap.has(key)) {
            const lead: Lead = {
              id: apt.id,
              name: apt.customer_name,
              email: apt.email || apt.customer_email || '',
              phone: apt.phone_number || apt.customer_phone || '',
              status: 'warm' as const,
              lastContact: apt.created_at,
              appointmentsCount: 0,
              callsCount: 0,
              objections: [],
              motivation: ''
            };
            patientMap.set(key, lead);
          }
          
          const lead = patientMap.get(key)!;
          lead.appointmentsCount++;
          if (new Date(apt.created_at) > new Date(lead.lastContact || 0)) {
            lead.lastContact = apt.created_at;
          }
        });
      }

      // Get calls for each lead
      if (calls && calls.length > 0) {
        calls.forEach(call => {
          const key = call.patientName.toLowerCase().trim();
          if (patientMap.has(key)) {
            const lead = patientMap.get(key)!;
            lead.callsCount++;
            if (new Date(call.timestamp) > new Date(lead.lastContact || 0)) {
              lead.lastContact = call.timestamp.toISOString();
            }
          }
        });
      }

      // Try to get objections and motivations from call analyses
      for (const [key, lead] of patientMap.entries()) {
        try {
          const { data: analyses } = await supabase
            .from('call_analyses')
            .select('analysis_data')
            .eq('user_id', user.id)
            .like('analysis_data->>customerName', `%${lead.name}%`)
            .order('created_at', { ascending: false })
            .limit(1);

          if (analyses && analyses.length > 0) {
            const analysis = analyses[0].analysis_data;
            if (analysis?.objections) {
              lead.objections = analysis.objections.map((obj: any) => obj.type);
            }
            if (analysis?.customerPersonality?.motivationCategory) {
              lead.motivation = analysis.customerPersonality.motivationCategory;
            }
          }
        } catch (error) {
          console.warn('Error fetching analysis for lead:', error);
        }
      }

      // Convert to array and sort by last contact
      const leadsArray = Array.from(patientMap.values()).sort((a, b) => {
        const dateA = new Date(a.lastContact || 0).getTime();
        const dateB = new Date(b.lastContact || 0).getTime();
        return dateB - dateA;
      });

      setLeads(leadsArray);
    } catch (error) {
      console.error('Error loading leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'hot':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warm':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'cold':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getObjectionIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      'cost-value': <DollarSign className="h-3 w-3" />,
      'timing': <Clock className="h-3 w-3" />,
      'safety-risk': <HeartPulse className="h-3 w-3" />,
    };
    return icons[type] || <Clock className="h-3 w-3" />;
  };

  const filteredLeads = searchTerm
    ? leads.filter(lead =>
        lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.phone.includes(searchTerm)
      )
    : leads;

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
              placeholder="Search leads..."
              className="w-full pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Lead
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-3xl font-bold text-gray-900">Leads</h1>
              <div className="text-sm text-gray-600">
                {filteredLeads.length} {filteredLeads.length === 1 ? 'lead' : 'leads'}
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12 text-gray-500">Loading leads...</div>
            ) : filteredLeads.length === 0 ? (
              <Card className="p-12 text-center">
                <p className="text-gray-500 mb-4">No leads found</p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Lead
                </Button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredLeads.map((lead) => (
                  <Card
                    key={lead.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => navigate(`/leads/${lead.id}`)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-10 w-10">
                            <AvatarFallback>
                              {lead.name.charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <h3 className="font-semibold text-gray-900">{lead.name}</h3>
                            <Badge className={cn("mt-1 text-xs", getStatusColor(lead.status))}>
                              {lead.status.charAt(0).toUpperCase() + lead.status.slice(1)}
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center text-sm text-gray-600">
                          <Mail className="h-4 w-4 mr-2" />
                          {lead.email || 'No email'}
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Phone className="h-4 w-4 mr-2" />
                          {lead.phone || 'No phone'}
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="h-4 w-4 mr-2" />
                          {lead.appointmentsCount} appointment{lead.appointmentsCount !== 1 ? 's' : ''}
                        </div>
                        {lead.callsCount > 0 && (
                          <div className="flex items-center text-sm text-gray-600">
                            <Phone className="h-4 w-4 mr-2" />
                            {lead.callsCount} call{lead.callsCount !== 1 ? 's' : ''}
                          </div>
                        )}
                      </div>

                      {lead.objections && lead.objections.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="flex flex-wrap gap-1">
                            {lead.objections.slice(0, 3).map((obj, idx) => (
                              <div
                                key={idx}
                                className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs text-gray-700"
                              >
                                {getObjectionIcon(obj)}
                                {obj}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default LeadsList;
