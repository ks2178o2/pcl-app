import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { useProfile } from './useProfile';
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
  status?: string;
  notes?: string;
  type?: string;
  duration_minutes?: number;
}

// Note: The decrypt_sensitive_data function should be created in the database
// Run create_encryption_functions.sql in your Supabase SQL Editor

export const useAppointments = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { profile } = useProfile();
  const { toast } = useToast();

  const loadAppointments = async (targetDate?: Date) => {
    if (!user) return;

    try {
      setLoading(true);
      
      // Get appointments for the specified date (default: today)
      // Use user's timezone from settings, default to Pacific time if not set
      const userTimezone = profile?.timezone || 'America/Los_Angeles';
      const dateToUse = targetDate || new Date();
      
      // Get date components in user's timezone
      const userDateStr = dateToUse.toLocaleDateString('en-US', { 
        timeZone: userTimezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
      const [month, day, year] = userDateStr.split('/').map(Number);
      
      // Create date string in YYYY-MM-DD format
      const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      
      // Create start and end of day in user's timezone, then convert to UTC for query
      // Method: Create a string representing midnight in user's TZ, then parse it to get UTC equivalent
      // We'll create dates and test what they represent in user's TZ until we find midnight
      const tzFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: userTimezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
      
      // Start with a reasonable guess: UTC midnight for this date
      // Then adjust until we find what UTC time shows as midnight in user's TZ
      let dayStartUTC = new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0));
      
      // Get what this UTC time represents in user's TZ
      let tzParts = tzFormatter.formatToParts(dayStartUTC);
      let tzHour = parseInt(tzParts.find(p => p.type === 'hour')?.value || '0');
      let tzDayFromParts = parseInt(tzParts.find(p => p.type === 'day')?.value || String(day));
      let tzMonthFromParts = parseInt(tzParts.find(p => p.type === 'month')?.value || String(month));
      let tzYearFromParts = parseInt(tzParts.find(p => p.type === 'year')?.value || String(year));
      
      // If UTC midnight doesn't show as midnight in user's TZ, adjust
      // If user's TZ shows hour X when UTC is midnight, then user's midnight is at UTC hour (24-X) on same/adjacent day
      if (tzHour !== 0 || tzDayFromParts !== day || tzMonthFromParts !== month || tzYearFromParts !== year) {
        // Calculate offset: if UTC shows as hour X in user's TZ, adjust by X hours
        // If tzDay is different, also adjust day
        if (tzDayFromParts < day || (tzDayFromParts === day && tzHour > 12)) {
          // User's TZ is ahead of UTC (UTC midnight = earlier day/time in user's TZ)
          // So user's midnight = later UTC time (add hours)
          dayStartUTC = new Date(Date.UTC(year, month - 1, day, tzHour, 0, 0, 0));
        } else {
          // User's TZ is behind UTC
          // Adjust backwards
          const hoursBack = 24 - tzHour;
          dayStartUTC = new Date(Date.UTC(year, month - 1, day - 1, hoursBack, 0, 0, 0));
        }
        
        // Verify by checking one more time
        tzParts = tzFormatter.formatToParts(dayStartUTC);
        const verifyHour = parseInt(tzParts.find(p => p.type === 'hour')?.value || '0');
        const verifyDay = parseInt(tzParts.find(p => p.type === 'day')?.value || String(day));
        
        // If still not correct, use a binary search approach or just iterate
        if (verifyHour !== 0 || verifyDay !== day) {
          // Fallback: iterate to find correct time (should rarely happen)
          for (let h = 0; h < 24; h++) {
            const testDate = new Date(Date.UTC(year, month - 1, day, h, 0, 0, 0));
            const testParts = tzFormatter.formatToParts(testDate);
            const testHour = parseInt(testParts.find(p => p.type === 'hour')?.value || '0');
            const testDay = parseInt(testParts.find(p => p.type === 'day')?.value || String(day));
            const testMonth = parseInt(testParts.find(p => p.type === 'month')?.value || String(month));
            const testYear = parseInt(testParts.find(p => p.type === 'year')?.value || String(year));
            
            if (testHour === 0 && testDay === day && testMonth === month && testYear === year) {
              dayStartUTC = testDate;
              break;
            }
          }
        }
      }
      
      // End of day is start of next day minus 1ms
      const dayEndUTC = new Date(dayStartUTC);
      dayEndUTC.setUTCDate(dayEndUTC.getUTCDate() + 1);
      dayEndUTC.setUTCMilliseconds(-1);
      
      console.log('📅 Loading appointments for date:', {
        targetDate: dateToUse.toLocaleDateString(),
        userTimezone,
        userDate: userDateStr,
        utcRange: `${dayStartUTC.toISOString()} to ${dayEndUTC.toISOString()}`
      });

      const { data, error } = await supabase
        .from('appointments')
        .select('*')
        .eq('user_id', user.id)
        .gte('appointment_date', dayStartUTC.toISOString())
        .lt('appointment_date', dayEndUTC.toISOString())
        .order('appointment_date', { ascending: true });
      
      console.log('📊 Found appointments:', data?.length || 0);

      if (error) {
        console.error('Error loading appointments:', error);
        return;
      }

      // ===================================================================
      // TODO: ENCRYPTION/DECRYPTION - TEMPORARILY DISABLED FOR TESTING
      // ===================================================================
      // The encrypt/decrypt mechanisms have been commented out to allow
      // continued testing. See ENCRYPTION_TODO.md for details on:
      // - Re-enabling encryption on insert/update
      // - Re-enabling decryption on read
      // - Testing the encryption functions thoroughly
      // - Setting production encryption keys
      // ===================================================================
      
      // Decrypt sensitive data using RPC call with timeout
      // DISABLED: const decryptWithTimeout = async (encrypted: string, timeoutMs = 5000): Promise<string | null> => {
      //   if (!encrypted) return null;
      //   
      //   try {
      //     const timeoutPromise = new Promise<null>((resolve) => {
      //       setTimeout(() => resolve(null), timeoutMs);
      //     });
      //     
      //     const decryptPromise = supabase.rpc('decrypt_sensitive_data', {
      //       encrypted_data: encrypted
      //     }).then(({ data, error }) => {
      //       if (error) {
      //         console.warn('Decrypt error:', error.message);
      //         return null;
      //       }
      //       return data;
      //     });
      //     
      //     const result = await Promise.race([decryptPromise, timeoutPromise]);
      //     return result;
      //   } catch (error: any) {
      //     console.warn('Decrypt exception:', error?.message || error);
      //     return null;
      //   }
      // };

      // DISABLED: console.log('🔓 Decrypting', data?.length || 0, 'appointments...');
      // DISABLED: const decryptedAppointments = await Promise.all(
      //   (data || []).map(async (appointment: any) => {
      //     try {
      //       let decryptedEmail = appointment.customer_email || appointment.email;
      //       if (decryptedEmail) {
      //         const emailResult = await decryptWithTimeout(decryptedEmail);
      //         decryptedEmail = emailResult || decryptedEmail;
      //       }
      //       let decryptedPhone = appointment.customer_phone || appointment.phone_number;
      //       if (decryptedPhone) {
      //         const phoneResult = await decryptWithTimeout(decryptedPhone);
      //         decryptedPhone = phoneResult || decryptedPhone;
      //       }
      //       return {
      //         ...appointment,
      //         email: decryptedEmail,
      //         phone_number: decryptedPhone
      //       };
      //     } catch (decryptError) {
      //       console.error('Error decrypting appointment data:', decryptError);
      //       return {
      //         ...appointment,
      //         email: appointment.customer_email || appointment.email,
      //         phone_number: appointment.customer_phone || appointment.phone_number
      //       };
      //     }
      //   })
      // );

      // Use appointments as-is without decryption
      const appointmentsToSet = (data || []).map((appointment: any) => ({
        ...appointment,
        email: appointment.customer_email || appointment.email,
        phone_number: appointment.customer_phone || appointment.phone_number
      }));

      console.log('✅ Setting', appointmentsToSet.length, 'appointments (decryption disabled)');
      setAppointments(appointmentsToSet);
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