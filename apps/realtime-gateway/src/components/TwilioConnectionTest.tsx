import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { supabase } from '@/integrations/supabase/client';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export const TwilioConnectionTest: React.FC = () => {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const testConnection = async () => {
    setTesting(true);
    setResult(null);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
      const resp = await fetch(`${API_BASE_URL}/api/twilio/test-connection`, {
        headers: {
          Authorization: session?.access_token ? `Bearer ${session.access_token}` : ''
        }
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok) {
        setResult({ success: false, message: data?.detail || resp.statusText });
      } else {
        setResult({ success: !!data?.success, message: data?.success ? 'Twilio connection successful!' : (data?.message || 'Failed') });
      }
    } catch (error) {
      setResult({ 
        success: false, 
        message: `Test failed: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Twilio Connection Test
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Button 
            onClick={testConnection} 
            disabled={testing}
            className="w-full"
          >
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Twilio Connection'
            )}
          </Button>
          
          {result && (
            <div className={`flex items-center gap-2 p-3 rounded-lg ${
              result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>
              {result.success ? (
                <CheckCircle className="h-5 w-5" />
              ) : (
                <XCircle className="h-5 w-5" />
              )}
              <span className="text-sm">{result.message}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};