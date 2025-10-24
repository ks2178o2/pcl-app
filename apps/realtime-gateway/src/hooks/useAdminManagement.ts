import { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface UpdateRegionData {
  id: string;
  name: string;
  organization_id: string;
}

interface UpdateCenterData {
  id: string;
  name: string;
  address?: string;
  region_id: string;
}

export const useAdminManagement = () => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const toggleOrganizationStatus = async (id: string, isActive: boolean) => {
    setLoading(true);
    try {
      const { error } = await supabase
        .from('organizations')
        .update({ is_active: isActive } as any)
        .eq('id', id);

      if (error) throw error;
      
      toast({
        title: "Success",
        description: `Organization ${isActive ? 'activated' : 'deactivated'} successfully`
      });
      
      return { error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { error };
    } finally {
      setLoading(false);
    }
  };

  const toggleRegionStatus = async (id: string, isActive: boolean) => {
    setLoading(true);
    try {
      const { error } = await supabase
        .from('regions')
        .update({ is_active: isActive } as any)
        .eq('id', id);

      if (error) throw error;
      
      toast({
        title: "Success",
        description: `Region ${isActive ? 'activated' : 'deactivated'} successfully`
      });
      
      return { error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { error };
    } finally {
      setLoading(false);
    }
  };

  const toggleCenterStatus = async (id: string, isActive: boolean) => {
    setLoading(true);
    try {
      const { error } = await supabase
        .from('centers')
        .update({ is_active: isActive } as any)
        .eq('id', id);

      if (error) throw error;
      
      toast({
        title: "Success",
        description: `Center ${isActive ? 'activated' : 'deactivated'} successfully`
      });
      
      return { error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { error };
    } finally {
      setLoading(false);
    }
  };

  const updateRegion = async (data: UpdateRegionData) => {
    setLoading(true);
    try {
      const { data: result, error } = await supabase
        .from('regions')
        .update({
          name: data.name,
          organization_id: data.organization_id
        })
        .eq('id', data.id)
        .select()
        .single();

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Region updated successfully"
      });
      
      return { data: result, error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { data: null, error };
    } finally {
      setLoading(false);
    }
  };

  const updateCenter = async (data: UpdateCenterData) => {
    setLoading(true);
    try {
      const { data: result, error } = await supabase
        .from('centers')
        .update({
          name: data.name,
          address: data.address,
          region_id: data.region_id
        })
        .eq('id', data.id)
        .select()
        .single();

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Center updated successfully"
      });
      
      return { data: result, error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { data: null, error };
    } finally {
      setLoading(false);
    }
  };

  const deleteRegion = async (id: string) => {
    setLoading(true);
    try {
      const { error } = await supabase
        .from('regions')
        .delete()
        .eq('id', id);

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Region deleted successfully"
      });
      
      return { error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { error };
    } finally {
      setLoading(false);
    }
  };

  const deleteCenter = async (id: string) => {
    setLoading(true);
    try {
      const { error } = await supabase
        .from('centers')
        .delete()
        .eq('id', id);

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Center deleted successfully"
      });
      
      return { error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { error };
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    updateRegion,
    updateCenter,
    deleteRegion,
    deleteCenter,
    toggleOrganizationStatus,
    toggleRegionStatus,
    toggleCenterStatus
  };
};