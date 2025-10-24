import React, { useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, Trash2, Info } from 'lucide-react';
import { useAppointments } from '@/hooks/useAppointments';
import { Alert, AlertDescription } from '@/components/ui/alert';

export const AppointmentUpload = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { loading, uploadAppointments, clearAppointments, appointments } = useAppointments();

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      console.log('No file selected');
      return;
    }

    console.log('File selected:', file.name, 'type:', file.type);
    const success = await uploadAppointments(file);
    if (success && fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleClearAppointments = async () => {
    if (appointments.length > 0 && window.confirm('Are you sure you want to clear all appointments?')) {
      await clearAppointments();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Appointment Schedule
        </CardTitle>
        <CardDescription>
          Upload your upcoming appointments to select customers during call recording
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <strong>Supported formats:</strong> CSV or JSON files with fields: name, date, time
            <br />
            <strong>CSV format:</strong> Customer Name, Date (MM/DD/YYYY), Time (HH:MM AM/PM)
            <br />
            <strong>JSON format:</strong> {`[{"name": "John Doe", "date": "01/15/2024", "time": "2:00 PM"}]`}
          </AlertDescription>
        </Alert>

        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.json,.txt"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            onClick={handleUploadClick}
            disabled={loading}
            className="flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            Upload Appointments
          </Button>
          
          {appointments.length > 0 && (
            <Button
              variant="outline"
              onClick={handleClearAppointments}
              disabled={loading}
              className="flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear All ({appointments.length})
            </Button>
          )}
        </div>

        {appointments.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {appointments.length} upcoming appointment{appointments.length !== 1 ? 's' : ''} loaded
          </div>
        )}
      </CardContent>
    </Card>
  );
};