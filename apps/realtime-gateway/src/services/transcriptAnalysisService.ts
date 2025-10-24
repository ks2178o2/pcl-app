export interface CallAnalysis {
  objections: Objection[];
  actionItems: ActionItem[];
  sentiment: SentimentAnalysis;
  summary: string;
  modelUsed: string;
  customerPersonality: CustomerPersonality;
  urgencyScoring: UrgencyScoring;
  trustAndSafety: TrustAndSafety;
  financialPsychology: FinancialPsychology;
  personalizedRecommendations: PersonalizedRecommendation[];
  salesPerformance: SalesPerformance;
  conversationFlow: ConversationFlow;
  coachingRecommendations: CoachingRecommendation[];
}

export interface CustomerPersonality {
  personalityType: 'research-driven' | 'trust-focused' | 'results-oriented' | 'price-conscious' | 'impulse-emotional';
  motivationCategory: 'life-event' | 'health-driven' | 'confidence-esteem' | 'maintenance-prevention';
  communicationStyle: {
    preferredTone: 'professional' | 'warm' | 'direct' | 'supportive';
    informationDepth: 'detailed' | 'summary' | 'visual';
    decisionSpeed: 'quick' | 'deliberate' | 'consultative';
  };
  psychographics: {
    riskTolerance: 'conservative' | 'moderate' | 'aggressive';
    socialInfluence: 'high' | 'medium' | 'low';
    qualityFocus: 'premium' | 'value' | 'budget';
  };
  behavioralIndicators: string[];
  confidence: number;
}

export interface UrgencyScoring {
  overallUrgency: number; // 0-10 scale
  urgencyFactors: {
    timelinePressure: number; // upcoming events, deadlines
    emotionalState: number; // frustration, excitement level
    financialWindow: number; // budget availability, payment readiness
    seasonalFactors: number; // seasonal timing considerations
    socialPressure: number; // peer influence, social events
  };
  buyingSignals: string[];
  delayIndicators: string[];
  urgencyTriggers: string[];
}

export interface TrustAndSafety {
  trustLevel: number; // 0-10 scale
  safetyCompensation: 'high' | 'medium' | 'low';
  credibilityNeeds: string[];
  riskConcerns: string[];
  reassuranceRequired: string[];
  socialProofNeeds: ('testimonials' | 'before-after' | 'credentials' | 'referrals')[];
}

export interface FinancialPsychology {
  paymentComfort: 'upfront' | 'financing' | 'flexible';
  priceAnchor: 'value-focused' | 'budget-conscious' | 'premium-seeker';
  financialDecisionStyle: 'analytical' | 'emotional' | 'consultative';
  investmentMindset: 'necessity' | 'improvement' | 'luxury';
  budgetRange: string;
  financingInterest: boolean;
  valuePerception: number; // 0-10 scale
}

export interface PersonalizedRecommendation {
  category: 'communication' | 'content' | 'timing' | 'social-proof' | 'financing' | 'reassurance';
  priority: 'high' | 'medium' | 'low';
  recommendation: string;
  reasoning: string;
  suggestedContent: string;
  expectedImpact: string;
}

export interface SalesPerformance {
  talkRatio: number; // 0-100 percentage of salesperson talking
  questioningQuality: number; // 0-10 scale
  listeningScore: number; // 0-10 scale
  rapportBuilding: number; // 0-10 scale
  needsDiscovery: number; // 0-10 scale
  presentationEffectiveness: number; // 0-10 scale
  objectionHandling: number; // 0-10 scale
  closingAttempts: number;
  strengths: string[];
  improvementAreas: string[];
}

export interface ConversationFlow {
  phases: ConversationPhase[];
  topicTransitions: TopicTransition[];
  sentimentJourney: SentimentPoint[];
  engagementLevels: EngagementPoint[];
}

export interface ConversationPhase {
  phase: 'opening' | 'discovery' | 'presentation' | 'objection-handling' | 'closing' | 'next-steps';
  startTime: string;
  endTime: string;
  duration: number;
  effectiveness: number;
  keyMoments: string[];
}

export interface TopicTransition {
  fromTopic: string;
  toTopic: string;
  timestamp: string;
  smoothness: number;
  reason: string;
}

export interface SentimentPoint {
  timestamp: string;
  sentiment: number; // -1 to 1 scale
  trigger: string;
}

export interface EngagementPoint {
  timestamp: string;
  level: number; // 0-10 scale
  indicators: string[];
}

export interface CoachingRecommendation {
  category: 'questioning' | 'listening' | 'presentation' | 'objection-handling' | 'closing' | 'rapport' | 'discovery';
  priority: 'high' | 'medium' | 'low';
  recommendation: string;
  specificExample: string;
  suggestedApproach: string;
  practiceExercise: string;
}

export interface Objection {
  type: 'safety-risk' | 'cost-value' | 'timing' | 'social-concerns' | 'provider-trust' | 'results-skepticism' | 'other';
  text: string;
  speaker: string;
  confidence: number;
  segment: string;
}

export interface ActionItem {
  type: 'consultation' | 'follow-up' | 'education' | 'financial-planning' | 'scheduling' | 'referral' | 'other';
  text: string;
  priority: 'high' | 'medium' | 'low';
  dueDate?: string;
  assignee: string;
  confidence: number;
}

export interface SentimentAnalysis {
  overall: 'positive' | 'neutral' | 'negative';
  customerEngagement: number; // 0-10 scale
  interestLevel: number; // 0-10 scale
  concerns: string[];
}

export type LLMProvider = 'gemini' | 'openai';
export type AnalysisEngine = 'auto' | 'vendor' | 'llm';

class TranscriptAnalysisService {
  private async callLLM(prompt: string, provider: LLMProvider = 'gemini'): Promise<string> {
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      
      const functionName = provider === 'gemini' ? 'analyze-transcript-gemini' : 'analyze-transcript';
      
      const { data, error } = await supabase.functions.invoke(functionName, {
        body: { prompt },
      });

      if (error) {
        console.error(`${provider} Edge Function error:`, error);
        
        // Check if this is a rate limit error
        if (error.message?.includes('Rate limit') || error.message?.includes('429')) {
          throw new Error(`${provider} rate limit exceeded. Please try again in a few minutes.`);
        }
        
        throw new Error(`Failed to analyze transcript with ${provider}: ${error.message}`);
      }

      if (!data || !data.analysis) {
        // Check if data contains rate limit error
        if (data?.error?.includes('Rate limit')) {
          throw new Error(`${provider} rate limit exceeded. Please try again in a few minutes.`);
        }
        
        console.error(`No analysis data returned from ${provider} edge function:`, data);
        throw new Error(`${provider} edge function returned empty response`);
      }

      return data.analysis;
    } catch (error) {
      console.error(`Error calling ${provider}:`, error);
      throw error;
    }
  }

  private async callWithFallback(prompt: string): Promise<{ analysis: string, provider: string }> {
    const providers: LLMProvider[] = ['gemini', 'openai'];
    
    for (let i = 0; i < providers.length; i++) {
      const provider = providers[i];
      try {
        console.log(`Attempting analysis with ${provider}...`);
        const analysis = await this.callLLM(prompt, provider);
        console.log(`Successfully analyzed with ${provider}`);
        return { analysis, provider };
      } catch (error) {
        console.error(`${provider} failed:`, error);
        
        // If this is the last provider, throw the error
        if (i === providers.length - 1) {
          throw error;
        }
        
        console.log(`Falling back to next provider...`);
      }
    }
    
    throw new Error('All LLM providers failed');
  }

  async getStoredAnalysis(callRecordId: string): Promise<CallAnalysis | null> {
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      const { data, error } = await supabase
        .from('call_analyses')
        .select('analysis_data, status')
        .eq('call_record_id', callRecordId)
        .eq('status', 'completed')
        .maybeSingle();

      if (error) throw error;
      if (!data) return null;

      return data.analysis_data as unknown as CallAnalysis;
    } catch (error) {
      console.error('Error getting stored analysis:', error);
      return null;
    }
  }

  async saveAnalysis(callRecordId: string, userId: string, analysis: CallAnalysis): Promise<void> {
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      
      // Extract metrics for database columns
      const extractedMetrics = this.extractMetricsFromAnalysis(analysis);

      const { error } = await supabase
        .from('call_analyses')
        .upsert({
          call_record_id: callRecordId,
          user_id: userId,
          analysis_data: analysis as any,
          status: 'completed',
          ...extractedMetrics
        });

      if (error) throw error;
    } catch (error) {
      console.error('Error saving analysis:', error);
      throw error;
    }
  }

  private extractMetricsFromAnalysis(analysis: CallAnalysis) {
    return {
      overall_urgency: analysis.urgencyScoring?.overallUrgency || null,
      personality_type: analysis.customerPersonality?.personalityType || null,
      motivation_category: analysis.customerPersonality?.motivationCategory || null,
      trust_level: analysis.trustAndSafety?.trustLevel || null,
      overall_sentiment: analysis.sentiment?.overall || null,
      customer_engagement: analysis.sentiment?.customerEngagement || null,
      sales_performance_score: this.calculateSalesPerformanceScore(analysis.salesPerformance) || null,
      objections_count: analysis.objections?.length || 0,
      action_items_count: analysis.actionItems?.length || 0
    };
  }

  private calculateSalesPerformanceScore(salesPerformance: any): number | null {
    if (!salesPerformance) return null;
    
    // Calculate average score from multiple performance metrics
    const metrics = [
      salesPerformance.questioningQuality,
      salesPerformance.listeningScore,
      salesPerformance.rapportBuilding,
      salesPerformance.needsDiscovery,
      salesPerformance.presentationEffectiveness,
      salesPerformance.objectionHandling
    ].filter(metric => typeof metric === 'number');
    
    if (metrics.length === 0) return null;
    return metrics.reduce((sum, metric) => sum + metric, 0) / metrics.length;
  }

  private buildVendorContext(vendorInsights: any): string {
    if (!vendorInsights) return '';

    let context = `\n=== VENDOR INSIGHTS FROM ${vendorInsights.provider.toUpperCase()} ===\n`;
    
    if (vendorInsights.summary) {
      context += `Summary: ${vendorInsights.summary}\n`;
    }
    
    if (vendorInsights.sentiment && vendorInsights.sentiment.length > 0) {
      context += `Sentiment Analysis: ${JSON.stringify(vendorInsights.sentiment)}\n`;
    }
    
    if (vendorInsights.topics && vendorInsights.topics.length > 0) {
      const topics = vendorInsights.topics.map((t: any) => t.topic || t.text).join(', ');
      context += `Key Topics: ${topics}\n`;
    }
    
    if (vendorInsights.intents && vendorInsights.intents.length > 0) {
      const intents = vendorInsights.intents.map((i: any) => i.intent || i.text).join(', ');
      context += `Customer Intents: ${intents}\n`;
    }
    
    if (vendorInsights.entities && vendorInsights.entities.length > 0) {
      const entities = vendorInsights.entities.map((e: any) => `${e.entity_type}: ${e.text}`).join(', ');
      context += `Entities: ${entities}\n`;
    }
    
    context += `=== END VENDOR INSIGHTS ===\n\n`;
    return context;
  }

  private createAnalysisFromVendorInsights(vendorInsights: any, customerName: string, salespersonName: string): CallAnalysis {
    // Create a basic analysis structure populated primarily from vendor insights
    const analysis: CallAnalysis = {
      objections: [],
      actionItems: [],
      sentiment: {
        overall: 'neutral',
        customerEngagement: 5,
        interestLevel: 5,
        concerns: []
      },
      summary: vendorInsights.summary || 'Analysis based on vendor insights only.',
      modelUsed: `${vendorInsights.provider} insights only`,
      customerPersonality: {
        personalityType: 'research-driven',
        motivationCategory: 'health-driven',
        communicationStyle: {
          preferredTone: 'professional',
          informationDepth: 'detailed',
          decisionSpeed: 'deliberate'
        },
        psychographics: {
          riskTolerance: 'moderate',
          socialInfluence: 'medium',
          qualityFocus: 'value'
        },
        behavioralIndicators: [],
        confidence: 0.7
      },
      urgencyScoring: {
        overallUrgency: 5,
        urgencyFactors: {
          timelinePressure: 5,
          emotionalState: 5,
          financialWindow: 5,
          seasonalFactors: 5,
          socialPressure: 5
        },
        buyingSignals: [],
        delayIndicators: [],
        urgencyTriggers: []
      },
      trustAndSafety: {
        trustLevel: 5,
        safetyCompensation: 'medium',
        credibilityNeeds: [],
        riskConcerns: [],
        reassuranceRequired: [],
        socialProofNeeds: []
      },
      financialPsychology: {
        paymentComfort: 'flexible',
        priceAnchor: 'value-focused',
        financialDecisionStyle: 'analytical',
        investmentMindset: 'improvement',
        budgetRange: 'Not specified',
        financingInterest: false,
        valuePerception: 5
      },
      personalizedRecommendations: [],
      salesPerformance: {
        talkRatio: 50,
        questioningQuality: 5,
        listeningScore: 5,
        rapportBuilding: 5,
        needsDiscovery: 5,
        presentationEffectiveness: 5,
        objectionHandling: 5,
        closingAttempts: 0,
        strengths: [],
        improvementAreas: []
      },
      conversationFlow: {
        phases: [],
        topicTransitions: [],
        sentimentJourney: [],
        engagementLevels: []
      },
      coachingRecommendations: []
    };

    // Enhance with vendor sentiment if available
    if (vendorInsights.sentiment && vendorInsights.sentiment.length > 0) {
      const avgSentiment = vendorInsights.sentiment.reduce((sum: number, s: any) => sum + (s.sentiment || 0), 0) / vendorInsights.sentiment.length;
      analysis.sentiment.overall = avgSentiment > 0.3 ? 'positive' : avgSentiment < -0.3 ? 'negative' : 'neutral';
      analysis.sentiment.customerEngagement = Math.round((avgSentiment + 1) * 5); // Convert -1,1 to 0-10
      analysis.sentiment.interestLevel = Math.round((avgSentiment + 1) * 5);
    }

    return analysis;
  }

  async analyzeTranscript(
    transcript: string,
    customerName: string,
    salespersonName: string,
    callRecordId?: string,
    userId?: string,
    analysisEngine: AnalysisEngine = 'auto',
    vendorInsights?: any
  ): Promise<CallAnalysis> {
    // Handle vendor-only analysis
    if (analysisEngine === 'vendor' && vendorInsights) {
      return this.createAnalysisFromVendorInsights(vendorInsights, customerName, salespersonName);
    }

    // Build context with vendor insights for auto/LLM analysis
    let vendorContext = '';
    if (vendorInsights && analysisEngine === 'auto') {
      vendorContext = this.buildVendorContext(vendorInsights);
    }

    const prompt = `
${vendorContext}

Analyze this healthcare consultation transcript and extract insights for healthcare consumer psychology and sales optimization. This is a conversation between a healthcare provider/salesperson and a potential patient considering elective procedures (med spa, cosmetic surgery, dental procedures, etc.). Return a JSON object with ALL the following fields populated:

{
  "objections": [
    {
      "type": "safety-risk|cost-value|timing|social-concerns|provider-trust|results-skepticism|other",
      "text": "Brief description of the objection",
      "speaker": "Customer name who raised the objection",
      "confidence": 0.8,
      "segment": "Exact quote from transcript"
    }
  ],
  "actionItems": [
    {
      "type": "consultation|follow-up|education|financial-planning|scheduling|referral|other",
      "text": "Description of the action needed",
      "priority": "high|medium|low",
      "dueDate": "If mentioned, format as YYYY-MM-DD or relative like 'next week'",
      "assignee": "Who should do this (provider or patient name)",
      "confidence": 0.9
    }
  ],
  "sentiment": {
    "overall": "positive|neutral|negative",
    "customerEngagement": 7,
    "interestLevel": 8,
    "concerns": ["List of main customer concerns"]
  },
  "summary": "2-3 sentence summary of the consultation outcome and next steps",
  "customerPersonality": {
    "personalityType": "research-driven|trust-focused|results-oriented|price-conscious|impulse-emotional",
    "motivationCategory": "life-event|health-driven|confidence-esteem|maintenance-prevention",
    "communicationStyle": {
      "preferredTone": "professional|warm|direct|supportive",
      "informationDepth": "detailed|summary|visual",
      "decisionSpeed": "quick|deliberate|consultative"
    },
    "psychographics": {
      "riskTolerance": "conservative|moderate|aggressive",
      "socialInfluence": "high|medium|low",
      "qualityFocus": "premium|value|budget"
    },
    "behavioralIndicators": ["Language patterns, decision-making clues, and communication preferences observed"],
    "confidence": 0.85
  },
  "urgencyScoring": {
    "overallUrgency": 7,
    "urgencyFactors": {
      "timelinePressure": 6,
      "emotionalState": 8,
      "financialWindow": 7,
      "seasonalFactors": 5,
      "socialPressure": 4
    },
    "buyingSignals": ["Indicators of readiness to proceed"],
    "delayIndicators": ["Factors that might delay decision"],
    "urgencyTriggers": ["Events or motivations creating urgency"]
  },
  "trustAndSafety": {
    "trustLevel": 8,
    "safetyCompensation": "high|medium|low",
    "credibilityNeeds": ["What they need to trust the provider"],
    "riskConcerns": ["Safety and procedure concerns expressed"],
    "reassuranceRequired": ["What would help them feel more confident"],
    "socialProofNeeds": ["testimonials", "before-after", "credentials", "referrals"]
  },
  "financialPsychology": {
    "paymentComfort": "upfront|financing|flexible",
    "priceAnchor": "value-focused|budget-conscious|premium-seeker",
    "financialDecisionStyle": "analytical|emotional|consultative",
    "investmentMindset": "necessity|improvement|luxury",
    "budgetRange": "Budget range if mentioned or inferred",
    "financingInterest": true,
    "valuePerception": 7
  },
  "personalizedRecommendations": [
    {
      "category": "communication|content|timing|social-proof|financing|reassurance",
      "priority": "high|medium|low",
      "recommendation": "Specific recommendation for follow-up approach",
      "reasoning": "Why this approach fits their personality and situation",
      "suggestedContent": "Specific content or materials to share",
      "expectedImpact": "Expected impact on conversion likelihood"
    }
  ],
  "salesPerformance": {
    "talkRatio": 60,
    "questioningQuality": 7,
    "listeningScore": 8,
    "rapportBuilding": 7,
    "needsDiscovery": 6,
    "presentationEffectiveness": 7,
    "objectionHandling": 6,
    "closingAttempts": 2,
    "strengths": ["List provider/salesperson strengths demonstrated"],
    "improvementAreas": ["Areas for improvement in healthcare sales approach"]
  },
  "conversationFlow": {
    "phases": [
      {
        "phase": "opening|discovery|presentation|objection-handling|closing|next-steps",
        "startTime": "Estimated start time",
        "endTime": "Estimated end time",
        "duration": 300,
        "effectiveness": 7,
        "keyMoments": ["Key moments in this phase"]
      }
    ],
    "topicTransitions": [
      {
        "fromTopic": "Previous topic",
        "toTopic": "New topic",
        "timestamp": "When it happened",
        "smoothness": 8,
        "reason": "Why the transition occurred"
      }
    ],
    "sentimentJourney": [
      {
        "timestamp": "Point in conversation",
        "sentiment": 0.6,
        "trigger": "What caused this sentiment"
      }
    ],
    "engagementLevels": [
      {
        "timestamp": "Point in conversation",
        "level": 7,
        "indicators": ["What indicated this engagement level"]
      }
    ]
  },
  "coachingRecommendations": [
    {
      "category": "questioning|listening|presentation|objection-handling|closing|rapport|discovery",
      "priority": "high|medium|low",
      "recommendation": "Specific coaching recommendation for healthcare sales",
      "specificExample": "Example from this consultation",
      "suggestedApproach": "How to improve for healthcare consumers",
      "practiceExercise": "Exercise to practice this skill with healthcare consumers"
    }
  ]
}

Patient/Customer: ${customerName}
Healthcare Provider/Salesperson: ${salespersonName}

Transcript:
${transcript}

Analyze the consultation thoroughly with focus on healthcare consumer psychology, buying behavior, and personalized follow-up strategies. Consider this is an elective healthcare service (cosmetic, dental, wellness) where the customer is making a personal investment decision. Always return complete JSON with all fields populated (use empty arrays/objects where no data exists). Focus on actionable intelligence for healthcare sales optimization and customer psychology insights.

${vendorContext ? 'Incorporate the vendor insights provided above into your analysis where relevant, using them to enhance the depth and accuracy of your psychological and sales analysis.' : ''}`;

    try {
      const { analysis: response, provider } = await this.callWithFallback(prompt);
      const parsedAnalysis = JSON.parse(response) as CallAnalysis;
      
      const engineSuffix = analysisEngine === 'auto' && vendorInsights ? ` + ${vendorInsights.provider}` : '';
      const modelName = provider === 'gemini' ? `gemini-2.0-flash-exp${engineSuffix}` : `gpt-4.1-2025-04-14${engineSuffix}`;
      const analysis = {
        ...parsedAnalysis,
        modelUsed: modelName
      };

      // Save to database if callRecordId and userId are provided
      if (callRecordId && userId) {
        await this.saveAnalysis(callRecordId, userId, analysis);
      }

      return analysis;
    } catch (error) {
      console.error('Error analyzing transcript:', error);
      // Return fallback analysis with all required fields
      return {
        objections: [],
        actionItems: [],
        sentiment: {
          overall: 'neutral',
          customerEngagement: 5,
          interestLevel: 5,
          concerns: []
        },
        summary: 'Analysis unavailable - please try again later.',
        modelUsed: 'gpt-4.1-2025-04-14 (failed)',
        customerPersonality: {
          personalityType: 'research-driven',
          motivationCategory: 'health-driven',
          communicationStyle: {
            preferredTone: 'professional',
            informationDepth: 'detailed',
            decisionSpeed: 'deliberate'
          },
          psychographics: {
            riskTolerance: 'moderate',
            socialInfluence: 'medium',
            qualityFocus: 'value'
          },
          behavioralIndicators: [],
          confidence: 0.7
        },
        urgencyScoring: {
          overallUrgency: 5,
          urgencyFactors: {
            timelinePressure: 5,
            emotionalState: 5,
            financialWindow: 5,
            seasonalFactors: 5,
            socialPressure: 5
          },
          buyingSignals: [],
          delayIndicators: [],
          urgencyTriggers: []
        },
        trustAndSafety: {
          trustLevel: 5,
          safetyCompensation: 'medium',
          credibilityNeeds: [],
          riskConcerns: [],
          reassuranceRequired: [],
          socialProofNeeds: []
        },
        financialPsychology: {
          paymentComfort: 'flexible',
          priceAnchor: 'value-focused',
          financialDecisionStyle: 'analytical',
          investmentMindset: 'improvement',
          budgetRange: 'Not specified',
          financingInterest: false,
          valuePerception: 5
        },
        personalizedRecommendations: [],
        salesPerformance: {
          talkRatio: 50,
          questioningQuality: 5,
          listeningScore: 5,
          rapportBuilding: 5,
          needsDiscovery: 5,
          presentationEffectiveness: 5,
          objectionHandling: 5,
          closingAttempts: 0,
          strengths: [],
          improvementAreas: []
        },
        conversationFlow: {
          phases: [],
          topicTransitions: [],
          sentimentJourney: [],
          engagementLevels: []
        },
        coachingRecommendations: []
      };
    }
  }

  // Utility methods
  getObjectionTypeColor(type: Objection['type']): string {
    const colors = {
      'safety-risk': 'bg-red-50 text-red-700 border-red-200',
      'cost-value': 'bg-orange-50 text-orange-700 border-orange-200',
      'timing': 'bg-yellow-50 text-yellow-700 border-yellow-200',
      'social-concerns': 'bg-purple-50 text-purple-700 border-purple-200',
      'provider-trust': 'bg-blue-50 text-blue-700 border-blue-200',
      'results-skepticism': 'bg-pink-50 text-pink-700 border-pink-200',
      'other': 'bg-gray-50 text-gray-700 border-gray-200'
    };
    return colors[type] || colors.other;
  }

  getActionItemTypeIcon(type: ActionItem['type']): string {
    const icons = {
      'consultation': '🩺',
      'follow-up': '📞',
      'education': '📚',
      'financial-planning': '💰',
      'scheduling': '📅',
      'referral': '🤝',
      'other': '📋'
    };
    return icons[type] || icons.other;
  }

  getPriorityColor(priority: ActionItem['priority']): string {
    const colors = {
      'high': 'bg-red-50 text-red-700 border-red-200',
      'medium': 'bg-yellow-50 text-yellow-700 border-yellow-200',
      'low': 'bg-green-50 text-green-700 border-green-200'
    };
    return colors[priority];
  }

  getSentimentColor(sentiment: SentimentAnalysis['overall']): string {
    const colors = {
      'positive': 'text-green-600',
      'neutral': 'text-gray-600',
      'negative': 'text-red-600'
    };
    return colors[sentiment];
  }

  getSentimentIcon(sentiment: SentimentAnalysis['overall']): string {
    const icons = {
      'positive': '😊',
      'neutral': '😐',
      'negative': '😟'
    };
    return icons[sentiment];
  }
}

export const transcriptAnalysisService = new TranscriptAnalysisService();