import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Loader2, BarChart3, TrendingUp, Calendar, RefreshCw } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { NavigationMenu } from '@/components/NavigationMenu';
import { useToast } from '@/hooks/use-toast';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';

interface CallTypeStatistics {
  call_type: string;
  total: number;
  scheduled: number;
  not_scheduled: number;
  other_question: number;
  success_rate: number;
  avg_quality_score: number;
  total_duration_seconds: number;
}

interface CallCategoryStatistics {
  category: string;
  total: number;
  avg_quality_score: number;
  total_duration_seconds: number;
}

interface CallStatisticsResponse {
  total_calls: number;
  call_type_breakdown: CallTypeStatistics[];
  call_category_breakdown: CallCategoryStatistics[];
  date_range: {
    start: string;
    end: string;
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export const CallStatisticsTest: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<CallStatisticsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchStatistics = async () => {
    if (!user) {
      setError('Please log in to view statistics');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Get auth token
      const { data: sessionData } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
      const token = sessionData?.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      // Build URL with optional date filters
      let url = `${API_BASE_URL}/api/call-statistics/call-types`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      console.log('🔍 Fetching statistics from:', url);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result: CallStatisticsResponse = await response.json();
      console.log('✅ Statistics fetched:', result);
      setData(result);

      toast({
        title: 'Statistics loaded',
        description: `Found ${result.total_calls} calls with statistics`,
      });
    } catch (err: any) {
      console.error('❌ Error fetching statistics:', err);
      setError(err.message || 'Failed to fetch statistics');
      toast({
        title: 'Error',
        description: err.message || 'Failed to fetch statistics',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Auto-fetch on mount
    fetchStatistics();
  }, [user]);

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <div className="min-h-screen bg-background">
      <NavigationMenu />
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BarChart3 className="h-8 w-8" />
              Call Statistics API Test
            </h1>
            <p className="text-muted-foreground mt-2">
              Test the <code className="bg-muted px-1 rounded">/api/call-statistics/call-types</code> endpoint
            </p>
          </div>
          <Button onClick={fetchStatistics} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </>
            )}
          </Button>
        </div>

        {/* Date Filters */}
        <Card>
          <CardHeader>
            <CardTitle>Date Range Filters</CardTitle>
            <CardDescription>Optionally filter statistics by date range</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-date">Start Date (YYYY-MM-DD)</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="2024-01-01"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end-date">End Date (YYYY-MM-DD)</Label>
                <Input
                  id="end-date"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="2024-12-31"
                />
              </div>
            </div>
            <Button onClick={fetchStatistics} className="mt-4" disabled={loading}>
              Apply Filters
            </Button>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="border-red-500">
            <CardHeader>
              <CardTitle className="text-red-600">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-600">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Loading State */}
        {loading && !data && (
          <Card>
            <CardContent className="p-12 text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p>Loading statistics...</p>
            </CardContent>
          </Card>
        )}

        {/* Statistics Display */}
        {data && !loading && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{data.total_calls}</div>
                  <p className="text-xs text-muted-foreground">
                    {data.date_range.start && data.date_range.end && (
                      <>
                        {new Date(data.date_range.start).toLocaleDateString()} -{' '}
                        {new Date(data.date_range.end).toLocaleDateString()}
                      </>
                    )}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Call Types</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{data.call_type_breakdown.length}</div>
                  <p className="text-xs text-muted-foreground">Unique call types</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Categories</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{data.call_category_breakdown.length}</div>
                  <p className="text-xs text-muted-foreground">Call categories</p>
                </CardContent>
              </Card>
            </div>

            {/* Call Type Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Call Type Breakdown</CardTitle>
                <CardDescription>Statistics by call type with success rates and quality scores</CardDescription>
              </CardHeader>
              <CardContent>
                {data.call_type_breakdown.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No call type data available</p>
                ) : (
                  <>
                    {/* Bar Chart */}
                    <div className="mb-6">
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data.call_type_breakdown}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="call_type"
                            angle={-45}
                            textAnchor="end"
                            height={100}
                          />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="total" fill={COLORS[0]} name="Total Calls" />
                          <Bar dataKey="scheduled" fill={COLORS[1]} name="Scheduled" />
                          <Bar dataKey="not_scheduled" fill={COLORS[2]} name="Not Scheduled" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Table */}
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Call Type</TableHead>
                          <TableHead>Total</TableHead>
                          <TableHead>Scheduled</TableHead>
                          <TableHead>Not Scheduled</TableHead>
                          <TableHead>Other</TableHead>
                          <TableHead>Success Rate</TableHead>
                          <TableHead>Avg Quality</TableHead>
                          <TableHead>Total Duration</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {data.call_type_breakdown.map((type, index) => (
                          <TableRow key={index}>
                            <TableCell className="font-medium">{type.call_type}</TableCell>
                            <TableCell>{type.total}</TableCell>
                            <TableCell>
                              <Badge variant="default">{type.scheduled}</Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="secondary">{type.not_scheduled}</Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">{type.other_question}</Badge>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  type.success_rate >= 50
                                    ? 'default'
                                    : type.success_rate >= 30
                                    ? 'secondary'
                                    : 'destructive'
                                }
                              >
                                {type.success_rate.toFixed(1)}%
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={type.avg_quality_score >= 7 ? 'default' : 'secondary'}>
                                {type.avg_quality_score.toFixed(1)}/10
                              </Badge>
                            </TableCell>
                            <TableCell>{formatDuration(type.total_duration_seconds)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Call Category Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Call Category Breakdown</CardTitle>
                <CardDescription>Statistics by call category (consult_scheduled, consult_not_scheduled, etc.)</CardDescription>
              </CardHeader>
              <CardContent>
                {data.call_category_breakdown.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No category data available</p>
                ) : (
                  <>
                    {/* Pie Chart */}
                    <div className="mb-6">
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={data.call_category_breakdown}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={100}
                            fill="#8884d8"
                            dataKey="total"
                          >
                            {data.call_category_breakdown.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Table */}
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Category</TableHead>
                          <TableHead>Total Calls</TableHead>
                          <TableHead>Avg Quality Score</TableHead>
                          <TableHead>Total Duration</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {data.call_category_breakdown.map((category, index) => (
                          <TableRow key={index}>
                            <TableCell className="font-medium">{category.category}</TableCell>
                            <TableCell>{category.total}</TableCell>
                            <TableCell>
                              <Badge variant={category.avg_quality_score >= 7 ? 'default' : 'secondary'}>
                                {category.avg_quality_score.toFixed(1)}/10
                              </Badge>
                            </TableCell>
                            <TableCell>{formatDuration(category.total_duration_seconds)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Raw JSON Data */}
            <Card>
              <CardHeader>
                <CardTitle>Raw API Response</CardTitle>
                <CardDescription>Full JSON response from the API endpoint</CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

