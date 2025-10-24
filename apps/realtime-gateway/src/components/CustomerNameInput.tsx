import React, { useState } from 'react';
import { Check, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAppointments } from '@/hooks/useAppointments';
import { format, isToday, isTomorrow, isThisWeek } from 'date-fns';

interface CustomerNameInputProps {
  value: string;
  onChange: (value: string) => void;
}

export const CustomerNameInput: React.FC<CustomerNameInputProps> = ({ value, onChange }) => {
  const [open, setOpen] = useState(false);
  const [useDropdown, setUseDropdown] = useState(true);
  const { appointments } = useAppointments();

  const formatAppointmentTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const time = format(date, 'h:mm a');
    
    if (isToday(date)) {
      return `Today at ${time}`;
    } else if (isTomorrow(date)) {
      return `Tomorrow at ${time}`;
    } else if (isThisWeek(date)) {
      return `${format(date, 'EEEE')} at ${time}`;
    } else {
      return `${format(date, 'MMM d')} at ${time}`;
    }
  };

  const selectedAppointment = appointments.find(apt => apt.customer_name === value);

  if (!useDropdown || appointments.length === 0) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="customer-name">Customer Name *</Label>
          {appointments.length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setUseDropdown(true)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Select from appointments ({appointments.length})
            </Button>
          )}
        </div>
        <Input
          id="customer-name"
          placeholder="Enter customer name..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required
        />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Customer Name *</Label>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setUseDropdown(false)}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          Enter manually
        </Button>
      </div>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
          >
            {value ? (
              <div className="flex flex-col items-start">
                <span>{value}</span>
                {selectedAppointment && (
                  <span className="text-xs text-muted-foreground">
                    {formatAppointmentTime(selectedAppointment.appointment_date)}
                  </span>
                )}
              </div>
            ) : (
              "Select upcoming appointment..."
            )}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0">
          <Command>
            <CommandInput placeholder="Search appointments..." />
            <CommandList>
              <CommandEmpty>No appointments found.</CommandEmpty>
              <CommandGroup>
                {appointments.map((appointment) => (
                  <CommandItem
                    key={appointment.id}
                    value={appointment.customer_name}
                    onSelect={(currentValue) => {
                      onChange(currentValue === value ? "" : appointment.customer_name);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === appointment.customer_name ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex flex-col">
                      <span>{appointment.customer_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatAppointmentTime(appointment.appointment_date)}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
};