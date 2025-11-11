import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { MessageSquare, Send, Phone } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";

interface SMSSenderProps {
  isOpen: boolean;
  onClose: () => void;
  callRecordId: string;
  customerName: string;
  customerPhone?: string;
  analysisData?: any;
}

export const SMSSender = ({ 
  isOpen, 
  onClose, 
  callRecordId, 
  customerName, 
  customerPhone = '', 
  analysisData 
}: SMSSenderProps) => {
  const [formData, setFormData] = useState({
    recipientPhone: customerPhone,
    message: ''
  });
  const [isSending, setIsSending] = useState(false);
  const { toast } = useToast();

  const handleSend = async () => {
    if (!formData.recipientPhone.trim() || !formData.message.trim()) {
      toast({
        title: "Missing Information",
        description: "Please enter both phone number and message.",
        variant: "destructive",
      });
      return;
    }

    setIsSending(true);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('Not authenticated');
      }

      const { getApiUrl } = await import('@/utils/apiConfig');
      const resp = await fetch(getApiUrl('/api/twilio/send-sms'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          callRecordId,
          recipientPhone: formData.recipientPhone,
          recipientName: customerName,
          message: formData.message,
          messageType: 'follow_up'
        })
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok || data?.success !== true) {
        const msg = data?.detail || data?.error || resp.statusText || 'Failed to send SMS';
        throw new Error(msg);
      }

      toast({
        title: "SMS Sent Successfully",
        description: `Message sent to ${customerName}`,
      });

      // Reset form and close
      setFormData({ recipientPhone: customerPhone, message: '' });
      onClose();
    } catch (error: any) {
      console.error('SMS sending failed:', error);
      toast({
        title: "Failed to Send SMS",
        description: error.message || "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setIsSending(false);
    }
  };

  // Common SMS templates
  const smsTemplates = [
    {
      label: "Follow-up",
      content: `Hi ${customerName}, thanks for speaking with us today. Just wanted to follow up on our conversation. Please let me know if you have any questions!`
    },
    {
      label: "Appointment Reminder",
      content: `Hi ${customerName}, this is a reminder about your upcoming appointment. Please confirm if you can still make it.`
    },
    {
      label: "Thank You",
      content: `Hi ${customerName}, thank you for your time today. We appreciate your business and look forward to working with you.`
    }
  ];

  const handleTemplateSelect = (template: typeof smsTemplates[0]) => {
    setFormData(prev => ({ ...prev, message: template.content }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Send SMS to {customerName}
          </DialogTitle>
          <DialogDescription>
            Send a text message to follow up on your conversation.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Phone Number Input */}
          <div className="space-y-2">
            <Label htmlFor="phone" className="flex items-center gap-2">
              <Phone className="h-4 w-4" />
              Phone Number
            </Label>
            <Input
              id="phone"
              type="tel"
              placeholder="+1 (555) 123-4567"
              value={formData.recipientPhone}
              onChange={(e) => setFormData(prev => ({ ...prev, recipientPhone: e.target.value }))}
            />
          </div>

          {/* SMS Templates */}
          <div className="space-y-3">
            <Label>Quick Templates</Label>
            <div className="grid gap-2">
              {smsTemplates.map((template, index) => (
                <Card key={index} className="cursor-pointer hover:bg-muted/50 transition-colors">
                  <CardContent className="p-3">
                    <div 
                      className="space-y-1"
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <div className="font-medium text-sm">{template.label}</div>
                      <div className="text-xs text-muted-foreground line-clamp-2">
                        {template.content}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Message Input */}
          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              placeholder="Type your message here..."
              value={formData.message}
              onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
              rows={4}
              className="resize-none"
            />
            <div className="text-xs text-muted-foreground text-right">
              {formData.message.length}/160 characters
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleSend} 
              disabled={isSending || !formData.recipientPhone.trim() || !formData.message.trim()}
            >
              <Send className="h-4 w-4 mr-2" />
              {isSending ? "Sending..." : "Send SMS"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};