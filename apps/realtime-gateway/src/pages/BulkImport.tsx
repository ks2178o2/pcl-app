import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Upload, 
  FileAudio, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Loader2,
  Link as LinkIcon,
  User,
  Database,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  AlertTriangle,
  Target,
  FileText,
  RotateCw,
  Send
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { NavigationMenu } from '@/components/NavigationMenu';
import { useToast } from '@/hooks/use-toast';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { FollowUpPlanPanel } from '@/components/FollowUpPlanPanel';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';

interface CallRecord {
  id: string;
  transcript?: string;
  call_category?: string;
  call_type?: string;
  consult_scheduled?: boolean;
  objection_detected?: boolean;
  categorization_confidence?: number;
  categorization_notes?: string;
}

interface Objection {
  id: string;
  objection_type: string;
  objection_text: string;
  transcript_segment?: string;
  confidence?: number;
}

interface ObjectionOvercome {
  id: string;
  objection_id: string;
  overcome_method: string;
  transcript_quote: string;
  confidence?: number;
}

interface BulkImportFile {
  id: string;
  file_name: string;
  status: string;
  error_message?: string;
  file_size?: number;
  file_format?: string;
  original_url?: string;
  call_record_id?: string;
  call_record?: CallRecord;
  objections?: Objection[];
  objection_overcomes?: ObjectionOvercome[];
}

interface BulkImportJob {
  job_id: string;
  status: string;
  customer_name: string;
  total_files: number;
  processed_files: number;
  failed_files: number;
  progress_percentage: number;
  error_message?: string;
  call_log_mapping_skipped?: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  files?: BulkImportFile[];
  discovered_files?: number;
  unique_files?: number;
  discovery_details?: {
    discovered: number;
    duplicates_by_url: { url: string; count: number }[];
    entries: { name: string; file_id?: string; url?: string }[];
  };
}

export const BulkImportPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // Set browser tab title
  useEffect(() => {
    document.title = 'PCL-Call-Center-MVP';
    // Cleanup: restore original title when component unmounts
    return () => {
      document.title = 'PitCrew';
    };
  }, []);
  
  const [customerName, setCustomerName] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [provider, setProvider] = useState<'openai' | 'gemini'>('openai');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<BulkImportJob | null>(null);
  const [jobsList, setJobsList] = useState<BulkImportJob[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [activeTab, setActiveTab] = useState<'new-import' | 'status' | 'history'>('new-import');
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());
  const [retranscribing, setRetranscribing] = useState<Set<string>>(new Set());
  const [generatingPlans, setGeneratingPlans] = useState<Set<string>>(new Set());
  const [planPanelOpen, setPlanPanelOpen] = useState(false);
  const [selectedCallRecordId, setSelectedCallRecordId] = useState<string | null>(null);
  const [callRecordWithPlan, setCallRecordWithPlan] = useState<{ callRecordId: string; transcript: string; customerName: string } | null>(null);
  const [callsWithPlans, setCallsWithPlans] = useState<Set<string>>(new Set());

  // Load dismissed alerts from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('bulkImport_dismissedAlerts');
      if (stored) {
        setDismissedAlerts(new Set(JSON.parse(stored)));
      }
    } catch (e) {
      console.warn('Failed to load dismissed alerts from localStorage:', e);
    }
  }, []);

  useEffect(() => {
    if (user) {
      loadJobsList();
    }
  }, [user]);

  useEffect(() => {
    if (currentJobId) {
      let pollCount = 0;
      const maxPolls = 120; // Poll for up to 6 minutes (120 * 3s = 360s)
      
      const interval = setInterval(() => {
        pollCount++;
        fetchJobStatus(currentJobId);
        
        // Check if we have any files with "Processing..." transcripts - if so, keep polling
        const hasProcessingTranscripts = jobStatus?.files?.some(
          (f: BulkImportFile) => 
            f.call_record?.transcript === "Processing..." || 
            f.call_record?.transcript === "Transcribing audio..."
        );
        
        // Stop polling after max attempts if job is completed AND no transcripts are processing
        if (pollCount >= maxPolls && jobStatus?.status === 'completed' && !hasProcessingTranscripts) {
          clearInterval(interval);
          setCurrentJobId(null);
        }
      }, 3000); // Poll every 3 seconds

      return () => clearInterval(interval);
    }
  }, [currentJobId, jobStatus?.status, jobStatus?.files]);

  // Auto-refresh completed jobs without results when viewing them
  useEffect(() => {
    if (jobStatus && jobStatus.status === 'completed' && currentJobId) {
      const hasResults = jobStatus.files && jobStatus.files.some((file: BulkImportFile) => 
        file.call_record && (file.call_record.transcript || file.call_record.call_category)
      );
      
      // If completed but no results, refresh immediately and then every 5 seconds for up to 30 seconds
      if (!hasResults && jobStatus.total_files > 0) {
        fetchJobStatus(currentJobId);
        
        const refreshInterval = setInterval(() => {
          fetchJobStatus(currentJobId);
        }, 5000); // Refresh every 5 seconds
        
        // Stop after 30 seconds (6 refreshes)
        const timeout = setTimeout(() => {
          clearInterval(refreshInterval);
        }, 30000);
        
        return () => {
          clearInterval(refreshInterval);
          clearTimeout(timeout);
        };
      }
    }
  }, [jobStatus?.status, jobStatus?.files, currentJobId]);

  const loadJobsList = async () => {
    if (!user) return;

    setIsLoadingJobs(true);
    try {
      const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
      const token = sessionData?.session?.access_token;

      const response = await fetch(`${API_BASE_URL}/api/bulk-import/jobs`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load jobs');
      }

      const jobs = await response.json();
      setJobsList(jobs);
    } catch (error) {
      console.error('Error loading jobs:', error);
      toast({
        title: 'Error',
        description: 'Failed to load import jobs',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingJobs(false);
    }
  };

  const fetchJobStatus = async (jobId: string) => {
    if (!user) return;

    try {
      const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
      const token = sessionData?.session?.access_token;

      // Always include files for detailed status
      const response = await fetch(`${API_BASE_URL}/api/bulk-import/status/${jobId}?include_files=true`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }

      const status = await response.json();
      
      // Check which calls have follow-up plans
      if (status.files && user) {
        try {
          const { supabase: supabaseClient } = await import('@/integrations/supabase/client');
          const userId = (user as any)?.id;
          if (userId) {
            const callRecordIds = status.files
              .map((f: BulkImportFile) => f.call_record?.id)
              .filter((id: string | undefined): id is string => !!id);
            
            if (callRecordIds.length > 0) {
              const { data: plans } = await supabaseClient
                .from('follow_up_plans')
                .select('call_record_id')
                .eq('user_id', userId)
                .in('call_record_id', callRecordIds);
              
              if (plans) {
                setCallsWithPlans(new Set(plans.map((p: any) => p.call_record_id)));
              }
            }
          }
        } catch (err) {
          console.warn('Error checking for existing plans:', err);
        }
      }
      
      // Update retranscribing state BEFORE setting job status
      // Keep retranscribing state if transcript is "Processing..." or "Transcribing audio..."
      setRetranscribing(prev => {
        const newSet = new Set(prev);
        if (status.files) {
          status.files.forEach((file: BulkImportFile) => {
            const callRecordId = file.call_record?.id;
            if (callRecordId && newSet.has(callRecordId)) {
              const transcript = file.call_record?.transcript || '';
              // If transcript is no longer "Processing..." or "Transcribing audio...", clear the retranscribing state
              // This means transcription completed (got actual transcript) or failed (got error message)
              if (transcript !== "Processing..." && transcript !== "Transcribing audio..." && transcript.trim().length > 0) {
                console.log(`✅ Frontend: Clearing retranscribing state for call_record_id=${callRecordId}, transcript_length=${transcript.length}`);
                newSet.delete(callRecordId);
              } else {
                console.log(`🔄 Frontend: Keeping retranscribing state for call_record_id=${callRecordId}, transcript="${transcript}"`);
              }
              // Otherwise, keep it in retranscribing state to show the badge
            }
          });
        }
        return newSet;
      });
      
      console.log(`📥 Frontend: Fetched job status for jobId=${jobId}, files_count=${status.files?.length || 0}`);
      if (status.files) {
        status.files.forEach((file: BulkImportFile) => {
          const transcript = file.call_record?.transcript || '';
          const hasCategory = file.call_record?.call_category;
          const hasObjections = file.objections?.length > 0;
          if (transcript && transcript !== "Processing..." && transcript !== "Transcribing audio...") {
            console.log(`📝 Frontend: File ${file.file_name} has transcript (length=${transcript.length}), category=${hasCategory || 'none'}, objections=${hasObjections ? file.objections.length : 0}, status=${file.status}`);
          } else if (hasCategory || hasObjections) {
            console.log(`📝 Frontend: File ${file.file_name} has analysis (category=${hasCategory || 'none'}, objections=${hasObjections ? file.objections.length : 0}) but transcript=${transcript ? 'processing' : 'missing'}, status=${file.status}`);
          }
        });
      }
      
      setJobStatus(status);

      // Check if completed job has results
      const hasResults = status.files && status.files.some((file: BulkImportFile) => 
        file.call_record && (file.call_record.transcript || file.call_record.call_category)
      );
      
      // Stop polling if job is completed or failed, BUT continue polling if completed without results
      if (status.status === 'failed') {
        setCurrentJobId(null);
        loadJobsList(); // Refresh jobs list
      } else if (status.status === 'completed') {
        // If completed but no results, continue polling for a bit to catch late-arriving data
        if (!hasResults && status.total_files > 0) {
          // Continue polling for up to 30 more seconds (10 more polls at 3s intervals)
          // This will be handled by the existing polling interval
          console.log('Job completed but no results yet, continuing to poll...');
        } else {
          // Has results or no files, stop polling
          setCurrentJobId(null);
          loadJobsList(); // Refresh jobs list
        }
      }
    } catch (error) {
      console.error('Error fetching job status:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch job status. Please refresh the page.',
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!customerName.trim() || !sourceUrl.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please log in to use bulk import',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
      const token = sessionData?.session?.access_token;

      const response = await fetch(`${API_BASE_URL}/api/bulk-import/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_name: customerName.trim(),
          source_url: sourceUrl.trim(),
          provider: provider,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start bulk import');
      }

      const result = await response.json();
      setCurrentJobId(result.job_id);
      await fetchJobStatus(result.job_id);
      
      // Switch to status tab to show the new job
      setActiveTab('status');

      toast({
        title: 'Import Started',
        description: `Bulk import job started for ${customerName}`,
      });

      // Reset form
      setCustomerName('');
      setSourceUrl('');
      loadJobsList();

    } catch (error) {
      console.error('Error starting bulk import:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to start bulk import',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', label: string, icon?: React.ReactNode }> = {
      pending: { variant: 'secondary', label: 'Pending', icon: <Clock className="h-3 w-3 mr-1" /> },
      discovering: { variant: 'secondary', label: 'Discovering', icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" /> },
      downloading: { variant: 'secondary', label: 'Downloading', icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" /> },
      converting: { variant: 'secondary', label: 'Converting', icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" /> },
      uploading: { variant: 'secondary', label: 'Uploading', icon: <Upload className="h-3 w-3 mr-1" /> },
      transcribing: { variant: 'secondary', label: 'Transcribing', icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" /> },
      analyzing: { variant: 'secondary', label: 'Analyzing', icon: <TrendingUp className="h-3 w-3 mr-1" /> },
      categorized: { variant: 'default', label: 'Categorized', icon: <CheckCircle className="h-3 w-3 mr-1" /> },
      completed: { variant: 'default', label: 'Completed', icon: <CheckCircle className="h-3 w-3 mr-1" /> },
      failed: { variant: 'destructive', label: 'Failed', icon: <XCircle className="h-3 w-3 mr-1" /> },
    };

    const config = statusConfig[status] || { variant: 'outline', label: status };
    return (
      <Badge variant={config.variant} className="flex items-center">
        {config.icon}
        {config.label}
      </Badge>
    );
  };

  const getPipelineStages = () => {
    return [
      { id: 'pending', label: 'Pending', icon: Clock },
      { id: 'downloading', label: 'Downloading', icon: Upload },
      { id: 'uploading', label: 'Uploading', icon: Upload },
      { id: 'transcribing', label: 'Transcribing', icon: MessageSquare },
      { id: 'analyzing', label: 'Analyzing', icon: TrendingUp },
      { id: 'categorized', label: 'Categorized', icon: Target },
      { id: 'completed', label: 'Completed', icon: CheckCircle },
    ];
  };

  const getStatusStageIndex = (status: string): number => {
    const stageMap: Record<string, number> = {
      'pending': 0,
      'downloading': 1,
      'uploading': 2,
      'transcribing': 3,
      'analyzing': 4,
      'categorized': 5,
      'completed': 6,
    };
    return stageMap[status] ?? 0;
  };

  const getStageProgress = (status: string): { currentStage: number; progress: number } => {
    const stages = getPipelineStages();
    const currentIndex = getStatusStageIndex(status);
    
    if (status === 'completed') {
      return { currentStage: stages.length - 1, progress: 100 };
    }
    
    if (status === 'failed') {
      // Keep progress at current stage but mark as failed
      return { currentStage: Math.max(0, currentIndex), progress: (currentIndex / (stages.length - 1)) * 100 };
    }
    
    // Calculate progress based on current stage
    // For in-progress stages, show partial progress (assume 50% through current stage)
    const progress = ((currentIndex + 0.5) / (stages.length - 1)) * 100;
    return { currentStage: currentIndex, progress: Math.min(100, Math.max(0, progress)) };
  };

  const FileProgressBar: React.FC<{ file: BulkImportFile }> = ({ file }) => {
    const stages = getPipelineStages();
    const { currentStage, progress } = getStageProgress(file.status);
    const isFailed = file.status === 'failed';
    
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="font-medium text-gray-700">Pipeline Progress</span>
          <span className="text-gray-500">{progress.toFixed(0)}%</span>
        </div>
        <div className="relative">
          {/* Progress Bar Background */}
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                isFailed ? 'bg-red-500' : 'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {/* Stage Indicators */}
          <div className="flex justify-between mt-2">
            {stages.map((stage, index) => {
              const StageIcon = stage.icon;
              const isActive = index <= currentStage;
              const isCurrent = index === currentStage && !isFailed;
              const isCompleted = index < currentStage;
              
              return (
                <div
                  key={stage.id}
                  className="flex flex-col items-center flex-1 relative"
                >
                  {/* Connector Line */}
                  {index < stages.length - 1 && (
                    <div
                      className={`absolute top-3 left-[60%] w-full h-0.5 ${
                        isCompleted ? 'bg-blue-500' : index === currentStage ? 'bg-blue-300' : 'bg-gray-200'
                      }`}
                      style={{ zIndex: 0 }}
                    />
                  )}
                  
                  {/* Stage Icon */}
                  <div
                    className={`relative z-10 w-6 h-6 rounded-full flex items-center justify-center border-2 transition-all ${
                      isFailed && index === currentStage
                        ? 'bg-red-100 border-red-500 text-red-600'
                        : isCurrent
                        ? 'bg-blue-500 border-blue-600 text-white shadow-lg scale-110'
                        : isCompleted
                        ? 'bg-blue-500 border-blue-600 text-white'
                        : 'bg-white border-gray-300 text-gray-400'
                    }`}
                  >
                    {isCurrent && file.status !== 'completed' && file.status !== 'failed' ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <StageIcon className="h-3 w-3" />
                    )}
                  </div>
                  
                  {/* Stage Label */}
                  <span
                    className={`text-xs mt-1 text-center ${
                      isCurrent || isCompleted
                        ? 'font-medium text-gray-900'
                        : 'text-gray-500'
                    }`}
                    style={{ fontSize: '0.65rem', lineHeight: '1rem' }}
                  >
                    {stage.label.split(' ')[0]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <NavigationMenu />
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Call center recordings analysis</h1>
          <p className="text-gray-600">
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'new-import' | 'status' | 'history')} className="space-y-6">
          <TabsList>
            <TabsTrigger value="new-import">New Import</TabsTrigger>
            <TabsTrigger value="status">Current Job</TabsTrigger>
            <TabsTrigger value="history">Job History</TabsTrigger>
          </TabsList>

          <TabsContent value="new-import">
            <Card>
              <CardHeader>
                <CardTitle>Start New Bulk Import</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="customer-name">
                      <User className="inline mr-2 h-4 w-4" />
                      Project Name *
                    </Label>
                    <Input
                      id="customer-name"
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      placeholder="Enter project name"
                      required
                      disabled={isSubmitting}
                    />
                    <p className="text-sm text-gray-500">
                      A storage bucket will be created with this name
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="source-url">
                      <LinkIcon className="inline mr-2 h-4 w-4" />
                      Source URL *
                    </Label>
                    <Input
                      id="source-url"
                      type="url"
                      value={sourceUrl}
                      onChange={(e) => setSourceUrl(e.target.value)}
                      placeholder="https://example.com/audio-files"
                      required
                      disabled={isSubmitting}
                    />
                    <p className="text-sm text-gray-500">
                      URL to a folder or page containing audio files (WAV, MP3, M4A, WebM, OGG up to 1GB)
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      💡 For Google Drive folders: Make sure the folder is shared with "Anyone with the link" and use the folder sharing URL
                    </p>
                  </div>

                  <Button
                    type="submit"
                    disabled={isSubmitting || !customerName.trim() || !sourceUrl.trim()}
                    className="w-full"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Starting Import...
                      </>
                    ) : (
                      <>
                        <Upload className="mr-2 h-4 w-4" />
                        Start Bulk Import
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="status">
            {jobStatus ? (
              <Card>
                <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <CardTitle>Import Status</CardTitle>
                    <CardDescription>
                      Job for <span className="font-mono">{jobStatus.customer_name}</span>
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-3 mt-3 sm:mt-0">
                    {/* Discovered/Unique badges */}
                    {(() => {
                      const discovered = (jobStatus as any).discovery_details?.discovered ?? (jobStatus as any).discovered_files ?? jobStatus.total_files;
                      const unique = (jobStatus as any).unique_files ?? ((jobStatus as any).files?.length ?? null);
                      return (
                        <>
                          {discovered !== undefined && discovered !== null && (
                            <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 border border-gray-200">
                              Discovered: {discovered}
                            </span>
                          )}
                          {unique !== undefined && unique !== null && (
                            <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 border border-gray-200">
                              Unique: {unique}
                            </span>
                          )}
                        </>
                      );
                    })()}
                    <Button variant="outline" size="sm" onClick={() => jobStatus?.job_id && fetchJobStatus(jobStatus.job_id)}>
                      <Loader2 className="h-3 w-3 mr-1" />
                      Refresh Results
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Discovery Details */}
                  { (jobStatus as any).discovery_details && (
                    <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded">
                      <details>
                        <summary className="text-sm font-semibold cursor-pointer">Discovery Details</summary>
                        <div className="mt-2 text-xs text-gray-700 space-y-2">
                          <div className="flex flex-wrap gap-3">
                            <span>Discovered: {(jobStatus as any).discovery_details?.discovered ?? (jobStatus as any).discovered_files}</span>
                            <span>Unique: {(jobStatus as any).unique_files ?? '—'}</span>
                          </div>
                          {Array.isArray((jobStatus as any).discovery_details?.found_file_names) && (
                            <div>
                              <div className="font-medium">Found File Names ({((jobStatus as any).discovery_details.found_file_names).length}):</div>
                              <div className="text-xs font-mono bg-white p-2 rounded border mt-1">
                                {((jobStatus as any).discovery_details.found_file_names).join(', ')}
                              </div>
                            </div>
                          )}
                          {Array.isArray((jobStatus as any).discovery_details?.duplicates_by_url) && (jobStatus as any).discovery_details.duplicates_by_url.length > 0 && (
                            <div>
                              <div className="font-medium">Duplicates by URL</div>
                              <ul className="list-disc ml-5">
                                {(jobStatus as any).discovery_details.duplicates_by_url.map((d: any, idx: number) => (
                                  <li key={idx} className="break-all">{d.url} (x{d.count})</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {Array.isArray((jobStatus as any).discovery_details?.entries) && (
                            <div>
                              <div className="font-medium">Entries</div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {(jobStatus as any).discovery_details.entries.map((e: any, idx: number) => (
                                  <div key={idx} className="p-2 border rounded bg-white text-[11px]">
                                    <div className="font-mono truncate">{e.name || 'unknown'}</div>
                                    {e.file_id && <div className="text-gray-500">file_id: {e.file_id}</div>}
                                    {e.url && <div className="text-gray-500 break-all">url: {e.url}</div>}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </details>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Status</span>
                    {getStatusBadge(jobStatus.status)}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">Overall Progress</span>
                      <span className="font-semibold">{jobStatus.progress_percentage.toFixed(1)}%</span>
                    </div>
                    <Progress value={jobStatus.progress_percentage} className="h-2" />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{jobStatus.processed_files} of {jobStatus.total_files} files completed</span>
                      {jobStatus.total_files > 0 && (
                        <span>
                          {Math.round((jobStatus.processed_files / jobStatus.total_files) * 100)}% complete
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Call Type Statistics */}
                  {jobStatus.files && jobStatus.files.length > 0 && (() => {
                    const callTypeStats = new Map<string, { total: number; scheduled: number; not_scheduled: number }>();
                    jobStatus.files.forEach((file: BulkImportFile) => {
                      if (file.call_record?.call_type) {
                        const type = file.call_record.call_type;
                        if (!callTypeStats.has(type)) {
                          callTypeStats.set(type, { total: 0, scheduled: 0, not_scheduled: 0 });
                        }
                        const stats = callTypeStats.get(type)!;
                        stats.total++;
                        if (file.call_record.call_category === 'consult_scheduled') {
                          stats.scheduled++;
                        } else if (file.call_record.call_category === 'consult_not_scheduled') {
                          stats.not_scheduled++;
                        }
                      }
                    });
                    
                    if (callTypeStats.size > 0) {
                      return (
                        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                          <details>
                            <summary className="text-sm font-semibold cursor-pointer text-blue-900">
                              Call Type Statistics ({callTypeStats.size} types)
                            </summary>
                            <div className="mt-2 space-y-2">
                              {Array.from(callTypeStats.entries())
                                .sort((a, b) => b[1].total - a[1].total)
                                .map(([type, stats]) => {
                                  const successRate = stats.total > 0 ? Math.round((stats.scheduled / stats.total) * 100) : 0;
                                  return (
                                    <div key={type} className="text-xs bg-white p-2 rounded border">
                                      <div className="font-medium">
                                        {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                      </div>
                                      <div className="flex gap-3 mt-1 text-gray-600">
                                        <span>Total: {stats.total}</span>
                                        <span className="text-green-600">✅ Scheduled: {stats.scheduled}</span>
                                        <span className="text-red-600">❌ Not Scheduled: {stats.not_scheduled}</span>
                                        <span className="font-semibold">Success Rate: {successRate}%</span>
                                      </div>
                                    </div>
                                  );
                                })}
                            </div>
                          </details>
                        </div>
                      );
                    }
                    return null;
                  })()}

                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold">{jobStatus.total_files}</div>
                      <div className="text-sm text-gray-600">Total Files</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{jobStatus.processed_files}</div>
                      <div className="text-sm text-gray-600">Processed</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">{jobStatus.failed_files}</div>
                      <div className="text-sm text-gray-600">Failed</div>
                    </div>
                  </div>

                  {jobStatus.error_message && !jobStatus.error_message.includes("Call log file mapping skipped") && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{jobStatus.error_message}</p>
                    </div>
                  )}

                  {/* Call Log Mapping Skipped Alert - Persistent */}
                  {jobStatus.call_log_mapping_skipped && !dismissedAlerts.has(jobStatus.job_id) && (
                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-2 flex-1">
                          <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-sm font-medium text-yellow-900">
                              Call Log File Mapping Skipped
                            </p>
                            <p className="text-sm text-yellow-800 mt-1">
                              No call log file was provided for this import job. The call log mapping step has been skipped. 
                              Audio files will be processed without mapping to external call log data.
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            const newDismissed = new Set(dismissedAlerts);
                            newDismissed.add(jobStatus.job_id);
                            setDismissedAlerts(newDismissed);
                            // Persist to localStorage
                            try {
                              localStorage.setItem('bulkImport_dismissedAlerts', JSON.stringify(Array.from(newDismissed)));
                            } catch (e) {
                              console.warn('Failed to save dismissed alerts to localStorage:', e);
                            }
                          }}
                          className="ml-4 text-yellow-600 hover:text-yellow-800 flex-shrink-0"
                          aria-label="Dismiss alert"
                        >
                          <XCircle className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  )}

                  {/* File Discovery Status */}
                  {jobStatus.status === 'discovering' && (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                        <div>
                          <p className="text-sm font-medium text-blue-900">Discovering audio files...</p>
                          <p className="text-xs text-blue-700 mt-1">
                            Scanning the source URL for audio files. This may take a moment.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Files List - Always show if we have files or if discovery is complete */}
                  {(jobStatus.files && jobStatus.files.length > 0) || jobStatus.total_files > 0 ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">Files ({jobStatus.files?.length || 0} of {jobStatus.total_files || 0})</h3>
                        <div className="text-sm text-gray-600">
                          {jobStatus.processed_files} processed • {jobStatus.failed_files} failed
                        </div>
                      </div>
                      
                      {jobStatus.files && jobStatus.files.length > 0 ? (
                        <div className="space-y-2 border rounded-lg p-4 bg-white">
                          {jobStatus.files.map((file: BulkImportFile, index: number) => {
                            const isExpanded = expandedFiles.has(file.id);
                            // Allow expansion if file has results (transcript or analysis) OR if status indicates completion
                            const hasAnyResults = file.call_record && (
                              (file.call_record.transcript && file.call_record.transcript !== "Processing..." && file.call_record.transcript !== "Transcribing audio...") ||
                              file.call_record.call_category ||
                              file.call_record.call_type ||
                              file.objections?.length > 0
                            );
                            const canExpand = hasAnyResults || file.status === 'completed' || file.status === 'categorized' || file.status === 'analyzing';
                            const hasResults = file.call_record && (file.status === 'completed' || file.status === 'categorized' || hasAnyResults);
                            
                            return (
                              <div
                                key={file.id || index}
                                className="border border-gray-200 rounded-lg overflow-hidden"
                              >
                                {/* File Header - Always Visible */}
                                <div
                                  className={`flex items-start justify-between p-3 bg-gray-50 transition-colors ${
                                    canExpand ? 'hover:bg-gray-100 cursor-pointer' : ''
                                  }`}
                                  onClick={() => {
                                    if (canExpand) {
                                      const newExpanded = new Set(expandedFiles);
                                      if (isExpanded) {
                                        newExpanded.delete(file.id);
                                      } else {
                                        newExpanded.add(file.id);
                                      }
                                      setExpandedFiles(newExpanded);
                                    }
                                  }}
                                >
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-2 mb-1">
                                      <FileAudio className="h-4 w-4 text-gray-500 flex-shrink-0" />
                                      <span className="text-sm font-medium text-gray-900 truncate">
                                        {file.file_name || 'Unknown file'}
                                      </span>
                                      {hasResults && (
                                        <Badge variant="outline" className="ml-2 text-xs">
                                          <FileText className="h-3 w-3 mr-1" />
                                          Results Available
                                        </Badge>
                                      )}
                                    </div>
                                    
                                    {file.file_size && (
                                      <p className="text-xs text-gray-500 ml-6">
                                        Size: {(file.file_size / 1024 / 1024).toFixed(2)} MB
                                        {file.file_format && ` • Format: ${file.file_format.toUpperCase()}`}
                                      </p>
                                    )}
                                    
                                    {/* Pipeline Progress Bar */}
                                    <div className="ml-6 mt-2">
                                      <FileProgressBar file={file} />
                                    </div>
                                    
                                    {file.error_message && (
                                      <p className="text-xs text-red-600 mt-1 ml-6">
                                        Error: {file.error_message}
                                      </p>
                                    )}
                                  </div>
                                  
                                  <div className="ml-4 flex items-center space-x-2 flex-shrink-0">
                                    {getStatusBadge(file.status)}
                                    {canExpand && (
                                      isExpanded ? (
                                        <ChevronUp className="h-4 w-4 text-gray-400" />
                                      ) : (
                                        <ChevronDown className="h-4 w-4 text-gray-400" />
                                      )
                                    )}
                                  </div>
                                </div>

                                {/* Expandable Results Section */}
                                {isExpanded && (
                                  <div className="p-4 bg-white border-t border-gray-200 space-y-4">
                      {/* Categorization Results */}
                      {file.call_record && (file.call_record.call_category || file.call_record.call_type) && (
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <Target className="h-4 w-4 text-blue-600" />
                            <h4 className="text-sm font-semibold">Call Classification</h4>
                          </div>
                          <div className="ml-6 space-y-2">
                            {(() => {
                              const isHeuristic = file.call_record.categorization_notes?.includes("[HEURISTIC]") ||
                                                  (file.call_record.call_category === 'other_question' && 
                                                   file.call_record.categorization_confidence === 0.5);
                              return (
                                <>
                                  {isHeuristic && (
                                    <Badge variant="outline" className="mb-2 text-xs bg-gray-200 text-gray-600 border-gray-400">
                                      HEURISTIC (Not LLM)
                                    </Badge>
                                  )}
                                  
                                  {/* Call Category (Success/Failure Status) */}
                                  {file.call_record.call_category && (
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="text-xs text-gray-600 font-medium">Status:</span>
                                      <Badge variant={
                                        file.call_record.call_category === 'consult_scheduled' ? 'default' :
                                        file.call_record.call_category === 'consult_not_scheduled' ? 'secondary' :
                                        'outline'
                                      } className={isHeuristic ? 'opacity-75' : ''}>
                                        {file.call_record.call_category === 'consult_scheduled' ? '✅ Consult Scheduled' :
                                         file.call_record.call_category === 'consult_not_scheduled' ? '❌ Consult Not Scheduled' :
                                         file.call_record.call_category?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                      </Badge>
                                    </div>
                                  )}
                                  
                                  {/* Call Type (Granular Category) */}
                                  {file.call_record.call_type && (
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="text-xs text-gray-600 font-medium">Type:</span>
                                      <Badge variant="outline" className={isHeuristic ? 'opacity-75' : ''}>
                                        {file.call_record.call_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                      </Badge>
                                    </div>
                                  )}
                                  
                                  {file.call_record.categorization_confidence && (
                                    <p className={`text-xs mt-1 ${isHeuristic ? 'text-gray-400' : 'text-gray-500'}`}>
                                      Confidence: {(file.call_record.categorization_confidence * 100).toFixed(0)}%
                                      {isHeuristic && " (Hardcoded)"}
                                    </p>
                                  )}
                                  {file.call_record.categorization_notes && (
                                    <p className={`text-xs mt-1 italic ${isHeuristic ? 'text-gray-400' : 'text-gray-600'}`}>
                                      {file.call_record.categorization_notes.replace(" [HEURISTIC]", "")}
                                    </p>
                                  )}
                                  {/* Generate/View Action Plan button for unsuccessful calls */}
                                  {file.call_record && file.call_record.call_category !== 'consult_scheduled' &&
                                    file.call_record.transcript && file.call_record.transcript !== 'Processing...' && file.call_record.transcript !== 'Transcribing audio...' && (
                                    <div className="mt-2 flex gap-2">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        disabled={generatingPlans.has(file.call_record.id)}
                                        onClick={async (e) => {
                                          e.stopPropagation();
                                          const callRecordId = file.call_record?.id;
                                          if (!callRecordId) return;
                                          
                                          // Check if plan already exists
                                          try {
                                            const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
                                            const token = sessionData?.session?.access_token;
                                            const { supabase: supabaseClient } = await import('@/integrations/supabase/client');
                                            const userId = (user as any)?.id;
                                            
                                            if (userId) {
                                              const { data: existingPlan } = await supabaseClient
                                                .from('follow_up_plans')
                                                .select('id')
                                                .eq('call_record_id', callRecordId)
                                                .eq('user_id', userId)
                                                .maybeSingle();
                                              
                                              if (existingPlan) {
                                                // Plan exists, open view panel
                                                setCallRecordWithPlan({
                                                  callRecordId,
                                                  transcript: file.call_record.transcript,
                                                  customerName: jobStatus?.customer_name || 'Customer'
                                                });
                                                setSelectedCallRecordId(callRecordId);
                                                setPlanPanelOpen(true);
                                                return;
                                              }
                                            }
                                          } catch (checkErr) {
                                            console.warn('Error checking for existing plan:', checkErr);
                                          }
                                          
                                          // No plan exists, generate one
                                          setGeneratingPlans(prev => new Set(prev).add(callRecordId));
                                          try {
                                            const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
                                            const token = sessionData?.session?.access_token;
                                            const salespersonName = (user as any)?.user_metadata?.full_name || (user as any)?.email || 'Salesperson';
                                            const analysisData: any = {
                                              objections: file.objections || [],
                                              objection_overcomes: file.objection_overcomes || [],
                                              category: file.call_record.call_category,
                                              call_type: file.call_record.call_type,
                                              confidence: file.call_record.categorization_confidence,
                                              notes: file.call_record.categorization_notes,
                                            };
                                            const resp = await fetch(`${API_BASE_URL}/api/call-center/followup/generate`, {
                                              method: 'POST',
                                              headers: {
                                                'Authorization': `Bearer ${token}`,
                                                'Content-Type': 'application/json',
                                              },
                                              body: JSON.stringify({
                                                callRecordId,
                                                transcript: file.call_record.transcript,
                                                analysisData,
                                                customerName: jobStatus?.customer_name || 'Customer',
                                                salespersonName,
                                                provider: 'auto'
                                              })
                                            });
                                            if (!resp.ok) {
                                              const error = await resp.text();
                                              throw new Error(error || 'Failed to generate follow-up plan');
                                            }
                                            toast({
                                              title: 'Action plan generated',
                                              description: 'A 5-day follow-up plan (3 touchpoints) has been created for this call.',
                                            });
                                            // Mark this call as having a plan
                                            setCallsWithPlans(prev => new Set(prev).add(callRecordId));
                                            // Open the plan panel after generation
                                            setCallRecordWithPlan({
                                              callRecordId,
                                              transcript: file.call_record.transcript,
                                              customerName: jobStatus?.customer_name || 'Customer'
                                            });
                                            setSelectedCallRecordId(callRecordId);
                                            setPlanPanelOpen(true);
                                          } catch (err) {
                                            console.error('Generate plan error:', err);
                                            toast({
                                              title: 'Error',
                                              description: err instanceof Error ? err.message : 'Failed to generate action plan',
                                              variant: 'destructive',
                                            });
                                          } finally {
                                            setGeneratingPlans(prev => {
                                              const next = new Set(prev);
                                              next.delete(callRecordId);
                                              return next;
                                            });
                                          }
                                        }}
                                        className="h-7 text-xs"
                                      >
                                        {generatingPlans.has(file.call_record.id) ? (
                                          <>
                                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                            Generating Plan...
                                          </>
                                        ) : callsWithPlans.has(file.call_record.id) ? (
                                          <>
                                            <Target className="h-3 w-3 mr-1" />
                                            View Action Plan
                                          </>
                                        ) : (
                                          <>
                                            <Send className="h-3 w-3 mr-1" />
                                            Generate 5-Day Action Plan
                                          </>
                                        )}
                                      </Button>
                                    </div>
                                  )}
                                </>
                              );
                            })()}
                          </div>
                        </div>
                      )}

                      {/* Transcript */}
                      {file.call_record && file.call_record.transcript && 
                       file.call_record.transcript !== "Processing..." && 
                       file.call_record.transcript !== "Transcribing audio..." && 
                       file.call_record.transcript.trim().length > 0 &&
                       !retranscribing.has(file.call_record.id || '') && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <MessageSquare className={`h-4 w-4 ${
                                file.call_record.transcript.includes("timeout") || file.call_record.transcript.includes("Transcription timeout") || file.call_record.transcript.toLowerCase().includes("error")
                                  ? "text-orange-600" 
                                  : "text-green-600"
                              }`} />
                              <h4 className="text-sm font-semibold">Transcript</h4>
                            </div>
                            {/* Show retranscribe button if we have a call_record_id and not currently retranscribing */}
                            {file.call_record?.id && !retranscribing.has(file.call_record.id) && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  if (!file.call_record?.id) return;
                                  
                                  const callRecordId = file.call_record.id;
                                  console.log(`🔄 Frontend: Retranscribe button clicked for call_record_id=${callRecordId}`);
                                  setRetranscribing(prev => new Set(prev).add(callRecordId));
                                  
                                  try {
                                    const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
                                    const token = sessionData?.session?.access_token;
                                    
                                    console.log(`🔄 Frontend: Making POST request to /api/bulk-import/retranscribe/${callRecordId}`);
                                    const response = await fetch(
                                      `${API_BASE_URL}/api/bulk-import/retranscribe/${callRecordId}`,
                                      {
                                        method: 'POST',
                                        headers: {
                                          'Authorization': `Bearer ${token}`,
                                          'Content-Type': 'application/json',
                                        },
                                      }
                                    );
                                    
                                    console.log(`🔄 Frontend: Response status=${response.status}, ok=${response.ok}`);
                                    
                                    if (!response.ok) {
                                      const error = await response.json().catch(() => ({ detail: 'Failed to retranscribe' }));
                                      throw new Error(error.detail || 'Failed to retranscribe');
                                    }
                                    
                                    toast({
                                      title: "Transcription restarted",
                                      description: "Transcription has been restarted. Please wait for it to complete.",
                                    });
                                    
                                    // Optimistically update the UI immediately to show "Processing..." and clear analysis data
                                    // This ensures the UI updates instantly without waiting for server response
                                    if (jobStatus?.files) {
                                      const updatedFiles = jobStatus.files.map((f: BulkImportFile) => {
                                        // Match by call_record_id (most reliable) or file id
                                        const matchesById = f.call_record?.id === callRecordId;
                                        const matchesByFileId = f.id === file.id;
                                        
                                        if (matchesById || matchesByFileId) {
                                          return {
                                            ...f,
                                            call_record: {
                                              ...(f.call_record || {}),
                                              id: callRecordId, // Ensure call_record_id is set
                                              transcript: "Processing...",
                                              call_category: undefined,
                                              categorization_confidence: undefined,
                                              categorization_notes: undefined
                                            },
                                            objections: [], // Clear objections
                                            objection_overcomes: [] // Clear objection overcomes
                                          };
                                        }
                                        return f;
                                      });
                                      
                                      setJobStatus({
                                        ...jobStatus,
                                        files: updatedFiles
                                      });
                                      
                                      // Force a re-render by updating retranscribing state
                                      setRetranscribing(prev => new Set(prev).add(callRecordId));
                                    }
                                    
                                    // Start aggressive polling for retranscription
                                    let pollCount = 0;
                                    const maxPolls = 60; // Poll for up to 5 minutes (60 * 5s = 300s)
                                    const pollInterval = setInterval(() => {
                                      pollCount++;
                                      if (currentJobId) {
                                        fetchJobStatus(currentJobId);
                                      }
                                      
                                      // Stop polling if we've exceeded max attempts or if transcript is no longer "Processing..."
                                      const shouldStop = pollCount >= maxPolls;
                                      if (shouldStop) {
                                        clearInterval(pollInterval);
                                      }
                                    }, 5000);
                                    
                                    // Also refresh immediately after a short delay to get real status
                                    setTimeout(() => {
                                      if (currentJobId) {
                                        fetchJobStatus(currentJobId);
                                      }
                                    }, 2000);
                                    
                                    // Don't clear retranscribing state here - let it persist until we get confirmation
                                    // The state will be cleared automatically when fetchJobStatus sees the transcript is no longer "Processing..."
                                  } catch (error) {
                                    toast({
                                      title: "Error",
                                      description: error instanceof Error ? error.message : "Failed to retranscribe",
                                      variant: "destructive",
                                    });
                                    // Only clear retranscribing state on error
                                    setRetranscribing(prev => {
                                      const newSet = new Set(prev);
                                      newSet.delete(callRecordId);
                                      return newSet;
                                    });
                                  }
                                }}
                                disabled={retranscribing.has(file.call_record.id || '')}
                                className="h-7 text-xs"
                              >
                                {retranscribing.has(file.call_record.id || '') ? (
                                  <>
                                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                    Retranscribing...
                                  </>
                                ) : (
                                  <>
                                    <RotateCw className="h-3 w-3 mr-1" />
                                    Retranscribe
                                  </>
                                )}
                              </Button>
                            )}
                          </div>
                          <div className={`ml-6 p-3 rounded border max-h-64 overflow-y-auto ${
                            file.call_record.transcript.includes("timeout") || file.call_record.transcript.includes("Transcription timeout") || file.call_record.transcript.toLowerCase().includes("error")
                              ? "bg-orange-50 border-orange-200"
                              : "bg-gray-50 border-gray-200"
                          }`}>
                            <p className={`text-sm whitespace-pre-wrap ${
                              file.call_record.transcript.includes("timeout") || file.call_record.transcript.includes("Transcription timeout") || file.call_record.transcript.toLowerCase().includes("error")
                                ? "text-orange-800"
                                : "text-gray-700"
                            }`}>
                              {file.call_record.transcript}
                            </p>
                          </div>
                        </div>
                      )}
                      
                      {/* Show loading message if transcript is still processing */}
                      {file.call_record && 
                       file.call_record.transcript && 
                       (file.call_record.transcript === "Processing..." || 
                        file.call_record.transcript === "Transcribing audio...") && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <MessageSquare className="h-4 w-4 text-blue-600" />
                              <h4 className="text-sm font-semibold">Transcript</h4>
                            </div>
                            <div className="flex items-center space-x-2">
                              {retranscribing.has(file.call_record.id || '') && (
                                <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  Retranscribing...
                                </Badge>
                              )}
                              {/* Always show retranscribe button if we have a call_record_id */}
                              {file.call_record?.id && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={async () => {
                                    if (!file.call_record?.id) return;
                                    
                                    const callRecordId = file.call_record.id;
                                    console.log(`🔄 Frontend: Retranscribe button clicked for call_record_id=${callRecordId}`);
                                    setRetranscribing(prev => new Set(prev).add(callRecordId));
                                    
                                    try {
                                      const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
                                      const token = sessionData?.session?.access_token;
                                      
                                      console.log(`🔄 Frontend: Making POST request to /api/bulk-import/retranscribe/${callRecordId}`);
                                      const response = await fetch(
                                        `${API_BASE_URL}/api/bulk-import/retranscribe/${callRecordId}`,
                                        {
                                          method: 'POST',
                                          headers: {
                                            'Authorization': `Bearer ${token}`,
                                            'Content-Type': 'application/json',
                                          },
                                        }
                                      );
                                      
                                      console.log(`🔄 Frontend: Response status=${response.status}, ok=${response.ok}`);
                                      
                                      if (!response.ok) {
                                        const error = await response.json().catch(() => ({ detail: 'Failed to retranscribe' }));
                                        throw new Error(error.detail || 'Failed to retranscribe');
                                      }
                                      
                                      toast({
                                        title: "Transcription restarted",
                                        description: "Transcription has been restarted. Please wait for it to complete.",
                                      });
                                      
                                      // Optimistically update the UI immediately to show "Processing..." and clear analysis data
                                      if (jobStatus?.files) {
                                        const updatedFiles = jobStatus.files.map((f: BulkImportFile) => {
                                          const matchesById = f.call_record?.id === callRecordId;
                                          const matchesByFileId = f.id === file.id;
                                          
                                          if (matchesById || matchesByFileId) {
                                            return {
                                              ...f,
                                              call_record: {
                                                ...(f.call_record || {}),
                                                id: callRecordId,
                                                transcript: "Processing...",
                                                call_category: undefined,
                                                categorization_confidence: undefined,
                                                categorization_notes: undefined
                                              },
                                              objections: [], // Clear objections
                                              objection_overcomes: [] // Clear objection overcomes
                                            };
                                          }
                                          return f;
                                        });
                                        
                                        setJobStatus({
                                          ...jobStatus,
                                          files: updatedFiles
                                        });
                                        
                                        setRetranscribing(prev => new Set(prev).add(callRecordId));
                                      }
                                      
                                      // Start aggressive polling for retranscription
                                      console.log(`🔄 Frontend: Starting aggressive polling for retranscription, currentJobId=${currentJobId}`);
                                      let pollCount = 0;
                                      const maxPolls = 60;
                                      const pollInterval = setInterval(() => {
                                        pollCount++;
                                        console.log(`🔄 Frontend: Polling attempt ${pollCount}/${maxPolls} for jobId=${currentJobId}`);
                                        if (currentJobId) {
                                          fetchJobStatus(currentJobId);
                                        }
                                        
                                        const shouldStop = pollCount >= maxPolls;
                                        if (shouldStop) {
                                          console.log(`🔄 Frontend: Stopping polling after ${maxPolls} attempts`);
                                          clearInterval(pollInterval);
                                        }
                                      }, 5000);
                                      
                                      setTimeout(() => {
                                        console.log(`🔄 Frontend: Immediate fetch after 2s delay for jobId=${currentJobId}`);
                                        if (currentJobId) {
                                          fetchJobStatus(currentJobId);
                                        }
                                      }, 2000);
                                    } catch (error) {
                                      toast({
                                        title: "Error",
                                        description: error instanceof Error ? error.message : "Failed to retranscribe",
                                        variant: "destructive",
                                      });
                                      setRetranscribing(prev => {
                                        const newSet = new Set(prev);
                                        newSet.delete(callRecordId);
                                        return newSet;
                                      });
                                    }
                                  }}
                                  disabled={retranscribing.has(file.call_record.id || '')}
                                  className="h-7 text-xs"
                                >
                                  {retranscribing.has(file.call_record.id || '') ? (
                                    <>
                                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                      Retranscribing...
                                    </>
                                  ) : (
                                    <>
                                      <RotateCw className="h-3 w-3 mr-1" />
                                      Retranscribe
                                    </>
                                  )}
                                </Button>
                              )}
                            </div>
                          </div>
                          <div className="ml-6 p-3 bg-blue-50 border border-blue-200 rounded">
                            <div className="flex items-center space-x-2">
                              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                              <div>
                                <p className="text-sm font-medium text-blue-900">
                                  {retranscribing.has(file.call_record.id || '') 
                                    ? "Retranscribing audio..." 
                                    : file.call_record.transcript === "Processing..." 
                                      ? "Transcript is being processed..." 
                                      : "Transcribing audio..."}
                                </p>
                                {(retranscribing.has(file.call_record.id || '') || (jobStatus.status === 'completed' && file.call_record.transcript === "Processing...")) && (
                                  <p className="text-xs text-blue-700 mt-1">
                                    {retranscribing.has(file.call_record.id || '') 
                                      ? "This may take a few minutes. The page will automatically update when complete."
                                      : "Transcription appears to be stuck. Click 'Retranscribe' to restart the process."}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Objections */}
                      {file.objections && file.objections.length > 0 && (
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <AlertTriangle className="h-4 w-4 text-orange-600" />
                            <h4 className="text-sm font-semibold">Objections Detected ({file.objections.length})</h4>
                          </div>
                          <div className="ml-6 space-y-3">
                            {[...file.objections]
                              .sort((a, b) => {
                                // Sort by confidence in descending order (highest first)
                                const aConf = a.confidence ?? 0;
                                const bConf = b.confidence ?? 0;
                                return bConf - aConf;
                              })
                              .map((objection) => {
                                const isHeuristic = objection.objection_text?.includes("[HEURISTIC]") || 
                                                    objection.transcript_segment === "Heuristic detection" ||
                                                    objection.confidence === 0.6;
                                const relatedOvercomes = (file.objection_overcomes || []).filter((o) => o.objection_id === objection.id);
                                return (
                                  <div key={objection.id} className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {/* Left: Objection card */}
                                    <div className={`p-3 border rounded ${
                                      isHeuristic 
                                        ? "bg-gray-100 border-gray-300 opacity-75" 
                                        : "bg-orange-50 border-orange-200"
                                    }`}>
                                      <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                          {isHeuristic && (
                                            <Badge variant="outline" className="mb-2 text-xs bg-gray-200 text-gray-600 border-gray-400">
                                              HEURISTIC (Not LLM)
                                            </Badge>
                                          )}
                                          <Badge variant="outline" className={`mb-2 ${isHeuristic ? 'ml-2' : ''}`}>
                                            {objection.objection_type?.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                          </Badge>
                                          <p className={`text-sm font-medium ${isHeuristic ? 'text-gray-600' : 'text-gray-900'}`}>
                                            {objection.objection_text?.replace(" [HEURISTIC]", "") || objection.objection_text}
                                          </p>
                                          {objection.transcript_segment && objection.transcript_segment !== "Heuristic detection" && (
                                            <p className={`text-xs mt-2 italic ${isHeuristic ? 'text-gray-500' : 'text-gray-600'}`}>
                                              "{objection.transcript_segment}"
                                            </p>
                                          )}
                                          {objection.confidence && (
                                            <p className={`text-xs mt-1 ${isHeuristic ? 'text-gray-400' : 'text-gray-500'}`}>
                                              Confidence: {(objection.confidence * 100).toFixed(0)}%
                                              {isHeuristic && " (Hardcoded)"}
                                            </p>
                                          )}
                                        </div>
                                      </div>
                                    </div>

                                    {/* Right: Resolution card(s) for this objection */}
                                    <div className="space-y-2">
                                      <div className="flex items-center space-x-2">
                                        <CheckCircle className="h-3 w-3 text-green-600" />
                                        <span className="text-xs font-semibold text-green-700">Resolution</span>
                                      </div>
                                      {relatedOvercomes.length > 0 ? (
                                        <div className="space-y-2">
                                          {relatedOvercomes.map((overcome) => {
                                            const relatedIsHeuristic = isHeuristic || overcome.confidence === 0.8;
                                            return (
                                              <div key={overcome.id} className={`p-3 border rounded ${relatedIsHeuristic ? 'bg-gray-100 border-gray-300 opacity-75' : 'bg-green-50 border-green-200'}`}>
                                                <p className={`text-sm font-medium ${relatedIsHeuristic ? 'text-gray-600' : 'text-gray-900'}`}>
                                                  {overcome.overcome_method}
                                                </p>
                                                {overcome.transcript_quote && (
                                                  <p className={`text-xs mt-1 italic ${relatedIsHeuristic ? 'text-gray-500' : 'text-gray-600'}`}>
                                                    "{overcome.transcript_quote}"
                                                  </p>
                                                )}
                                                {overcome.confidence && (
                                                  <p className={`text-xs mt-1 ${relatedIsHeuristic ? 'text-gray-400' : 'text-gray-500'}`}>
                                                    Confidence: {(overcome.confidence * 100).toFixed(0)}%
                                                    {relatedIsHeuristic && ' (Heuristic)'}
                                                  </p>
                                                )}
                                              </div>
                                            );
                                          })}
                                        </div>
                                      ) : (
                                        <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                                          <p className="text-xs text-gray-600">No resolution evidence detected yet for this objection.</p>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                          </div>
                        </div>
                      )}

                      {/* Objection Overcomes */}
                      {file.objection_overcomes && file.objection_overcomes.length > 0 && (!file.objections || file.objections.length === 0) && (
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <h4 className="text-sm font-semibold">Objection Overcomes ({file.objection_overcomes.length})</h4>
                          </div>
                          <div className="ml-6 space-y-3">
                            {file.objection_overcomes.map((overcome) => {
                              const relatedObjection = file.objections?.find(obj => obj.id === overcome.objection_id);
                              const isHeuristic = relatedObjection?.objection_text?.includes("[HEURISTIC]") ||
                                                 overcome.confidence === 0.8; // Default fallback confidence
                              return (
                                <div key={overcome.id} className={`p-3 border rounded ${
                                  isHeuristic 
                                    ? "bg-gray-100 border-gray-300 opacity-75" 
                                    : "bg-green-50 border-green-200"
                                }`}>
                                  <div className="space-y-2">
                                    {isHeuristic && (
                                      <Badge variant="outline" className="mb-2 text-xs bg-gray-200 text-gray-600 border-gray-400">
                                        HEURISTIC (Not LLM)
                                      </Badge>
                                    )}
                                    {relatedObjection && (
                                      <div>
                                        <Badge variant="outline" className="text-xs">
                                          {relatedObjection.objection_type?.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        </Badge>
                                      </div>
                                    )}
                                    <p className={`text-sm font-medium ${isHeuristic ? 'text-gray-600' : 'text-gray-900'}`}>
                                      {overcome.overcome_method}
                                    </p>
                                    {overcome.transcript_quote && (
                                      <p className={`text-xs mt-2 italic ${isHeuristic ? 'text-gray-500' : 'text-gray-600'}`}>
                                        "{overcome.transcript_quote}"
                                      </p>
                                    )}
                                    {overcome.confidence && (
                                      <p className={`text-xs mt-1 ${isHeuristic ? 'text-gray-400' : 'text-gray-500'}`}>
                                        Confidence: {(overcome.confidence * 100).toFixed(0)}%
                                        {isHeuristic && " (Hardcoded)"}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                                    {/* No Results Message or Loading State */}
                                    {!file.call_record ? (
                                      <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                                        <div className="flex items-center space-x-2">
                                          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                                          <p className="text-xs text-blue-800">
                                            {file.status === 'analyzing' 
                                              ? 'Analysis in progress... Results will appear here when ready.'
                                              : file.status === 'completed'
                                              ? 'Loading analysis results... This may take a few moments.'
                                              : 'Waiting for analysis to complete...'}
                                          </p>
                                        </div>
                                      </div>
                                    ) : !file.call_record.transcript && !file.objections?.length && file.status === 'completed' && (
                                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                                        <p className="text-xs text-yellow-800">
                                          Analysis completed but no results available yet. This may take a few moments to appear.
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      ) : jobStatus.total_files > 0 ? (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="text-sm text-yellow-800">
                            {jobStatus.total_files} file(s) found, but file details are not yet available. 
                            Files are being processed...
                          </p>
                        </div>
                      ) : null}
                    </div>
                  ) : jobStatus.status !== 'discovering' && jobStatus.status !== 'pending' ? (
                    <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                      <p className="text-sm text-gray-600">
                        No files found at the source URL. Please verify the URL contains audio files.
                      </p>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-gray-500">
                  No active import job. Start a new import to see status here.
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="history">
            {isLoadingJobs ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                  <p>Loading jobs...</p>
                </CardContent>
              </Card>
            ) : jobsList.length > 0 ? (
              <div className="space-y-4">
                {jobsList.map((job) => (
                  <Card key={job.job_id}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="font-semibold text-lg">{job.customer_name}</h3>
                          <p className="text-sm text-gray-500">
                            {new Date(job.created_at).toLocaleString()}
                          </p>
                        </div>
                        {getStatusBadge(job.status)}
                      </div>

                      <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between text-sm">
                          <span>Progress</span>
                          <span>{job.progress_percentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={job.progress_percentage} />
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Total:</span> {job.total_files}
                        </div>
                        <div>
                          <span className="text-gray-600">Processed:</span>{' '}
                          <span className="text-green-600">{job.processed_files}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Failed:</span>{' '}
                          <span className="text-red-600">{job.failed_files}</span>
                        </div>
                      </div>

                      {job.error_message && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                          {job.error_message}
                        </div>
                      )}

                      <div className="flex gap-2 mt-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            setCurrentJobId(job.job_id);
                            await fetchJobStatus(job.job_id);
                            // Switch to status tab
                            setActiveTab('status');
                          }}
                        >
                          View Details
                        </Button>
                        {(job.status === 'analyzing' || job.status === 'uploading' || job.status === 'converting') && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setCurrentJobId(job.job_id);
                              // Start polling
                              const interval = setInterval(() => {
                                fetchJobStatus(job.job_id);
                                if (jobStatus && (jobStatus.status === 'completed' || jobStatus.status === 'failed')) {
                                  clearInterval(interval);
                                }
                              }, 3000);
                            }}
                          >
                            <Clock className="mr-2 h-4 w-4" />
                            Monitor Progress
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-gray-500">
                  No import jobs found. Start a new import to see history here.
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
      
      {/* Right-side panel for viewing follow-up plan */}
      <Sheet open={planPanelOpen} onOpenChange={setPlanPanelOpen}>
        <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>5-Day Follow-Up Action Plan</SheetTitle>
            <SheetDescription>
              {callRecordWithPlan ? `Plan for ${callRecordWithPlan.customerName}` : 'Loading plan...'}
            </SheetDescription>
          </SheetHeader>
          {callRecordWithPlan && selectedCallRecordId && (
            <div className="mt-6">
              <FollowUpPlanPanel
                callId={selectedCallRecordId}
                transcript={callRecordWithPlan.transcript}
                analysisData={{
                  objections: jobStatus?.files?.find((f: BulkImportFile) => f.call_record?.id === selectedCallRecordId)?.objections || [],
                  objection_overcomes: jobStatus?.files?.find((f: BulkImportFile) => f.call_record?.id === selectedCallRecordId)?.objection_overcomes || [],
                  category: jobStatus?.files?.find((f: BulkImportFile) => f.call_record?.id === selectedCallRecordId)?.call_record?.call_category,
                }}
                customerName={callRecordWithPlan.customerName}
                salespersonName={(user as any)?.user_metadata?.full_name || (user as any)?.email || 'Salesperson'}
              />
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default BulkImportPage;

