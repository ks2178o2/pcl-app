import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Mail, MessageSquare, Clock, Eye, EyeOff, BarChart3, RefreshCw, Phone } from 'lucide-react';
import { useEmailActivities, EmailActivity } from '@/hooks/useEmailActivities';
import { useSMSActivities, SMSActivity } from '@/hooks/useSMSActivities';
import { format } from 'date-fns';

interface FollowupActivitiesPanelProps {
  callRecordId?: string;
}

type CombinedActivity = (EmailActivity | SMSActivity) & { type: 'email' | 'sms' };

export const FollowupActivitiesPanel: React.FC<FollowupActivitiesPanelProps> = ({
  callRecordId
}) => {
  const { activities: emailActivities, loading: emailLoading, error: emailError, refetch: refetchEmails, stats } = useEmailActivities(callRecordId);
  const { activities: smsActivities, loading: smsLoading, refetch: refetchSMS } = useSMSActivities(callRecordId);

  const loading = emailLoading || smsLoading;

  const refetchAll = () => {
    refetchEmails();
    refetchSMS();
  };

  // Combine and sort activities by created date
  const combinedActivities: CombinedActivity[] = [
    ...emailActivities.map(activity => ({ ...activity, type: 'email' as const })),
    ...smsActivities.map(activity => ({ ...activity, type: 'sms' as const }))
  ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Follow-up Activities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (emailError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Follow-up Activities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-muted-foreground mb-4">Failed to load activities</p>
            <Button variant="outline" onClick={refetchAll}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getStatusBadgeVariant = (activity: CombinedActivity) => {
    if (activity.type === 'email') {
      const emailActivity = activity as EmailActivity;
      if (emailActivity.delivery_status === 'failed') return 'destructive';
      if (emailActivity.total_opens > 0) return 'default';
      return 'secondary';
    } else {
      const smsActivity = activity as SMSActivity;
      if (smsActivity.delivery_status === 'failed') return 'destructive';
      if (smsActivity.delivery_status === 'delivered') return 'default';
      return 'secondary';
    }
  };

  const getStatusText = (activity: CombinedActivity) => {
    if (activity.type === 'email') {
      const emailActivity = activity as EmailActivity;
      if (emailActivity.delivery_status === 'failed') return 'Failed';
      if (emailActivity.total_opens > 0) {
        return `Opened ${emailActivity.total_opens}x`;
      }
      return 'Sent';
    } else {
      const smsActivity = activity as SMSActivity;
      if (smsActivity.delivery_status === 'failed') return 'Failed';
      if (smsActivity.delivery_status === 'delivered') return 'Delivered';
      return 'Sent';
    }
  };

  const getActivityIcon = (type: 'email' | 'sms') => {
    return type === 'email' ? <Mail className="h-4 w-4" /> : <Phone className="h-4 w-4" />;
  };

  const getActivityTitle = (activity: CombinedActivity) => {
    if (activity.type === 'email') {
      return (activity as EmailActivity).subject;
    } else {
      return `SMS: ${(activity as SMSActivity).message_content.substring(0, 50)}...`;
    }
  };

  const getRecipientInfo = (activity: CombinedActivity) => {
    if (activity.type === 'email') {
      const emailActivity = activity as EmailActivity;
      return emailActivity.recipient_email;
    } else {
      const smsActivity = activity as SMSActivity;
      return smsActivity.recipient_phone;
    }
  };

  const getSentTime = (activity: CombinedActivity) => {
    if (activity.type === 'email') {
      return (activity as EmailActivity).sent_at;
    } else {
      return (activity as SMSActivity).sent_at || activity.created_at;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Follow-up Activities
          </CardTitle>
          <Button variant="outline" size="sm" onClick={refetchAll}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Stats Summary - Only show if we have email activities */}
        {emailActivities.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{stats.totalSent}</div>
              <div className="text-sm text-muted-foreground">Emails Sent</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{stats.totalOpened}</div>
              <div className="text-sm text-muted-foreground">Emails Opened</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{smsActivities.length}</div>
              <div className="text-sm text-muted-foreground">SMS Sent</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{stats.openRate.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">Email Open Rate</div>
            </div>
          </div>
        )}

        {/* Activities List */}
        {combinedActivities.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No follow-up activities yet</p>
            <p className="text-sm text-muted-foreground mt-2">
              Send your first follow-up email or SMS to start tracking engagement
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {combinedActivities.map((activity) => (
              <Card key={`${activity.type}-${activity.id}`} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getActivityIcon(activity.type)}
                      <h4 className="font-medium">{getActivityTitle(activity)}</h4>
                      <Badge variant={getStatusBadgeVariant(activity)}>
                        {getStatusText(activity)}
                      </Badge>
                    </div>
                    
                    <div className="text-sm text-muted-foreground space-y-1">
                      <div className="flex items-center gap-4">
                        <span>To: {getRecipientInfo(activity)}</span>
                        <span>Sent: {format(new Date(getSentTime(activity)), 'MMM d, yyyy h:mm a')}</span>
                      </div>
                      
                      {activity.type === 'email' && (activity as EmailActivity).total_opens > 0 && (
                        <div className="flex items-center gap-4 text-green-600">
                          <span className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            First opened: {(activity as EmailActivity).first_open_at ? format(new Date((activity as EmailActivity).first_open_at!), 'MMM d, h:mm a') : 'N/A'}
                          </span>
                          {(activity as EmailActivity).total_read_time_seconds > 0 && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              Read time: {formatDuration((activity as EmailActivity).total_read_time_seconds)}
                            </span>
                          )}
                        </div>
                      )}
                      
                      {activity.type === 'sms' && (activity as SMSActivity).delivered_at && (
                        <div className="text-green-600 text-xs">
                          Delivered: {format(new Date((activity as SMSActivity).delivered_at!), 'MMM d, h:mm a')}
                        </div>
                      )}
                      
                      {activity.type === 'email' && (activity as EmailActivity).last_engagement_at && (
                        <div className="text-xs">
                          Last activity: {format(new Date((activity as EmailActivity).last_engagement_at!), 'MMM d, yyyy h:mm a')}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center gap-2 text-sm">
                      {activity.type === 'email' ? (
                        (activity as EmailActivity).total_opens > 0 ? (
                          <Eye className="h-4 w-4 text-green-600" />
                        ) : (
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                        )
                      ) : (
                        <MessageSquare className="h-4 w-4 text-blue-600" />
                      )}
                      <Badge variant="outline" className="text-xs">
                        {activity.type === 'email' ? (activity as EmailActivity).email_type : (activity as SMSActivity).message_type}
                      </Badge>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};