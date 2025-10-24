import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Search, Plus, User } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { usePatients } from '@/hooks/usePatients';
import { usePatientSearch } from '@/hooks/usePatientSearch';

// Validation schema for patient creation
const patientSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(100, "Name must be less than 100 characters"),
  email: z.string().email("Please enter a valid email address").optional().or(z.literal('')),
  phone: z.string()
    .regex(/^[\+]?[1-9][\d]{0,15}$/, "Please enter a valid phone number")
    .optional()
    .or(z.literal('')),
});

type PatientFormData = z.infer<typeof patientSchema>;

interface Patient {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  friendlyId: string;
}

interface PatientSelectorProps {
  onPatientSelect: (patient: Patient | null) => void;
  selectedPatient: Patient | null;
  disabled?: boolean;
}

export const PatientSelector: React.FC<PatientSelectorProps> = ({
  onPatientSelect,
  selectedPatient,
  disabled = false
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [showingSearchResults, setShowingSearchResults] = useState(false);
  const { toast } = useToast();
  
  const { patients, loading: patientsLoading, createPatient } = usePatients();
  const { search, loading: searchLoading, error: searchError } = usePatientSearch();

  const form = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      name: '',
      email: '',
      phone: '',
    },
  });

  // Handle search with 3+3 character requirement
  const handleSearch = async (searchValue: string) => {
    setSearchTerm(searchValue);
    
    if (!searchValue.trim()) {
      setSearchResults([]);
      setShowingSearchResults(false);
      return;
    }

    const parts = searchValue.trim().split(/\s+/);
    if (parts.length >= 2 && parts[0].length >= 3 && parts[1].length >= 3) {
      const results = await search(searchValue);
      setSearchResults(results);
      setShowingSearchResults(true);
    } else {
      setSearchResults([]);
      setShowingSearchResults(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(searchTerm);
    }
  };

  // Use search results if searching, otherwise show recent patients
  const displayedPatients = showingSearchResults ? searchResults : patients.slice(0, 10);

  const handleCreatePatient = async (data: PatientFormData) => {
    try {
      const newPatient = await createPatient({
        name: data.name.trim(),
        email: data.email?.trim() || undefined,
        phone: data.phone?.trim() || undefined,
      });

      onPatientSelect(newPatient);
      setIsCreateDialogOpen(false);
      form.reset();

      toast({
        title: "Success",
        description: `Patient ${newPatient.friendlyId} created successfully`
      });
    } catch (error) {
      console.error('Error creating patient:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create patient",
        variant: "destructive"
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          Patient Selection
        </CardTitle>
        <CardDescription>
          Select an existing patient or create a new one for this interaction
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {selectedPatient ? (
          <div className="p-4 bg-primary/5 rounded-lg border">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">{selectedPatient.name}</h4>
                <Badge variant="secondary" className="mt-1">
                  {selectedPatient.friendlyId}
                </Badge>
                {selectedPatient.email && (
                  <p className="text-sm text-muted-foreground mt-1">{selectedPatient.email}</p>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPatientSelect(null)}
                disabled={disabled}
              >
                Change
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search patients by first and last name (3+ chars each), press Enter..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="pl-10"
                  disabled={disabled}
                />
              </div>
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button disabled={disabled}>
                    <Plus className="h-4 w-4 mr-2" />
                    New Patient
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create New Patient</DialogTitle>
                    <DialogDescription>
                      Add a new patient to your system with a unique patient ID
                    </DialogDescription>
                  </DialogHeader>
                  <Form {...form}>
                    <form onSubmit={form.handleSubmit(handleCreatePatient)} className="space-y-4">
                      <FormField
                        control={form.control}
                        name="name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Full Name *</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="Enter patient's full name"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <FormField
                        control={form.control}
                        name="email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Email</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="Enter patient's email"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <FormField
                        control={form.control}
                        name="phone"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Phone</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="Enter patient's phone number (e.g., +1234567890)"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <div className="flex justify-end gap-2 pt-4">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setIsCreateDialogOpen(false);
                            form.reset();
                          }}
                        >
                          Cancel
                        </Button>
                        <Button type="submit" disabled={form.formState.isSubmitting}>
                          {form.formState.isSubmitting ? 'Creating...' : 'Create Patient'}
                        </Button>
                      </div>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>
            </div>

            {(searchLoading || patientsLoading) && (
              <div className="text-center py-4 text-muted-foreground">
                <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
                <p className="mt-2">Loading patients...</p>
              </div>
            )}

            {searchError && (
              <div className="text-center py-4 text-destructive">
                <p>Error searching patients: {searchError}</p>
              </div>
            )}

            {!searchLoading && !patientsLoading && displayedPatients.length > 0 && (
              <div className="max-h-60 overflow-y-auto space-y-2">
                <div className="text-sm text-muted-foreground mb-2">
                  {showingSearchResults ? `Search results (${displayedPatients.length})` : 'Recent patients'}
                </div>
                {displayedPatients.map((patient) => (
                  <div
                    key={patient.id}
                    className="p-3 border rounded-lg cursor-pointer hover:bg-accent/50 transition-colors"
                    onClick={() => !disabled && onPatientSelect(patient)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{patient.name}</h4>
                        <Badge variant="outline" className="mt-1">
                          {patient.friendlyId}
                        </Badge>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        {patient.email && <div>{patient.email}</div>}
                        {patient.phone && <div>{patient.phone}</div>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!searchLoading && !patientsLoading && showingSearchResults && searchResults.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No patients found matching "{searchTerm}"</p>
                <p className="text-sm">Try creating a new patient instead</p>
              </div>
            )}

            {!searchLoading && !patientsLoading && !showingSearchResults && searchTerm && (
              <div className="text-center py-4 text-muted-foreground">
                <p className="text-sm">Enter first and last name (3+ characters each) and press Enter to search</p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};