import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Menu, Home, Calendar, Mic, Search, Settings, LogOut, BarChart3, Shield, Trophy, KeyRound } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useUserRoles } from '@/hooks/useUserRoles';

export const NavigationMenu = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signOut } = useAuth();
  const { isLeader, isCoach, isSystemAdmin } = useUserRoles();
  const [open, setOpen] = React.useState(false);

  const handleSignOut = async () => {
    await signOut();
    navigate('/auth');
  };

  const handleNavigation = (path: string) => {
    setOpen(false);
    try {
      const from = location.pathname;
      const leaving = (prefix: string) => from.startsWith(prefix) && !path.startsWith(prefix);
      const pruneKeys = (pred: (k: string) => boolean) => {
        const rm: string[] = [];
        for (let i = 0; i < sessionStorage.length; i++) {
          const k = sessionStorage.key(i) as string; if (!k) continue;
          if (pred(k)) rm.push(k);
        }
        rm.forEach(k => sessionStorage.removeItem(k));
      };
      // Analysis module keys
      if (leaving('/analysis')) {
        pruneKeys(k => k.startsWith('callData:') || k.startsWith('signedAudioUrl:') || k.startsWith('analysis:') || k.startsWith('player:') || k === 'analysisFilters' || k.startsWith('analysisTab:') || k.startsWith('followupPlan:') || k.startsWith('followupMsgs:') || k.startsWith('followupTab:'));
      }
      // Search module keys
      if (leaving('/search')) {
        pruneKeys(k => k === 'searchFilters' || k.startsWith('searchCalls:') || k === 'searchScrollTop');
      }
      // Appointments/Schedule keys (if used later)
      if (leaving('/appointments') || leaving('/schedule')) {
        pruneKeys(k => k.startsWith('appointments:') || k === 'appointmentsScroll');
      }
    } catch {}
    navigate(path);
  };

  const menuItems = [
    { label: 'Home', icon: Home, onClick: () => handleNavigation('/') },
    { label: 'Appointments', icon: Calendar, onClick: () => handleNavigation('/appointments') },
    { label: 'Voice Profile', icon: Mic, onClick: () => handleNavigation('/voice-profile') },
    { label: 'Call Analysis', icon: Search, onClick: () => handleNavigation('/search') },
    { label: 'Pt Pref.', icon: Settings, onClick: () => handleNavigation('/contact-preferences') },
    { label: 'Leaderboard', icon: Trophy, onClick: () => handleNavigation('/leaderboard') },
    { label: 'Security', icon: KeyRound, onClick: () => handleNavigation('/security-settings') },
  ];

  if (isLeader() || isCoach()) {
    menuItems.push({
      label: 'Enterprise Reports',
      icon: BarChart3,
      onClick: () => handleNavigation('/enterprise-reports')
    });
  }

  if (isSystemAdmin()) {
    menuItems.push({
      label: 'System Admin',
      icon: Shield,
      onClick: () => handleNavigation('/system-admin')
    });
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 w-9 p-0">
          <Menu className="h-4 w-4" />
          <span className="sr-only">Open navigation menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48 bg-background border">
        {menuItems.map((item, index) => (
          <DropdownMenuItem
            key={index}
            onClick={item.onClick}
            className="flex items-center gap-2 cursor-pointer hover:bg-muted"
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => {
            setOpen(false);
            handleSignOut();
          }}
          className="flex items-center gap-2 cursor-pointer hover:bg-muted text-destructive"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};