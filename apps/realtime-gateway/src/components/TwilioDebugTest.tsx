import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { supabase } from '@/integrations/supabase/client';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
export const TwilioDebugTest: React.FC = () => {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const testCredentials = async () => {
    setTesting(true);
    setResult(null);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const { getApiUrl } = await import('@/utils/apiConfig');
      const resp = await fetch(getApiUrl('/api/twilio/debug'), {
        headers: {
          Authorization: session?.access_token ? `Bearer ${session.access_token}` : ''
        }
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok) {
        setResult({ success: false, message: data?.detail || resp.statusText, data: null });
      } else {
        setResult(data);
      }
    } catch (error) {
      setResult({
        success: false,
        message: `Test failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        data: null
      });
    } finally {
      setTesting(false);
    }
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle>Twilio Debug Test</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button onClick={testCredentials} disabled={testing}>
          {testing && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Test Twilio Connection
        </Button>
        
        {result && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {result.success ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              <span className="font-medium">
                {result.success ? 'Connection Successful' : 'Connection Failed'}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{result.message}</p>
            {result.data && (
              <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                {JSON.stringify(result.data, null, 2)}
              </pre>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};