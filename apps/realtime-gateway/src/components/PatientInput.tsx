import React, { useState } from 'react';
import { Check, ChevronsUpDown, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useAppointments } from '@/hooks/useAppointments';
import { usePatients } from '@/hooks/usePatients';
import { usePatientSearch } from '@/hooks/usePatientSearch';
import { format, isToday, isTomorrow, isThisWeek } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
interface PatientInputProps {
  value: {
    id?: string;
    name: string;
  };
  onChange: (value: {
    id?: string;
    name: string;
  }) => void;
}
export const PatientInput: React.FC<PatientInputProps> = ({
  value,
  onChange
}) => {
  const [open, setOpen] = useState(false);
  const [useDropdown, setUseDropdown] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newPatientName, setNewPatientName] = useState('');
  const [newPatientEmail, setNewPatientEmail] = useState('');
  const [newPatientPhone, setNewPatientPhone] = useState('');
  const {
    appointments
  } = useAppointments();
  const {
    patients,
    createPatient,
    loading
  } = usePatients();
  const { toast } = useToast();
  const { results: searchResults, search, clear: clearSearch } = usePatientSearch();
  const [query, setQuery] = useState('');

  const handleSearchSubmit = async () => {
    const parts = query.trim().split(/\s+/);
    if (parts.length < 2 || parts[0].length < 3 || parts[1].length < 3) {
      toast({
        title: 'Enter full name',
        description: 'Type at least 3 letters of first and last name, then press Enter.',
      });
      return;
    }
    await search(query);
  };
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
  const selectedPatient = patients.find(p => p.id === value.id);
  const selectedAppointment = appointments.find(apt => apt.customer_name === value.name);
  const handleCreatePatient = async () => {
    if (!newPatientName.trim()) {
      toast({
        title: "Error",
        description: "Patient name is required",
        variant: "destructive"
      });
      return;
    }
    try {
      const patient = await createPatient({
        name: newPatientName.trim(),
        email: newPatientEmail.trim() || undefined,
        phone: newPatientPhone.trim() || undefined
      });
      onChange({ id: patient.id, name: patient.name });
      setShowCreateDialog(false);
      setNewPatientName('');
      setNewPatientEmail('');
      setNewPatientPhone('');
      setQuery('');
      clearSearch();
      toast({ title: 'Success', description: 'Patient created successfully' });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create patient",
        variant: "destructive"
      });
    }
  };
  if (!useDropdown || appointments.length === 0 && patients.length === 0) {
    return <div className="space-y-2">
        <div className="flex items-center justify-between my-[5px]">
          <Label htmlFor="patient-name">Patient Name *</Label>
          <div className="flex gap-2">
            {(appointments.length > 0 || patients.length > 0) && <Button type="button" variant="ghost" size="sm" onClick={() => setUseDropdown(true)} className="text-xs text-muted-foreground hover:text-foreground">
                Select from list ({appointments.length + patients.length})
              </Button>}
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button type="button" variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
                  <Plus className="h-3 w-3 mr-1" />
                  New Patient
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Patient</DialogTitle>
                  <DialogDescription>
                    Add a new patient to your list.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="new-patient-name">Patient Name *</Label>
                    <Input id="new-patient-name" value={newPatientName} onChange={e => setNewPatientName(e.target.value)} placeholder="Enter patient name..." />
                  </div>
                  <div>
                    <Label htmlFor="new-patient-email">Email</Label>
                    <Input id="new-patient-email" type="email" value={newPatientEmail} onChange={e => setNewPatientEmail(e.target.value)} placeholder="Enter email address..." />
                  </div>
                  <div>
                    <Label htmlFor="new-patient-phone">Phone</Label>
                    <Input id="new-patient-phone" type="tel" value={newPatientPhone} onChange={e => setNewPatientPhone(e.target.value)} placeholder="Enter phone number..." />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreatePatient} disabled={loading}>
                    Create Patient
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
        <Input id="patient-name" placeholder="Enter patient name..." value={value.name} onChange={e => onChange({
        id: undefined,
        name: e.target.value
      })} required />
      </div>;
  }
  const allOptions = [...patients.map(p => ({
    type: 'patient',
    ...p
  })), ...appointments.map(apt => ({
    type: 'appointment',
    id: apt.id,
    name: apt.customer_name,
    appointment_date: apt.appointment_date
  }))];
  return <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Patient Name *</Label>
        <div className="flex gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={() => setUseDropdown(false)} className="text-xs text-muted-foreground hover:text-foreground">
            Enter manually
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button type="button" variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
                <Plus className="h-3 w-3 mr-1" />
                New Patient
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Patient</DialogTitle>
                <DialogDescription>
                  Add a new patient to your list.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="new-patient-name">Patient Name *</Label>
                  <Input id="new-patient-name" value={newPatientName} onChange={e => setNewPatientName(e.target.value)} placeholder="Enter patient name..." />
                </div>
                <div>
                  <Label htmlFor="new-patient-email">Email</Label>
                  <Input id="new-patient-email" type="email" value={newPatientEmail} onChange={e => setNewPatientEmail(e.target.value)} placeholder="Enter email address..." />
                </div>
                <div>
                  <Label htmlFor="new-patient-phone">Phone</Label>
                  <Input id="new-patient-phone" type="tel" value={newPatientPhone} onChange={e => setNewPatientPhone(e.target.value)} placeholder="Enter phone number..." />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreatePatient} disabled={loading}>
                  Create Patient
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open} className="w-full justify-between">
            {value.name ? <div className="flex flex-col items-start">
                <span>{value.name}</span>
                {selectedAppointment && <span className="text-xs text-muted-foreground">
                    {formatAppointmentTime(selectedAppointment.appointment_date)}
                  </span>}
                {selectedPatient && <span className="text-xs text-muted-foreground">
                    ID: {selectedPatient.friendlyId}
                  </span>}
              </div> : "Select patient or upcoming appointment..."}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0">
          <Command>
            <CommandInput
              placeholder="Type first name + last name (e.g. 'John Doe' or 'Joh Doe')..."
              value={query}
              onValueChange={setQuery}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSearchSubmit();
                }
              }}
            />
            <CommandList>
              {searchResults.length > 0 && (
                <CommandGroup heading="Patient matches">
                  {searchResults.map((p) => (
                    <CommandItem
                      key={`search-${p.id}`}
                      value={p.name}
                      onSelect={() => {
                        onChange({ id: p.id, name: p.name });
                        setOpen(false);
                        setQuery('');
                        clearSearch();
                      }}
                    >
                      <Check className={cn('mr-2 h-4 w-4', value.name === p.name ? 'opacity-100' : 'opacity-0')} />
                      <div className="flex flex-col">
                        <span>{p.name}</span>
                        {p.friendlyId && (
                          <span className="text-xs text-muted-foreground">ID: {p.friendlyId}</span>
                        )}
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              <CommandEmpty>No patients found.</CommandEmpty>
              <CommandGroup>
                {allOptions.map((option: any) => <CommandItem key={`${option.type}-${option.id}`} value={option.name} onSelect={() => {
                onChange({
                  id: option.type === 'patient' ? option.id : undefined,
                  name: option.name
                });
                setOpen(false);
              }}>
                    <Check className={cn("mr-2 h-4 w-4", value.name === option.name ? "opacity-100" : "opacity-0")} />
                    <div className="flex flex-col">
                      <span>{option.name}</span>
                      {option.type === 'appointment' && <span className="text-xs text-muted-foreground">
                          {formatAppointmentTime(option.appointment_date)}
                        </span>}
                      {option.type === 'patient' && option.friendlyId && <span className="text-xs text-muted-foreground">
                          ID: {option.friendlyId}
                        </span>}
                    </div>
                  </CommandItem>)}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>;
};