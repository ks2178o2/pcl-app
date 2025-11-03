import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { use2FA } from '@/hooks/use2FA';
import { toast } from '@/hooks/use-toast';
import { InputOTP, InputOTPGroup, InputOTPSlot } from '@/components/ui/input-otp';
import { CheckCircle, Copy, Download } from 'lucide-react';

interface TwoFactorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const TwoFactorModal = ({ open, onOpenChange }: TwoFactorModalProps) => {
  const [step, setStep] = useState<'setup' | 'verify' | 'complete'>('setup');
  const [qrCode, setQrCode] = useState<string>('');
  const [secret, setSecret] = useState<string>('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const { setup2FA, verifyCode, enable2FA, loading } = use2FA();

  const handleSetup = async () => {
    try {
      setError('');
      const result = await setup2FA();
      setQrCode(result.qr_code);
      setSecret(result.secret);
      setBackupCodes(result.backup_codes);
      setStep('verify');
    } catch (err: any) {
      setError(err.message || 'Failed to setup 2FA');
    }
  };

  const handleVerify = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    try {
      setError('');
      const isValid = await verifyCode(verificationCode);
      
      if (!isValid) {
        setError('Invalid code. Please try again.');
        return;
      }

      // Enable 2FA
      await enable2FA(verificationCode);
      
      setStep('complete');
      toast({
        title: "2FA Enabled",
        description: "Two-factor authentication has been enabled for your account.",
      });
    } catch (err: any) {
      setError(err.message || 'Failed to verify code');
    }
  };

  const handleCopySecret = () => {
    navigator.clipboard.writeText(secret);
    toast({
      title: "Copied!",
      description: "Secret key copied to clipboard",
    });
  };

  const handleDownloadBackupCodes = () => {
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

  const handleClose = () => {
    setStep('setup');
    setVerificationCode('');
    setError('');
    setQrCode('');
    setSecret('');
    setBackupCodes([]);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Setup Two-Factor Authentication</DialogTitle>
          <DialogDescription>
            {step === 'setup' && 'Scan the QR code with your authenticator app'}
            {step === 'verify' && 'Enter the verification code to enable 2FA'}
            {step === 'complete' && '2FA has been enabled successfully'}
          </DialogDescription>
        </DialogHeader>

        {step === 'setup' && (
          <div className="space-y-4">
            <div className="flex justify-center items-center bg-muted rounded-lg p-8">
              {qrCode ? (
                <img src={`data:image/png;base64,${qrCode}`} alt="QR Code" className="w-64 h-64" />
              ) : (
                <div className="w-64 h-64 flex items-center justify-center text-muted-foreground">
                  Click "Generate QR Code" to begin
                </div>
              )}
            </div>

            {secret && (
              <div className="space-y-2">
                <Label>Manual Entry Key</Label>
                <div className="flex gap-2">
                  <Input value={secret} readOnly className="font-mono" />
                  <Button type="button" variant="outline" onClick={handleCopySecret}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Use this key if you can't scan the QR code
                </p>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Button
                onClick={handleSetup}
                disabled={loading}
                className="flex-1"
              >
                {qrCode ? 'Regenerate QR Code' : 'Generate QR Code'}
              </Button>
              <Button
                onClick={handleClose}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {step === 'verify' && (
          <div className="space-y-4">
            <div className="flex justify-center items-center bg-muted rounded-lg p-8">
              <img src={`data:image/png;base64,${qrCode}`} alt="QR Code" className="w-48 h-48" />
            </div>

            <div className="space-y-2">
              <Label>Enter Verification Code</Label>
              <div className="flex justify-center">
                <InputOTP
                  value={verificationCode}
                  onChange={(value) => {
                    setVerificationCode(value);
                    setError('');
                  }}
                  maxLength={6}
                >
                  <InputOTPGroup>
                    <InputOTPSlot index={0} />
                    <InputOTPSlot index={1} />
                    <InputOTPSlot index={2} />
                    <InputOTPSlot index={3} />
                    <InputOTPSlot index={4} />
                    <InputOTPSlot index={5} />
                  </InputOTPGroup>
                </InputOTP>
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Enter the 6-digit code from your authenticator app
              </p>
            </div>

            {backupCodes.length > 0 && (
              <Alert>
                <AlertDescription>
                  <strong>Save your backup codes!</strong>
                  <div className="mt-2 space-y-1">
                    {backupCodes.slice(0, 5).map((code, i) => (
                      <div key={i} className="font-mono text-xs">{code}</div>
                    ))}
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleDownloadBackupCodes}
                    className="mt-2"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download All Backup Codes
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Button
                onClick={handleVerify}
                disabled={loading || verificationCode.length !== 6}
                className="flex-1"
              >
                Verify & Enable
              </Button>
              <Button
                onClick={() => setStep('setup')}
                variant="outline"
              >
                Back
              </Button>
            </div>
          </div>
        )}

        {step === 'complete' && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <CheckCircle className="h-16 w-16 text-green-500" />
            </div>

            <Alert>
              <AlertDescription>
                <strong>2FA has been enabled successfully!</strong>
                <p className="mt-2">Your account is now protected with two-factor authentication.</p>
              </AlertDescription>
            </Alert>

            {backupCodes.length > 0 && (
              <Alert>
                <AlertDescription>
                  <strong>Keep these backup codes safe!</strong>
                  <div className="mt-2 space-y-1">
                    {backupCodes.map((code, i) => (
                      <div key={i} className="font-mono text-xs">{code}</div>
                    ))}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            <Button
              onClick={handleClose}
              className="w-full"
            >
              Done
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

