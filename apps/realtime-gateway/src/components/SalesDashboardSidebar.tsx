import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { 
  LayoutDashboard, 
  Calendar, 
  Users, 
  Clock, 
  Settings, 
  HelpCircle,
  Plus,
  LogOut
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { cn } from '@/lib/utils';

export const SalesDashboardSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut } = useAuth();
  const { profile } = useProfile();

  const handleSignOut = async () => {
    console.log('🔓 Signing out...');
    const { error } = await signOut();
    if (error) {
      console.error('❌ Error signing out:', error);
    } else {
      console.log('✅ Signed out successfully');
      navigate('/auth');
    }
  };

  const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
    { icon: Calendar, label: "Today's Schedule", path: "/schedule" },
    { icon: Users, label: "Leads", path: "/leads" }, // Links to leads page
    { icon: Clock, label: "Activity Log", path: "/activity" },
  ];

  const bottomItems = [
    { icon: Settings, label: "Settings", path: "/settings" },
    { icon: HelpCircle, label: "Help", path: "/help" },
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
          <Plus className="h-5 w-5 text-white" />
        </div>
        <span className="ml-2 text-lg font-semibold text-gray-900">PitCrew Labs</span>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navItems.map((item) => (
          <SidebarNavItem 
            key={item.path}
            icon={<item.icon className="h-5 w-5" />} 
            label={item.label} 
            active={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          />
        ))}
      </nav>
      
      {/* Bottom Actions */}
      <div className="px-4 py-4 border-t border-gray-200 space-y-1">
        {bottomItems.map((item) => (
          <SidebarNavItem 
            key={item.path}
            icon={<item.icon className="h-5 w-5" />} 
            label={item.label} 
            onClick={() => navigate(item.path)}
          />
        ))}
      </div>
      
      {/* User Profile */}
      <div className="px-4 py-4 border-t border-gray-200 space-y-3">
        <div className="flex items-center space-x-3">
          <Avatar className="h-10 w-10">
            <AvatarFallback>
              {profile?.salesperson_name?.charAt(0) || user?.email?.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {profile?.salesperson_name || 'Sales Rep'}
            </p>
            <p className="text-xs text-gray-500 truncate">Sales Representative</p>
          </div>
          <div className="h-3 w-3 bg-green-500 rounded-full"></div>
        </div>
        <Button
          variant="outline"
          className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
          onClick={handleSignOut}
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
};

interface SidebarNavItemProps {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
}

const SidebarNavItem: React.FC<SidebarNavItemProps> = ({ icon, label, active = false, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
        active 
          ? "bg-accent text-primary" 
          : "text-gray-700 hover:bg-gray-100"
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
};

