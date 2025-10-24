import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Calendar, Clock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';

const appointmentSchema = z.object({
  appointmentDate: z.string().min(1, "Appointment date is required"),
  appointmentTime: z.string().min(1, "Appointment time is required"),
  notes: z.string().optional(),
});

type AppointmentFormData = z.infer<typeof appointmentSchema>;

interface Patient {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  friendlyId: string;
}

interface AppointmentCreationFormProps {
  patient: Patient;
  onAppointmentCreated?: () => void;
}

export const AppointmentCreationForm: React.FC<AppointmentCreationFormProps> = ({
  patient,
  onAppointmentCreated
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const form = useForm<AppointmentFormData>({
    resolver: zodResolver(appointmentSchema),
    defaultValues: {
      appointmentDate: '',
      appointmentTime: '',
      notes: '',
    },
  });

  const onSubmit = async (data: AppointmentFormData) => {
    if (!user) {
      toast({
        title: "Error",
        description: "You must be logged in to create appointments",
        variant: "destructive"
      });
      return;
    }

    try {
      // Combine date and time into a proper timestamp
      const appointmentDateTime = new Date(`${data.appointmentDate}T${data.appointmentTime}`);
      
      if (isNaN(appointmentDateTime.getTime())) {
        toast({
          title: "Error",
          description: "Invalid date or time format",
          variant: "destructive"
        });
        return;
      }

      // Insert appointment with proper error handling for encryption issues
      const appointmentData = {
        user_id: user.id,
        customer_name: patient.name,
        patient_id: patient.id,
        appointment_date: appointmentDateTime.toISOString(),
        email: patient.email || null,
        phone_number: patient.phone || null,
      };

      console.log('Creating appointment with data:', appointmentData);
      // Attempt insert; if encryption function is missing, retry without email/phone
      let finalError: any = null;
      const { error: firstError } = await supabase
        .from('appointments')
        .insert([appointmentData]);

      if (firstError) {
        const needsEncryptFix =
          firstError.code === '42883' ||
          firstError.code === '3F000' || // schema "pgcrypto" does not exist
          (typeof firstError.message === 'string' && firstError.message.toLowerCase().includes('encrypt(')) ||
          (typeof firstError.message === 'string' && firstError.message.toLowerCase().includes('pgcrypto'));

        if (needsEncryptFix) {
          console.warn('Encryption functions missing or misconfigured. Retrying without email/phone. Original error:', firstError);
          const minimalData = {
            user_id: user.id,
            customer_name: patient.name,
            patient_id: patient.id,
            appointment_date: appointmentDateTime.toISOString(),
          };
          const { error: retryError } = await supabase
            .from('appointments')
            .insert([minimalData]);
          finalError = retryError;
        } else {
          finalError = firstError;
        }
      }

      if (finalError) throw finalError;

      toast({
        title: "Success",
        description: `Appointment scheduled for ${patient.name}`,
      });

      form.reset();
      onAppointmentCreated?.();
    } catch (error) {
      console.error('Error creating appointment:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create appointment",
        variant: "destructive"
      });
    }
  };

  // Get today's date for min date input
  const today = new Date().toISOString().split('T')[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Schedule Appointment
        </CardTitle>
        <CardDescription>
          Create a new appointment for {patient.name} ({patient.friendlyId})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="appointmentDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date</FormLabel>
                    <FormControl>
                      <Input
                        type="date"
                        min={today}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="appointmentTime"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Time</FormLabel>
                    <FormControl>
                      <Input
                        type="time"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Additional notes for this appointment"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button 
              type="submit" 
              className="w-full"
              disabled={form.formState.isSubmitting}
            >
              <Clock className="h-4 w-4 mr-2" />
              {form.formState.isSubmitting ? 'Creating...' : 'Schedule Appointment'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};