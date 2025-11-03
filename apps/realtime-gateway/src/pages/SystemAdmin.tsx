import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { OrganizationSetup } from '@/components/admin/OrganizationSetup';
import { UserManagement } from '@/components/admin/UserManagement';
import { AdminManagement } from '@/components/admin/AdminManagement';
import { IdleTimeoutManagement } from '@/components/admin/IdleTimeoutManagement';
import RAGFeatureManagement from '@/components/admin/RAGFeatureManagement';
import { EnhancedContextManagement } from '@/components/admin/EnhancedContextManagement';
import { EnhancedUploadManager } from '@/components/admin/EnhancedUploadManager';
import { RAGPermissionsManager } from '@/components/admin/RAGPermissionsManager';
import { useUserRoles } from '@/hooks/useUserRoles';
import { useSecureAdminAccess } from '@/hooks/useSecureAdminAccess';
import { useOrganizationData } from '@/hooks/useOrganizationData';
import { Navigate } from 'react-router-dom';
import { Shield, Building, Users, BarChart3, Settings2, Database, Lock } from 'lucide-react';
import SystemCheck from './SystemCheck';

export const SystemAdmin = () => {
  const { loading, roles } = useUserRoles();
  const { organizationId } = useOrganizationData();
  const { 
    shouldShowAdminNavigation,
    hasAnyAdminAccess,
    canManageSystem,
    canManageOrganization,
    canManageUsers,
    adminLevel,
    getAccessDeniedMessage
  } = useSecureAdminAccess();

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>;
  }

  const hasAccess = shouldShowAdminNavigation();

  console.log('SystemAdmin Security Check:', { 
    hasAccess, 
    adminLevel, 
    canManageSystem, 
    canManageOrganization 
  });

  if (!hasAccess) {
    return (
      <div className="container mx-auto py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="h-8 w-8 text-destructive" />
            <h1 className="text-3xl font-bold">Access Denied</h1>
          </div>
          <p className="text-muted-foreground">
            {getAccessDeniedMessage('organization')}
          </p>
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <p className="text-sm">Security Info:</p>
            <ul className="text-xs mt-2">
              <li>Roles: {roles.join(', ') || 'None'}</li>
              <li>Admin Level: {adminLevel}</li>
              <li>Has Admin Access: {hasAnyAdminAccess ? 'Yes' : 'No'}</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  console.log('SystemAdmin: Access granted, rendering admin panel');

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">
            {adminLevel === 'system' ? 'System Administration' : 'Organization Administration'}
          </h1>
        </div>
        <p className="text-muted-foreground">
          {adminLevel === 'system' 
            ? 'Manage organizations, users, and system-wide configurations' 
            : 'Manage users and configurations within your organization'
          }
        </p>
        {adminLevel !== 'system' && (
          <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              You have organization-level admin access. Some system-wide features may not be visible.
            </p>
          </div>
        )}
      </div>

      <Tabs defaultValue="organizations" className="space-y-6">
        <TabsList className={`grid w-full ${canManageSystem ? 'grid-cols-9' : 'grid-cols-6'}`}>
          {canManageSystem && (
            <TabsTrigger value="organizations" className="flex items-center gap-2">
              <Building className="h-4 w-4" />
              Organizations
            </TabsTrigger>
          )}
          <TabsTrigger value="management" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            Management
          </TabsTrigger>
          {canManageUsers && (
            <TabsTrigger value="users" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Users
            </TabsTrigger>
          )}
          <TabsTrigger value="rag-features" className="flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            RAG Features
          </TabsTrigger>
          <TabsTrigger value="rag-permissions" className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            RAG Permissions
          </TabsTrigger>
          <TabsTrigger value="knowledge-base" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Knowledge Base
          </TabsTrigger>
          <TabsTrigger value="timeout-settings" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Timeout Settings
          </TabsTrigger>
          {canManageSystem && (
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              System Analytics
            </TabsTrigger>
          )}
          {canManageSystem && (
            <TabsTrigger value="system-check" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              System Check
            </TabsTrigger>
          )}
        </TabsList>

        {canManageSystem && (
          <TabsContent value="organizations">
            <Card>
              <CardHeader>
                <CardTitle>Organization Setup</CardTitle>
                <CardDescription>
                  Set up new customer organizations with their hierarchical structure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <OrganizationSetup />
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="management">
          <AdminManagement />
        </TabsContent>

        {canManageUsers && (
          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>
                  {canManageSystem 
                    ? 'Create and manage users across all organizations'
                    : 'Create and manage users within your organization'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                <UserManagement />
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="timeout-settings">
          <IdleTimeoutManagement />
        </TabsContent>

        <TabsContent value="rag-features">
          <Card>
            <CardHeader>
              <CardTitle>RAG Feature Management</CardTitle>
              <CardDescription>
                Configure RAG features for your organization. Enable or disable features based on your needs.
              </CardDescription>
            </CardHeader>
              <CardContent>
              <RAGFeatureManagement organizationId={organizationId || ""} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rag-permissions">
          <RAGPermissionsManager />
        </TabsContent>

        <TabsContent value="knowledge-base">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Knowledge Base Management</CardTitle>
                <CardDescription>
                  Manage global context items, tenant access, and context sharing for organization: {organizationId}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EnhancedContextManagement />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upload Manager</CardTitle>
                <CardDescription>
                  Upload knowledge base content via files, web scraping, or bulk API operations.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EnhancedUploadManager />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {canManageSystem && (
          <TabsContent value="analytics">
            <Card>
              <CardHeader>
                <CardTitle>System Analytics</CardTitle>
                <CardDescription>
                  View system-wide metrics and usage statistics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Total Organizations
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">12</div>
                      <p className="text-xs text-muted-foreground">+2 from last month</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Active Users
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">1,247</div>
                      <p className="text-xs text-muted-foreground">+85 from last month</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Total Call Records
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">23,456</div>
                      <p className="text-xs text-muted-foreground">+1,234 this week</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {canManageSystem && (
          <TabsContent value="system-check">
            <SystemCheck />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};