import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { supabase } from '@/integrations/supabase/client';
import { useUserRoles } from '@/hooks/useUserRoles';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { Calendar, TrendingUp, Users, MessageSquare, Star, Filter } from 'lucide-react';

interface SalespersonMetrics {
  id: string;
  name: string;
  center_name: string;
  region_name: string;
  total_calls: number;
  avg_quality_score: number;
  total_duration_hours: number;
  last_call_date: string;
  conversion_rate: number;
}

interface CallTypeBreakdown {
  call_type: string;
  total: number;
  scheduled: number;
  not_scheduled: number;
  success_rate: number;
  avg_quality_score: number;
}

interface ReportsData {
  totalRecordings: number;
  avgQualityScore: number;
  totalSalespeople: number;
  activeRegions: number;
  salespersonMetrics: SalespersonMetrics[];
  qualityTrends: Array<{ date: string; score: number; calls: number }>;
  centerMetrics: Array<{ name: string; calls: number; quality: number }>;
  callTypeBreakdown: CallTypeBreakdown[];
  callCategoryBreakdown: {
    scheduled: number;
    not_scheduled: number;
    other_question: number;
  };
}

export const EnterpriseReports = () => {
  const [reportsData, setReportsData] = useState<ReportsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const [selectedCenter, setSelectedCenter] = useState<string>('all');
  
  const { isLeader, isCoach, isSystemAdmin, roles } = useUserRoles();
  const { regions, centers } = useOrganizationData();

  useEffect(() => {
    const hasPermission = roles.includes('leader') || roles.includes('coach') || roles.includes('system_admin');
    if (hasPermission && roles.length > 0) {
      fetchReportsData();
    }
  }, [roles, selectedRegion, selectedCenter]);

  const fetchReportsData = async () => {
    setLoading(true);
    try {
      // Fetch call records with quality scores - simplified query without joins that don't exist
      let query = supabase
        .from('call_records')
        .select(`
          *,
          call_analyses(overall_sentiment, sales_performance_score, trust_level)
        `)
        .not('call_analyses', 'is', null);

      const { data: callRecords, error } = await query;

      if (error) {
        console.error('Error fetching reports data:', error);
        return;
      }

      // If we have call records, fetch related user and center data separately
      let usersData = [];
      let centersData = [];
      
      if (callRecords && callRecords.length > 0) {
        // Get unique user IDs and fetch profiles
        const userIds = [...new Set(callRecords.map(r => r.user_id))];
        const { data: profiles } = await supabase
          .from('profiles')
          .select('id, salesperson_name')
          .in('id', userIds);
        
        usersData = profiles || [];

        // Get unique center IDs and fetch centers with regions
        const centerIds = [...new Set(callRecords.map(r => r.center_id).filter(Boolean))];
        if (centerIds.length > 0) {
            const { data: centers } = await supabase
              .from('centers')
              .select(`
                id, 
                name,
                region:regions(name)
              `)
              .in('id', centerIds);
          
          centersData = centers || [];
        }
      }

      // Process the data with separate lookups
      const processedData = processReportsData(callRecords || [], usersData, centersData);
      setReportsData(processedData);
    } catch (error) {
      console.error('Error in fetchReportsData:', error);
    } finally {
      setLoading(false);
    }
  };

  const processReportsData = (callRecords: any[], usersData: any[] = [], centersData: any[] = []): ReportsData => {
    const totalRecordings = callRecords.length;
    const validScores = callRecords
      .map(r => r.call_analyses?.[0]?.sales_performance_score)
      .filter(score => score !== null && score !== undefined);
    
    const avgQualityScore = validScores.length > 0 
      ? validScores.reduce((sum, score) => sum + score, 0) / validScores.length 
      : 0;

    // Group by salesperson
    const salespersonData = callRecords.reduce((acc, record) => {
      const userId = record.user_id;
      const userProfile = usersData.find(u => u.id === userId);
      const name = userProfile?.salesperson_name || 'Unknown';
      const centerData = centersData.find(c => c.id === record.center_id);
      const centerName = centerData?.name || 'Unknown';
      const regionName = centerData?.region?.name || 'Unknown';
      
      if (!acc[userId]) {
        acc[userId] = {
          id: userId,
          name,
          center_name: centerName,
          region_name: regionName,
          calls: [],
          total_duration: 0
        };
      }
      
      acc[userId].calls.push(record);
      acc[userId].total_duration += record.duration_seconds || 0;
      return acc;
    }, {} as any);

    const salespersonMetrics: SalespersonMetrics[] = Object.values(salespersonData).map((sp: any) => {
      const qualityScores = sp.calls
        .map((call: any) => call.call_analyses?.[0]?.sales_performance_score)
        .filter((score: any) => score !== null && score !== undefined);
      
      return {
        id: sp.id,
        name: sp.name,
        center_name: sp.center_name,
        region_name: sp.region_name,
        total_calls: sp.calls.length,
        avg_quality_score: qualityScores.length > 0 
          ? qualityScores.reduce((sum: number, score: number) => sum + score, 0) / qualityScores.length 
          : 0,
        total_duration_hours: sp.total_duration / 3600,
        last_call_date: sp.calls.sort((a: any, b: any) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0]?.created_at || '',
        conversion_rate: Math.random() * 30 + 10 // Mock data for now
      };
    });

    // Generate quality trends (last 30 days)
    const qualityTrends = generateQualityTrends(callRecords);

    // Generate center metrics
    const centerMetrics = generateCenterMetrics(callRecords, centersData);

    // Generate call_type breakdown
    const callTypeBreakdown = generateCallTypeBreakdown(callRecords);

    // Generate call_category breakdown
    const callCategoryBreakdown = {
      scheduled: callRecords.filter(r => r.call_category === 'consult_scheduled').length,
      not_scheduled: callRecords.filter(r => r.call_category === 'consult_not_scheduled').length,
      other_question: callRecords.filter(r => r.call_category === 'other_question' || !r.call_category).length
    };

      return {
        totalRecordings,
        avgQualityScore,
        totalSalespeople: Object.keys(salespersonData).length,
        activeRegions: new Set(centersData.map(c => c.region?.name).filter(Boolean)).size,
        salespersonMetrics: salespersonMetrics.sort((a, b) => b.avg_quality_score - a.avg_quality_score),
        qualityTrends,
        centerMetrics,
        callTypeBreakdown,
        callCategoryBreakdown
      };
  };

  const generateCallTypeBreakdown = (callRecords: any[]): CallTypeBreakdown[] => {
    const typeMap = new Map<string, { total: number; scheduled: number; not_scheduled: number; qualityScores: number[] }>();
    
    callRecords.forEach(record => {
      const callType = record.call_type || 'unknown';
      const category = record.call_category;
      const qualityScore = record.call_analyses?.[0]?.sales_performance_score;
      
      if (!typeMap.has(callType)) {
        typeMap.set(callType, { total: 0, scheduled: 0, not_scheduled: 0, qualityScores: [] });
      }
      
      const stats = typeMap.get(callType)!;
      stats.total++;
      
      if (category === 'consult_scheduled') {
        stats.scheduled++;
      } else if (category === 'consult_not_scheduled') {
        stats.not_scheduled++;
      }
      
      if (qualityScore !== null && qualityScore !== undefined) {
        stats.qualityScores.push(qualityScore);
      }
    });
    
    return Array.from(typeMap.entries()).map(([call_type, stats]) => ({
      call_type: call_type === 'unknown' ? 'Not Classified' : call_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      total: stats.total,
      scheduled: stats.scheduled,
      not_scheduled: stats.not_scheduled,
      success_rate: stats.total > 0 ? Math.round((stats.scheduled / stats.total) * 100) : 0,
      avg_quality_score: stats.qualityScores.length > 0 
        ? Math.round((stats.qualityScores.reduce((sum, score) => sum + score, 0) / stats.qualityScores.length) * 10) / 10
        : 0
    })).sort((a, b) => b.total - a.total);
  };

  const generateQualityTrends = (callRecords: any[]) => {
    // Group calls by date and calculate average scores
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return date.toISOString().split('T')[0];
    }).reverse();

    return last30Days.map(date => {
      const dayRecords = callRecords.filter(r => 
        r.created_at.split('T')[0] === date
      );
      
      const scores = dayRecords
        .map(r => r.call_analyses?.[0]?.sales_performance_score)
        .filter(score => score !== null && score !== undefined);
      
      return {
        date,
        score: scores.length > 0 ? scores.reduce((sum, s) => sum + s, 0) / scores.length : 0,
        calls: dayRecords.length
      };
    });
  };

  const generateCenterMetrics = (callRecords: any[], centersData: any[] = []) => {
    const centerData = callRecords.reduce((acc, record) => {
      const centerInfo = centersData.find(c => c.id === record.center_id);
      const centerName = centerInfo?.name || 'Unknown';
      
      if (!acc[centerName]) {
        acc[centerName] = { calls: [], scores: [] };
      }
      acc[centerName].calls.push(record);
      
      const score = record.call_analyses?.[0]?.sales_performance_score;
      if (score !== null && score !== undefined) {
        acc[centerName].scores.push(score);
      }
      return acc;
    }, {} as any);

    return Object.entries(centerData).map(([name, data]: [string, any]) => ({
      name,
      calls: data.calls.length,
      quality: data.scores.length > 0 
        ? data.scores.reduce((sum: number, score: number) => sum + score, 0) / data.scores.length 
        : 0
    }));
  };

  if (!isLeader() && !isCoach() && !isSystemAdmin()) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">You don't have permission to view enterprise reports.</p>
        </CardContent>
      </Card>
    );
  }

  if (loading || !reportsData) {
    return (
      <Card>
        <CardContent className="p-6">
          <p>Loading reports...</p>
        </CardContent>
      </Card>
    );
  }

  const COLORS = ['hsl(var(--primary))', 'hsl(var(--secondary))', 'hsl(var(--accent))', 'hsl(var(--muted))'];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Select value={selectedRegion} onValueChange={setSelectedRegion}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select Region" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Regions</SelectItem>
                {regions.map(region => (
                  <SelectItem key={region.id} value={region.id}>{region.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedCenter} onValueChange={setSelectedCenter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select Center" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Centers</SelectItem>
                {centers
                  .filter(center => selectedRegion === 'all' || center.region_id === selectedRegion)
                  .map(center => (
                    <SelectItem key={center.id} value={center.id}>{center.name}</SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Recordings</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reportsData.totalRecordings}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Quality Score</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reportsData.avgQualityScore.toFixed(1)}/10</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Salespeople</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reportsData.totalSalespeople}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Regions</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reportsData.activeRegions}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="salespeople" className="space-y-4">
        <TabsList>
          <TabsTrigger value="salespeople">Salespeople Rankings</TabsTrigger>
          <TabsTrigger value="trends">Quality Trends</TabsTrigger>
          <TabsTrigger value="centers">Center Performance</TabsTrigger>
          <TabsTrigger value="call-types">Call Type Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="salespeople" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Salesperson Performance Rankings</CardTitle>
              <CardDescription>Ranked by average conversation quality score</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rank</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Center</TableHead>
                    <TableHead>Region</TableHead>
                    <TableHead>Total Calls</TableHead>
                    <TableHead>Avg Quality</TableHead>
                    <TableHead>Hours Logged</TableHead>
                    <TableHead>Last Call</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportsData.salespersonMetrics.map((person, index) => (
                    <TableRow key={person.id}>
                      <TableCell>
                        <Badge variant={index < 3 ? "default" : "secondary"}>
                          #{index + 1}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">{person.name}</TableCell>
                      <TableCell>{person.center_name}</TableCell>
                      <TableCell>{person.region_name}</TableCell>
                      <TableCell>{person.total_calls}</TableCell>
                      <TableCell>
                        <Badge variant={person.avg_quality_score >= 7 ? "default" : "destructive"}>
                          {person.avg_quality_score.toFixed(1)}/10
                        </Badge>
                      </TableCell>
                      <TableCell>{person.total_duration_hours.toFixed(1)}h</TableCell>
                      <TableCell>
                        {person.last_call_date ? new Date(person.last_call_date).toLocaleDateString() : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quality Score Trends (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={reportsData.qualityTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(date) => new Date(date).toLocaleDateString()} />
                  <YAxis domain={[0, 10]} />
                  <Tooltip 
                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                    formatter={(value: number, name: string) => [
                      name === 'score' ? `${value.toFixed(1)}/10` : value, 
                      name === 'score' ? 'Quality Score' : 'Calls'
                    ]}
                  />
                  <Line type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2} />
                  <Line type="monotone" dataKey="calls" stroke="hsl(var(--secondary))" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="centers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Center Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={reportsData.centerMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="calls" fill="hsl(var(--primary))" />
                  <Bar dataKey="quality" fill="hsl(var(--secondary))" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="call-types" className="space-y-4">
          {/* Call Category Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Call Status Breakdown</CardTitle>
              <CardDescription>Distribution of calls by success status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {reportsData.callCategoryBreakdown.scheduled}
                  </div>
                  <div className="text-sm text-muted-foreground">✅ Scheduled</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {reportsData.callCategoryBreakdown.not_scheduled}
                  </div>
                  <div className="text-sm text-muted-foreground">❌ Not Scheduled</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-gray-600">
                    {reportsData.callCategoryBreakdown.other_question}
                  </div>
                  <div className="text-sm text-muted-foreground">❓ Other Question</div>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Scheduled', value: reportsData.callCategoryBreakdown.scheduled, fill: COLORS[0] },
                      { name: 'Not Scheduled', value: reportsData.callCategoryBreakdown.not_scheduled, fill: COLORS[1] },
                      { name: 'Other Question', value: reportsData.callCategoryBreakdown.other_question, fill: COLORS[2] }
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {[
                      { name: 'Scheduled', value: reportsData.callCategoryBreakdown.scheduled },
                      { name: 'Not Scheduled', value: reportsData.callCategoryBreakdown.not_scheduled },
                      { name: 'Other Question', value: reportsData.callCategoryBreakdown.other_question }
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Call Type Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Call Type Breakdown</CardTitle>
              <CardDescription>Performance metrics by call type</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={reportsData.callTypeBreakdown}>
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
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Call Type</TableHead>
                    <TableHead>Total Calls</TableHead>
                    <TableHead>Scheduled</TableHead>
                    <TableHead>Not Scheduled</TableHead>
                    <TableHead>Success Rate</TableHead>
                    <TableHead>Avg Quality</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportsData.callTypeBreakdown.map((type, index) => (
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
                        <Badge variant={type.success_rate >= 50 ? "default" : type.success_rate >= 30 ? "secondary" : "destructive"}>
                          {type.success_rate}%
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={type.avg_quality_score >= 7 ? "default" : "secondary"}>
                          {type.avg_quality_score.toFixed(1)}/10
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};