import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { SalesDashboardSidebar } from '@/components/SalesDashboardSidebar';
import { 
  Play,
  Edit,
  MessageSquare,
  Video,
  Phone,
  DollarSign,
  Clock,
  HeartPulse
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { supabase } from '@/integrations/supabase/client';
import { cn } from '@/lib/utils';

interface LeadStatus {
  id: string;
  label: string;
  color: string;
}

interface DetectedObjection {
  id: string;
  type: string;
  label: string;
  icon: React.ReactNode;
}

interface CommunicationPlanItem {
  id: string;
  day: number;
  title: string;
  subtitle: string;
  type: 'sms' | 'email' | 'voicemail';
  content: string;
  subject?: string;
  videoUrl?: string;
  status: 'ready' | 'scheduled' | 'sent';
  scheduledFor?: Date;
  canSendNow: boolean;
}

const LeadDetails = () => {
  const navigate = useNavigate();
  const { leadId } = useParams();
  const { user } = useAuth();
  const { profile } = useProfile();

  const [lead, setLead] = useState<any>(null);
  const [objections, setObjections] = useState<DetectedObjection[]>([]);
  const [plan, setPlan] = useState<CommunicationPlanItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || !leadId) return;
    loadLeadDetails();
  }, [user, leadId]);

  const loadLeadDetails = async () => {
    try {
      setLoading(true);
      
      // Fetch lead/patient data
      const { data: leadData } = await supabase
        .from('patients')
        .select('*')
        .eq('id', leadId)
        .single();

      if (!leadData) {
        console.error('Lead not found');
        return;
      }

      setLead(leadData);

      // Fetch call analyses to detect objections
      const { data: analyses } = await supabase
        .from('call_records')
        .select('*, call_analyses(*)')
        .eq('customer_name', leadData.full_name)
        .order('created_at', { ascending: false })
        .limit(5);

      // Extract objections from analyses
      const detectedObjections = extractObjections(analyses);
      setObjections(detectedObjections);

      // Generate/regenerate communication plan based on detected objections
      const communicationPlan = generateCommunicationPlan(detectedObjections, leadData, analyses);
      setPlan(communicationPlan);

    } catch (error) {
      console.error('Error loading lead details:', error);
    } finally {
      setLoading(false);
    }
  };

  const extractObjections = (analyses: any[]): DetectedObjection[] => {
    const objectionsMap: Map<string, DetectedObjection> = new Map();

    analyses.forEach((record: any) => {
      const analysis = record.call_analyses?.[0]?.analysis_data;
      if (!analysis?.objections) return;

      analysis.objections.forEach((obj: any) => {
        if (!objectionsMap.has(obj.type)) {
          objectionsMap.set(obj.type, {
            id: obj.type,
            type: obj.type,
            label: getObjectionLabel(obj.type),
            icon: getObjectionIcon(obj.type),
          });
        }
      });
    });

    return Array.from(objectionsMap.values());
  };

  const getObjectionLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'cost-value': 'Cost Concerns',
      'timing': 'Time Commitment',
      'safety-risk': 'Fear of Procedure',
      'social-concerns': 'Social Concerns',
      'provider-trust': 'Trust Issues',
      'results-skepticism': 'Results Doubt',
    };
    return labels[type] || type;
  };

  const getObjectionIcon = (type: string): React.ReactNode => {
    const icons: Record<string, React.ReactNode> = {
      'cost-value': <DollarSign className="h-4 w-4" />,
      'timing': <Clock className="h-4 w-4" />,
      'safety-risk': <HeartPulse className="h-4 w-4" />,
      'social-concerns': <MessageSquare className="h-4 w-4" />,
      'provider-trust': <HeartPulse className="h-4 w-4" />,
      'results-skepticism': <HeartPulse className="h-4 w-4" />,
    };
    return icons[type] || <MessageSquare className="h-4 w-4" />;
  };

  const generateCommunicationPlan = (
    objections: DetectedObjection[],
    leadData: any,
    analyses: any[]
  ): CommunicationPlanItem[] => {
    // This is the "central nervous system" logic that regenerates the plan
    // based on detected objections and patient context
    const plan: CommunicationPlanItem[] = [];
    
    // Day 1: Immediate follow-up SMS addressing primary objection
    if (objections.length > 0) {
      const primaryObjection = objections[0];
      const personalization = getPersonalizationForObjection(primaryObjection, leadData);
      
      plan.push({
        id: 'day-1-sms',
        day: 1,
        title: 'Immediate Follow-up',
        subtitle: 'Suggested SMS',
        type: 'sms',
        content: `Hi ${leadData.full_name.split(' ')[0]}, great speaking with you. I understand your concerns about ${primaryObjection.label.toLowerCase()}. We have flexible ${getSolutionForObjection(primaryObjection.type)} that makes this more affordable than you think. I'll send an email with details. Let me know if you have questions!`,
        status: 'ready',
        canSendNow: true,
      });
    }

    // Day 3: Email with video addressing multiple concerns
    if (objections.length >= 2) {
      const addressedConcerns = objections.slice(0, 2).map(o => o.label).join(' and ');
      
      plan.push({
        id: 'day-3-email',
        day: 3,
        title: 'Address Concerns',
        subtitle: 'Email with Digital Twin Video',
        type: 'email',
        subject: `Your new smile is within reach, ${leadData.full_name.split(' ')[0]}`,
        content: `Hi ${leadData.full_name.split(' ')[0]}, Following up on our chat, I've attached a short personalized video that walks through our ${getSolutionForObjection(objections[0]?.type)} and addresses the ${addressedConcerns.toLowerCase()}. Many of our patients are surprised at how manageable it is. Let me know what you think!`,
        videoUrl: '/api/video/digital-twin', // Placeholder
        status: 'scheduled',
        scheduledFor: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
        canSendNow: false,
      });
    }

    // Day 5: Gentle nudge voicemail if procedure fear detected
    const hasProcedureFear = objections.some(o => o.type === 'safety-risk');
    if (hasProcedureFear) {
      plan.push({
        id: 'day-5-voicemail',
        day: 5,
        title: 'Gentle Nudge',
        subtitle: 'Ringless Voicemail Drop',
        type: 'voicemail',
        content: `Hey ${leadData.full_name.split(' ')[0]}, just leaving a quick message. Hope you had a chance to see the video I sent. If you're feeling nervous about the procedure, that's completely normal. We can schedule a chat with one of our patient coordinators who's been through it. Talk soon.`,
        status: 'scheduled',
        scheduledFor: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
        canSendNow: false,
      });
    }

    return plan;
  };

  const getPersonalizationForObjection = (objection: DetectedObjection, leadData: any): string => {
    // Personalize content based on objection type and lead data
    const personalizations: Record<string, string> = {
      'cost-value': 'flexible financing options',
      'timing': 'efficient scheduling that works around your schedule',
      'safety-risk': 'comprehensive safety protocols we follow',
      'social-concerns': 'discreet process we maintain',
      'provider-trust': 'credentials and success stories',
      'results-skepticism': 'before/after galleries',
    };
    return personalizations[objection.type] || 'information about our services';
  };

  const getSolutionForObjection = (type: string): string => {
    const solutions: Record<string, string> = {
      'cost-value': 'financing options',
      'timing': 'procedure timeline',
      'safety-risk': 'safety measures',
      'social-concerns': 'privacy guarantees',
      'provider-trust': 'credentials',
      'results-skepticism': 'results portfolio',
    };
    return solutions[type] || 'solutions';
  };

  const handleSendNow = async (item: CommunicationPlanItem) => {
    // TODO: Implement actual sending logic
    console.log('Sending:', item);
    // Mark as sent
    setPlan(prev => prev.map(p => 
      p.id === item.id ? { ...p, status: 'sent' as const } : p
    ));
  };

  const handleSchedule = async (item: CommunicationPlanItem) => {
    // TODO: Implement scheduling logic
    console.log('Scheduling:', item);
  };

  const handleRegeneratePlan = async () => {
    // Regenerate the communication plan based on current state
    // This simulates the "central nervous system" reacting to new information
    if (lead) {
      await loadLeadDetails();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg">Loading lead details...</div>
        </div>
      </div>
    );
  }

  if (!lead || !user || !profile) {
    return null;
  }

  const leadName = lead.full_name;
  const firstName = leadName.split(' ')[0];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Sidebar */}
      <SalesDashboardSidebar />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        {/* Header */}
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-8">
          <div className="flex items-center gap-4">
            <Avatar className="h-24 w-24">
              <AvatarFallback className="text-2xl">
                {firstName.charAt(0)}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col justify-center">
              <h1 className="text-2xl font-bold text-gray-900">{leadName}</h1>
              <p className="text-base text-gray-600">
                {lead.email || ''} {lead.phone ? `| ${lead.phone}` : ''}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-sm text-gray-600">Lead Status:</p>
                <Badge className="bg-orange-100 text-orange-900 border-orange-200">
                  Warm
                </Badge>
              </div>
            </div>
          </div>
          <Button 
            onClick={handleRegeneratePlan}
            className="bg-blue-600 hover:bg-blue-700 w-full max-w-[480px] md:w-auto"
          >
            <Play className="h-4 w-4 mr-2" />
            Start Automated Follow-Up
          </Button>
        </header>

        <div className="flex flex-col gap-8">
          {/* Detected Objections */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Detected Objections</h2>
            <div className="flex flex-wrap gap-3">
              {objections.map((obj) => (
                <div
                  key={obj.id}
                  className="flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-900 hover:bg-blue-50 hover:border-blue-300 transition-colors"
                >
                  <div className="text-orange-600">{obj.icon}</div>
                  <span>{obj.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Communication Plan Timeline */}
          <div className="relative pl-8">
            <div className="absolute left-4 top-4 bottom-0 w-0.5 bg-gray-200"></div>
            <div className="flex flex-col gap-10">
              {plan.map((item, idx) => {
                const Icon = item.type === 'sms' ? MessageSquare : item.type === 'email' ? Video : Phone;
                const iconBg = idx === 0 ? 'bg-blue-600' : idx === 1 ? 'bg-blue-600' : 'bg-blue-600';
                
                return (
                  <div key={item.id} className="relative">
                    <div className={cn("absolute -left-8 top-0 flex size-8 items-center justify-center rounded-full text-white", iconBg)}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="ml-4">
                      <Card>
                        <CardContent className="p-6">
                          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                              <p className="text-sm font-medium text-gray-600">
                                Day {item.day}: {item.title}
                              </p>
                              <h3 className="text-lg font-bold text-gray-900">{item.subtitle}</h3>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button 
                                variant="outline" 
                                size="sm"
                                className="border-gray-200 hover:bg-gray-50"
                              >
                                <Edit className="h-4 w-4 mr-2" />
                                Edit
                              </Button>
                              {item.canSendNow ? (
                                <Button 
                                  size="sm" 
                                  onClick={() => handleSendNow(item)}
                                  className="bg-teal-600 hover:bg-teal-700"
                                >
                                  Send Now
                                </Button>
                              ) : (
                                <Button 
                                  size="sm" 
                                  onClick={() => handleSchedule(item)}
                                  className="bg-teal-600 hover:bg-teal-700"
                                >
                                  Schedule
                                </Button>
                              )}
                            </div>
                          </div>

                          {/* Content Preview */}
                          {item.type === 'sms' || item.type === 'voicemail' ? (
                            <div className="mt-4 p-4 rounded-lg bg-gray-50 border border-gray-200">
                              <p className="text-gray-600 leading-relaxed">"{item.content}"</p>
                            </div>
                          ) : (
                            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                              <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                                <p className="font-semibold text-gray-900 mb-1">
                                  Subject: {item.subject}
                                </p>
                                <p className="text-gray-600 leading-relaxed">"{item.content}"</p>
                              </div>
                              {item.videoUrl && (
                                <div className="relative aspect-video rounded-lg bg-gray-200 flex items-center justify-center overflow-hidden">
                                  <div className="absolute inset-0 bg-black/40"></div>
                                  <Button
                                    variant="ghost"
                                    className="relative grid place-content-center size-14 rounded-full bg-white/30 backdrop-blur-sm text-white hover:bg-white/50"
                                  >
                                    <Play className="h-8 w-8" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LeadDetails;

