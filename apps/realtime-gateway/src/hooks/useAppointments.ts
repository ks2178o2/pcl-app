import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { useToast } from '@/hooks/use-toast';

export interface Appointment {
  id: string;
  customer_name: string;
  appointment_date: string;
  created_at: string;
  updated_at: string;
  patient_id?: string;
  email?: string;
  phone_number?: string;
}

export const useAppointments = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();

  const loadAppointments = async () => {
    if (!user) return;

    try {
      setLoading(true);
      
      // Get appointments that are not more than 4 hours in the past
      const fourHoursAgo = new Date();
      fourHoursAgo.setHours(fourHoursAgo.getHours() - 4);

      const { data, error } = await supabase
        .from('appointments')
        .select('*')
        .eq('user_id', user.id)
        .gte('appointment_date', fourHoursAgo.toISOString())
        .order('appointment_date', { ascending: true });

      if (error) {
        console.error('Error loading appointments:', error);
        return;
      }

      // Decrypt sensitive data using RPC call
      const decryptedAppointments = await Promise.all(
        (data || []).map(async (appointment) => {
          try {
            // Decrypt email if it exists
            let decryptedEmail = appointment.email;
            if (appointment.email) {
              const { data: emailResult } = await supabase.rpc('decrypt_sensitive_data', {
                encrypted_data: appointment.email
              });
              decryptedEmail = emailResult || appointment.email;
            }

            // Decrypt phone if it exists
            let decryptedPhone = appointment.phone_number;
            if (appointment.phone_number) {
              const { data: phoneResult } = await supabase.rpc('decrypt_sensitive_data', {
                encrypted_data: appointment.phone_number
              });
              decryptedPhone = phoneResult || appointment.phone_number;
            }

            return {
              ...appointment,
              email: decryptedEmail,
              phone_number: decryptedPhone
            };
          } catch (decryptError) {
            console.error('Error decrypting appointment data:', decryptError);
            return appointment; // Return original data if decryption fails
          }
        })
      );

      setAppointments(decryptedAppointments);
    } catch (error) {
      console.error('Error loading appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadAppointments = async (file: File) => {
    if (!user) return false;

    try {
      setLoading(true);
      console.log('Starting file upload:', file.name, file.size, 'bytes');
      const text = await file.text();
      console.log('File content loaded, parsing...');
      const appointments = parseAppointmentFile(text, file.name);
      console.log('Parsed appointments:', appointments.length);
      
      if (appointments.length === 0) {
        toast({
          title: "No valid appointments found",
          description: "Please check your file format and try again.",
          variant: "destructive",
        });
        return false;
      }

      // Insert appointments into database
      const appointmentsToInsert = appointments.map(apt => ({
        user_id: user.id,
        customer_name: apt.customer_name,
        appointment_date: apt.appointment_date,
        patient_id: apt.patient_id || null,
        email: apt.email || null,
        phone_number: apt.phone_number || null,
      }));

      const { error } = await supabase
        .from('appointments')
        .insert(appointmentsToInsert);

      if (error) {
        console.error('Error uploading appointments:', error);
        toast({
          title: "Upload failed",
          description: "There was an error uploading your appointments.",
          variant: "destructive",
        });
        return false;
      }

      toast({
        title: "Upload successful",
        description: `${appointments.length} appointments uploaded successfully.`,
      });

      await loadAppointments();
      return true;
    } catch (error) {
      console.error('Error uploading appointments:', error);
      toast({
        title: "Upload failed",
        description: "There was an error processing your file.",
        variant: "destructive",
      });
      return false;
    } finally {
      setLoading(false);
    }
  };

  const clearAppointments = async () => {
    if (!user) return false;

    try {
      setLoading(true);
      const { error } = await supabase
        .from('appointments')
        .delete()
        .eq('user_id', user.id);

      if (error) {
        console.error('Error clearing appointments:', error);
        return false;
      }

      setAppointments([]);
      toast({
        title: "Appointments cleared",
        description: "All appointments have been removed.",
      });
      return true;
    } catch (error) {
      console.error('Error clearing appointments:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, [user]);

  return {
    appointments,
    loading,
    uploadAppointments,
    clearAppointments,
    loadAppointments,
  };
};

const parseAppointmentFile = (content: string, fileName: string): Array<{customer_name: string, appointment_date: string, patient_id?: string, email?: string, phone_number?: string}> => {
  const appointments: Array<{customer_name: string, appointment_date: string, patient_id?: string, email?: string, phone_number?: string}> = [];
  
  try {
    if (fileName.toLowerCase().endsWith('.json')) {
      const data = JSON.parse(content);
      const array = Array.isArray(data) ? data : [data];
      
      for (const item of array) {
        const name = item.name || item.customer_name || item.customername || item.customer;
        const dateTime = item.date || item.datetime || item.appointment_date;
        const time = item.time;
        const patientId = item.patient_id || item.patientid || item.id;
        const email = item.email || item.email_address;
        const phone = item.phone || item.phone_number || item.phonenumber;
        
        if (name && dateTime) {
          const combinedDateTime = time ? `${dateTime} ${time}` : dateTime;
          const date = parseFlexibleDate(combinedDateTime);
          if (date) {
            appointments.push({
              customer_name: name.trim(),
              appointment_date: date.toISOString(),
              patient_id: patientId ? String(patientId).trim() : undefined,
              email: email ? String(email).trim() : undefined,
              phone_number: phone ? String(phone).trim() : undefined,
            });
          }
        }
      }
    } else {
      // Parse CSV with header detection
      const lines = content.split('\n').filter(line => line.trim());
      if (lines.length < 2) return appointments;
      
      const headers = parseCSVLine(lines[0]).map(h => h.toLowerCase().trim());
      
      for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const values = parseCSVLine(line);
        if (values.length === 0 || values.every(v => !v.trim())) continue;
        
        const row: any = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        
        const name = row['customer_name'] || row['customername'] || row['name'] || row['customer'] || row['customer name'];
        const dateValue = row['appointment_date'] || row['appointmentdate'] || row['date'] || row['appointment date'] || row['datetime'];
        const timeValue = row['time'] || row['appointment_time'];
        const patientId = row['patient_id'] || row['patientid'] || row['id'];
        const email = row['email'] || row['email_address'];
        const phone = row['phone'] || row['phone_number'] || row['phonenumber'];
        
        if (name && dateValue) {
          // Try to parse combined date/time or separate fields
          const combinedDateTime = timeValue ? `${dateValue} ${timeValue}` : dateValue;
          const date = parseFlexibleDate(combinedDateTime);
          
          if (date) {
            appointments.push({
              customer_name: name.trim(),
              appointment_date: date.toISOString(),
              patient_id: patientId ? String(patientId).trim() : undefined,
              email: email ? String(email).trim() : undefined,
              phone_number: phone ? String(phone).trim() : undefined,
            });
          }
        }
      }
    }
  } catch (error) {
    console.error('Error parsing file:', error);
  }
  
  return appointments;
};

const parseCSVLine = (line: string): string[] => {
  const values: string[] = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  
  values.push(current);
  return values;
};

const parseFlexibleDate = (dateTimeStr: string): Date | null => {
  try {
    const cleanStr = dateTimeStr.replace(/['"]/g, '').trim();
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
  } catch (error) {
    return null;
  }
};