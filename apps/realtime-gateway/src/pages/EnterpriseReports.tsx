import { NavigationMenu } from "@/components/NavigationMenu";
import { EnterpriseReports as EnterpriseReportsComponent } from "@/components/EnterpriseReports";
import { useUserRoles } from "@/hooks/useUserRoles";
import { Card, CardContent } from "@/components/ui/card";

const EnterpriseReports = () => {
  const { isLeader, isCoach, isSystemAdmin, roles, loading } = useUserRoles();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <NavigationMenu />
        <main className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="p-6">
              <p>Loading...</p>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  // Check access after loading is complete - grant access to system admins immediately
  const hasAccess = !loading && (isLeader() || isCoach() || isSystemAdmin());

  if (!loading && !hasAccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <NavigationMenu />
        <main className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="p-6">
              <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
              <p className="text-muted-foreground">
                You need to be a coach, leader, or system administrator to access enterprise reports.
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Current roles: {roles.length > 0 ? roles.join(', ') : 'None'}
              </p>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <NavigationMenu />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Enterprise Reports</h1>
          <p className="text-muted-foreground">
            Comprehensive analytics and performance insights across your organization
          </p>
        </div>
        
        <EnterpriseReportsComponent />
      </main>
    </div>
  );
};

export default EnterpriseReports;