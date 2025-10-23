/**
 * Comprehensive tests for RAG Feature Management Frontend Components
 * Tests all RAG-related components with proper mocking and user interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Import components
import { RAGFeatureSelector } from '../components/rag/RAGFeatureSelector';
import { RAGFeatureToggleCard } from '../components/rag/RAGFeatureToggleCard';
import { RAGFeatureCategorySection } from '../components/rag/RAGFeatureCategorySection';
import { RAGFeatureManagement } from '../components/admin/RAGFeatureManagement';
import { OrganizationHierarchy } from '../components/admin/OrganizationHierarchy';
import { SharingApprovals } from '../components/admin/SharingApprovals';
import { RAGFeatureErrorBoundary } from '../components/rag/RAGFeatureErrorBoundary';

// Import hooks
import { useRAGFeatures } from '../hooks/useRAGFeatures';

// Import types
import { EffectiveRAGFeature, OrganizationTreeNode, SharingRequest } from '../types/rag-features';

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

// Mock the auth hooks
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

// Mock UI components
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
const mockRAGFeatures: EffectiveRAGFeature[] = [
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

const mockOrganizationTree: OrganizationTreeNode[] = [
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

const mockSharingRequests: SharingRequest[] = [
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
  {
    id: 'req-2',
    source_organization_id: 'sibling-org',
    target_organization_id: 'org-456',
    rag_feature: 'customer_insight_rag',
    item_id: 'item-456',
    sharing_type: 'cross_org',
    status: 'approved',
    shared_by: 'manager@sibling.com',
    created_at: '2024-01-14T15:45:00Z',
    updated_at: '2024-01-14T16:00:00Z',
    approved_by: 'admin@current.com',
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

describe('RAGFeatureSelector', () => {
  const TestWrapper = createTestWrapper();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(
      <TestWrapper>
        <RAGFeatureSelector
          value=""
          onChange={() => {}}
          organizationId="org-456"
          placeholder="Select a RAG feature"
        />
      </TestWrapper>
    );

    expect(screen.getByText('Select a RAG feature')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    // Mock loading state
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: [],
      isLoading: true,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureSelector
          value=""
          onChange={() => {}}
          organizationId="org-456"
        />
      </TestWrapper>
    );

    expect(screen.getByTestId('loader')).toBeInTheDocument();
    expect(screen.getByText('Loading RAG features...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const error = new Error('Failed to load features');
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: [],
      isLoading: false,
      error,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureSelector
          value=""
          onChange={() => {}}
          organizationId="org-456"
        />
      </TestWrapper>
    );

    expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
  });

  it('displays available features', () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureSelector
          value=""
          onChange={() => {}}
          organizationId="org-456"
        />
      </TestWrapper>
    );

    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText('Customer Intelligence')).toBeInTheDocument();
  });

  it('filters features by category', () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
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

    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    expect(screen.queryByText('Performance Improvement')).not.toBeInTheDocument();
  });

  it('calls onChange when feature is selected', async () => {
    const onChange = vi.fn();
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureSelector
          value=""
          onChange={onChange}
          organizationId="org-456"
        />
      </TestWrapper>
    );

    const select = screen.getByRole('combobox');
    await userEvent.selectOptions(select, 'best_practice_kb');

    expect(onChange).toHaveBeenCalledWith('best_practice_kb');
  });
});

describe('RAGFeatureToggleCard', () => {
  it('renders feature toggle card', () => {
    const feature = mockRAGFeatures[0];
    const onToggle = vi.fn();

    render(
      <RAGFeatureToggleCard
        feature={feature}
        onToggle={onToggle}
      />
    );

    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText('Sales best practices and proven methodologies')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeChecked();
  });

  it('shows inherited feature indicator', () => {
    const feature = mockRAGFeatures[1]; // Inherited feature
    const onToggle = vi.fn();

    render(
      <RAGFeatureToggleCard
        feature={feature}
        onToggle={onToggle}
      />
    );

    expect(screen.getByText(/Inherited/)).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeDisabled();
  });

  it('calls onToggle when switch is clicked', async () => {
    const feature = mockRAGFeatures[0];
    const onToggle = vi.fn();

    render(
      <RAGFeatureToggleCard
        feature={feature}
        onToggle={onToggle}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    await userEvent.click(checkbox);

    expect(onToggle).toHaveBeenCalledWith('best_practice_kb', false);
  });

  it('disables toggle when disabled prop is true', () => {
    const feature = mockRAGFeatures[0];
    const onToggle = vi.fn();

    render(
      <RAGFeatureToggleCard
        feature={feature}
        onToggle={onToggle}
        disabled={true}
      />
    );

    expect(screen.getByRole('checkbox')).toBeDisabled();
  });
});

describe('RAGFeatureCategorySection', () => {
  it('renders category section with features', () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    const onToggle = vi.fn();

    render(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={onToggle}
      />
    );

    expect(screen.getByText('Sales Features')).toBeInTheDocument();
    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText('Customer Intelligence')).toBeInTheDocument();
  });

  it('renders empty state when no features', () => {
    const onToggle = vi.fn();

    render(
      <RAGFeatureCategorySection
        category="admin"
        features={[]}
        onToggle={onToggle}
      />
    );

    expect(screen.queryByText('Admin Features')).not.toBeInTheDocument();
  });

  it('handles bulk toggle actions', async () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    const onToggle = vi.fn();

    render(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={onToggle}
      />
    );

    // Look for bulk action buttons (these would be implemented in the actual component)
    const bulkButtons = screen.queryAllByText(/Enable All|Disable All/);
    expect(bulkButtons.length).toBeGreaterThan(0);
  });
});

describe('RAGFeatureManagement', () => {
  const TestWrapper = createTestWrapper();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders management panel', () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureManagement />
      </TestWrapper>
    );

    expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
    expect(screen.getByText('Sales')).toBeInTheDocument();
    expect(screen.getByText('Manager')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: [],
      isLoading: true,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureManagement />
      </TestWrapper>
    );

    expect(screen.getByTestId('loader')).toBeInTheDocument();
    expect(screen.getByText('Loading RAG feature settings...')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    render(
      <TestWrapper>
        <RAGFeatureManagement />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search RAG features...');
    await userEvent.type(searchInput, 'best practice');

    // After typing, the filtered results should be shown
    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    expect(screen.queryByText('Customer Intelligence')).not.toBeInTheDocument();
  });

  it('handles bulk actions', async () => {
    const bulkUpdateToggles = vi.fn();
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles,
    });

    render(
      <TestWrapper>
        <RAGFeatureManagement />
      </TestWrapper>
    );

    const bulkEnableButton = screen.getByText('Bulk Enable All');
    await userEvent.click(bulkEnableButton);

    // Should show confirmation dialog
    expect(screen.getByText('Confirm Bulk Action')).toBeInTheDocument();
  });
});

describe('OrganizationHierarchy', () => {
  const TestWrapper = createTestWrapper();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders organization hierarchy', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockOrganizationTree,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <OrganizationHierarchy rootOrganizationId="org-123" />
      </TestWrapper>
    );

    expect(screen.getByText('Parent Organization')).toBeInTheDocument();
    expect(screen.getByText('Child Organization')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <OrganizationHierarchy rootOrganizationId="org-123" />
      </TestWrapper>
    );

    expect(screen.getByTestId('loader')).toBeInTheDocument();
    expect(screen.getByText('Loading organization hierarchy...')).toBeInTheDocument();
  });

  it('handles organization selection', async () => {
    const onOrganizationSelect = vi.fn();
    vi.mocked(useQuery).mockReturnValue({
      data: mockOrganizationTree,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <OrganizationHierarchy
          rootOrganizationId="org-123"
          onOrganizationSelect={onOrganizationSelect}
        />
      </TestWrapper>
    );

    const childOrg = screen.getByText('Child Organization');
    await userEvent.click(childOrg);

    expect(onOrganizationSelect).toHaveBeenCalledWith(mockOrganizationTree[0].children[0]);
  });

  it('shows feature counts', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockOrganizationTree,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <OrganizationHierarchy rootOrganizationId="org-123" />
      </TestWrapper>
    );

    expect(screen.getByText('(15/20 RAG Features)')).toBeInTheDocument();
  });
});

describe('SharingApprovals', () => {
  const TestWrapper = createTestWrapper();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sharing approvals', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockSharingRequests,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <SharingApprovals organizationId="org-456" />
      </TestWrapper>
    );

    expect(screen.getByText('Pending Sharing Approvals')).toBeInTheDocument();
    expect(screen.getByText('best_practice_kb')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <SharingApprovals organizationId="org-456" />
      </TestWrapper>
    );

    expect(screen.getByTestId('loader')).toBeInTheDocument();
    expect(screen.getByText('Loading sharing requests...')).toBeInTheDocument();
  });

  it('handles approval action', async () => {
    const approveMutation = vi.fn();
    vi.mocked(useQuery).mockReturnValue({
      data: mockSharingRequests,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    vi.mocked(useMutation).mockReturnValue({
      mutate: approveMutation,
      isLoading: false,
      error: null,
    });

    render(
      <TestWrapper>
        <SharingApprovals organizationId="org-456" />
      </TestWrapper>
    );

    const approveButton = screen.getByText('Approve');
    await userEvent.click(approveButton);

    expect(approveMutation).toHaveBeenCalledWith('req-1');
  });

  it('handles rejection action', async () => {
    const rejectMutation = vi.fn();
    vi.mocked(useQuery).mockReturnValue({
      data: mockSharingRequests,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    vi.mocked(useMutation).mockReturnValue({
      mutate: rejectMutation,
      isLoading: false,
      error: null,
    });

    render(
      <TestWrapper>
        <SharingApprovals organizationId="org-456" />
      </TestWrapper>
    );

    const rejectButton = screen.getByText('Reject');
    await userEvent.click(rejectButton);

    // Should show rejection dialog
    expect(screen.getByText('Reject Sharing Request')).toBeInTheDocument();
  });

  it('shows empty state when no requests', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <SharingApprovals organizationId="org-456" />
      </TestWrapper>
    );

    expect(screen.getByText('No pending sharing requests.')).toBeInTheDocument();
  });
});

describe('RAGFeatureErrorBoundary', () => {
  const TestWrapper = createTestWrapper();

  it('renders children when no error', () => {
    render(
      <TestWrapper>
        <RAGFeatureErrorBoundary>
          <div>Test content</div>
        </RAGFeatureErrorBoundary>
      </TestWrapper>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders error fallback when error occurs', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <TestWrapper>
        <RAGFeatureErrorBoundary>
          <ThrowError />
        </RAGFeatureErrorBoundary>
      </TestWrapper>
    );

    expect(screen.getByText('Something went wrong with RAG features')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('handles reset functionality', async () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <TestWrapper>
        <RAGFeatureErrorBoundary>
          <ThrowError />
        </RAGFeatureErrorBoundary>
      </TestWrapper>
    );

    const resetButton = screen.getByText('Try Again');
    await userEvent.click(resetButton);

    // Error boundary should reset and show children again
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });
});

describe('useRAGFeatures Hook', () => {
  const TestWrapper = createTestWrapper();

  it('returns loading state initially', () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: [],
      isLoading: true,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    const TestComponent = () => {
      const { isLoading } = useRAGFeatures({ organizationId: 'org-456' });
      return <div>{isLoading ? 'Loading...' : 'Loaded'}</div>;
    };

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('returns features when loaded', () => {
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    const TestComponent = () => {
      const { enabledFeatures } = useRAGFeatures({ organizationId: 'org-456' });
      return <div>{enabledFeatures.length} features loaded</div>;
    };

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByText('3 features loaded')).toBeInTheDocument();
  });

  it('handles error state', () => {
    const error = new Error('Failed to load features');
    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: [],
      isLoading: false,
      error,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn(),
    });

    const TestComponent = () => {
      const { error } = useRAGFeatures({ organizationId: 'org-456' });
      return <div>{error ? 'Error occurred' : 'No error'}</div>;
    };

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });
});

describe('Integration Tests', () => {
  const TestWrapper = createTestWrapper();

  it('complete RAG feature management workflow', async () => {
    const updateToggle = vi.fn();
    const bulkUpdateToggles = vi.fn();

    vi.mocked(useRAGFeatures).mockReturnValue({
      enabledFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      globalFeatures: [],
      organizationToggles: [],
      updateToggle,
      bulkUpdateToggles,
    });

    render(
      <TestWrapper>
        <RAGFeatureManagement />
      </TestWrapper>
    );

    // 1. Search for a feature
    const searchInput = screen.getByPlaceholderText('Search RAG features...');
    await userEvent.type(searchInput, 'best practice');

    // 2. Toggle a feature
    const toggleCard = screen.getByText('Best Practice Knowledge Base');
    const checkbox = toggleCard.closest('div')?.querySelector('input[type="checkbox"]');
    if (checkbox) {
      await userEvent.click(checkbox);
      expect(updateToggle).toHaveBeenCalledWith({
        ragFeature: 'best_practice_kb',
        enabled: false,
        reason: 'Manual toggle by admin',
      });
    }

    // 3. Perform bulk action
    const bulkEnableButton = screen.getByText('Bulk Enable All');
    await userEvent.click(bulkEnableButton);

    // Confirm bulk action
    const confirmButton = screen.getByText('Continue');
    await userEvent.click(confirmButton);

    expect(bulkUpdateToggles).toHaveBeenCalled();
  });

  it('organization hierarchy with feature inheritance', async () => {
    const onOrganizationSelect = vi.fn();
    const onFeatureInheritanceView = vi.fn();

    vi.mocked(useQuery).mockReturnValue({
      data: mockOrganizationTree,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <TestWrapper>
        <OrganizationHierarchy
          rootOrganizationId="org-123"
          onOrganizationSelect={onOrganizationSelect}
          onFeatureInheritanceView={onFeatureInheritanceView}
        />
      </TestWrapper>
    );

    // Click on child organization
    const childOrg = screen.getByText('Child Organization');
    await userEvent.click(childOrg);

    expect(onOrganizationSelect).toHaveBeenCalledWith(mockOrganizationTree[0].children[0]);

    // Click on inheritance view button
    const inheritanceButton = screen.getByText('View Inheritance');
    await userEvent.click(inheritanceButton);

    expect(onFeatureInheritanceView).toHaveBeenCalledWith(mockOrganizationTree[0].children[0]);
  });

  it('sharing approvals workflow', async () => {
    const approveMutation = vi.fn();
    const rejectMutation = vi.fn();

    vi.mocked(useQuery).mockReturnValue({
      data: mockSharingRequests,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    vi.mocked(useMutation).mockReturnValue({
      mutate: approveMutation,
      isLoading: false,
      error: null,
    });

    render(
      <TestWrapper>
        <SharingApprovals organizationId="org-456" />
      </TestWrapper>
    );

    // Approve a request
    const approveButton = screen.getByText('Approve');
    await userEvent.click(approveButton);

    expect(approveMutation).toHaveBeenCalledWith('req-1');

    // Reject a request
    vi.mocked(useMutation).mockReturnValue({
      mutate: rejectMutation,
      isLoading: false,
      error: null,
    });

    const rejectButton = screen.getByText('Reject');
    await userEvent.click(rejectButton);

    // Fill rejection reason
    const reasonTextarea = screen.getByPlaceholderText('e.g., Not relevant to our organization, security concerns, etc.');
    await userEvent.type(reasonTextarea, 'Not relevant');

    // Confirm rejection
    const confirmRejectButton = screen.getByText('Reject Request');
    await userEvent.click(confirmRejectButton);

    expect(rejectMutation).toHaveBeenCalledWith({
      requestId: 'req-1',
      reason: 'Not relevant',
    });
  });
});
