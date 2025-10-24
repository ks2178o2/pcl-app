import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Mail, Clock, Eye, EyeOff, BarChart3, RefreshCw } from 'lucide-react';
import { useEmailActivities, EmailActivity } from '@/hooks/useEmailActivities';
import { format } from 'date-fns';

interface EmailActivitiesPanelProps {
  callRecordId?: string;
}

export const EmailActivitiesPanel: React.FC<EmailActivitiesPanelProps> = ({
  callRecordId
}) => {
  const { activities, loading, error, refetch, stats } = useEmailActivities(callRecordId);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Activities
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

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Activities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-muted-foreground mb-4">Failed to load email activities</p>
            <Button variant="outline" onClick={refetch}>
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

  const getStatusBadgeVariant = (status: string, totalOpens: number) => {
    if (status === 'failed') return 'destructive';
    if (totalOpens > 0) return 'default';
    return 'secondary';
  };

  const getStatusText = (activity: EmailActivity) => {
    if (activity.delivery_status === 'failed') return 'Failed';
    if (activity.total_opens > 0) {
      return `Opened ${activity.total_opens}x`;
    }
    return 'Sent';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Activities
          </CardTitle>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Stats Summary */}
        {activities.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{stats.totalSent}</div>
              <div className="text-sm text-muted-foreground">Sent</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{stats.totalOpened}</div>
              <div className="text-sm text-muted-foreground">Opened</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{stats.openRate.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">Open Rate</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-primary">{formatDuration(Math.round(stats.averageReadTime))}</div>
              <div className="text-sm text-muted-foreground">Avg. Read Time</div>
            </div>
          </div>
        )}

        {/* Activities List */}
        {activities.length === 0 ? (
          <div className="text-center py-8">
            <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No email activities yet</p>
            <p className="text-sm text-muted-foreground mt-2">
              Send your first follow-up email to start tracking engagement
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {activities.map((activity) => (
              <Card key={activity.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-medium">{activity.subject}</h4>
                      <Badge variant={getStatusBadgeVariant(activity.delivery_status, activity.total_opens)}>
                        {getStatusText(activity)}
                      </Badge>
                    </div>
                    
                    <div className="text-sm text-muted-foreground space-y-1">
                      <div className="flex items-center gap-4">
                        <span>To: {activity.recipient_email}</span>
                        <span>Sent: {format(new Date(activity.sent_at), 'MMM d, yyyy h:mm a')}</span>
                      </div>
                      
                      {activity.total_opens > 0 && (
                        <div className="flex items-center gap-4 text-green-600">
                          <span className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            First opened: {activity.first_open_at ? format(new Date(activity.first_open_at), 'MMM d, h:mm a') : 'N/A'}
                          </span>
                          {activity.total_read_time_seconds > 0 && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              Read time: {formatDuration(activity.total_read_time_seconds)}
                            </span>
                          )}
                        </div>
                      )}
                      
                      {activity.last_engagement_at && (
                        <div className="text-xs">
                          Last activity: {format(new Date(activity.last_engagement_at), 'MMM d, yyyy h:mm a')}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center gap-2 text-sm">
                      {activity.total_opens > 0 ? (
                        <Eye className="h-4 w-4 text-green-600" />
                      ) : (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      )}
                      <Badge variant="outline" className="text-xs">
                        {activity.email_type}
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