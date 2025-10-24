import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, Mic, Upload, Clock, User } from 'lucide-react';
import { useAppointments } from '@/hooks/useAppointments';
import { useProfile } from '@/hooks/useProfile';
import { ChunkedAudioRecorder } from '@/components/ChunkedAudioRecorder';
import { AudioUploadModal } from '@/components/AudioUploadModal';
import { useCallRecords } from '@/hooks/useCallRecords';
import { useCenterSession } from '@/hooks/useCenterSession';

interface Appointment {
  id: string;
  customer_name: string;
  appointment_date: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  patient_id?: string;
}

interface AppointmentWithStatus extends Appointment {
  status: 'upcoming' | 'current' | 'recent' | 'past';
  timeDescription: string;
}

export const AppointmentsList: React.FC = () => {
  const { appointments, loading, loadAppointments } = useAppointments();
  const { profile } = useProfile();
  const { handleChunkedRecordingComplete } = useCallRecords();
  const { activeCenter } = useCenterSession();
  const [appointmentsWithStatus, setAppointmentsWithStatus] = useState<AppointmentWithStatus[]>([]);
  const [recordingCustomer, setRecordingCustomer] = useState<string>('');
  const [recordingPatientId, setRecordingPatientId] = useState<string>('');
  const [showAudioUpload, setShowAudioUpload] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<AppointmentWithStatus | null>(null);

  useEffect(() => {
    loadAppointments();
  }, []);

  useEffect(() => {
    if (appointments.length > 0) {
      const now = new Date();
      const fourHoursAgo = new Date(now.getTime() - 4 * 60 * 60 * 1000);
      
      const processed = appointments
        .map(appointment => {
          const appointmentDate = new Date(appointment.appointment_date);
          const diffMs = appointmentDate.getTime() - now.getTime();
          const diffHours = diffMs / (1000 * 60 * 60);
          const diffMinutes = Math.abs(diffMs / (1000 * 60));

          let status: 'upcoming' | 'current' | 'recent' | 'past';
          let timeDescription: string;

          if (Math.abs(diffHours) < 0.5) {
            // Within 30 minutes
            status = 'current';
            timeDescription = diffHours > 0 ? `In ${Math.round(diffMinutes)} minutes` : `${Math.round(diffMinutes)} minutes ago`;
          } else if (diffHours > 0) {
            // Future appointment
            status = 'upcoming';
            if (diffHours < 24) {
              timeDescription = `In ${Math.round(diffHours)} hours`;
            } else {
              const diffDays = Math.round(diffHours / 24);
              timeDescription = `In ${diffDays} day${diffDays > 1 ? 's' : ''}`;
            }
          } else if (appointmentDate > fourHoursAgo) {
            // Recent past (within 4 hours)
            status = 'recent';
            timeDescription = `${Math.round(Math.abs(diffHours))} hours ago`;
          } else {
            // Older past appointment
            status = 'past';
            const diffDays = Math.round(Math.abs(diffHours) / 24);
            timeDescription = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
          }

          return {
            ...appointment,
            status,
            timeDescription
          } as AppointmentWithStatus;
        })
        .sort((a, b) => {
          // Sort by appointment date, upcoming first
          const dateA = new Date(a.appointment_date);
          const dateB = new Date(b.appointment_date);
          return dateA.getTime() - dateB.getTime();
        })
        .slice(0, 10); // Show next 10 appointments

      setAppointmentsWithStatus(processed);
    } else {
      setAppointmentsWithStatus([]);
    }
  }, [appointments]);

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'current':
        return <Badge className="bg-green-500 hover:bg-green-600">Current</Badge>;
      case 'upcoming':
        return <Badge variant="secondary">Upcoming</Badge>;
      case 'recent':
        return <Badge className="bg-orange-500 hover:bg-orange-600">Recent</Badge>;
      case 'past':
        return <Badge variant="outline">Past</Badge>;
      default:
        return null;
    }
  };

  const handleStartRecording = (customerName: string, patientId: string) => {
    setRecordingCustomer(customerName);
    setRecordingPatientId(patientId);
  };

  const handleStopRecording = () => {
    setRecordingCustomer('');
    setRecordingPatientId('');
  };

  const handleRecordingComplete = (callRecordId: string, duration: number) => {
    handleChunkedRecordingComplete(callRecordId, duration);
    setRecordingCustomer('');
    setRecordingPatientId('');
  };

  const handleUploadAudio = (appointment: AppointmentWithStatus) => {
    setSelectedAppointment(appointment);
    setShowAudioUpload(true);
  };

  const handleAudioUploadComplete = () => {
    setShowAudioUpload(false);
    setSelectedAppointment(null);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-muted-foreground">Loading appointments...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (appointmentsWithStatus.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <div className="text-lg font-medium mb-2">No appointments found</div>
            <div className="text-muted-foreground">Upload your appointment schedule to get started</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Your Schedule (Next 10)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {appointmentsWithStatus.map((appointment) => (
            <div key={appointment.id} className="border rounded-lg p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{appointment.customer_name}</span>
                    {getStatusBadge(appointment.status)}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    {formatDateTime(appointment.appointment_date)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {appointment.timeDescription}
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                {(appointment.status === 'upcoming' || appointment.status === 'current') && (
                  <>
                    {recordingCustomer === appointment.customer_name ? (
                      <div className="flex-1">
                        <ChunkedAudioRecorder
                          onRecordingComplete={handleRecordingComplete}
                          patientName={appointment.customer_name}
                          patientId={appointment.patient_id}
                          centerId={activeCenter || undefined}
                          disabled={false}
                        />
                      </div>
                    ) : (
                      <Button
                        onClick={() => handleStartRecording(appointment.customer_name, appointment.patient_id || '')}
                        className="flex items-center gap-2"
                        disabled={recordingCustomer !== '' || !activeCenter}
                      >
                        <Mic className="h-4 w-4" />
                        Start Recording
                      </Button>
                    )}
                  </>
                )}

                {appointment.status === 'recent' && (
                  <Button
                    variant="outline"
                    onClick={() => handleUploadAudio(appointment)}
                    className="flex items-center gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    Upload Audio
                  </Button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {selectedAppointment && (
        <AudioUploadModal
          open={showAudioUpload}
          onOpenChange={setShowAudioUpload}
          appointment={selectedAppointment}
          onUploadComplete={handleAudioUploadComplete}
        />
      )}
    </>
  );
};