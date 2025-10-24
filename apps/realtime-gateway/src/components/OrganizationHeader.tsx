import React from 'react';
import { useProfile } from '@/hooks/useProfile';
import { useOrganizations } from '@/hooks/useOrganizations';
import { Building2 } from 'lucide-react';
import { CenterIndicator } from './CenterIndicator';

export const OrganizationHeader = () => {
  const { profile } = useProfile();
  const { organizations } = useOrganizations();

  const currentOrg = organizations.find(org => org.id === profile?.organization_id);

  if (!currentOrg) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-primary/10 to-secondary/10 border-b border-primary/20">
      <div className="container mx-auto px-6 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4" />
            <span className="font-medium text-foreground">{currentOrg.name}</span>
            <span className="text-xs">Sales System</span>
          </div>
          <CenterIndicator />
        </div>
      </div>
    </div>
  );
};