import { useState, useEffect } from 'react';
import { useToast } from './use-toast';

export interface IdleTimeoutSetting {
  id: string;
  role: string;
  organization_id?: string;
  timeout_minutes: number;
  warning_minutes: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

// Default timeout settings for different roles
const DEFAULT_TIMEOUT_SETTINGS: IdleTimeoutSetting[] = [
  {
    id: 'default-doctor',
    role: 'doctor',
    timeout_minutes: 10,
    warning_minutes: 2,
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-salesperson',
    role: 'salesperson',
    timeout_minutes: 15,
    warning_minutes: 2,
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-leader',
    role: 'leader',
    timeout_minutes: 30,
    warning_minutes: 3,
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-system_admin',
    role: 'system_admin',
    timeout_minutes: 60,
    warning_minutes: 5,
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const useIdleTimeoutSettings = () => {
  const [settings, setSettings] = useState<IdleTimeoutSetting[]>(DEFAULT_TIMEOUT_SETTINGS);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // For now, we'll use default settings. In the future when idle_timeout_settings
  // table is properly synced, we can implement actual database operations
  const fetchSettings = async () => {
    setLoading(true);
    try {
      // Simulate loading time
      await new Promise(resolve => setTimeout(resolve, 500));
      setSettings(DEFAULT_TIMEOUT_SETTINGS);
    } catch (error) {
      console.error('Error fetching timeout settings:', error);
      toast({
        title: "Error",
        description: "Failed to load timeout settings.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const createSetting = async (setting: Omit<IdleTimeoutSetting, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      const newSetting: IdleTimeoutSetting = {
        ...setting,
        id: `custom-${Date.now()}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setSettings(prev => [...prev, newSetting]);
      toast({
        title: "Success",
        description: "Timeout setting created successfully.",
      });
      
      return newSetting;
    } catch (error) {
      console.error('Error creating timeout setting:', error);
      toast({
        title: "Error",
        description: "Failed to create timeout setting.",
        variant: "destructive",
      });
      throw error;
    }
  };

  const updateSetting = async (id: string, updates: Partial<IdleTimeoutSetting>) => {
    try {
      const updatedSetting = {
        ...updates,
        updated_at: new Date().toISOString(),
      };

      setSettings(prev => prev.map(s => 
        s.id === id ? { ...s, ...updatedSetting } : s
      ));
      
      toast({
        title: "Success",
        description: "Timeout setting updated successfully.",
      });
      
      return updatedSetting;
    } catch (error) {
      console.error('Error updating timeout setting:', error);
      toast({
        title: "Error",
        description: "Failed to update timeout setting.",
        variant: "destructive",
      });
      throw error;
    }
  };

  const deleteSetting = async (id: string) => {
    try {
      setSettings(prev => prev.filter(s => s.id !== id));
      toast({
        title: "Success",
        description: "Timeout setting deleted successfully.",
      });
    } catch (error) {
      console.error('Error deleting timeout setting:', error);
      toast({
        title: "Error",
        description: "Failed to delete timeout setting.",
        variant: "destructive",
      });
      throw error;
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return {
    settings,
    loading,
    createSetting,
    updateSetting,
    deleteSetting,
    refetch: fetchSettings,
  };
};