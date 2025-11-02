import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
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
  Phone as PhoneIcon
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { useAppointments, Appointment } from '@/hooks/useAppointments';
import { useCallRecords } from '@/hooks/useCallRecords';
import { supabase } from '@/integrations/supabase/client';
import { cn } from '@/lib/utils';

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
  const { appointments, loading: appointmentsLoading } = useAppointments();
  const { calls } = useCallRecords();
  
  const [selectedAppointment, setSelectedAppointment] = useState<SelectedAppointment | null>(null);
  const [filter, setFilter] = useState<'all' | 'consults' | 'confirmed' | 'pending'>('all');
  const [isRecording, setIsRecording] = useState(false);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!user || !profile) return;
    
    // Load appointments if not already loaded
    if (appointments.length > 0 && !selectedAppointment) {
      // Select first appointment by default
      const firstAppointment = appointments[0];
      loadPatientDetails(firstAppointment.id);
      setSelectedAppointment(firstAppointment);
    }
  }, [user, profile, appointments]);

  const loadPatientDetails = async (appointmentId: string) => {
    try {
      const appointment = appointments.find(apt => apt.id === appointmentId);
      if (!appointment) return;

      // Try to get patient info from call analyses for this customer
      const patientName = appointment.customer_name;
      
      // Get calls for this customer
      const { data: patientCalls } = await supabase
        .from('call_records')
        .select('*, call_analyses(*)')
        .eq('customer_name', patientName)
        .order('created_at', { ascending: false })
        .limit(5);

      // Extract patient info from call analyses
      let motivation = '';
      let likelyObjection = '';
      let pastInteractions = '';
      
      if (patientCalls && patientCalls.length > 0) {
        const latestAnalysis = patientCalls[0]?.call_analyses?.[0]?.analysis_data;
        
        if (latestAnalysis?.customerPersonality?.motivationCategory) {
          motivation = latestAnalysis.customerPersonality.motivationCategory;
        }
        
        if (latestAnalysis?.objections && latestAnalysis.objections.length > 0) {
          likelyObjection = latestAnalysis.objections[0].type;
        }
        
        const callCount = patientCalls.length;
        pastInteractions = `${callCount} call${callCount !== 1 ? 's' : ''}`;
      }

      // Mock patient info for now (can be enhanced with real patient data)
      const patientInfo: PatientInfo = {
        motivation: motivation || 'Wants to feel confident and look great for daughter\'s wedding in 5 months',
        likelyObjection: likelyObjection || 'Financing / Cost',
        pastInteractions: pastInteractions || '2 calls, 1 email',
      };

      setSelectedAppointment({
        ...appointment,
        patientInfo,
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

  const filteredAppointments = appointments;

  const filterCounts = {
    all: filteredAppointments.length,
    consults: filteredAppointments.length,
    confirmed: filteredAppointments.filter(apt => apt.appointment_date).length,
    pending: 0, // Mock for now
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
              <h1 className="text-3xl font-bold text-gray-900">
                Today's Patient Meeting Schedule
              </h1>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Add Meeting
              </Button>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-3 mb-4 overflow-x-auto pb-2 border-b border-gray-200">
              <button
                onClick={() => setFilter('all')}
                className={cn(
                  "shrink-0 pb-2 px-3 text-sm font-medium border-b-2 transition-colors",
                  filter === 'all'
                    ? "text-blue-600 border-blue-600 font-semibold"
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
                    ? "text-blue-600 border-blue-600 font-semibold"
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
                    ? "text-blue-600 border-blue-600 font-semibold"
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
                    ? "text-blue-600 border-blue-600 font-semibold"
                    : "text-gray-500 border-transparent hover:border-gray-300"
                )}
              >
                Pending ({filterCounts.pending})
              </button>
            </div>

            {/* Appointment List */}
            <div className="flex flex-col gap-4">
              {appointmentsLoading ? (
                <div className="text-center py-8 text-gray-500">Loading appointments...</div>
              ) : filteredAppointments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No appointments scheduled for today</div>
              ) : (
                filteredAppointments.map((appointment, idx) => {
                  const aptDate = new Date(appointment.appointment_date);
                  const timeStr = aptDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                  const isSelected = selectedAppointment?.id === appointment.id;
                  
                  return (
                    <div
                      key={appointment.id}
                      onClick={() => handleAppointmentSelect(appointment)}
                      className={cn(
                        "flex gap-4 p-4 justify-between items-start rounded-lg border transition-colors cursor-pointer",
                        isSelected
                          ? "bg-blue-50 border-blue-500 shadow-sm"
                          : "bg-white border-gray-200 hover:border-blue-200"
                      )}
                    >
                      <div className="flex items-start gap-4 flex-1">
                        <div className="flex size-7 items-center justify-center pt-1">
                          <Checkbox className="rounded border-gray-300" />
                        </div>
                        <div className="flex flex-1 flex-col justify-center gap-2">
                          <div>
                            <p className="text-base font-medium text-gray-900">
                              {timeStr} - {appointment.customer_name} - Initial Consult
                            </p>
                            {appointment.patient_id && (
                              <p className="text-sm text-gray-600">Age 48, Female</p>
                            )}
                          </div>
                          {selectedAppointment?.patientInfo && idx === 0 && (
                            <div className="flex flex-col gap-1 text-sm text-gray-600">
                              {selectedAppointment.patientInfo.motivation && (
                                <p className="flex items-start gap-2">
                                  <span>💙</span>
                                  <span>Motivation: {selectedAppointment.patientInfo.motivation}</span>
                                </p>
                              )}
                              {selectedAppointment.patientInfo.likelyObjection && (
                                <p className="flex items-start gap-2">
                                  <span>🎯</span>
                                  <span>Likely Objection: {selectedAppointment.patientInfo.likelyObjection}</span>
                                </p>
                              )}
                              {selectedAppointment.patientInfo.pastInteractions && (
                                <p className="flex items-start gap-2">
                                  <span>📝</span>
                                  <span>Past Interactions: {selectedAppointment.patientInfo.pastInteractions}</span>
                                </p>
                              )}
                            </div>
                          )}
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
                        <p className="text-blue-600 cursor-pointer hover:underline">
                          {selectedAppointment.email}
                        </p>
                      </div>
                    )}
                    {selectedAppointment.phone_number && (
                      <div className="flex items-center gap-3">
                        <PhoneIcon className="h-5 w-5 text-gray-600" />
                        <p className="text-blue-600 cursor-pointer hover:underline">
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
                        : "bg-blue-600 hover:bg-blue-700 text-white"
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

