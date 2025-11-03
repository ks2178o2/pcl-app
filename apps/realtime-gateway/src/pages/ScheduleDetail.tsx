import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { SalesDashboardSidebar } from '@/components/SalesDashboardSidebar';
import { 
  Plus,
  MoreVertical,
  Calendar as CalendarIcon,
  Mic,
  StopCircle,
  Mail,
  Phone,
  Cake,
  Mail as MailIcon,
  Phone as PhoneIcon,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { useAppointments, Appointment } from '@/hooks/useAppointments';
import { useCallRecords } from '@/hooks/useCallRecords';
import { supabase } from '@/integrations/supabase/client';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface PatientInfo {
  dob?: string;
  age?: number;
  gender?: string;
  motivation?: string;
  likelyObjection?: string;
  pastInteractions?: string;
  referred?: boolean;
  highIntent?: boolean;
}

interface SelectedAppointment extends Appointment {
  patientInfo?: PatientInfo;
  calls?: any[];
  emails?: any[];
}

const ScheduleDetail = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { profile } = useProfile();
  const { appointments, loading: appointmentsLoading, loadAppointments } = useAppointments();
  const { calls, loadCalls } = useCallRecords();
  
  const [selectedAppointment, setSelectedAppointment] = useState<SelectedAppointment | null>(null);
  const [filter, setFilter] = useState<'all' | 'consults' | 'confirmed' | 'pending' | 'no-show'>('all');
  const [isRecording, setIsRecording] = useState(false);
  const [notes, setNotes] = useState('');
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [patientInfoMap, setPatientInfoMap] = useState<Map<string, PatientInfo>>(new Map());

  const loadPatientDetailsForAllAppointments = async () => {
    if (!appointments || appointments.length === 0) return;

    const newPatientInfoMap = new Map<string, PatientInfo>();

    // Load patient details for all appointments in parallel
    await Promise.all(
      appointments.map(async (appointment) => {
        const patientName = appointment.customer_name;
        
        try {
          // Get calls for this customer
          const { data: patientCalls } = await supabase
            .from('call_records')
            .select('*, call_analyses(*)')
            .eq('customer_name', patientName)
            .eq('user_id', user?.id || '')
            .order('start_time', { ascending: false })
            .limit(10);

          // Extract patient info from call analyses (CNS updates based on latest interactions)
          let motivation = '';
          let likelyObjection = '';
          let pastInteractions = '';
          
          // Get patient interactions from the patient_interactions table
          const { data: patientInteractions } = await supabase
            .from('patient_interactions')
            .select('interaction_type, interaction_date, notes, metadata')
            .eq('patient_name', patientName)
            .eq('user_id', user?.id || '')
            .eq('organization_id', profile?.organization_id || '')
            .order('interaction_date', { ascending: false });
          
          // Get appointments for this patient (for reference)
          const { data: patientAppointments } = await supabase
            .from('appointments')
            .select('id, created_at, type, status')
            .eq('customer_name', patientName)
            .eq('user_id', user?.id || '')
            .order('created_at', { ascending: false });
          
          if (patientCalls && patientCalls.length > 0) {
            // Get the most recent analysis (CNS uses latest interaction data)
            const latestAnalysis = patientCalls[0]?.call_analyses?.[0]?.analysis_data;
            
            if (latestAnalysis?.customerPersonality?.motivationCategory) {
              motivation = latestAnalysis.customerPersonality.motivationCategory;
            }
            
            if (latestAnalysis?.objections && latestAnalysis.objections.length > 0) {
              // Get the most recent objection type
              likelyObjection = latestAnalysis.objections[0].type;
            }
          }
          
          // Build interaction history from patient_interactions table
          // Count interactions by type (excluding current appointment)
          const interactionCounts: Record<string, number> = {};
          
          if (patientInteractions && patientInteractions.length > 0) {
            // Filter out the current appointment's interaction if it exists
            const relevantInteractions = patientInteractions.filter(interaction => {
              // Exclude current appointment interactions (they'll be counted separately)
              const isCurrentAppointment = interaction.metadata?.type === appointment.type &&
                                          new Date(interaction.interaction_date).toDateString() === 
                                          new Date(appointment.appointment_date).toDateString();
              return !isCurrentAppointment;
            });
            
            relevantInteractions.forEach(interaction => {
              const type = interaction.interaction_type;
              interactionCounts[type] = (interactionCounts[type] || 0) + 1;
            });
          }
          
          // Build readable interaction history string
          const interactionParts: string[] = [];
          
          // Map interaction types to readable phrases
          const typePhrases: Record<string, string> = {
            'call': 'call center conversation',
            'email': 'email exchange',
            'sms': 'SMS exchange',
            'webform': 'webform submission',
            'walk_in': 'walk-in visit',
            'online_inquiry': 'online inquiry',
            'referral': 'referral intake',
            'social_media': 'social media contact',
            'appointment': 'appointment',
            'consultation': 'consultation',
            'follow_up': 'follow-up visit'
          };
          
          // Add interactions in order (most common first)
          const sortedTypes = Object.entries(interactionCounts)
            .sort((a, b) => b[1] - a[1]);
          
          sortedTypes.forEach(([type, count]) => {
            const phrase = typePhrases[type] || type;
            if (count === 1) {
              interactionParts.push(`1 ${phrase}`);
            } else {
              // Handle pluralization correctly
              const pluralPhrase = type === 'follow_up' ? 'follow-up visits' :
                                  type === 'walk_in' ? 'walk-in visits' :
                                  type === 'online_inquiry' ? 'online inquiries' :
                                  type === 'social_media' ? 'social media contacts' :
                                  type === 'webform' ? 'webform submissions' :
                                  `${phrase}s`;
              interactionParts.push(`${count} ${pluralPhrase}`);
            }
          });
          
          // If no interactions found, show default
          if (interactionParts.length === 0) {
            pastInteractions = 'No prior interactions';
          } else {
            // Format as comma-separated list with proper grammar
            if (interactionParts.length === 1) {
              pastInteractions = interactionParts[0];
            } else if (interactionParts.length === 2) {
              pastInteractions = `${interactionParts[0]} and ${interactionParts[1]}`;
            } else {
              const last = interactionParts.pop();
              pastInteractions = `${interactionParts.join(', ')}, and ${last}`;
            }
          }
          
          // Fallback if no call data for motivation/objection
          if (!motivation) {
            motivation = 'Initial interest - needs assessment';
          }
          if (!likelyObjection) {
            likelyObjection = 'Unknown - to be determined';
          }

          const patientInfo: PatientInfo = {
            motivation,
            likelyObjection,
            pastInteractions,
          };

          newPatientInfoMap.set(appointment.id, patientInfo);
        } catch (error) {
          console.error(`Error loading patient details for ${patientName}:`, error);
          // Set default info on error
          newPatientInfoMap.set(appointment.id, {
            motivation: 'Loading...',
            likelyObjection: 'Loading...',
            pastInteractions: 'Loading...',
          });
        }
      })
    );

    setPatientInfoMap(newPatientInfoMap);
  };

  const loadPatientDetails = async (appointmentId: string) => {
    try {
      const appointment = appointments.find(apt => apt.id === appointmentId);
      if (!appointment) return;

      // Get patient info from the map
      const patientInfo = patientInfoMap.get(appointmentId);

      // Get calls for the right panel
      const patientName = appointment.customer_name;
      const { data: patientCalls } = await supabase
        .from('call_records')
        .select('*, call_analyses(*)')
        .eq('customer_name', patientName)
        .eq('user_id', user?.id || '')
        .order('start_time', { ascending: false })
        .limit(10);

      setSelectedAppointment({
        ...appointment,
        patientInfo: patientInfo || undefined,
        calls: patientCalls || [],
      });
    } catch (error) {
      console.error('Error loading patient details:', error);
    }
  };

  const handleAppointmentSelect = async (appointment: Appointment) => {
    setSelectedAppointment(appointment);
    await loadPatientDetails(appointment.id);
  };

  const handleStartConsult = () => {
    setIsRecording(true);
    // TODO: Start recording for this appointment
    // Navigate to recording or start recording service
  };

  const handleFinishRecording = () => {
    setIsRecording(false);
    // TODO: Stop recording and save
  };

  // Load appointments when date changes
  useEffect(() => {
    if (!user || !profile) return;
    
    // Load recent calls
    loadCalls(50);
    
    // Load appointments for selected date
    loadAppointments(selectedDate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, profile, selectedDate]);

  // Load patient details for all appointments when appointments change
  useEffect(() => {
    if (appointments.length > 0 && user) {
      loadPatientDetailsForAllAppointments();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appointments, user]);

  // Select first appointment when appointments are loaded
  useEffect(() => {
    if (appointments.length > 0 && !selectedAppointment) {
      const firstAppointment = appointments[0];
      loadPatientDetails(firstAppointment.id);
      setSelectedAppointment(firstAppointment);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appointments, patientInfoMap]);

  // Filter appointments based on selected filter
  const filteredAppointments = appointments.filter(apt => {
    if (filter === 'all') return true;
    if (filter === 'confirmed') return apt.status?.toLowerCase() === 'confirmed';
    if (filter === 'pending') return apt.status?.toLowerCase() === 'pending';
    if (filter === 'no-show') return apt.status?.toLowerCase() === 'no show';
    return true;
  });

  const filterCounts = {
    all: appointments.length,
    consults: appointments.length,
    confirmed: appointments.filter(apt => apt.status?.toLowerCase() === 'confirmed').length,
    pending: appointments.filter(apt => apt.status?.toLowerCase() === 'pending').length,
    'no-show': appointments.filter(apt => apt.status?.toLowerCase() === 'no show').length,
  };

  const handleDateChange = (newDate: Date) => {
    setSelectedDate(newDate);
    setSelectedAppointment(null); // Clear selection when changing dates
  };

  const handlePreviousDay = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() - 1);
    handleDateChange(newDate);
  };

  const handleNextDay = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + 1);
    handleDateChange(newDate);
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
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Content Area with Two Columns */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Panel - Appointment List */}
          <div className="flex-1 flex flex-col p-6 overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-4">
                {/* Calendar Navigation */}
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={handlePreviousDay}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" size="sm" className="min-w-[140px]">
                        <CalendarIcon className="h-4 w-4 mr-2" />
                        {format(selectedDate, 'MMM d, yyyy')}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={selectedDate}
                        onSelect={(date) => date && handleDateChange(date)}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  
                  <Button variant="outline" size="sm" onClick={handleNextDay}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Meeting
              </Button>
            </div>
            
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              {format(selectedDate, 'EEEE') === format(new Date(), 'EEEE') && 
               format(selectedDate, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')
                ? "Today's Patient Meeting Schedule"
                : `${format(selectedDate, 'EEEE')}'s Patient Meeting Schedule`}
            </h2>

            {/* Filter Tabs */}
            <div className="flex gap-3 mb-4 overflow-x-auto pb-2 border-b border-gray-200">
              <button
                onClick={() => setFilter('all')}
                className={cn(
                  "shrink-0 pb-2 px-3 text-sm font-medium border-b-2 transition-colors",
                  filter === 'all'
                    ? "text-primary border-primary font-semibold"
                    : "text-gray-500 border-transparent hover:border-gray-300"
                )}
              >
                All Meetings ({filterCounts.all})
              </button>
              <button
                onClick={() => setFilter('consults')}
                className={cn(
                  "shrink-0 pb-2 px-3 text-sm font-medium border-b-2 transition-colors",
                  filter === 'consults'
                    ? "text-primary border-primary font-semibold"
                    : "text-gray-500 border-transparent hover:border-gray-300"
                )}
              >
                Consults ({filterCounts.consults})
              </button>
              <button
                onClick={() => setFilter('confirmed')}
                className={cn(
                  "shrink-0 pb-2 px-3 text-sm font-medium border-b-2 transition-colors",
                  filter === 'confirmed'
                    ? "text-primary border-primary font-semibold"
                    : "text-gray-500 border-transparent hover:border-gray-300"
                )}
              >
                Confirmed ({filterCounts.confirmed})
              </button>
              <button
                onClick={() => setFilter('pending')}
                className={cn(
                  "shrink-0 pb-2 px-3 text-sm font-medium border-b-2 transition-colors",
                  filter === 'pending'
                    ? "text-primary border-primary font-semibold"
                    : "text-gray-500 border-transparent hover:border-gray-300"
                )}
              >
                Pending ({filterCounts.pending})
              </button>
              <button
                onClick={() => setFilter('no-show')}
                className={cn(
                  "shrink-0 pb-2 px-3 text-sm font-medium border-b-2 transition-colors",
                  filter === 'no-show'
                    ? "text-primary border-primary font-semibold"
                    : "text-gray-500 border-transparent hover:border-gray-300"
                )}
              >
                No Shows ({filterCounts['no-show']})
              </button>
            </div>

            {/* Appointment List */}
            <div className="flex flex-col gap-4">
              {appointmentsLoading ? (
                <div className="text-center py-8 text-gray-500">Loading appointments...</div>
              ) : filteredAppointments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No appointments scheduled for {format(selectedDate, 'MMMM d, yyyy')}
                </div>
              ) : (
                filteredAppointments.map((appointment, idx) => {
                  // Parse the appointment date - Supabase returns timestamps as ISO strings
                  // The database stores them in UTC, so we need to ensure proper parsing
                  const appointmentDateStr = appointment.appointment_date;
                  
                  // Ensure the date string is treated as UTC if it doesn't have timezone info
                  // Supabase should return ISO strings with 'Z' or timezone offset, but be defensive
                  let aptDate: Date;
                  if (!appointmentDateStr.includes('T')) {
                    // Just a date, append time and timezone
                    aptDate = new Date(appointmentDateStr + 'T00:00:00Z');
                  } else if (appointmentDateStr.endsWith('Z') || appointmentDateStr.includes('+') || appointmentDateStr.includes('-', 10)) {
                    // Has timezone info (Z for UTC, or +/- for offset)
                    aptDate = new Date(appointmentDateStr);
                  } else {
                    // No timezone info, treat as UTC (Supabase stores in UTC)
                    aptDate = new Date(appointmentDateStr + 'Z');
                  }
                  
                  // Debug: Log first appointment to check parsing
                  if (idx === 0) {
                    const pacificTime = aptDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Los_Angeles' });
                    const utcTime = aptDate.toUTCString();
                    console.log('🕐 Appointment date parsing:');
                    console.log('  Raw string:', appointmentDateStr);
                    console.log('  Parsed ISO:', aptDate.toISOString());
                    console.log('  Pacific time:', pacificTime);
                    console.log('  UTC time:', utcTime);
                    console.log('  Customer:', appointment.customer_name);
                  }
                  
                  // Use user's timezone from settings, default to Pacific time if not set
                  const displayTimezone = profile?.timezone || 'America/Los_Angeles';
                  const timeStr = aptDate.toLocaleTimeString('en-US', { 
                    hour: 'numeric', 
                    minute: '2-digit',
                    timeZone: displayTimezone
                  });
                  const isSelected = selectedAppointment?.id === appointment.id;
                  
                  return (
                    <div
                      key={appointment.id}
                      onClick={() => handleAppointmentSelect(appointment)}
                      className={cn(
                        "flex gap-4 p-4 justify-between items-start rounded-lg border transition-colors cursor-pointer",
                        isSelected
                          ? "bg-accent border-primary shadow-sm"
                          : "bg-white border-gray-200 hover:border-primary/30"
                      )}
                    >
                      <div className="flex items-start gap-4 flex-1">
                        <div className="flex size-7 items-center justify-center pt-1">
                          <Checkbox className="rounded border-gray-300" />
                        </div>
                        <div className="flex flex-1 flex-col justify-center gap-2">
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="text-base font-medium text-gray-900">
                                {timeStr} - {appointment.customer_name} - {appointment.type || 'Initial Consult'}
                              </p>
                              {appointment.status && (
                                <Badge 
                                  variant={
                                    appointment.status.toLowerCase() === 'confirmed' ? 'default' :
                                    appointment.status.toLowerCase() === 'pending' ? 'secondary' :
                                    appointment.status.toLowerCase() === 'no show' ? 'destructive' :
                                    'outline'
                                  }
                                  className={cn(
                                    appointment.status.toLowerCase() === 'confirmed' && 'bg-green-100 text-green-800 hover:bg-green-100',
                                    appointment.status.toLowerCase() === 'pending' && 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100',
                                    appointment.status.toLowerCase() === 'no show' && 'bg-red-100 text-red-800 hover:bg-red-100',
                                    appointment.status.toLowerCase() === 'scheduled' && 'bg-blue-100 text-blue-800 hover:bg-blue-100'
                                  )}
                                >
                                  {appointment.status}
                                </Badge>
                              )}
                            </div>
                            {appointment.patient_id && (
                              <p className="text-sm text-gray-600">Age 48, Female</p>
                            )}
                            {appointment.notes && (
                              <p className="text-sm text-gray-600 mt-1 italic">{appointment.notes}</p>
                            )}
                          </div>
                          {/* Show patient insights for follow-up appointments or selected appointment */}
                          {(() => {
                            const isFollowUp = appointment.type?.toLowerCase() === 'follow-up';
                            const shouldShowDetails = isFollowUp || (selectedAppointment?.id === appointment.id);
                            const patientInfo = patientInfoMap.get(appointment.id);
                            
                            return shouldShowDetails && patientInfo ? (
                              <div className="flex flex-col gap-1 text-sm text-gray-600 mt-2">
                                {patientInfo.motivation && (
                                  <p className="flex items-start gap-2">
                                    <span>💙</span>
                                    <span>Motivation: {patientInfo.motivation}</span>
                                  </p>
                                )}
                                {patientInfo.likelyObjection && (
                                  <p className="flex items-start gap-2">
                                    <span>🎯</span>
                                    <span>Likely Objection: {patientInfo.likelyObjection}</span>
                                  </p>
                                )}
                                {patientInfo.pastInteractions && (
                                  <p className="flex items-start gap-2">
                                    <span>📝</span>
                                    <span>Past Interactions: {patientInfo.pastInteractions}</span>
                                  </p>
                                )}
                              </div>
                            ) : null;
                          })()}
                        </div>
                      </div>
                      <div className="shrink-0 flex items-center gap-4 pt-1">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <CalendarIcon className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel - Patient Details */}
          <aside className="w-[380px] flex-shrink-0 border-l border-gray-200 bg-white p-6 flex flex-col gap-6 overflow-y-auto">
            {selectedAppointment ? (
              <>
                <div className="flex flex-col">
                  <h2 className="text-xl font-bold text-gray-900">
                    {selectedAppointment.customer_name}
                  </h2>
                  <p className="text-gray-600">Initial Consult Details</p>
                </div>

                {/* Patient Info */}
                <div className="flex flex-col gap-4">
                  <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                    Patient Info
                  </h3>
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3">
                      <Cake className="h-5 w-5 text-gray-600" />
                      <p className="text-gray-900">DOB: 03/15/1976 (Age 48)</p>
                    </div>
                    {selectedAppointment.email && (
                      <div className="flex items-center gap-3">
                        <MailIcon className="h-5 w-5 text-gray-600" />
                        <p className="text-primary cursor-pointer hover:underline">
                          {selectedAppointment.email}
                        </p>
                      </div>
                    )}
                    {selectedAppointment.phone_number && (
                      <div className="flex items-center gap-3">
                        <PhoneIcon className="h-5 w-5 text-gray-600" />
                        <p className="text-primary cursor-pointer hover:underline">
                          {selectedAppointment.phone_number}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Start Consult Button */}
                <div className="flex gap-2">
                  <button
                    onClick={isRecording ? handleFinishRecording : handleStartConsult}
                      className={cn(
                        "flex-1 flex items-center justify-center rounded-lg h-10 px-4 text-sm font-bold transition-colors",
                        isRecording
                          ? "bg-red-600 hover:bg-red-700 text-white"
                          : "bg-primary hover:opacity-90 text-white"
                      )}
                  >
                    {isRecording ? (
                      <>
                        <StopCircle className="h-4 w-4 mr-2" />
                        Finish Recording
                      </>
                    ) : (
                      <>
                        <Mic className="h-4 w-4 mr-2" />
                        Start Consult
                      </>
                    )}
                  </button>
                </div>

                {/* Patient History & Notes */}
                <div className="flex flex-col gap-4 mt-2 flex-1">
                  <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                    Patient History & Notes
                  </h3>
                  <div className="flex-1 rounded-lg border border-gray-200 bg-gray-50 p-3">
                    <Textarea
                      className="w-full bg-transparent border-0 focus:ring-0 p-1 text-sm resize-none min-h-[60px]"
                      placeholder="Add a new note..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                    />
                  </div>
                  <div className="flex flex-col gap-4">
                    {selectedAppointment.calls && selectedAppointment.calls.length > 0 ? (
                      selectedAppointment.calls.map((call: any, idx: number) => {
                        const callDate = new Date(call.created_at);
                        return (
                          <div key={idx} className="flex gap-3">
                            <div className="flex items-center justify-center size-8 rounded-full bg-blue-100 flex-shrink-0">
                              <Phone className="h-4 w-4 text-blue-600" />
                            </div>
                            <div>
                              <p className="text-sm text-gray-900">
                                {call.transcript || 'Call with patient'}
                              </p>
                              <p className="text-xs text-gray-600">
                                {callDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </p>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-sm text-gray-500 text-center py-4">
                        No past interactions
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Select an appointment to view details
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
};

export default ScheduleDetail;

