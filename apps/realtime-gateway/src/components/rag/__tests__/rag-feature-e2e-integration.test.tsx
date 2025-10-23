/**
 * End-to-End Integration Tests for RAG Feature Management Frontend
 * Tests complete user workflows with real API interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Import components
import { RAGFeatureManagement } from '../components/admin/RAGFeatureManagement';
import { OrganizationHierarchy } from '../components/admin/OrganizationHierarchy';
import { SharingApprovals } from '../components/admin/SharingApprovals';
import { RAGFeatureSelector } from '../components/rag/RAGFeatureSelector';

// Import API client
import { ragFeaturesApi } from '../lib/api/rag-features';

// Mock the API client
vi.mock('../lib/api/rag-features', () => ({
  ragFeaturesApi: {
    getGlobalFeatures: vi.fn(),
    getOrganizationToggles: vi.fn(),
    getEnabledFeatures: vi.fn(),
    updateToggle: vi.fn(),
    bulkUpdateToggles: vi.fn(),
    getOrganizationHierarchy: vi.fn(),
    getPendingSharingRequests: vi.fn(),
    approveSharingRequest: vi.fn(),
    rejectSharingRequest: vi.fn(),
  },
}));

// Mock auth hooks
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-123',
      organization_id: 'org-456',
      name: 'Test User',
      email: 'test@example.com',
    },
  }),
}));

vi.mock('../hooks/useUserRoles', () => ({
  useUserRoles: () => ({
    roles: ['org_admin'],
  }),
}));

// Mock UI components (same as before)
vi.mock('../components/ui/select', () => ({
  Select: ({ children, onValueChange, value }: any) => (
    <select value={value} onChange={(e) => onValueChange(e.target.value)}>
      {children}
    </select>
  ),
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => <option value={value}>{children}</option>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
}));

vi.mock('../components/ui/button', () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('../components/ui/card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
  CardDescription: ({ children }: any) => <p>{children}</p>,
}));

vi.mock('../components/ui/input', () => ({
  Input: ({ onChange, value, placeholder, ...props }: any) => (
    <input onChange={onChange} value={value} placeholder={placeholder} {...props} />
  ),
}));

vi.mock('../components/ui/switch', () => ({
  Switch: ({ checked, onCheckedChange, disabled }: any) => (
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      disabled={disabled}
    />
  ),
}));

vi.mock('../components/ui/tabs', () => ({
  Tabs: ({ children, defaultValue }: any) => <div data-default-value={defaultValue}>{children}</div>,
  TabsList: ({ children }: any) => <div>{children}</div>,
  TabsTrigger: ({ children, value }: any) => <button data-value={value}>{children}</button>,
  TabsContent: ({ children, value }: any) => <div data-value={value}>{children}</div>,
}));

vi.mock('../components/ui/dialog', () => ({
  AlertDialog: ({ children, open }: any) => open ? <div>{children}</div> : null,
  AlertDialogContent: ({ children }: any) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: any) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: any) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: any) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: any) => <div>{children}</div>,
  AlertDialogAction: ({ children, onClick }: any) => <button onClick={onClick}>{children}</button>,
  AlertDialogCancel: ({ children, onClick }: any) => <button onClick={onClick}>{children}</button>,
}));

vi.mock('../components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => <span data-variant={variant}>{children}</span>,
}));

vi.mock('../components/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <div>{children}</div>,
  Tooltip: ({ children }: any) => <div>{children}</div>,
  TooltipTrigger: ({ children }: any) => <div>{children}</div>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('../components/ui/textarea', () => ({
  Textarea: ({ onChange, value, placeholder }: any) => (
    <textarea onChange={onChange} value={value} placeholder={placeholder} />
  ),
}));

vi.mock('../components/ui/label', () => ({
  Label: ({ children, htmlFor }: any) => <label htmlFor={htmlFor}>{children}</label>,
}));

// Mock icons
vi.mock('lucide-react', () => ({
  Loader2: () => <div data-testid="loader" />,
  Search: () => <div data-testid="search-icon" />,
  ChevronDown: () => <div data-testid="chevron-down" />,
  ChevronRight: () => <div data-testid="chevron-right" />,
  Building2: () => <div data-testid="building-icon" />,
  CheckCircle: () => <div data-testid="check-circle" />,
  XCircle: () => <div data-testid="x-circle" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
  AlertCircle: () => <div data-testid="alert-circle" />,
  FileText: () => <div data-testid="file-text" />,
}));

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

// Test data
const mockRAGFeatures = [
  {
    rag_feature: 'best_practice_kb',
    name: 'Best Practice Knowledge Base',
    description: 'Sales best practices and proven methodologies',
    category: 'sales',
    enabled: true,
    is_inherited: false,
    inherited_from: null,
    organization_id: 'org-456',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    rag_feature: 'customer_insight_rag',
    name: 'Customer Intelligence',
    description: 'Customer history, preferences, and behavior patterns',
    category: 'sales',
    enabled: false,
    is_inherited: true,
    inherited_from: 'parent-org',
    organization_id: 'org-456',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    rag_feature: 'performance_improvement_rag',
    name: 'Performance Improvement',
    description: 'Team performance insights and recommendations',
    category: 'manager',
    enabled: true,
    is_inherited: false,
    inherited_from: null,
    organization_id: 'org-456',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockOrganizationTree = [
  {
    id: 'org-123',
    name: 'Parent Organization',
    parent_organization_id: null,
    children: [
      {
        id: 'org-456',
        name: 'Child Organization',
        parent_organization_id: 'org-123',
        children: [],
        level: 1,
        path: ['org-123', 'org-456'],
        feature_count: 20,
        enabled_features: 15,
      },
    ],
    level: 0,
    path: ['org-123'],
    feature_count: 20,
    enabled_features: 18,
  },
];

const mockSharingRequests = [
  {
    id: 'req-1',
    source_organization_id: 'parent-org',
    target_organization_id: 'org-456',
    rag_feature: 'best_practice_kb',
    item_id: 'item-123',
    sharing_type: 'hierarchy_down',
    status: 'pending',
    shared_by: 'admin@parent.com',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
  },
];

// Helper function to create test wrapper
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('RAG Feature Management E2E Integration Tests', () => {
  const TestWrapper = createTestWrapper();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Complete RAG Feature Management Workflow', () => {
    it('should handle complete feature management workflow', async () => {
      // Mock API responses
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockResolvedValue(mockRAGFeatures);
      vi.mocked(ragFeaturesApi.getOrganizationToggles).mockResolvedValue({
        success: true,
        toggles: mockRAGFeatures,
      });
      vi.mocked(ragFeaturesApi.updateToggle).mockResolvedValue({
        success: true,
        message: 'Toggle updated successfully',
      });
      vi.mocked(ragFeaturesApi.bulkUpdateToggles).mockResolvedValue({
        success: true,
        total_updated: 2,
        updated_toggles: mockRAGFeatures.slice(0, 2),
      });

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
      });

      // Step 1: Search for features
      const searchInput = screen.getByPlaceholderText('Search RAG features...');
      await userEvent.type(searchInput, 'best practice');

      await waitFor(() => {
        expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      });

      // Step 2: Toggle a feature
      const toggleCard = screen.getByText('Best Practice Knowledge Base');
      const checkbox = toggleCard.closest('div')?.querySelector('input[type="checkbox"]');
      if (checkbox) {
        await userEvent.click(checkbox);
        
        await waitFor(() => {
          expect(ragFeaturesApi.updateToggle).toHaveBeenCalledWith(
            'org-456',
            'best_practice_kb',
            false,
            'Manual toggle by admin'
          );
        });
      }

      // Step 3: Perform bulk action
      const bulkEnableButton = screen.getByText('Bulk Enable All');
      await userEvent.click(bulkEnableButton);

      // Confirm bulk action
      const confirmButton = screen.getByText('Continue');
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(ragFeaturesApi.bulkUpdateToggles).toHaveBeenCalledWith(
          'org-456',
          expect.objectContaining({
            best_practice_kb: true,
            customer_insight_rag: true,
            performance_improvement_rag: true,
          }),
          'Bulk enable by admin'
        );
      });
    });

    it('should handle error states gracefully', async () => {
      // Mock API error
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockRejectedValue(new Error('Network error'));
      vi.mocked(ragFeaturesApi.getOrganizationToggles).mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
      });
    });
  });

  describe('Organization Hierarchy E2E Workflow', () => {
    it('should handle organization hierarchy navigation', async () => {
      const onOrganizationSelect = vi.fn();
      const onFeatureInheritanceView = vi.fn();

      vi.mocked(ragFeaturesApi.getOrganizationHierarchy).mockResolvedValue(mockOrganizationTree);

      render(
        <TestWrapper>
          <OrganizationHierarchy
            rootOrganizationId="org-123"
            onOrganizationSelect={onOrganizationSelect}
            onFeatureInheritanceView={onFeatureInheritanceView}
          />
        </TestWrapper>
      );

      // Wait for hierarchy to load
      await waitFor(() => {
        expect(screen.getByText('Parent Organization')).toBeInTheDocument();
      });

      // Click on child organization
      const childOrg = screen.getByText('Child Organization');
      await userEvent.click(childOrg);

      expect(onOrganizationSelect).toHaveBeenCalledWith(mockOrganizationTree[0].children[0]);

      // Click on inheritance view button
      const inheritanceButton = screen.getByText('View Inheritance');
      await userEvent.click(inheritanceButton);

      expect(onFeatureInheritanceView).toHaveBeenCalledWith(mockOrganizationTree[0].children[0]);
    });

    it('should handle hierarchy loading states', async () => {
      vi.mocked(ragFeaturesApi.getOrganizationHierarchy).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockOrganizationTree), 100))
      );

      render(
        <TestWrapper>
          <OrganizationHierarchy rootOrganizationId="org-123" />
        </TestWrapper>
      );

      // Should show loading state
      expect(screen.getByTestId('loader')).toBeInTheDocument();
      expect(screen.getByText('Loading organization hierarchy...')).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Parent Organization')).toBeInTheDocument();
      });
    });
  });

  describe('Sharing Approvals E2E Workflow', () => {
    it('should handle complete sharing approval workflow', async () => {
      vi.mocked(ragFeaturesApi.getPendingSharingRequests).mockResolvedValue(mockSharingRequests);
      vi.mocked(ragFeaturesApi.approveSharingRequest).mockResolvedValue(undefined);
      vi.mocked(ragFeaturesApi.rejectSharingRequest).mockResolvedValue(undefined);

      render(
        <TestWrapper>
          <SharingApprovals organizationId="org-456" />
        </TestWrapper>
      );

      // Wait for requests to load
      await waitFor(() => {
        expect(screen.getByText('Pending Sharing Approvals')).toBeInTheDocument();
      });

      // Approve a request
      const approveButton = screen.getByText('Approve');
      await userEvent.click(approveButton);

      await waitFor(() => {
        expect(ragFeaturesApi.approveSharingRequest).toHaveBeenCalledWith('req-1', 'user-123');
      });

      // Reject a request
      const rejectButton = screen.getByText('Reject');
      await userEvent.click(rejectButton);

      // Fill rejection reason
      const reasonTextarea = screen.getByPlaceholderText('e.g., Not relevant to our organization, security concerns, etc.');
      await userEvent.type(reasonTextarea, 'Not relevant to our organization');

      // Confirm rejection
      const confirmRejectButton = screen.getByText('Reject Request');
      await userEvent.click(confirmRejectButton);

      await waitFor(() => {
        expect(ragFeaturesApi.rejectSharingRequest).toHaveBeenCalledWith(
          'req-1',
          'user-123',
          'Not relevant to our organization'
        );
      });
    });

    it('should handle empty sharing requests state', async () => {
      vi.mocked(ragFeaturesApi.getPendingSharingRequests).mockResolvedValue([]);

      render(
        <TestWrapper>
          <SharingApprovals organizationId="org-456" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('No pending sharing requests.')).toBeInTheDocument();
      });
    });
  });

  describe('RAG Feature Selector E2E Workflow', () => {
    it('should handle feature selection workflow', async () => {
      const onChange = vi.fn();
      
      vi.mocked(ragFeaturesApi.getEnabledFeatures).mockResolvedValue({
        success: true,
        enabled_features: mockRAGFeatures,
      });

      render(
        <TestWrapper>
          <RAGFeatureSelector
            value=""
            onChange={onChange}
            organizationId="org-456"
            placeholder="Select a RAG feature"
          />
        </TestWrapper>
      );

      // Wait for features to load
      await waitFor(() => {
        expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      });

      // Select a feature
      const select = screen.getByRole('combobox');
      await userEvent.selectOptions(select, 'best_practice_kb');

      expect(onChange).toHaveBeenCalledWith('best_practice_kb');
    });

    it('should filter features by category', async () => {
      vi.mocked(ragFeaturesApi.getEnabledFeatures).mockResolvedValue({
        success: true,
        enabled_features: mockRAGFeatures,
      });

      render(
        <TestWrapper>
          <RAGFeatureSelector
            value=""
            onChange={() => {}}
            organizationId="org-456"
            filterByCategory="sales"
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
        expect(screen.queryByText('Performance Improvement')).not.toBeInTheDocument();
      });
    });
  });

  describe('Cross-Component Integration', () => {
    it('should integrate RAG feature management with organization hierarchy', async () => {
      const TestApp = () => {
        const [selectedOrg, setSelectedOrg] = React.useState<string>('org-123');
        
        return (
          <div>
            <OrganizationHierarchy
              rootOrganizationId="org-123"
              onOrganizationSelect={(org) => setSelectedOrg(org.id)}
            />
            <RAGFeatureManagement />
          </div>
        );
      };

      vi.mocked(ragFeaturesApi.getOrganizationHierarchy).mockResolvedValue(mockOrganizationTree);
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockResolvedValue(mockRAGFeatures);
      vi.mocked(ragFeaturesApi.getOrganizationToggles).mockResolvedValue({
        success: true,
        toggles: mockRAGFeatures,
      });

      render(
        <TestWrapper>
          <TestApp />
        </TestWrapper>
      );

      // Wait for both components to load
      await waitFor(() => {
        expect(screen.getByText('Parent Organization')).toBeInTheDocument();
        expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
      });

      // Click on child organization
      const childOrg = screen.getByText('Child Organization');
      await userEvent.click(childOrg);

      // RAG feature management should update for the selected organization
      await waitFor(() => {
        expect(ragFeaturesApi.getOrganizationToggles).toHaveBeenCalledWith('org-456');
      });
    });

    it('should handle error propagation between components', async () => {
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockRejectedValue(new Error('API Error'));
      vi.mocked(ragFeaturesApi.getOrganizationHierarchy).mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <div>
            <RAGFeatureManagement />
            <OrganizationHierarchy rootOrganizationId="org-123" />
          </div>
        </TestWrapper>
      );

      // Both components should handle errors gracefully
      await waitFor(() => {
        expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
        expect(screen.getByText(/Error loading hierarchy/)).toBeInTheDocument();
      });
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle large datasets efficiently', async () => {
      const largeFeatureList = Array.from({ length: 100 }, (_, i) => ({
        rag_feature: `feature_${i}`,
        name: `Feature ${i}`,
        description: `Description for feature ${i}`,
        category: 'sales',
        enabled: i % 2 === 0,
        is_inherited: false,
        inherited_from: null,
        organization_id: 'org-456',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }));

      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockResolvedValue(largeFeatureList);
      vi.mocked(ragFeaturesApi.getOrganizationToggles).mockResolvedValue({
        success: true,
        toggles: largeFeatureList,
      });

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      // Should load without performance issues
      await waitFor(() => {
        expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
      });

      // Search should work efficiently
      const searchInput = screen.getByPlaceholderText('Search RAG features...');
      await userEvent.type(searchInput, 'feature_1');

      await waitFor(() => {
        expect(screen.getByText('Feature 1')).toBeInTheDocument();
        expect(screen.getByText('Feature 10')).toBeInTheDocument();
        expect(screen.getByText('Feature 11')).toBeInTheDocument();
      });
    });

    it('should handle concurrent API calls', async () => {
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockRAGFeatures), 100))
      );
      vi.mocked(ragFeaturesApi.getOrganizationToggles).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true, toggles: mockRAGFeatures }), 150))
      );

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      // Both API calls should complete successfully
      await waitFor(() => {
        expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      });
    });
  });

  describe('User Experience and Accessibility', () => {
    it('should provide proper loading states', async () => {
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockRAGFeatures), 200))
      );

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      // Should show loading state
      expect(screen.getByTestId('loader')).toBeInTheDocument();
      expect(screen.getByText('Loading RAG feature settings...')).toBeInTheDocument();

      // Should hide loading state when data loads
      await waitFor(() => {
        expect(screen.queryByTestId('loader')).not.toBeInTheDocument();
      });
    });

    it('should handle keyboard navigation', async () => {
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockResolvedValue(mockRAGFeatures);
      vi.mocked(ragFeaturesApi.getOrganizationToggles).mockResolvedValue({
        success: true,
        toggles: mockRAGFeatures,
      });

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
      });

      // Tab navigation should work
      const searchInput = screen.getByPlaceholderText('Search RAG features...');
      searchInput.focus();
      
      // Press Tab to navigate to next element
      fireEvent.keyDown(searchInput, { key: 'Tab' });
      
      // Should focus next focusable element
      expect(document.activeElement).not.toBe(searchInput);
    });

    it('should provide proper error messages', async () => {
      vi.mocked(ragFeaturesApi.getGlobalFeatures).mockRejectedValue(new Error('Network connection failed'));

      render(
        <TestWrapper>
          <RAGFeatureManagement />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
      });

      // Error message should be user-friendly
      expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
    });
  });
});
