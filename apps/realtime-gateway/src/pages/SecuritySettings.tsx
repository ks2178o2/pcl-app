import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import { use2FA } from '@/hooks/use2FA';
import { useLoginHistory } from '@/hooks/useLoginHistory';
import { NavigationMenu } from '@/components/NavigationMenu';
import { useToast } from '@/hooks/use-toast';
import { 
  ArrowLeft, 
  Shield, 
  Clock, 
  Smartphone,
  Key,
  Copy,
  Download,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import type { Device } from '@/hooks/use2FA';
import type { LoginHistoryEntry } from '@/hooks/useLoginHistory';

export const SecuritySettings = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  // 2FA state
  const {
    loading: faLoading,
    status: faStatus,
    fetchStatus: fetchFAStatus,
    setup2FA,
    verifyCode: verifyFACode,
    enable2FA,
    disable2FA,
    listDevices,
    removeDevice
  } = use2FA();
  
  // Login history state
  const {
    history,
    loading: historyLoading,
    total,
    fetchHistory
  } = useLoginHistory();
  
  // 2FA setup state
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [qrCodeData, setQrCodeData] = useState<string | null>(null);
  const [twoFactorSecret, setTwoFactorSecret] = useState<string>('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [devices, setDevices] = useState<Device[]>([]);
  
  // Pagination state
  const [historyPage, setHistoryPage] = useState(0);
  const historyLimit = 20;

  useEffect(() => {
    if (user) {
      fetchFAStatus();
      loadDevices();
      fetchHistory(historyLimit, 0);
    }
  }, [user]);

  const loadDevices = async () => {
    try {
      const deviceList = await listDevices();
      setDevices(deviceList);
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  };

  const handleSetup2FA = async () => {
    try {
      const result = await setup2FA();
      setQrCodeData(result.qr_code);
      setTwoFactorSecret(result.secret);
      setBackupCodes(result.backup_codes);
      setShow2FASetup(true);
      toast({
        title: "2FA Setup Started",
        description: "Scan the QR code with your authenticator app.",
      });
    } catch (error: any) {
      toast({
        title: "Setup Failed",
        description: error.message || "Failed to start 2FA setup",
        variant: "destructive",
      });
    }
  };

  const handleVerifyAndEnable = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      toast({
        title: "Invalid Code",
        description: "Please enter a 6-digit verification code",
        variant: "destructive",
      });
      return;
    }

    setIsVerifying(true);
    try {
      await enable2FA(verificationCode);
      await fetchFAStatus();
      setShow2FASetup(false);
      setVerificationCode('');
      toast({
        title: "2FA Enabled",
        description: "Two-factor authentication has been successfully enabled.",
      });
    } catch (error: any) {
      toast({
        title: "Verification Failed",
        description: error.message || "Invalid verification code",
        variant: "destructive",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDisable2FA = async () => {
    try {
      await disable2FA();
      await fetchFAStatus();
      toast({
        title: "2FA Disabled",
        description: "Two-factor authentication has been disabled.",
      });
    } catch (error: any) {
      toast({
        title: "Failed to Disable",
        description: error.message || "Failed to disable 2FA",
        variant: "destructive",
      });
    }
  };

  const handleRemoveDevice = async (deviceId: string) => {
    try {
      await removeDevice(deviceId);
      await loadDevices();
      toast({
        title: "Device Removed",
        description: "The device has been removed from your account.",
      });
    } catch (error: any) {
      toast({
        title: "Failed to Remove",
        description: error.message || "Failed to remove device",
        variant: "destructive",
      });
    }
  };

  const copyBackupCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast({
      title: "Copied",
      description: "Backup code copied to clipboard",
    });
  };

  const downloadBackupCodes = () => {
    const content = backupCodes.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleHistoryPageChange = (newPage: number) => {
    const offset = newPage * historyLimit;
    fetchHistory(historyLimit, offset);
    setHistoryPage(newPage);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    if (status === 'success') {
      return <Badge variant="default" className="bg-green-100 text-green-800">Success</Badge>;
    } else if (status === 'failed') {
      return <Badge variant="destructive">Failed</Badge>;
    } else {
      return <Badge variant="secondary">Blocked</Badge>;
    }
  };

  const getMethodBadge = (method: string) => {
    const methods: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' }> = {
      'password': { label: 'Password', variant: 'default' },
      'magic_link': { label: 'Magic Link', variant: 'secondary' },
      '2fa_code': { label: '2FA Code', variant: 'outline' }
    };
    
    const methodInfo = methods[method] || { label: method, variant: 'secondary' as const };
    return <Badge variant={methodInfo.variant}>{methodInfo.label}</Badge>;
  };

  const is2FAEnabled = faStatus?.enabled ?? false;
  const is2FASetupRequired = faStatus?.setup_required ?? false;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
        <NavigationMenu />
      </div>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Shield className="h-8 w-8" />
          Security Settings
        </h1>
        <p className="text-muted-foreground">
          Manage your account security, two-factor authentication, and view your login history.
        </p>
      </div>

      <Tabs defaultValue="2fa" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="2fa">
            <Key className="h-4 w-4 mr-2" />
            Two-Factor Authentication
          </TabsTrigger>
          <TabsTrigger value="history">
            <Clock className="h-4 w-4 mr-2" />
            Login History
          </TabsTrigger>
        </TabsList>

        {/* 2FA Tab */}
        <TabsContent value="2fa" className="space-y-6">
          {/* 2FA Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Two-Factor Authentication
              </CardTitle>
              <CardDescription>
                Add an extra layer of security to your account.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Current Status */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {is2FAEnabled ? (
                    <>
                      <CheckCircle className="h-6 w-6 text-green-600" />
                      <div>
                        <div className="font-medium">2FA Enabled</div>
                        <div className="text-sm text-muted-foreground">
                          Your account is protected with two-factor authentication
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-6 w-6 text-yellow-600" />
                      <div>
                        <div className="font-medium">2FA Disabled</div>
                        <div className="text-sm text-muted-foreground">
                          Enable 2FA to secure your account
                        </div>
                      </div>
                    </>
                  )}
                </div>
                {is2FAEnabled ? (
                  <Button variant="destructive" onClick={handleDisable2FA} disabled={faLoading}>
                    Disable 2FA
                  </Button>
                ) : (
                  <Button onClick={handleSetup2FA} disabled={faLoading}>
                    Enable 2FA
                  </Button>
                )}
              </div>

              {/* 2FA Setup Flow */}
              {show2FASetup && (
                <Card className="border-primary">
                  <CardHeader>
                    <CardTitle>Complete 2FA Setup</CardTitle>
                    <CardDescription>
                      Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* QR Code */}
                    {qrCodeData && (
                      <div className="flex justify-center p-4 bg-white rounded-lg border">
                        <img 
                          src={qrCodeData} 
                          alt="QR Code for 2FA setup"
                          className="w-48 h-48"
                        />
                      </div>
                    )}

                    {/* Manual Entry */}
                    <div className="space-y-2">
                      <Label>Manual Entry Key</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          value={twoFactorSecret}
                          readOnly
                          className="font-mono text-sm"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            navigator.clipboard.writeText(twoFactorSecret);
                            toast({
                              title: "Copied",
                              description: "Secret key copied to clipboard",
                            });
                          }}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Backup Codes */}
                    {backupCodes.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label>Backup Codes</Label>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={downloadBackupCodes}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        </div>
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            Save these backup codes in a secure location. You can use them to access your account if you lose access to your authenticator device.
                          </AlertDescription>
                        </Alert>
                        <div className="grid grid-cols-2 gap-2">
                          {backupCodes.map((code, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between p-2 border rounded-lg font-mono text-sm"
                            >
                              <span>{code}</span>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyBackupCode(code)}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Verification */}
                    <div className="space-y-3">
                      <Label htmlFor="verification-code">Enter Verification Code</Label>
                      <Input
                        id="verification-code"
                        placeholder="000000"
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        maxLength={6}
                        className="text-center text-2xl tracking-widest font-mono"
                      />
                      <Button
                        onClick={handleVerifyAndEnable}
                        disabled={!verificationCode || verificationCode.length !== 6 || isVerifying}
                        className="w-full"
                      >
                        {isVerifying ? 'Verifying...' : 'Complete Setup'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Trusted Devices */}
              {is2FAEnabled && devices.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Trusted Devices</Label>
                    <Badge variant="secondary">{devices.length} devices</Badge>
                  </div>
                  <div className="space-y-2">
                    {devices.map((device) => (
                      <div
                        key={device.id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Smartphone className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{device.device_name || 'Unknown Device'}</div>
                            <div className="text-sm text-muted-foreground">
                              Last used {device.last_used_at ? formatDate(device.last_used_at) : 'Never'}
                              {device.is_primary && (
                                <Badge variant="outline" className="ml-2">
                                  Primary
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        {!device.is_primary && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveDevice(device.id)}
                          >
                            Remove
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Login History Tab */}
        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Login History
              </CardTitle>
              <CardDescription>
                View your recent login attempts and account activity.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {historyLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                  <p className="text-muted-foreground">Loading login history...</p>
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No login history available</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Login Entries */}
                  <div className="space-y-2">
                    {history.map((entry) => (
                      <div
                        key={entry.id}
                        className="flex items-center justify-between p-4 border rounded-lg"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            {getStatusBadge(entry.status)}
                            {getMethodBadge(entry.login_method)}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {entry.ip_address && <span className="mr-3">IP: {entry.ip_address}</span>}
                            {entry.device_name && <span className="mr-3">Device: {entry.device_name}</span>}
                            <span>Time: {formatDate(entry.login_at)}</span>
                          </div>
                          {entry.failure_reason && (
                            <Alert variant="destructive" className="mt-2">
                              <AlertDescription>{entry.failure_reason}</AlertDescription>
                            </Alert>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Pagination */}
                  {total > historyLimit && (
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-muted-foreground">
                        Showing {historyPage * historyLimit + 1} to {Math.min((historyPage + 1) * historyLimit, total)} of {total} entries
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleHistoryPageChange(historyPage - 1)}
                          disabled={historyPage === 0}
                        >
                          Previous
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleHistoryPageChange(historyPage + 1)}
                          disabled={(historyPage + 1) * historyLimit >= total}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SecuritySettings;

