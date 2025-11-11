import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AudioPlayer } from '@/components/AudioPlayer';
import { TranscriptViewer } from '@/components/TranscriptViewer';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { Search, Calendar, Clock, PlayCircle, FileText, Filter, Download, RefreshCw, Trash2, BarChart3, TrendingUp, Settings } from 'lucide-react';
import { format } from 'date-fns';
import { NavigationMenu } from '@/components/NavigationMenu';
import { OrganizationHeader } from '@/components/OrganizationHeader';
import { CenterFilter } from '@/components/CenterFilter';
import { useNavigate } from 'react-router-dom';

interface CallRecord {
  id: string;
  customer_name: string;
  duration_seconds: number;
  created_at: string;
  transcript: string | null;
  audio_file_url: string | null;
  center_id: string | null;
  call_category?: string;
  call_type?: string;
}

export const CallsSearch: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [filteredCalls, setFilteredCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);
  const [selectedAudioCall, setSelectedAudioCall] = useState<any>(null);
  const [isPlayerOpen, setIsPlayerOpen] = useState(false);
  
  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'customer' | 'duration'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [minDuration, setMinDuration] = useState('');
  const [maxDuration, setMaxDuration] = useState('');
  const [selectedCenter, setSelectedCenter] = useState('all');
  const [filterCallCategory, setFilterCallCategory] = useState<string>('all');
  const [filterCallType, setFilterCallType] = useState<string[]>([]);

  // Restore filters and cached calls on mount
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('searchFilters');
      if (raw) {
        const f = JSON.parse(raw);
        if (typeof f.searchTerm === 'string') setSearchTerm(f.searchTerm);
        if (typeof f.dateFrom === 'string') setDateFrom(f.dateFrom);
        if (typeof f.dateTo === 'string') setDateTo(f.dateTo);
        if (typeof f.sortBy === 'string') setSortBy(f.sortBy);
        if (typeof f.sortOrder === 'string') setSortOrder(f.sortOrder);
        if (typeof f.minDuration === 'string') setMinDuration(f.minDuration);
        if (typeof f.maxDuration === 'string') setMaxDuration(f.maxDuration);
        if (typeof f.selectedCenter === 'string') setSelectedCenter(f.selectedCenter);
        if (typeof f.filterCallCategory === 'string') setFilterCallCategory(f.filterCallCategory);
        if (Array.isArray(f.filterCallType)) setFilterCallType(f.filterCallType);
      }
      const cached = user ? sessionStorage.getItem(`searchCalls:${user.id}`) : null;
      if (cached) {
        const list = JSON.parse(cached) as CallRecord[];
        setCalls(list);
        setLoading(false);
      }
      const savedScroll = sessionStorage.getItem('searchScrollTop');
      if (savedScroll) {
        requestAnimationFrame(() => {
          try { window.scrollTo(0, parseInt(savedScroll, 10) || 0); } catch {}
        });
      }
    } catch {}
  }, [user]);

  // Persist filters and scroll
  useEffect(() => {
    try {
      sessionStorage.setItem('searchFilters', JSON.stringify({
        searchTerm, dateFrom, dateTo, sortBy, sortOrder, minDuration, maxDuration, selectedCenter,
        filterCallCategory, filterCallType
      }));
      const onScroll = () => sessionStorage.setItem('searchScrollTop', String(window.scrollY || 0));
      window.addEventListener('scroll', onScroll);
      return () => window.removeEventListener('scroll', onScroll);
    } catch {}
  }, [searchTerm, dateFrom, dateTo, sortBy, sortOrder, minDuration, maxDuration, selectedCenter, filterCallCategory, filterCallType]);

  useEffect(() => {
    if (user) {
      // If we already warmed from cache, refresh in background without flicker
      loadCalls();
    }
  }, [user]);

  useEffect(() => {
    applyFilters();
  }, [calls, searchTerm, dateFrom, dateTo, sortBy, sortOrder, minDuration, maxDuration, selectedCenter, filterCallCategory, filterCallType]);

  const loadCalls = async () => {
    if (!user) return;
    
    console.log('🔍 Loading all calls for search');
    setLoading(true);

    try {
      const { data, error } = await supabase
        .from('call_records')
        .select('*, centers(name)')
        .eq('user_id', user.id)
        .eq('recording_complete', true)
        .order('start_time', { ascending: false });
      
      // Ensure call_category and call_type are included
      if (data) {
        data.forEach(call => {
          if (!call.hasOwnProperty('call_category')) call.call_category = undefined;
          if (!call.hasOwnProperty('call_type')) call.call_type = undefined;
        });
      }

      if (error) throw error;

      console.log('✅ Loaded', data.length, 'calls for search');
      setCalls(data);
      try { sessionStorage.setItem(`searchCalls:${user.id}`, JSON.stringify(data)); } catch {}
    } catch (error) {
      console.error('❌ Error loading calls for search:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...calls];

    // Search by patient name
    if (searchTerm) {
      filtered = filtered.filter(call =>
        call.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by date range
    if (dateFrom) {
      filtered = filtered.filter(call =>
        new Date(call.created_at) >= new Date(dateFrom)
      );
    }
    if (dateTo) {
      filtered = filtered.filter(call =>
        new Date(call.created_at) <= new Date(dateTo + 'T23:59:59')
      );
    }

    // Filter by duration
    if (minDuration) {
      filtered = filtered.filter(call =>
        (call.duration_seconds || 0) >= parseInt(minDuration) * 60
      );
    }
    if (maxDuration) {
      filtered = filtered.filter(call =>
        (call.duration_seconds || 0) <= parseInt(maxDuration) * 60
      );
    }

    // Filter by center
    if (selectedCenter && selectedCenter !== 'all') {
      filtered = filtered.filter(call => call.center_id === selectedCenter);
    }

    // Filter by call_category
    if (filterCallCategory && filterCallCategory !== 'all') {
      filtered = filtered.filter(call => call.call_category === filterCallCategory);
    }

    // Filter by call_type (multi-select)
    if (filterCallType.length > 0) {
      filtered = filtered.filter(call => 
        call.call_type && filterCallType.includes(call.call_type)
      );
    }

    // Sort results
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'customer':
          aValue = a.customer_name.toLowerCase();
          bValue = b.customer_name.toLowerCase();
          break;
        case 'duration':
          aValue = a.duration_seconds || 0;
          bValue = b.duration_seconds || 0;
          break;
        case 'date':
        default:
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredCalls(filtered);
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handlePlayCall = async (call: CallRecord) => {
    if (!call.audio_file_url) {
      console.error('No audio file URL available');
      return;
    }

    try {
      // Get signed URL from Supabase storage
      const { data: signedUrlData, error: signedUrlError } = await supabase.storage
        .from('call-recordings')
        .createSignedUrl(call.audio_file_url, 60 * 60); // 1 hour expiry

      if (signedUrlError) {
        console.error('Error getting signed URL:', signedUrlError);
        return;
      }

      // Fetch the audio file using the signed URL
      const response = await fetch(signedUrlData.signedUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch audio file');
      }
      
      const audioBlob = await response.blob();
      
      // Convert to the format expected by AudioPlayer
      const audioCall = {
        id: call.id,
        customerName: call.customer_name,
        salespersonName: 'You', // Could be enhanced to get from profile
        duration: call.duration_seconds || 0,
        timestamp: new Date(call.created_at),
        status: 'completed' as const,
        transcript: call.transcript || undefined,
        audioBlob: audioBlob
      };
      
      // Store the call and audio call for the player
      setSelectedCall(call);
      setSelectedAudioCall(audioCall);
      setIsPlayerOpen(true);
    } catch (error) {
      console.error('Error fetching audio file:', error);
    }
  };

  const retryTranscription = async (call: CallRecord) => {
    if (!call.audio_file_url) {
      console.error('No audio file URL available for transcription');
      return;
    }

    try {
      console.log('Starting transcription retry for call:', call.id);
      
      // Get signed URL from Supabase storage
      const { data: signedUrlData, error: signedUrlError } = await supabase.storage
        .from('call-recordings')
        .createSignedUrl(call.audio_file_url, 60 * 60); // 1 hour expiry

      if (signedUrlError) {
        console.error('Error getting signed URL:', signedUrlError);
        return;
      }
      
      // Call FastAPI to transcribe this call by ID (backend fetches audio internally)
      const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
      const { data: sess } = await supabase.auth.getSession();
      const token = sess.session?.access_token;
      const resp = await fetch(`${API_BASE_URL}/api/transcribe/call-record/${encodeURIComponent(call.id)}?enable_diarization=true`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok) {
        console.error('Transcription failed:', data);
        alert('Transcription failed. Please check the console for details.');
      } else {
        console.log('Transcription retry successful:', data);
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      }
    } catch (error) {
      console.error('Error retrying transcription:', error);
    }
  };

  const softDeleteCall = async (call: CallRecord) => {
    if (!confirm(`Are you sure you want to delete the call with ${call.customer_name}? This action cannot be undone.`)) {
      return;
    }

    try {
      const { error } = await supabase
        .from('call_records')
        .update({ recording_complete: false })
        .eq('id', call.id)
        .eq('user_id', user!.id);

      if (error) {
        console.error('Error marking call as inactive:', error);
        return;
      }

      console.log('Call marked as inactive successfully');
      // Reload calls to remove the deleted item from view
      await loadCalls();
    } catch (error) {
      console.error('Error marking call as inactive:', error);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDateFrom('');
    setDateTo('');
    setMinDuration('');
    setMaxDuration('');
    setSelectedCenter('all');
    setFilterCallCategory('all');
    setFilterCallType([]);
    setSortBy('date');
    setSortOrder('desc');
  };

  const exportResults = () => {
    const csvContent = [
      ['Patient Name', 'Date', 'Duration', 'Call Status', 'Call Type', 'Has Transcript'].join(','),
      ...filteredCalls.map(call => [
        call.customer_name,
        format(new Date(call.created_at), 'yyyy-MM-dd HH:mm'),
        formatDuration(call.duration_seconds),
        call.call_category || 'N/A',
        call.call_type ? call.call_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'N/A',
        call.transcript ? 'Yes' : 'No'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `call-records-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">Loading calls...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <OrganizationHeader />
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Search Call Records</h1>
          <div className="flex items-center gap-2">
            <Button onClick={exportResults} variant="outline" className="gap-2">
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
            <NavigationMenu />
          </div>
        </div>

      {/* AI Analysis Promotion */}
      {filteredCalls.length > 0 && (
        <Card className="bg-gradient-to-r from-primary/5 via-secondary/5 to-accent/5 border-primary/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="bg-primary/10 p-3 rounded-full">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-1">AI-Powered Call Analysis</h3>
                  <p className="text-sm text-muted-foreground">
                    Get insights on deal progression, pain points, competitive intelligence, and sales coaching recommendations
                  </p>
                </div>
              </div>
              <div className="text-sm text-muted-foreground">
                Click "Analyze" on any call to unlock powerful AI insights
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search and Filter Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Search & Filter
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Patient Search */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Patient Name</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by patient name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Date From */}
            <div className="space-y-2">
              <label className="text-sm font-medium">From Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Date To */}
            <div className="space-y-2">
              <label className="text-sm font-medium">To Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Duration filters */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Min Duration (min)</label>
              <Input
                type="number"
                placeholder="0"
                value={minDuration}
                onChange={(e) => setMinDuration(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Max Duration (min)</label>
              <Input
                type="number"
                placeholder="60"
                value={maxDuration}
                onChange={(e) => setMaxDuration(e.target.value)}
              />
            </div>

            {/* Sort options */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Sort By</label>
              <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="customer">Patient Name</SelectItem>
                  <SelectItem value="duration">Duration</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Order</label>
              <Select value={sortOrder} onValueChange={(value: any) => setSortOrder(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Descending</SelectItem>
                  <SelectItem value="asc">Ascending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <CenterFilter 
              value={selectedCenter} 
              onChange={setSelectedCenter} 
              placeholder="All Centers"
            />
            
            {/* Call Category Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Call Status</label>
              <Select value={filterCallCategory} onValueChange={setFilterCallCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="consult_scheduled">✅ Consult Scheduled</SelectItem>
                  <SelectItem value="consult_not_scheduled">❌ Consult Not Scheduled</SelectItem>
                  <SelectItem value="other_question">❓ Other Question</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Call Type Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Call Type</label>
              <Select 
                value={filterCallType.length > 0 ? filterCallType[0] : 'all'} 
                onValueChange={(value) => {
                  if (value === 'all') {
                    setFilterCallType([]);
                  } else {
                    setFilterCallType([value]);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder={filterCallType.length > 0 ? `${filterCallType.length} selected` : "All Types"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="scheduling">Scheduling</SelectItem>
                  <SelectItem value="pricing">Pricing</SelectItem>
                  <SelectItem value="directions">Directions</SelectItem>
                  <SelectItem value="billing">Billing</SelectItem>
                  <SelectItem value="complaint">Complaint</SelectItem>
                  <SelectItem value="transfer_to_office">Transfer to Office</SelectItem>
                  <SelectItem value="general_question">General Question</SelectItem>
                  <SelectItem value="reschedule">Reschedule</SelectItem>
                  <SelectItem value="confirming_existing_appointment">Confirming Appointment</SelectItem>
                  <SelectItem value="cancellation">Cancellation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={clearFilters} variant="outline">
              Clear Filters
            </Button>
            <Badge variant="secondary">
              {filteredCalls.length} of {calls.length} calls
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Call Records</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredCalls.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No calls found matching your criteria
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Transcript</TableHead>
                  <TableHead>Analysis</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCalls.map((call) => (
                  <TableRow key={call.id}>
                    <TableCell className="font-medium">
                      {call.customer_name}
                    </TableCell>
                    <TableCell>
                      {format(new Date(call.created_at), 'MMM dd, yyyy HH:mm')}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {formatDuration(call.duration_seconds)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {call.call_category ? (
                        <Badge variant={
                          call.call_category === 'consult_scheduled' ? 'default' :
                          call.call_category === 'consult_not_scheduled' ? 'secondary' :
                          'outline'
                        }>
                          {call.call_category === 'consult_scheduled' ? '✅ Scheduled' :
                           call.call_category === 'consult_not_scheduled' ? '❌ Not Scheduled' :
                           call.call_category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Badge>
                      ) : (
                        <Badge variant="outline">-</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {call.call_type ? (
                        <Badge variant="outline">
                          {call.call_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Badge>
                      ) : (
                        <Badge variant="outline">-</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {call.transcript ? (
                        <Badge variant="default">Available</Badge>
                      ) : (
                        <Badge variant="secondary">Not Available</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {call.transcript ? (
                        <TranscriptViewer
                          transcript={call.transcript}
                          customerName={call.customer_name}
                          salespersonName="Salesperson"
                          duration={call.duration_seconds || 0}
                          timestamp={new Date(call.created_at)}
                          callId={call.id}
                          onRetryTranscription={() => retryTranscription(call)}
                        />
                      ) : (
                        <Button size="sm" variant="outline" disabled className="gap-1">
                          <BarChart3 className="h-4 w-4" />
                          No Analysis
                        </Button>
                      )}
                    </TableCell>
                     <TableCell>
                       <div className="flex gap-2">
                         {call.audio_file_url && (
                           <Button
                             size="sm"
                             variant="outline"
                             onClick={() => handlePlayCall(call)}
                             className="gap-1"
                           >
                             <PlayCircle className="h-4 w-4" />
                             Play
                           </Button>
                         )}
                         {!call.transcript && call.audio_file_url && (
                           <Button
                             size="sm"
                             variant="outline"
                             onClick={() => retryTranscription(call)}
                             className="gap-1"
                           >
                             <RefreshCw className="h-4 w-4" />
                             Retry Transcription
                           </Button>
                         )}
                         <Button
                           size="sm"
                           variant="outline"
                           onClick={() => navigate('/contact-preferences')}
                           className="gap-1"
                           title={`View contact preferences for ${call.customer_name}`}
                         >
                           <Settings className="h-4 w-4" />
                           Pt Pref.
                         </Button>
                         <Button
                           size="sm"
                           variant="outline"
                           onClick={() => softDeleteCall(call)}
                           className="gap-1 text-destructive hover:text-destructive"
                         >
                           <Trash2 className="h-4 w-4" />
                           Delete
                         </Button>
                       </div>
                     </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Audio Player Modal */}
      {selectedAudioCall && (
        <AudioPlayer
          call={selectedAudioCall}
          isOpen={isPlayerOpen}
          onClose={() => {
            setIsPlayerOpen(false);
            setSelectedCall(null);
            setSelectedAudioCall(null);
          }}
          onRetryTranscription={() => selectedCall && retryTranscription(selectedCall)}
        />
      )}
      </div>
    </div>
  );
};