import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useProfile } from '@/hooks/useProfile';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Trophy, TrendingUp, Award, Sparkles } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface SalespersonMetric {
  userId: string;
  name: string;
  recordings30Days: number;
  placeholderMetric1: number;
  placeholderMetric2: number;
  rank: number;
}

export default function Leaderboard() {
  const { profile, loading: profileLoading } = useProfile();
  const [metrics, setMetrics] = useState<SalespersonMetric[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (profile?.organization_id) {
      fetchLeaderboardData();
    }
  }, [profile]);

  const fetchLeaderboardData = async () => {
    if (!profile?.organization_id) return;

    setLoading(true);
    try {
      // Get all salespeople in the same organization
      const { data: profiles, error: profilesError } = await supabase
        .from('profiles')
        .select('id, user_id, salesperson_name')
        .eq('organization_id', profile.organization_id);

      if (profilesError) throw profilesError;

      // Get call records from last 30 days
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

      const { data: callRecords, error: recordsError } = await supabase
        .from('call_records')
        .select('user_id')
        .eq('organization_id', profile.organization_id)
        .gte('created_at', thirtyDaysAgo.toISOString());

      if (recordsError) throw recordsError;

      // Calculate metrics for each salesperson
      const metricsData: SalespersonMetric[] = profiles?.map(p => {
        const recordings = callRecords?.filter(r => r.user_id === p.user_id).length || 0;
        
        return {
          userId: p.user_id,
          name: p.salesperson_name || 'Unknown',
          recordings30Days: recordings,
          placeholderMetric1: Math.floor(Math.random() * 100), // Placeholder
          placeholderMetric2: Math.floor(Math.random() * 100), // Placeholder
          rank: 0
        };
      }) || [];

      // Sort by recordings and assign ranks
      metricsData.sort((a, b) => b.recordings30Days - a.recordings30Days);
      metricsData.forEach((m, idx) => m.rank = idx + 1);

      setMetrics(metricsData);
    } catch (error) {
      console.error('Error fetching leaderboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTrophyIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="h-8 w-8 text-yellow-400" />;
    if (rank === 2) return <Trophy className="h-7 w-7 text-gray-400" />;
    if (rank === 3) return <Trophy className="h-6 w-6 text-amber-600" />;
    return <Award className="h-5 w-5 text-muted-foreground" />;
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-400/20 to-yellow-600/20 border-yellow-400';
    if (rank === 2) return 'bg-gradient-to-r from-gray-300/20 to-gray-500/20 border-gray-400';
    if (rank === 3) return 'bg-gradient-to-r from-amber-500/20 to-amber-700/20 border-amber-600';
    return 'bg-card border-border';
  };

  const currentUserMetric = metrics.find(m => m.userId === profile?.user_id);

  if (profileLoading || loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-32 w-full" />
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6 relative overflow-hidden">
      {/* Decorative streamers */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <Sparkles className="absolute top-10 left-10 h-12 w-12 text-yellow-400/30 animate-pulse" />
        <Sparkles className="absolute top-20 right-20 h-16 w-16 text-blue-400/30 animate-pulse delay-75" />
        <Sparkles className="absolute bottom-20 left-1/4 h-10 w-10 text-pink-400/30 animate-pulse delay-150" />
        <Sparkles className="absolute top-1/3 right-1/3 h-14 w-14 text-purple-400/30 animate-pulse delay-300" />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <Trophy className="h-10 w-10 text-primary" />
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Sales Leaderboard
            </h1>
            <p className="text-muted-foreground">Top performers in the last 30 days</p>
          </div>
        </div>

        {/* Current User Highlight */}
        {currentUserMetric && (
          <Card className="mb-6 border-2 border-primary shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Your Performance
                </span>
                <span className="text-2xl font-bold text-primary">
                  Rank #{currentUserMetric.rank}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">{currentUserMetric.recordings30Days}</div>
                  <div className="text-sm text-muted-foreground">Recordings</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">{currentUserMetric.placeholderMetric1}</div>
                  <div className="text-sm text-muted-foreground">Metric 2 (TBD)</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">{currentUserMetric.placeholderMetric2}</div>
                  <div className="text-sm text-muted-foreground">Metric 3 (TBD)</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Leaderboard Rankings */}
        <div className="space-y-3">
          {metrics.map((metric) => (
            <Card
              key={metric.userId}
              className={`transition-all hover:scale-[1.02] ${getRankColor(metric.rank)} ${
                metric.userId === profile?.user_id ? 'ring-2 ring-primary' : ''
              }`}
            >
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  {/* Rank and Trophy */}
                  <div className="flex items-center justify-center w-16 h-16 rounded-full bg-background">
                    {getTrophyIcon(metric.rank)}
                  </div>

                  {/* Name and Rank */}
                  <div className="flex-1">
                    <h3 className="text-xl font-bold flex items-center gap-2">
                      {metric.name}
                      {metric.userId === profile?.user_id && (
                        <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">YOU</span>
                      )}
                    </h3>
                    <p className="text-sm text-muted-foreground">Rank #{metric.rank}</p>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-6 text-center">
                    <div>
                      <div className="text-2xl font-bold">{metric.recordings30Days}</div>
                      <div className="text-xs text-muted-foreground">Recordings</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metric.placeholderMetric1}</div>
                      <div className="text-xs text-muted-foreground">Metric 2</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metric.placeholderMetric2}</div>
                      <div className="text-xs text-muted-foreground">Metric 3</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {metrics.length === 0 && !loading && (
          <Card>
            <CardContent className="p-12 text-center">
              <Trophy className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg text-muted-foreground">No salespeople data available yet.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
