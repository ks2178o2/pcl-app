import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { ContactPreferencesPanel } from './ContactPreferencesPanel';
import { EmailSender } from './EmailSender';
import { SMSSender } from './SMSSender';
import { FollowupActivitiesPanel } from './FollowupActivitiesPanel';
import { useContactPreferences } from '@/hooks/useContactPreferences';
import { Send, Clock, Target, MessageSquare, Mail, Phone, Settings, Shield, Zap, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { CallAnalysis, AnalysisEngine } from '@/services/transcriptAnalysisService';

interface FollowUpPlan {
  id: string;
  strategy_type: string;
  recommended_timing: string;
  priority_score: number;
  customer_urgency: string;
  next_action: string;
  reasoning: string;
  compliance_notes?: string;
  status: string;
  created_at: string;
}

interface FollowUpMessage {
  id: string;
  channel_type: string;
  subject_line?: string;
  message_content: string;
  personalization_notes: string;
  tone: string;
  call_to_action: string;
  status: string;
  estimated_send_time?: string;
}

interface FollowUpPlanPanelProps {
  callId: string;
  transcript: string;
  analysisData: any;
  customerName: string;
  salespersonName: string;
}

const getUrgencyColor = (urgency: string) => {
  switch (urgency) {
    case 'high': return 'bg-destructive text-destructive-foreground';
    case 'medium': return 'bg-warning text-warning-foreground';
    case 'low': return 'bg-muted text-muted-foreground';
    default: return 'bg-muted text-muted-foreground';
  }
};

const getChannelIcon = (channel: string) => {
  switch (channel) {
    case 'email': return <Mail className="h-4 w-4" />;
    case 'sms': return <MessageSquare className="h-4 w-4" />;
    case 'voicemail': return <Phone className="h-4 w-4" />;
    default: return <Send className="h-4 w-4" />;
  }
};

const getTimingText = (timing: string) => {
  switch (timing) {
    case 'immediate': return 'Send immediately';
    case '24_hours': return 'Send in 24 hours';
    case '3_days': return 'Send in 3 days';
    case '1_week': return 'Send in 1 week';
    default: return timing;
  }
};

export const FollowUpPlanPanel: React.FC<FollowUpPlanPanelProps> = ({
  callId,
  transcript,
  analysisData,
  customerName,
  salespersonName
}) => {
  const [followUpPlan, setFollowUpPlan] = useState<FollowUpPlan | null>(null);
  const [messages, setMessages] = useState<FollowUpMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSMSSenderOpen, setIsSMSSenderOpen] = useState(false);
  const [provider, setProvider] = useState<'auto' | 'gemini' | 'openai'>(() => {
    const saved = localStorage.getItem('followup-provider');
    return (saved as 'auto' | 'gemini' | 'openai') || 'auto';
  });
  const { user } = useAuth();
  const { preferences } = useContactPreferences(callId);

  // Restore from cache immediately; refresh in background
  useEffect(() => {
    try {
      const cachedPlan = sessionStorage.getItem(`followupPlan:${callId}`);
      const cachedMsgs = sessionStorage.getItem(`followupMsgs:${callId}`);
      if (cachedPlan) setFollowUpPlan(JSON.parse(cachedPlan));
      if (cachedMsgs) setMessages(JSON.parse(cachedMsgs));
      if (cachedPlan || cachedMsgs) setIsLoading(false);
    } catch {}
  }, [callId]);

  // Extract stable user ID to prevent unnecessary re-fetches
  const userId = user?.id;

  useEffect(() => {
    if (userId && callId) {
      loadFollowUpPlan();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, callId]);

  const loadFollowUpPlan = async () => {
    if (!userId || !callId) return;
    
    try {
      setIsLoading(true);
      
      // Load existing follow-up plan - use maybeSingle() to avoid 406 errors
      const { data: planData, error: planError } = await supabase
        .from('follow_up_plans')
        .select('*')
        .eq('call_record_id', callId)
        .eq('user_id', userId)
        .maybeSingle();

      // Only log actual errors (not expected "no rows" cases)
      if (planError && planError.code !== 'PGRST116') {
        console.error('Error loading follow-up plan:', planError);
        // Don't throw - just continue without plan data
      }

      if (planData) {
        // Merge plan_data JSONB fields into the plan object if individual columns don't exist
        const mergedPlan = { ...planData };
        if (planData.plan_data && typeof planData.plan_data === 'object') {
          // Extract fields from plan_data JSONB if individual columns are missing
          const planDataObj = planData.plan_data;
          if (!mergedPlan.customer_urgency && planDataObj.customer_urgency) {
            mergedPlan.customer_urgency = planDataObj.customer_urgency;
          }
          if (!mergedPlan.priority_score && planDataObj.priority_score !== undefined) {
            mergedPlan.priority_score = planDataObj.priority_score;
          }
          if (!mergedPlan.strategy_type && planDataObj.strategy_type) {
            mergedPlan.strategy_type = planDataObj.strategy_type;
          }
          if (!mergedPlan.recommended_timing && planDataObj.recommended_timing) {
            mergedPlan.recommended_timing = planDataObj.recommended_timing;
          }
          if (!mergedPlan.next_action && planDataObj.next_action) {
            mergedPlan.next_action = planDataObj.next_action;
          }
          if (!mergedPlan.reasoning && planDataObj.reasoning) {
            mergedPlan.reasoning = planDataObj.reasoning;
          }
        }
        
        setFollowUpPlan(mergedPlan);
        try { sessionStorage.setItem(`followupPlan:${callId}`, JSON.stringify(mergedPlan)); } catch {}
        
        // Load associated messages
        const { data: messagesData, error: messagesError } = await supabase
          .from('follow_up_messages')
          .select('*')
          .eq('follow_up_plan_id', planData.id)
          .eq('user_id', userId);

        if (messagesError) {
          console.error('Error loading follow-up messages:', messagesError);
          // Don't throw - just continue without messages
        }

        // Merge message_data JSONB fields into message objects if individual columns don't exist
        const mergedMessages = (messagesData || []).map((msg: any) => {
          const mergedMsg = { ...msg };
          if (msg.message_data && typeof msg.message_data === 'object') {
            // Extract fields from message_data JSONB if individual columns are missing
            const msgDataObj = msg.message_data;
            if (!mergedMsg.channel_type && msgDataObj.channel_type) {
              mergedMsg.channel_type = msgDataObj.channel_type;
            }
            if (!mergedMsg.message_content && msgDataObj.message_content) {
              mergedMsg.message_content = msgDataObj.message_content;
            }
            if (!mergedMsg.subject_line && msgDataObj.subject_line) {
              mergedMsg.subject_line = msgDataObj.subject_line;
            }
            if (!mergedMsg.call_to_action && msgDataObj.call_to_action) {
              mergedMsg.call_to_action = msgDataObj.call_to_action;
            }
            if (!mergedMsg.personalization_notes && msgDataObj.personalization_notes) {
              mergedMsg.personalization_notes = msgDataObj.personalization_notes;
            }
            if (!mergedMsg.tone && msgDataObj.tone) {
              mergedMsg.tone = msgDataObj.tone;
            }
            if (!mergedMsg.estimated_send_time && msgDataObj.estimated_send_time) {
              mergedMsg.estimated_send_time = msgDataObj.estimated_send_time;
            }
          }
          return mergedMsg;
        });

        setMessages(mergedMessages);
        try { sessionStorage.setItem(`followupMsgs:${callId}`, JSON.stringify(mergedMessages)); } catch {}
      }
    } catch (error) {
      console.error('Error loading follow-up plan:', error);
      toast.error('Failed to load follow-up plan');
    } finally {
      setIsLoading(false);
    }
  };

  const generateFollowUpPlan = async (retryWithProvider?: 'gemini' | 'openai') => {
    if (!transcript || !analysisData) {
      toast.error('Transcript and analysis data are required to generate follow-up plan');
      return;
    }

    const useProvider = retryWithProvider || provider;

    try {
      setIsGenerating(true);
      
      const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
      const { data: sess } = await supabase.auth.getSession();
      const token = sess.session?.access_token;
      
      const resp = await fetch(`${API_BASE_URL}/api/followup/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({
          callRecordId: callId,
          transcript,
          analysisData,
          customerName,
          salespersonName,
          provider: useProvider === 'auto' ? null : useProvider
        }),
      });

      const data = await resp.json().catch(() => null);
      
      if (!resp.ok) {
        const errorMsg = data?.detail || data?.error || resp.statusText || 'Failed to generate follow-up plan';
        throw new Error(errorMsg);
      }

      if (data.error) {
        throw new Error(data.error);
      }

      const successMessage = `Follow-up plan generated successfully with ${data.provider || useProvider}!`;
      if (data.generationTime) {
        console.log(`Generation took ${data.generationTime}ms using ${data.provider}`);
      }
      
      toast.success(successMessage);
      await loadFollowUpPlan();
    } catch (error) {
      console.error('Error generating follow-up plan:', error);
      
      // Suggest alternative provider if current one failed
      const alternativeProvider = useProvider === 'gemini' ? 'openai' : 'gemini';
      const isProviderSpecific = useProvider !== 'auto';
      
      if (isProviderSpecific) {
        toast.error(`Failed with ${useProvider}. Try ${alternativeProvider}?`, {
          action: {
            label: `Retry with ${alternativeProvider}`,
            onClick: () => generateFollowUpPlan(alternativeProvider)
          }
        });
      } else {
        toast.error('Failed to generate follow-up plan');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleProviderChange = (newProvider: 'auto' | 'gemini' | 'openai') => {
    setProvider(newProvider);
    localStorage.setItem('followup-provider', newProvider);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Follow-Up Strategy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading follow-up plan...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!followUpPlan) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Follow-Up Strategy
          </CardTitle>
          <CardDescription>
            Generate a personalized follow-up strategy based on this call analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Follow-Up Plan Generated</h3>
            <p className="text-muted-foreground mb-4">
              Create a strategic follow-up plan with personalized messages based on the call analysis.
            </p>
            
            <div className="flex items-center gap-3 mb-6">
              <label className="text-sm font-medium">AI Provider:</label>
              <Select value={provider} onValueChange={handleProviderChange}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">
                    <div className="flex items-center gap-2">
                      <Zap className="h-3 w-3" />
                      Auto
                    </div>
                  </SelectItem>
                  <SelectItem value="gemini">Gemini</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              onClick={() => generateFollowUpPlan()}
              disabled={isGenerating}
              className="gap-2"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Generating Plan...
                </>
              ) : (
                <>
                  <Target className="h-4 w-4" />
                  Generate Follow-Up Plan
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Follow-Up Strategy
        </CardTitle>
        <CardDescription>
          AI-generated follow-up plan based on call analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs
          defaultValue={(typeof window !== 'undefined') ? (sessionStorage.getItem(`followupTab:${callId}`) || 'strategy') : 'strategy'}
          onValueChange={(v) => { try { sessionStorage.setItem(`followupTab:${callId}`, v); } catch {} }}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="strategy">Strategy</TabsTrigger>
            <TabsTrigger value="messages">Timeline ({messages.length})</TabsTrigger>
            <TabsTrigger value="activities">Follow-up Activity</TabsTrigger>
            <TabsTrigger value="preferences" className="flex items-center gap-1">
              <Settings className="h-3 w-3" />
              Preferences
              {preferences?.do_not_contact && <Shield className="h-3 w-3 text-destructive" />}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="strategy" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {followUpPlan.customer_urgency && (
                    <Badge className={getUrgencyColor(followUpPlan.customer_urgency)}>
                      {followUpPlan.customer_urgency.toUpperCase()} URGENCY
                    </Badge>
                  )}
                  {followUpPlan.priority_score !== undefined && (
                    <Badge variant="outline">
                      Priority: {followUpPlan.priority_score}/10
                    </Badge>
                  )}
                </div>
                
                {followUpPlan.recommended_timing && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    {getTimingText(followUpPlan.recommended_timing)}
                  </div>
                )}
                
                {followUpPlan.strategy_type && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    {getChannelIcon(followUpPlan.strategy_type)}
                    {followUpPlan.strategy_type.charAt(0).toUpperCase() + followUpPlan.strategy_type.slice(1)}
                  </div>
                )}
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium">Next Action</h4>
                <p className="text-sm text-muted-foreground">{followUpPlan.next_action || 'No action specified'}</p>
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-2">
              <h4 className="font-medium">Strategy Reasoning</h4>
              <p className="text-sm text-muted-foreground">{followUpPlan.reasoning || 'No reasoning provided'}</p>
            </div>
            
            {followUpPlan.compliance_notes && (
              <>
                <Separator />
                <div className="space-y-2">
                  <h4 className="font-medium">Compliance Notes</h4>
                  <p className="text-sm text-muted-foreground">{followUpPlan.compliance_notes}</p>
                </div>
              </>
            )}
            
            <div className="flex items-center gap-2 pt-4">
              <div className="flex items-center gap-2">
                <label className="text-xs font-medium">Provider:</label>
                <Select value={provider} onValueChange={handleProviderChange}>
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">
                      <div className="flex items-center gap-1">
                        <Zap className="h-3 w-3" />
                        Auto
                      </div>
                    </SelectItem>
                    <SelectItem value="gemini">Gemini</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Button 
                onClick={() => generateFollowUpPlan()}
                disabled={isGenerating}
                variant="outline"
                size="sm"
                className="gap-1"
              >
                <RefreshCw className="h-3 w-3" />
                Regenerate Plan
              </Button>
            </div>
          </TabsContent>
          
          <TabsContent value="messages" className="space-y-4">
            <div className="mb-4">
              <h4 className="font-medium mb-2">Multi-Day Touchpoint Timeline</h4>
              <p className="text-sm text-muted-foreground">
                Strategic follow-up sequence designed to nurture the prospect through {messages.length} touchpoints
              </p>
            </div>
            
            {messages
              .sort((a, b) => {
                const dayA = a.estimated_send_time ? new Date(a.estimated_send_time).getTime() : 0;
                const dayB = b.estimated_send_time ? new Date(b.estimated_send_time).getTime() : 0;
                return dayA - dayB;
              })
              .map((message, index) => {
                const sendDate = message.estimated_send_time ? new Date(message.estimated_send_time) : null;
                const dayNumber = sendDate ? Math.ceil((sendDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : index + 1;
                
                return (
                  <Card key={message.id} className="p-4 relative">
                    {/* Timeline connector */}
                    {index < messages.length - 1 && (
                      <div className="absolute left-8 top-16 w-0.5 h-8 bg-border"></div>
                    )}
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-medium">
                            {dayNumber > 0 ? dayNumber : index + 1}
                          </div>
                          <div className="flex items-center gap-2">
                            {getChannelIcon(message.channel_type)}
                            <span className="font-medium capitalize">{message.channel_type}</span>
                            <Badge variant="outline" className="text-xs">
                              {message.tone}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {sendDate && (
                            <Badge variant="secondary" className="text-xs">
                              Day {dayNumber > 0 ? dayNumber : index + 1}
                            </Badge>
                          )}
                          <Badge variant={message.status === 'draft' ? 'outline' : 'default'} className="text-xs">
                            {message.status}
                          </Badge>
                        </div>
                      </div>
                      
                      {sendDate && (
                        <div className="text-xs text-muted-foreground ml-11">
                          Scheduled: {sendDate.toLocaleDateString()} {sendDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      )}
                      
                      {message.subject_line && (
                        <div className="ml-11">
                          <span className="text-sm font-medium">Subject: </span>
                          <span className="text-sm text-muted-foreground">{message.subject_line}</span>
                        </div>
                      )}
                      
                      <div className="space-y-2 ml-11">
                        <h5 className="text-sm font-medium">Message Content</h5>
                        <div className="bg-muted/50 p-3 rounded-md text-sm border-l-2 border-primary/20">
                          {message.message_content}
                        </div>
                      </div>
                      
                      <div className="space-y-2 ml-11">
                        <h5 className="text-sm font-medium">Call to Action</h5>
                        <p className="text-sm text-muted-foreground font-medium">{message.call_to_action}</p>
                      </div>
                      
                      {message.personalization_notes && (
                        <div className="space-y-2 ml-11">
                          <h5 className="text-sm font-medium">Strategy Notes</h5>
                          <p className="text-sm text-muted-foreground italic">{message.personalization_notes}</p>
                        </div>
                      )}
                      
                      {/* Send Email Action */}
                      {message.channel_type === 'email' && (
                        <div className="flex justify-between items-center ml-11 pt-3 border-t border-border/50">
                          <div className="text-xs text-muted-foreground">
                            {preferences?.do_not_contact ? (
                              <span className="flex items-center gap-1 text-destructive">
                                <Shield className="h-3 w-3" />
                                Customer has opted out of contact
                              </span>
                            ) : !preferences?.email_allowed ? (
                              <span className="flex items-center gap-1 text-warning">
                                <Shield className="h-3 w-3" />
                                Email contact not preferred
                              </span>
                            ) : (
                              "Ready to send with AI-suggested content"
                            )}
                          </div>
                          
                          <EmailSender
                            callRecordId={callId}
                            customerName={customerName}
                            analysisData={analysisData}
                            prefilledSubject={message.subject_line || ''}
                            prefilledContent={message.message_content}
                            triggerLabel="Send this email"
                            triggerVariant={preferences?.do_not_contact || !preferences?.email_allowed ? "outline" : "default"}
                            triggerSize="sm"
                            onEmailSent={() => {
                              toast.success(`Email sent using AI-suggested content!`);
                            }}
                          />
                        </div>
                      )}
                    </div>
                  </Card>
                );
              })}
              
            {/* Quick Send Next Email CTA */}
            {messages.length > 0 && (
              <Card className="mt-6 p-4 bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Zap className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h4 className="font-medium">Ready to supercharge your follow-up?</h4>
                      <p className="text-sm text-muted-foreground">
                        Send your next strategic email with AI-optimized content
                      </p>
                    </div>
                  </div>
                  
                  <EmailSender
                    callRecordId={callId}
                    customerName={customerName}
                    analysisData={analysisData}
                    prefilledSubject={messages[0]?.subject_line || `Follow-up: ${customerName}`}
                    prefilledContent={messages[0]?.message_content || ''}
                    triggerLabel="Send Next Email"
                    triggerVariant="default"
                    triggerSize="default"
                    onEmailSent={() => {
                      toast.success("Strategic follow-up email sent!");
                    }}
                  />
                </div>
              </Card>
            )}
            
            <div className="mt-6 p-4 bg-muted/30 rounded-lg border border-primary/10">
              <div className="flex items-start gap-2">
                <Target className="h-4 w-4 text-primary mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-foreground">Multi-Touchpoint Strategy</p>
                  <p className="text-muted-foreground mt-1">
                    Research shows it takes 6-7 touchpoints to convert prospects. This timeline is designed to maintain engagement while providing value at each interaction.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="activities" className="space-y-4">
            {/* Email and SMS Action Buttons */}
            <div className="flex gap-4 p-4 bg-muted rounded-lg">
              <EmailSender
                callRecordId={callId || ''}
                customerName={customerName || 'Customer'}
                analysisData={analysisData}
                triggerLabel="Send Follow-up Email"
                triggerVariant="default"
              />
              <Button 
                onClick={() => setIsSMSSenderOpen(true)}
                className="flex items-center gap-2"
                variant="outline"
              >
                <Phone className="h-4 w-4" />
                Send SMS
              </Button>
            </div>
            
            {/* Follow-up Activities History */}
            <FollowupActivitiesPanel callRecordId={callId} />
          </TabsContent>
          
          <TabsContent value="preferences" className="space-y-4">
            <ContactPreferencesPanel 
              callRecordId={callId}
              customerName={customerName}
            />
          </TabsContent>
        </Tabs>
      </CardContent>
      
      {/* SMS Modal */}
      <SMSSender 
        isOpen={isSMSSenderOpen}
        onClose={() => setIsSMSSenderOpen(false)}
        callRecordId={callId || ''}
        customerName={customerName || ''}
      />
    </Card>
  );
};