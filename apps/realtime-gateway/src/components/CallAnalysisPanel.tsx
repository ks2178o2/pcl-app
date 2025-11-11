import React, { useState, memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  AlertTriangle, 
  CheckSquare, 
  TrendingUp, 
  Clock, 
  Users, 
  Target, 
  DollarSign, 
  Calendar,
  Settings,
  BarChart3,
  MessageSquare,
  BookOpen,
  Trophy,
  AlertCircle,
  Heart,
  Shield,
  RefreshCw,
  PlayCircle,
  Phone
} from 'lucide-react';
import { CallAnalysis, transcriptAnalysisService } from '@/services/transcriptAnalysisService';
import { SpeakerDiarizationPlayer } from './SpeakerDiarizationPlayer';
import { SpeakerMappingEditor } from './SpeakerMappingEditor';
import { EmailSender } from './EmailSender';
import { SMSSender } from './SMSSender';
import { TwilioDebugTest } from './TwilioDebugTest';
import { applyingSpeakerMapping } from '@/utils/speakerUtils';

interface CallAnalysisPanelProps {
  analysis: CallAnalysis | null;
  isLoading: boolean;
  analysisStatus?: {
    stage: 'waiting-transcript' | 'analyzing' | 'generating-insights' | 'complete' | 'error';
    message: string;
    progress: number; // 0-100
  } | null;
  transcript?: string;
  audioUrl?: string;
  onRegenerateTranscript?: () => void;
  regeneratingTranscript?: boolean;
  callDuration?: number;
  diarizationSegments?: any[];
  speakerMapping?: Record<string, string>;
  callRecordId?: string;
  customerName?: string;
  onSpeakerMappingUpdate?: (newMapping: Record<string, string>) => void;
  diarizationStatus?: string;
}

const CallAnalysisPanelComponent: React.FC<CallAnalysisPanelProps> = ({
  analysis,
  isLoading,
  analysisStatus,
  transcript,
  audioUrl,
  onRegenerateTranscript,
  regeneratingTranscript,
  callDuration = 300,
  diarizationSegments,
  speakerMapping,
  onSpeakerMappingUpdate,
  callRecordId,
  customerName,
  diarizationStatus
}) => {
  // Debug logging - only log when props actually change
  React.useEffect(() => {
    console.log('CallAnalysisPanel rendered with callRecordId:', callRecordId);
  }, [callRecordId]);
  const [isSpeakerEditorOpen, setIsSpeakerEditorOpen] = useState(false);
  const [currentSpeakerMapping, setCurrentSpeakerMapping] = useState<Record<string, string>>(speakerMapping || {});
  const [isSMSSenderOpen, setIsSMSSenderOpen] = useState(false);
  const [isEmailSenderOpen, setIsEmailSenderOpen] = useState(false);

  const safeReplace = (value: any, search: string, replaceWith: string) => {
    return typeof value === 'string' ? value.replace(search, replaceWith) : (value || '');
  };

  // Sync mapping when prop updates (e.g., after saving)
  React.useEffect(() => {
    setCurrentSpeakerMapping(speakerMapping || {});
  }, [speakerMapping]);

  const handleSpeakerMappingSave = (newMapping: Record<string, string>) => {
    setCurrentSpeakerMapping(newMapping);
    onSpeakerMappingUpdate?.(newMapping);
    setIsSpeakerEditorOpen(false);
  };
  if (isLoading) {
    const statusMessage = analysisStatus?.message || 'Analyzing transcript...';
    const progress = analysisStatus?.progress || 0;
    const stage = analysisStatus?.stage || 'analyzing';
    
    // Get icon based on stage
    const getStageIcon = () => {
      switch (stage) {
        case 'waiting-transcript':
          return <Clock className="h-5 w-5 animate-pulse" />;
        case 'analyzing':
          return <TrendingUp className="h-5 w-5 animate-pulse" />;
        case 'generating-insights':
          return <BarChart3 className="h-5 w-5 animate-pulse" />;
        case 'error':
          return <AlertCircle className="h-5 w-5 text-destructive" />;
        default:
          return <RefreshCw className="h-5 w-5 animate-spin" />;
      }
    };

    // Get stage label
    const getStageLabel = () => {
      switch (stage) {
        case 'waiting-transcript':
          return 'Waiting for Transcript';
        case 'analyzing':
          return 'Checking Analysis';
        case 'generating-insights':
          return 'Generating Insights';
        case 'error':
          return 'Error';
        default:
          return 'Processing';
      }
    };

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStageIcon()}
            Call Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{getStageLabel()}</span>
              <span className="text-muted-foreground">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground text-center">
              {statusMessage}
            </p>
          </div>
          
          {stage === 'waiting-transcript' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-900">
                The audio file is being transcribed. This typically takes 1-2 minutes depending on the length of the recording.
              </p>
            </div>
          )}
          
          {stage === 'generating-insights' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-sm text-amber-900">
                Our AI is analyzing the conversation and generating insights. This may take 30-60 seconds.
              </p>
            </div>
          )}
          
          {stage === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-900">
                {statusMessage}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (!analysis) {
    return (
      <div className="space-y-6">
        {audioUrl && transcript && !transcript.includes('failed') && transcript !== 'Transcribing audio...' && (
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium flex items-center gap-2">
                <PlayCircle className="h-4 w-4" />
                Interactive Audio & Speaker Transcript
              </h4>
              {diarizationSegments && diarizationSegments.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsSpeakerEditorOpen(true)}
                  className="flex items-center gap-2"
                >
                  <Settings className="h-4 w-4" />
                  Edit Speakers
                </Button>
              )}
            </div>

        <SpeakerDiarizationPlayer
              audioUrl={audioUrl}
              transcript={transcript}
              diarizationSegments={diarizationSegments}
              speakerMapping={currentSpeakerMapping}
              duration={callDuration}
          persistKey={callRecordId || undefined}
            />

            <SpeakerMappingEditor
              isOpen={isSpeakerEditorOpen}
              onClose={() => setIsSpeakerEditorOpen(false)}
              speakerMapping={currentSpeakerMapping}
              onSave={handleSpeakerMappingSave}
              diarizationSegments={diarizationSegments || []}
              confidence={diarizationSegments?.[0]?.confidence || 0.85}
            />
          </div>
        )}
      </div>
    );
  }

  // If analysis exists but is missing expected nested fields, render a safe fallback
  const isAnalysisComplete = Boolean(
    (analysis as any)?.sentiment &&
    (analysis as any)?.customerPersonality &&
    (analysis as any)?.urgencyScoring &&
    (analysis as any)?.salesPerformance &&
    (analysis as any)?.financialPsychology
  );

  if (!isAnalysisComplete) {
    return (
      <div className="space-y-6">
        {transcript && !transcript.includes('failed') && transcript !== 'Transcribing audio...' && (
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium flex items-center gap-2">
                <PlayCircle className="h-4 w-4" />
                Transcript
              </h4>
            </div>
            <ScrollArea className="h-64 rounded border p-3 bg-muted/30">
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                {transcript}
              </div>
            </ScrollArea>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Analysis in progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Some analysis sections aren’t available yet. This usually resolves once processing completes.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Safe aliases with defaults to avoid undefined property access
  const s = analysis.sentiment || { overall: 'neutral', customerEngagement: 0, interestLevel: 0, concerns: [] };
  const cp = analysis.customerPersonality || { personalityType: 'research-driven', motivationCategory: 'health-driven', communicationStyle: { preferredTone: 'professional', informationDepth: 'detailed', decisionSpeed: 'deliberate' }, psychographics: { riskTolerance: 'moderate', socialInfluence: 'medium', qualityFocus: 'value' }, behavioralIndicators: [], confidence: 0.7 } as any;
  const us = analysis.urgencyScoring || { overallUrgency: 0, urgencyFactors: { timelinePressure: 0, emotionalState: 0, financialWindow: 0, seasonalFactors: 0, socialPressure: 0 }, buyingSignals: [], delayIndicators: [], urgencyTriggers: [] };
  const fs = analysis.financialPsychology || { paymentComfort: 'flexible', priceAnchor: 'value-focused', financialDecisionStyle: 'analytical', investmentMindset: 'improvement', budgetRange: 'Not specified', financingInterest: false, valuePerception: 0 } as any;

  const getPersonalityColor = (type: string) => {
    const colors = {
      'research-driven': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300',
      'trust-focused': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300',
      'results-oriented': 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300',
      'price-conscious': 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300',
      'impulse-emotional': 'bg-pink-100 text-pink-800 dark:bg-pink-900/20 dark:text-pink-300'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
  };

  const getUrgencyColor = (urgency: number) => {
    if (urgency >= 8) return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
    if (urgency >= 6) return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300';
    if (urgency >= 4) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
    return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Healthcare Consumer Analysis</h3>
        </div>
        {analysis && (
          <Badge variant="secondary" className="text-xs">
            {analysis.modelUsed}
          </Badge>
        )}
      </div>

      {/* Transcript + Player */}
      {diarizationStatus && (
        <div className="text-xs text-muted-foreground border rounded-md p-2 bg-muted/30">
          {diarizationStatus}
        </div>
      )}
      {transcript && !transcript.includes('failed') && transcript !== 'Transcribing audio...' && (
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium flex items-center gap-2">
              <PlayCircle className="h-4 w-4" />
              Transcript & Speakers
            </h4>
            {diarizationSegments && diarizationSegments.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsSpeakerEditorOpen(true)}
                className="flex items-center gap-2"
              >
                <Settings className="h-4 w-4" />
                Edit Speakers
              </Button>
            )}
          </div>
          {(audioUrl && diarizationSegments && diarizationSegments.length > 0) ? (
            <SpeakerDiarizationPlayer
              audioUrl={audioUrl}
              transcript={transcript}
              diarizationSegments={diarizationSegments}
              speakerMapping={currentSpeakerMapping}
              duration={callDuration}
            />
          ) : (
            <ScrollArea className="h-64 rounded border p-3 bg-muted/30">
              <div className="space-y-2 text-sm">
                {(function() {
                  if (diarizationSegments && diarizationSegments.length > 0 && currentSpeakerMapping) {
                    try {
                      const { generateMappedTranscript } = require('@/utils/speakerUtils');
                      const mapped = generateMappedTranscript(diarizationSegments, currentSpeakerMapping);
                      return mapped.split('\n').map((line: string, idx: number) => (
                        <div key={idx}>{line}</div>
                      ));
                    } catch {
                      return transcript.split('\n').map((line, idx) => (<div key={idx}>{line}</div>));
                    }
                  }
                  return transcript.split('\n').map((line, idx) => (<div key={idx}>{line}</div>));
                })()}
              </div>
            </ScrollArea>
          )}

          <SpeakerMappingEditor
            isOpen={isSpeakerEditorOpen}
            onClose={() => setIsSpeakerEditorOpen(false)}
            speakerMapping={currentSpeakerMapping}
            onSave={handleSpeakerMappingSave}
            diarizationSegments={diarizationSegments || []}
            confidence={diarizationSegments?.[0]?.confidence || 0.85}
          />
        </div>
      )}

      {/* Persist active tab per call id */}
      <Tabs 
        defaultValue={(typeof window !== 'undefined' && callRecordId) ? (sessionStorage.getItem(`analysisTab:${callRecordId}`) || 'overview') : 'overview'} 
        onValueChange={(val) => {
          if (typeof window !== 'undefined' && callRecordId) {
            try { sessionStorage.setItem(`analysisTab:${callRecordId}`, val); } catch {}
          }
        }}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          <TabsTrigger value="psychology">Psychology</TabsTrigger>
          <TabsTrigger value="urgency">Urgency</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="coaching">Coaching</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">{/* Responsive scrollable container */}
              {/* Summary */}
              <div>
                <h4 className="font-medium mb-2">Consultation Summary</h4>
                <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
                  {analysis.summary}
                </p>
              </div>

              <Separator className="my-6" />

              {/* Customer Personality Overview */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Customer Profile
                </h4>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Personality Type:</span>
                      <Badge className={getPersonalityColor(analysis.customerPersonality?.personalityType || '')}>
                        {safeReplace(analysis.customerPersonality?.personalityType, '-', ' ')}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Motivation:</span>
                      <Badge variant="outline">
                        {safeReplace(analysis.customerPersonality?.motivationCategory, '-', ' ')}
                      </Badge>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Profile Confidence</span>
                      <span>{Math.round(analysis.customerPersonality.confidence * 100)}%</span>
                    </div>
                    <Progress value={analysis.customerPersonality.confidence * 100} className="h-2" />
                  </div>
                  
                  {/* Communication Preferences */}
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div className="text-center p-2 bg-muted rounded-lg">
                      <div className="font-medium">Tone</div>
                      <div className="capitalize">{analysis.customerPersonality.communicationStyle.preferredTone}</div>
                    </div>
                    <div className="text-center p-2 bg-muted rounded-lg">
                      <div className="font-medium">Info Depth</div>
                      <div className="capitalize">{analysis.customerPersonality.communicationStyle.informationDepth}</div>
                    </div>
                    <div className="text-center p-2 bg-muted rounded-lg">
                      <div className="font-medium">Decision Speed</div>
                      <div className="capitalize">{analysis.customerPersonality.communicationStyle.decisionSpeed}</div>
                    </div>
                  </div>
                </div>
              </div>

              <Separator className="my-6" />

              {/* Sentiment Analysis */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  {transcriptAnalysisService.getSentimentIcon(s.overall as any)}
                  Sentiment Analysis
                </h4>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div className="text-center p-2 bg-muted rounded-lg">
                    <div className="font-medium">Overall</div>
                    <div className={`capitalize ${transcriptAnalysisService.getSentimentColor((s.overall as any) || 'neutral')}`}>
                      {s.overall}
                    </div>
                  </div>
                  <div className="text-center p-2 bg-muted rounded-lg">
                    <div className="font-medium">Engagement</div>
                    <div className="text-lg">{s.customerEngagement}/10</div>
                  </div>
                  <div className="text-center p-2 bg-muted rounded-lg">
                    <div className="font-medium">Interest</div>
                    <div className="text-lg">{s.interestLevel}/10</div>
                  </div>
                </div>
                {(s.concerns || []).length > 0 && (
                  <div className="mt-3">
                    <div className="font-medium text-sm mb-2">Key Concerns:</div>
                    <div className="flex flex-wrap gap-1">
                      {s.concerns.map((concern, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {concern}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <Separator className="my-6" />

              {/* Objections & Action Items */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Objections ({analysis.objections.length})
                  </h4>
                  {analysis.objections.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No objections detected</p>
                  ) : (
                    <div className="space-y-2">
                      {analysis.objections.slice(0, 3).map((objection, index) => (
                        <div key={index} className="border rounded-lg p-3 text-sm">
                          <div className="flex items-center justify-between mb-1">
                            <Badge className={transcriptAnalysisService.getObjectionTypeColor(objection.type)}>
                              {safeReplace(objection.type, '-', ' ')}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(objection.confidence * 100)}%
                            </span>
                          </div>
                          <p className="font-medium">{objection.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <CheckSquare className="h-4 w-4" />
                    Action Items ({analysis.actionItems.length})
                  </h4>
                  {analysis.actionItems.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No action items identified</p>
                  ) : (
                    <div className="space-y-2">
                      {analysis.actionItems.slice(0, 3).map((item, index) => (
                        <div key={index} className="border rounded-lg p-3 text-sm">
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-1">
                              <span>{transcriptAnalysisService.getActionItemTypeIcon(item.type)}</span>
                              <Badge className={transcriptAnalysisService.getPriorityColor(item.priority)}>
                                {item.priority}
                              </Badge>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(item.confidence * 100)}%
                            </span>
                          </div>
                          <p className="font-medium">{item.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="psychology" className="space-y-6 mt-6">
          <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">{/* Responsive scrollable container */}
              {/* Customer Personality Deep Dive */}
              <div className="mb-6">
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Customer Personality Analysis
                </h4>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 border rounded-lg">
                      <div className="font-medium text-sm mb-2">Risk Tolerance</div>
                      <Badge variant="outline">{analysis.customerPersonality.psychographics.riskTolerance}</Badge>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <div className="font-medium text-sm mb-2">Social Influence</div>
                      <Badge variant="outline">{analysis.customerPersonality.psychographics.socialInfluence}</Badge>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <div className="font-medium text-sm mb-2">Quality Focus</div>
                      <Badge variant="outline">{analysis.customerPersonality.psychographics.qualityFocus}</Badge>
                    </div>
                  </div>
                  
                  {analysis.customerPersonality.behavioralIndicators.length > 0 && (
                    <div>
                      <div className="font-medium text-sm mb-2">Behavioral Indicators:</div>
                      <div className="space-y-1">
                        {analysis.customerPersonality.behavioralIndicators.map((indicator, index) => (
                          <div key={index} className="text-sm text-muted-foreground bg-muted p-2 rounded">
                            {indicator}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Trust & Safety */}
              <div className="my-6">
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Trust & Safety Analysis
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Trust Level:</span>
                    <div className="flex items-center gap-2">
                      <Progress value={analysis.trustAndSafety.trustLevel * 10} className="w-20 h-2" />
                      <span className="text-sm">{analysis.trustAndSafety.trustLevel}/10</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="font-medium mb-2">Credibility Needs:</div>
                      <div className="space-y-1">
                        {analysis.trustAndSafety.credibilityNeeds.map((need, index) => (
                          <div key={index} className="text-xs bg-muted p-1 rounded">{need}</div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="font-medium mb-2">Risk Concerns:</div>
                      <div className="space-y-1">
                        {analysis.trustAndSafety.riskConcerns.map((concern, index) => (
                          <div key={index} className="text-xs bg-muted p-1 rounded">{concern}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {analysis.trustAndSafety.socialProofNeeds.length > 0 && (
                    <div>
                      <div className="font-medium text-sm mb-2">Social Proof Needs:</div>
                      <div className="flex flex-wrap gap-1">
                        {analysis.trustAndSafety.socialProofNeeds.map((proof, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {proof}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Financial Psychology */}
              <div className="my-6">
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Financial Psychology
                </h4>
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 border rounded-lg text-center">
                      <div className="font-medium text-sm mb-1">Payment Style</div>
                      <Badge variant="outline">{analysis.financialPsychology.paymentComfort}</Badge>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <div className="font-medium text-sm mb-1">Price Focus</div>
                      <Badge variant="outline">{safeReplace(analysis.financialPsychology?.priceAnchor, '-', ' ')}</Badge>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <div className="font-medium text-sm mb-1">Decision Style</div>
                      <Badge variant="outline">{analysis.financialPsychology.financialDecisionStyle}</Badge>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Value Perception:</span>
                    <div className="flex items-center gap-2">
                      <Progress value={analysis.financialPsychology.valuePerception * 10} className="w-20 h-2" />
                      <span className="text-sm">{analysis.financialPsychology.valuePerception}/10</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><strong>Investment Mindset:</strong> {analysis.financialPsychology.investmentMindset}</div>
                    <div><strong>Budget Range:</strong> {analysis.financialPsychology.budgetRange}</div>
                    <div><strong>Financing Interest:</strong> {analysis.financialPsychology.financingInterest ? 'Yes' : 'No'}</div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Personalized Recommendations */}
              <div className="my-6">
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Personalized Recommendations
                </h4>
                {analysis.personalizedRecommendations.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No specific recommendations generated</p>
                ) : (
                  <div className="space-y-3">
                    {analysis.personalizedRecommendations.map((rec, index) => (
                      <div key={index} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <Badge variant="outline">{rec.category}</Badge>
                          <Badge className={transcriptAnalysisService.getPriorityColor(rec.priority)}>
                            {rec.priority}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium mb-1">{rec.recommendation}</p>
                        <p className="text-xs text-muted-foreground mb-2">{rec.reasoning}</p>
                        <div className="text-xs">
                          <div><strong>Content:</strong> {rec.suggestedContent}</div>
                          <div><strong>Expected Impact:</strong> {rec.expectedImpact}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="urgency" className="space-y-6 mt-6">
          <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">
            {/* Overall Urgency */}
            <div className="mb-6">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Urgency Analysis
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Overall Urgency:</span>
                  <div className="flex items-center gap-2">
                    <Badge className={getUrgencyColor(analysis.urgencyScoring.overallUrgency)}>
                      {analysis.urgencyScoring.overallUrgency}/10
                    </Badge>
                  </div>
                </div>
                
                <Progress value={analysis.urgencyScoring.overallUrgency * 10} className="h-3" />
                
                {/* Urgency Factors Breakdown */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Timeline Pressure:</span>
                      <span>{analysis.urgencyScoring.urgencyFactors.timelinePressure}/10</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Emotional State:</span>
                      <span>{analysis.urgencyScoring.urgencyFactors.emotionalState}/10</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Financial Window:</span>
                      <span>{analysis.urgencyScoring.urgencyFactors.financialWindow}/10</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Seasonal Factors:</span>
                      <span>{analysis.urgencyScoring.urgencyFactors.seasonalFactors}/10</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Social Pressure:</span>
                      <span>{analysis.urgencyScoring.urgencyFactors.socialPressure}/10</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* Buying Signals */}
            <div className="my-6">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Buying Signals
              </h4>
              {analysis.urgencyScoring.buyingSignals.length === 0 ? (
                <p className="text-sm text-muted-foreground">No strong buying signals detected</p>
              ) : (
                <div className="space-y-2">
                  {analysis.urgencyScoring.buyingSignals.map((signal, index) => (
                    <div key={index} className="text-sm bg-green-50 dark:bg-green-900/20 p-2 rounded border-l-4 border-green-500">
                      ✅ {signal}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Delay Indicators */}
            <div className="my-6">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Delay Indicators
              </h4>
              {analysis.urgencyScoring.delayIndicators.length === 0 ? (
                <p className="text-sm text-muted-foreground">No delay indicators detected</p>
              ) : (
                <div className="space-y-2">
                  {analysis.urgencyScoring.delayIndicators.map((indicator, index) => (
                    <div key={index} className="text-sm bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded border-l-4 border-yellow-500">
                      ⚠️ {indicator}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Urgency Triggers */}
            <div className="my-6">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Urgency Triggers
              </h4>
              {analysis.urgencyScoring.urgencyTriggers.length === 0 ? (
                <p className="text-sm text-muted-foreground">No urgency triggers identified</p>
              ) : (
                <div className="space-y-2">
                  {analysis.urgencyScoring.urgencyTriggers.map((trigger, index) => (
                    <div key={index} className="text-sm bg-blue-50 dark:bg-blue-900/20 p-2 rounded border-l-4 border-blue-500">
                      🎯 {trigger}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6 mt-6">
          <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">
            {/* Sales Performance Metrics */}
            <div className="mb-6">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Sales Performance
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Talk Ratio</span>
                      <span>{analysis.salesPerformance.talkRatio}%</span>
                    </div>
                    <Progress value={analysis.salesPerformance.talkRatio} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Questioning Quality</span>
                      <span>{analysis.salesPerformance.questioningQuality}/10</span>
                    </div>
                    <Progress value={analysis.salesPerformance.questioningQuality * 10} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Listening Score</span>
                      <span>{analysis.salesPerformance.listeningScore}/10</span>
                    </div>
                    <Progress value={analysis.salesPerformance.listeningScore * 10} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Rapport Building</span>
                      <span>{analysis.salesPerformance.rapportBuilding}/10</span>
                    </div>
                    <Progress value={analysis.salesPerformance.rapportBuilding * 10} className="h-2" />
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Needs Discovery</span>
                      <span>{analysis.salesPerformance.needsDiscovery}/10</span>
                    </div>
                    <Progress value={analysis.salesPerformance.needsDiscovery * 10} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Presentation</span>
                      <span>{analysis.salesPerformance.presentationEffectiveness}/10</span>
                    </div>
                    <Progress value={analysis.salesPerformance.presentationEffectiveness * 10} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Objection Handling</span>
                      <span>{analysis.salesPerformance.objectionHandling}/10</span>
                    </div>
                    <Progress value={analysis.salesPerformance.objectionHandling * 10} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Closing Attempts</span>
                      <span>{analysis.salesPerformance.closingAttempts}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* Strengths and Improvements */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Trophy className="h-4 w-4" />
                  Strengths
                </h4>
                {analysis.salesPerformance.strengths.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No strengths identified</p>
                ) : (
                  <div className="space-y-2">
                    {analysis.salesPerformance.strengths.map((strength, index) => (
                      <div key={index} className="text-sm bg-green-50 dark:bg-green-900/20 p-2 rounded">
                        ✅ {strength}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Areas for Improvement
                </h4>
                {analysis.salesPerformance.improvementAreas.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No improvement areas identified</p>
                ) : (
                  <div className="space-y-2">
                    {analysis.salesPerformance.improvementAreas.map((area, index) => (
                      <div key={index} className="text-sm bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded">
                        💡 {area}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="transcript" className="space-y-6 mt-6">
          <div className="space-y-6">
            {/* Follow-up Actions */}
            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
              <div>
                <h4 className="font-medium mb-1">Follow-up Actions</h4>
                <p className="text-sm text-muted-foreground">
                  Send personalized follow-up emails or SMS based on this conversation
                </p>
              </div>
              <div className="flex gap-2">
                <EmailSender
                  callRecordId={callRecordId || ''}
                  customerName={customerName || 'Customer'}
                  analysisData={analysis}
                  triggerLabel="Send Email"
                  triggerVariant="default"
                  triggerSize="sm"
                />
                <Button
                  onClick={() => setIsSMSSenderOpen(true)}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <MessageSquare className="h-4 w-4" />
                  Send SMS
                </Button>
              </div>
            </div>

            {/* Follow-up Activities Timeline */}
            

            {/* SMS Modal Component */}
            <SMSSender
              isOpen={isSMSSenderOpen}
              onClose={() => setIsSMSSenderOpen(false)}
              callRecordId={callRecordId || ''}
              customerName={customerName || 'Customer'}
              analysisData={analysis}
            />
            
            {/* Transcript Tab Content - Text Transcript Only */}
            <div className="space-y-4">
              <h4 className="font-medium mb-1 flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Full Transcript
              </h4>

              {!transcript || transcript === 'Transcribing audio...' ? (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">Transcript not available yet.</p>
                    {onRegenerateTranscript && (
                      <Button onClick={onRegenerateTranscript} disabled={!!regeneratingTranscript} className="flex items-center gap-2">
                        <RefreshCw className={`h-4 w-4 ${regeneratingTranscript ? 'animate-spin' : ''}`} />
                        {regeneratingTranscript ? 'Regenerating transcript...' : 'Regenerate transcript'}
                      </Button>
                    )}
                  </div>
                ) : transcript.includes('failed') ? (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">Transcription failed. You can try regenerating the transcript.</p>
                    {onRegenerateTranscript && (
                      <Button onClick={onRegenerateTranscript} disabled={!!regeneratingTranscript} variant="outline" className="flex items-center gap-2">
                        <RefreshCw className={`h-4 w-4 ${regeneratingTranscript ? 'animate-spin' : ''}`} />
                        {regeneratingTranscript ? 'Regenerating...' : 'Regenerate transcript'}
                      </Button>
                    )}
                  </div>
                ) : (
                  <ScrollArea className="h-[50vh] pr-2">
                    {(() => {
                      // Try to parse speaker-formatted transcript
                      const lines = transcript.split('\n').filter(l => l.trim());
                      const hasSpeakers = lines.some(line => 
                        line.match(/^\[([^\]]+)\]:\s*/) || 
                        line.match(/^([^:]+):\s*/)
                      );
                      
                      if (hasSpeakers) {
                        // Render with speaker formatting
                        return (
                          <div className="space-y-3">
                            {lines.map((line, index) => {
                              const speakerMatch = line.match(/^\[([^\]]+)\]:\s*(.*)$/) || line.match(/^([^:]+):\s*(.*)$/);
                              
                              if (speakerMatch) {
                                const speaker = speakerMatch[1].trim();
                                const text = speakerMatch[2].trim();
                                
                                // Color coding
                                const isSalesperson = speaker.toLowerCase().includes('sales') || 
                                                     speaker.toLowerCase().includes('provider');
                                const bgColor = isSalesperson 
                                  ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800' 
                                  : 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800';
                                const icon = isSalesperson ? '🎯' : '👤';
                                
                                return (
                                  <div key={index} className={`p-3 rounded-lg border ${bgColor}`}>
                                    <div className="font-semibold text-sm mb-1 flex items-center gap-2">
                                      <span>{icon}</span>
                                      <span>{speaker}</span>
                                    </div>
                                    <p className="text-sm leading-relaxed">{text}</p>
                                  </div>
                                );
                              }
                              
                              // Non-speaker line
                              return (
                                <div key={index} className="text-sm text-muted-foreground">
                                  {line}
                                </div>
                              );
                            })}
                          </div>
                        );
                      } else {
                        // No speaker formatting detected - show as plain text
                        return (
                          <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                            {transcript}
                          </div>
                        );
                      }
                    })()}
                  </ScrollArea>
                )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="coaching" className="space-y-6 mt-6">
          <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">
            <div>
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                Coaching Recommendations
              </h4>
              {analysis.coachingRecommendations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No coaching recommendations available</p>
              ) : (
                <div className="space-y-4">
                  {analysis.coachingRecommendations.map((coaching, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <Badge variant="outline" className="capitalize">
                          {coaching.category}
                        </Badge>
                        <Badge className={transcriptAnalysisService.getPriorityColor(coaching.priority)}>
                          {coaching.priority} priority
                        </Badge>
                      </div>
                      <h5 className="font-medium text-sm mb-2">{coaching.recommendation}</h5>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div>
                          <strong>Example:</strong> {coaching.specificExample}
                        </div>
                        <div>
                          <strong>Suggested Approach:</strong> {coaching.suggestedApproach}
                        </div>
                        <div>
                          <strong>Practice Exercise:</strong> {coaching.practiceExercise}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </TabsContent>

      </Tabs>

      {/* Twilio Debug Test - Temporary */}
      <div className="mt-6">
        <TwilioDebugTest />
      </div>

      {/* Modal dialogs */}
      
      <SMSSender 
        isOpen={isSMSSenderOpen}
        onClose={() => setIsSMSSenderOpen(false)}
        callRecordId={callRecordId || ''}
        customerName={customerName || ''}
      />
    </div>
  );
};

// Memoize the component to prevent unnecessary re-renders when parent state changes
export const CallAnalysisPanel = memo(CallAnalysisPanelComponent, (prevProps, nextProps) => {
  // Only re-render if these key props change
  return (
    prevProps.callRecordId === nextProps.callRecordId &&
    prevProps.analysis === nextProps.analysis &&
    prevProps.isLoading === nextProps.isLoading &&
    prevProps.analysisStatus?.stage === nextProps.analysisStatus?.stage &&
    prevProps.analysisStatus?.progress === nextProps.analysisStatus?.progress &&
    prevProps.transcript === nextProps.transcript &&
    prevProps.audioUrl === nextProps.audioUrl &&
    prevProps.regeneratingTranscript === nextProps.regeneratingTranscript &&
    prevProps.callDuration === nextProps.callDuration &&
    JSON.stringify(prevProps.speakerMapping) === JSON.stringify(nextProps.speakerMapping) &&
    JSON.stringify(prevProps.diarizationSegments) === JSON.stringify(nextProps.diarizationSegments)
  );
});