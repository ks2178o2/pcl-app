import React, { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Upload, FileText, Calendar, X, Check, AlertTriangle } from 'lucide-react';
import { useAppointments } from '@/hooks/useAppointments';
import { useToast } from '@/hooks/use-toast';

interface Appointment {
  customer_name: string;
  appointment_date: Date;
  patient_id?: string;
  email?: string;
  phone_number?: string;
}

interface AppointmentUploadWithPreviewProps {
  onUploadComplete?: () => void;
}

export const AppointmentUploadWithPreview: React.FC<AppointmentUploadWithPreviewProps> = ({ onUploadComplete }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { appointments, loading, uploadAppointments, clearAppointments } = useAppointments();
  const [previewAppointments, setPreviewAppointments] = useState<Appointment[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parseError, setParseError] = useState<string>('');
  const { toast } = useToast();

  const parseAppointmentFile = (text: string, fileName: string): Appointment[] => {
    const isCSV = fileName.toLowerCase().endsWith('.csv');
    const isJSON = fileName.toLowerCase().endsWith('.json');

    if (!isCSV && !isJSON) {
      throw new Error('File must be either CSV or JSON format');
    }

    if (isJSON) {
      try {
        const data = JSON.parse(text);
        const appointments = Array.isArray(data) ? data : [data];
        
        return appointments.map((item: any) => {
          const customerName = item.customer_name || item.customerName || item.name || 
                              item.Customer || item['Customer Name'] || '';
          
          if (!customerName) {
            throw new Error('Missing customer name in appointment data');
          }

          const dateStr = item.appointment_date || item.appointmentDate || item.date || 
                         item.Date || item['Appointment Date'] || item.datetime || '';
          const timeStr = item.time || item.appointment_time || '';
          
          if (!dateStr) {
            throw new Error('Missing appointment date in appointment data');
          }

          const combinedDateTime = timeStr ? `${dateStr} ${timeStr}` : dateStr;
          const parsedDate = parseDate(combinedDateTime);
          if (!parsedDate) {
            throw new Error(`Invalid date format: ${combinedDateTime}`);
          }

          return {
            customer_name: customerName,
            appointment_date: parsedDate,
            patient_id: item.patient_id || item.patientid || item.id || undefined,
            email: item.email || item.email_address || undefined,
            phone_number: item.phone || item.phone_number || item.phonenumber || undefined,
          };
        });
      } catch (error) {
        throw new Error(`Invalid JSON format: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    } else {
      // CSV parsing
      const lines = text.split('\n').filter(line => line.trim());
      if (lines.length < 2) {
        throw new Error('CSV must have at least a header row and one data row');
      }

      const headers = parseCSVLine(lines[0]).map(h => h.toLowerCase().trim());
      const appointments: Appointment[] = [];

      for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i]);
        if (values.length === 0 || values.every(v => !v.trim())) continue;

        const row: any = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });

        const customerName = row['customer_name'] || row['customername'] || row['name'] || 
                            row['customer'] || row['customer name'] || '';
        
        if (!customerName) {
          throw new Error(`Missing customer name in row ${i + 1}`);
        }

        const dateStr = row['appointment_date'] || row['appointmentdate'] || row['date'] || 
                       row['appointment date'] || row['datetime'] || '';
        const timeStr = row['time'] || row['appointment_time'] || '';
        
        if (!dateStr) {
          throw new Error(`Missing appointment date in row ${i + 1}`);
        }

        const combinedDateTime = timeStr ? `${dateStr} ${timeStr}` : dateStr;
        const parsedDate = parseDate(combinedDateTime);
        if (!parsedDate) {
          throw new Error(`Invalid date format in row ${i + 1}: ${combinedDateTime}`);
        }

        appointments.push({
          customer_name: customerName,
          appointment_date: parsedDate,
          patient_id: row['patient_id'] || row['patientid'] || row['id'] || undefined,
          email: row['email'] || row['email_address'] || undefined,
          phone_number: row['phone'] || row['phone_number'] || row['phonenumber'] || undefined,
        });
      }

      return appointments;
    }
  };

  const parseCSVLine = (line: string): string[] => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current.trim());
    return result;
  };

  const parseDate = (dateTimeStr: string): Date | null => {
    const cleanStr = dateTimeStr.trim();
    if (!cleanStr) return null;
    
    // Enhanced patterns with better AM/PM handling
    const patterns = [
      // MM/DD/YYYY H:MM AM/PM (with flexible spacing)
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})\s*(\d{1,2}):(\d{2})\s*(AM|PM)$/i,
      // MM/DD/YYYY HH:MM AM/PM
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)$/i,
      // MM/DD/YYYY H:MM (24-hour)
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})$/,
      // YYYY-MM-DD HH:MM
      /^(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$/,
      // MM/DD/YYYY (date only - default to 9 AM)
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/,
      // YYYY-MM-DD (date only - default to 9 AM)
      /^(\d{4})-(\d{1,2})-(\d{1,2})$/,
    ];
    
    for (const pattern of patterns) {
      const match = cleanStr.match(pattern);
      if (match) {
        let month: number, day: number, year: number, hour = 9, minute = 0;
        
        if (pattern.source.includes('(\\d{4})') && pattern.source.indexOf('(\\d{4})') === 2) {
          // YYYY-MM-DD format
          year = parseInt(match[1]);
          month = parseInt(match[2]) - 1;
          day = parseInt(match[3]);
          if (match[4]) hour = parseInt(match[4]);
          if (match[5]) minute = parseInt(match[5]);
        } else {
          // MM/DD/YYYY format
          month = parseInt(match[1]) - 1;
          day = parseInt(match[2]);
          year = parseInt(match[3]);
          if (match[4]) hour = parseInt(match[4]);
          if (match[5]) minute = parseInt(match[5]);
        }
        
        // Handle AM/PM
        if (match[6]) {
          const ampm = match[6].toUpperCase();
          if (ampm === 'PM' && hour !== 12) {
            hour += 12;
          } else if (ampm === 'AM' && hour === 12) {
            hour = 0;
          }
        }
        
        const date = new Date(year, month, day, hour, minute);
        if (!isNaN(date.getTime())) {
          return date;
        }
      }
    }
    
    // Fallback to native Date parsing
    const nativeDate = new Date(cleanStr);
    if (!isNaN(nativeDate.getTime())) {
      return nativeDate;
    }
    
    return null;
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setParseError('');

    try {
      const text = await file.text();
      const parsed = parseAppointmentFile(text, file.name);
      setPreviewAppointments(parsed);
      setShowPreview(true);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to parse file';
      setParseError(errorMessage);
      toast({
        title: 'File parsing error',
        description: errorMessage,
        variant: 'destructive'
      });
    }

    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleConfirmUpload = async () => {
    if (!selectedFile) return;

    const success = await uploadAppointments(selectedFile);
    if (success) {
      setShowPreview(false);
      setPreviewAppointments([]);
      setSelectedFile(null);
      onUploadComplete?.();
      toast({
        title: 'Upload successful',
        description: `${previewAppointments.length} appointments uploaded successfully`,
      });
    }
  };

  const handleCancelUpload = () => {
    setShowPreview(false);
    setPreviewAppointments([]);
    setSelectedFile(null);
    setParseError('');
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleClearAppointments = async () => {
    if (appointments.length === 0) return;
    
    const confirmed = confirm(`Are you sure you want to clear all ${appointments.length} loaded appointments? This action cannot be undone.`);
    if (confirmed) {
      await clearAppointments();
      onUploadComplete?.();
    }
  };

  const formatDateTime = (date: Date) => {
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Appointments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <FileText className="h-4 w-4" />
            <AlertDescription>
              <strong>Supported formats:</strong> CSV and JSON files
              <br />
              <strong>Required fields:</strong> customer_name, appointment_date
              <br />
              <strong>Optional fields:</strong> patient_id, email, phone_number
              <br />
              <strong>Date formats:</strong> MM/DD/YYYY HH:MM AM/PM, YYYY-MM-DD HH:MM, etc.
            </AlertDescription>
          </Alert>

          {parseError && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{parseError}</AlertDescription>
            </Alert>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.json"
            onChange={handleFileSelect}
            className="hidden"
          />

          <div className="flex gap-2">
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
                variant="destructive" 
                onClick={handleClearAppointments}
                disabled={loading}
                className="flex items-center gap-2"
              >
                <X className="h-4 w-4" />
                Clear All ({appointments.length})
              </Button>
            )}
          </div>

          {appointments.length > 0 && (
            <div className="text-sm text-muted-foreground">
              <Calendar className="h-4 w-4 inline mr-1" />
              {appointments.length} appointments loaded
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Preview Appointments</DialogTitle>
          </DialogHeader>
          
          <div className="flex-1 overflow-auto">
            <div className="mb-4">
              <p className="text-sm text-muted-foreground">
                Found {previewAppointments.length} appointments in the file. Review them below and confirm to upload.
              </p>
            </div>
            
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer Name</TableHead>
                  <TableHead>Appointment Date & Time</TableHead>
                  <TableHead>Patient ID</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Phone</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {previewAppointments.map((appointment, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">
                      {appointment.customer_name}
                    </TableCell>
                    <TableCell>
                      {formatDateTime(appointment.appointment_date)}
                    </TableCell>
                    <TableCell>
                      {appointment.patient_id || '-'}
                    </TableCell>
                    <TableCell>
                      {appointment.email || '-'}
                    </TableCell>
                    <TableCell>
                      {appointment.phone_number || '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancelUpload}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button onClick={handleConfirmUpload} disabled={loading}>
              <Check className="h-4 w-4 mr-2" />
              {loading ? 'Uploading...' : `Upload ${previewAppointments.length} Appointments`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};