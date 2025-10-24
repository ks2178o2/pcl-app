import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Mail, Send, Loader2, FileText, Lightbulb, RefreshCw } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';

interface EmailSenderProps {
  callRecordId: string;
  customerName: string;
  defaultEmail?: string;
  analysisData?: any;
  prefilledSubject?: string;
  prefilledContent?: string;
  triggerLabel?: string;
  triggerVariant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  triggerSize?: "default" | "sm" | "lg" | "icon";
  onEmailSent?: () => void;
  children?: React.ReactNode;
}

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  content: string;
  template_type: string;
}

export const EmailSender: React.FC<EmailSenderProps> = ({
  callRecordId,
  customerName,
  defaultEmail = '',
  analysisData,
  prefilledSubject = '',
  prefilledContent = '',
  triggerLabel = 'Send Email',
  triggerVariant = 'outline',
  triggerSize = 'sm',
  onEmailSent,
  children
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGeneratingSubjects, setIsGeneratingSubjects] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [subjectSuggestions, setSubjectSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [formData, setFormData] = useState({
    email: defaultEmail,
    subject: prefilledSubject,
    content: prefilledContent
  });
  
  const { toast } = useToast();
  const { user } = useAuth();

  // Load email templates and generate default subject
  useEffect(() => {
    const loadTemplatesAndGenerateSubject = async () => {
      if (!user) return;
      
      try {
        // Load templates first
        const { data, error } = await supabase
          .from('email_templates')
          .select('*')
          .eq('user_id', user.id)
          .order('is_default', { ascending: false });

        if (error) throw error;
        setTemplates(data || []);

        // Auto-select default template
        const defaultTemplate = data?.find(t => t.is_default);
        if (defaultTemplate) {
          setSelectedTemplate(defaultTemplate.id);
          handleTemplateSelect(defaultTemplate);
        }

        // Generate a default catchy subject line if content is available
        if (formData.content || defaultTemplate?.content) {
          await generateDefaultSubject();
        }
      } catch (error) {
        console.error('Failed to load templates:', error);
      }
    };

    if (isOpen) {
      loadTemplatesAndGenerateSubject();
    }
  }, [isOpen, user]);

  // Generate default subject line when opening the modal
  const generateDefaultSubject = async () => {
    // Skip if we already have a prefilled subject
    if (prefilledSubject) return;
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await supabase.functions.invoke('generate-email-subject', {
        body: {
          content: formData.content || 'Follow-up email after our conversation',
          customerName,
          analysisData,
          currentSubject: ''
        },
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (response.data?.suggestions?.length > 0) {
        // Use the first suggestion as the default subject
        setFormData(prev => ({ 
          ...prev, 
          subject: response.data.suggestions[0] 
        }));
      }
    } catch (error) {
      console.error('Failed to generate default subject:', error);
      // Fallback to a simple subject if AI fails
      setFormData(prev => ({ 
        ...prev, 
        subject: `Following up on our conversation, ${customerName}` 
      }));
    }
  };

  const handleTemplateSelect = (template: EmailTemplate) => {
    // Replace template variables
    let subject = template.subject;
    let content = template.content;

    // Basic variable replacement
    subject = subject.replace(/\{\{customer_name\}\}/g, customerName);
    content = content.replace(/\{\{customer_name\}\}/g, customerName);
    
    if (user?.user_metadata?.salesperson_name) {
      content = content.replace(/\{\{salesperson_name\}\}/g, user.user_metadata.salesperson_name);
    }

    // Add analysis summary if available
    if (analysisData) {
      const analysisSummary = generateAnalysisSummary(analysisData);
      content = content.replace(/\{\{analysis_summary\}\}/g, analysisSummary);
    }

    setFormData(prev => ({
      ...prev,
      subject,
      content
    }));
  };

  const generateAnalysisSummary = (analysis: any) => {
    if (!analysis) return '';
    
    const insights = [];
    
    if (analysis.overall_sentiment) {
      insights.push(`Overall sentiment: ${analysis.overall_sentiment}`);
    }
    
    if (analysis.customer_engagement !== undefined) {
      insights.push(`Customer engagement level: ${Math.round(analysis.customer_engagement * 100)}%`);
    }
    
    if (analysis.analysis_data?.key_points) {
      insights.push("Key discussion points:");
      analysis.analysis_data.key_points.forEach((point: string, index: number) => {
        insights.push(`${index + 1}. ${point}`);
      });
    }

    return insights.join('\n');
  };

  const generateSubjectSuggestions = async () => {
    if (!formData.content) {
      toast({
        title: "Missing Content",
        description: "Please enter email content first to generate subject suggestions.",
        variant: "destructive",
      });
      return;
    }

    setIsGeneratingSubjects(true);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No authentication session');

      const response = await supabase.functions.invoke('generate-email-subject', {
        body: {
          content: formData.content,
          customerName,
          analysisData,
          currentSubject: formData.subject
        },
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (response.error) {
        throw new Error(response.error.message || 'Failed to generate subject suggestions');
      }

      setSubjectSuggestions(response.data.suggestions || []);
      setShowSuggestions(true);

    } catch (error: any) {
      console.error('Failed to generate subject suggestions:', error);
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to generate subject suggestions. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGeneratingSubjects(false);
    }
  };

  const handleSendEmail = async () => {
    if (!formData.email || !formData.subject || !formData.content) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No authentication session');

      const response = await supabase.functions.invoke('send-follow-up-email', {
        body: {
          callRecordId,
          recipientEmail: formData.email,
          recipientName: customerName,
          subject: formData.subject,
          content: formData.content,
          emailType: 'follow_up'
        },
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (response.error) {
        throw new Error(response.error.message || 'Failed to send email');
      }

      toast({
        title: "Email Sent",
        description: `Follow-up email sent successfully to ${formData.email}`,
      });

      setIsOpen(false);
      setFormData({ email: defaultEmail, subject: prefilledSubject, content: prefilledContent });
      setSelectedTemplate('');
      
      // Call the onEmailSent callback if provided
      onEmailSent?.();

    } catch (error: any) {
      console.error('Failed to send email:', error);
      toast({
        title: "Email Failed",
        description: error.message || "Failed to send email. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant={triggerVariant} size={triggerSize} className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            {triggerLabel}
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Send Follow-up Email to {customerName}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Template Selector */}
          {templates.length > 0 && (
            <div>
              <Label htmlFor="template">Email Template</Label>
              <Select 
                value={selectedTemplate} 
                onValueChange={(value) => {
                  setSelectedTemplate(value);
                  const template = templates.find(t => t.id === value);
                  if (template) handleTemplateSelect(template);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a template..." />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        {template.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Recipient Email */}
          <div>
            <Label htmlFor="email">Recipient Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="customer@example.com"
              required
            />
          </div>

          {/* Subject */}
          <div>
            <div className="flex items-center justify-between">
              <Label htmlFor="subject">Subject *</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={generateSubjectSuggestions}
                disabled={isGeneratingSubjects}
                className="flex items-center gap-1 text-xs"
              >
                {isGeneratingSubjects ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Lightbulb className="h-3 w-3" />
                )}
                AI Suggest
              </Button>
            </div>
            <Input
              id="subject"
              value={formData.subject}
              onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
              placeholder="Email subject..."
              required
            />
            
            {/* AI Subject Suggestions */}
            {showSuggestions && subjectSuggestions.length > 0 && (
              <div className="mt-2 p-3 bg-muted rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-muted-foreground">AI Suggestions:</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSuggestions(false)}
                    className="text-xs h-6 px-2"
                  >
                    Hide
                  </Button>
                </div>
                <div className="space-y-1">
                  {subjectSuggestions.map((suggestion, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="cursor-pointer hover:bg-primary/10 block w-full text-left p-2 h-auto text-wrap"
                      onClick={() => {
                        setFormData(prev => ({ ...prev, subject: suggestion }));
                        setShowSuggestions(false);
                      }}
                    >
                      {suggestion}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div>
            <Label htmlFor="content">Email Content *</Label>
            <Textarea
              id="content"
              value={formData.content}
              onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
              placeholder="Write your email content here..."
              rows={12}
              className="resize-y"
              required
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSendEmail} 
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              {isLoading ? 'Sending...' : 'Send Email'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};