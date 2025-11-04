/**
 * Analysis Settings Management Component
 * Allows org admins and system admins to configure analysis provider order and enabled providers
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Save, RefreshCw, Brain, AlertCircle } from 'lucide-react';

const AVAILABLE_PROVIDERS = [
  { value: 'openai', label: 'OpenAI (GPT-4o-mini)' },
  { value: 'gemini', label: 'Google Gemini 2.0 Flash' },
];

export const AnalysisSettingsManagement: React.FC = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [providerOrder, setProviderOrder] = useState<string[]>(['openai', 'gemini']);
  const [enabledProviders, setEnabledProviders] = useState<string[]>(['openai', 'gemini']);
  const [primaryProvider, setPrimaryProvider] = useState<string>('openai');
  const [backupProvider, setBackupProvider] = useState<string>('gemini');

  const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';

  const loadSettings = async () => {
    setLoading(true);
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData?.session?.access_token;

      const resp = await fetch(`${API_BASE_URL}/api/analysis/settings`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!resp.ok) {
        if (resp.status === 404) {
          // No settings yet, use defaults
          return;
        }
        throw new Error(`Failed to load settings: ${resp.status}`);
      }

      const data = await resp.json();
      if (data.provider_order && Array.isArray(data.provider_order)) {
        setProviderOrder(data.provider_order);
        if (data.provider_order.length > 0) {
          setPrimaryProvider(data.provider_order[0]);
          setBackupProvider(data.provider_order[1] || data.provider_order[0]);
        }
      }
      if (data.enabled_providers && Array.isArray(data.enabled_providers)) {
        setEnabledProviders(data.enabled_providers);
      }
    } catch (error) {
      console.error('Error loading analysis settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to load analysis settings',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData?.session?.access_token;

      // Build provider order from primary/backup
      const order = [primaryProvider];
      if (backupProvider && backupProvider !== primaryProvider) {
        order.push(backupProvider);
      }

      const payload = {
        provider_order: order,
        enabled_providers: enabledProviders,
      };

      const resp = await fetch(`${API_BASE_URL}/api/analysis/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(`Failed to save: ${resp.status} ${errorText}`);
      }

      const data = await resp.json();
      setProviderOrder(data.provider_order || order);
      
      toast({
        title: 'Settings saved',
        description: 'Analysis provider settings have been updated successfully.',
      });
    } catch (error) {
      console.error('Error saving analysis settings:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save analysis settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleEnableProvider = (provider: string, enabled: boolean) => {
    if (enabled) {
      setEnabledProviders([...enabledProviders, provider].filter((p, i, arr) => arr.indexOf(p) === i));
    } else {
      setEnabledProviders(enabledProviders.filter(p => p !== provider));
      // Remove from primary/backup if disabled
      if (primaryProvider === provider) {
        const remaining = enabledProviders.filter(p => p !== provider);
        setPrimaryProvider(remaining[0] || 'openai');
      }
      if (backupProvider === provider) {
        const remaining = enabledProviders.filter(p => p !== provider && p !== primaryProvider);
        setBackupProvider(remaining[0] || primaryProvider);
      }
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Analysis Provider Settings
          </CardTitle>
          <CardDescription>
            Configure which AI models to use for transcript analysis and in what order (primary/backup).
            The system will try the primary provider first, then fall back to the backup if needed.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">Loading settings...</span>
            </div>
          ) : (
            <>
              {/* Provider Selection */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Primary Provider</Label>
                  <Select
                    value={primaryProvider}
                    onValueChange={setPrimaryProvider}
                    disabled={!enabledProviders.includes(primaryProvider)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_PROVIDERS.map(p => (
                        <SelectItem
                          key={p.value}
                          value={p.value}
                          disabled={!enabledProviders.includes(p.value)}
                        >
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground">
                    This provider will be used first for all transcript analysis.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Backup Provider</Label>
                  <Select
                    value={backupProvider}
                    onValueChange={setBackupProvider}
                    disabled={!enabledProviders.includes(backupProvider) || enabledProviders.length < 2}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_PROVIDERS.map(p => (
                        <SelectItem
                          key={p.value}
                          value={p.value}
                          disabled={p.value === primaryProvider || !enabledProviders.includes(p.value)}
                        >
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground">
                    This provider will be used if the primary provider fails or is unavailable.
                  </p>
                </div>
              </div>

              {/* Enabled Providers */}
              <div className="space-y-2">
                <Label>Enabled Providers</Label>
                <div className="space-y-2">
                  {AVAILABLE_PROVIDERS.map(provider => (
                    <div key={provider.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`enabled-${provider.value}`}
                        checked={enabledProviders.includes(provider.value)}
                        onChange={(e) => handleEnableProvider(provider.value, e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                      <Label htmlFor={`enabled-${provider.value}`} className="font-normal cursor-pointer">
                        {provider.label}
                      </Label>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  Only enabled providers can be selected as primary or backup.
                </p>
              </div>

              {/* Current Configuration Summary */}
              <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <AlertCircle className="h-4 w-4" />
                  Current Configuration
                </div>
                <div className="text-sm space-y-1">
                  <p>
                    <span className="font-medium">Provider Order:</span>{' '}
                    {providerOrder.length > 0 ? providerOrder.join(' → ') : 'Not set'}
                  </p>
                  <p>
                    <span className="font-medium">Enabled:</span>{' '}
                    {enabledProviders.length > 0 ? enabledProviders.join(', ') : 'None'}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3">
                <Button onClick={handleSave} disabled={saving} className="flex items-center gap-2">
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Settings'}
                </Button>
                <Button
                  variant="outline"
                  onClick={loadSettings}
                  disabled={loading || saving}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

