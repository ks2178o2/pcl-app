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
      const {
        data,
        error
      } = await supabase.functions.invoke('debug-sms');
      if (error) {
        setResult({
          success: false,
          message: `Error: ${error.message}`,
          data: null
        });
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