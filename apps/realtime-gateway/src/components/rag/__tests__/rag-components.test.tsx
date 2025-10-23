/**
 * Comprehensive Component Tests for RAG UI Components
 * Tests all RAG-related React components with React Testing Library
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Import components to test
import { RAGFeatureSelector } from '../components/rag/RAGFeatureSelector';
import { RAGFeatureToggleCard, CompactRAGFeatureToggleCard } from '../components/rag/RAGFeatureToggleCard';
import { RAGFeatureCategorySection, SimpleRAGFeatureCategorySection } from '../components/rag/RAGFeatureCategorySection';
import { RAGFeatureManagement } from '../components/admin/RAGFeatureManagement';
import { OrganizationHierarchy } from '../components/admin/OrganizationHierarchy';
import { SharingApprovals } from '../components/admin/SharingApprovals';
import { RAGFeatureErrorBoundary } from '../components/rag/RAGFeatureErrorBoundary';

// Import hooks and utilities
import { useRAGFeatures } from '../hooks/useRAGFeatures';
import { useRAGFeatureValidation } from '../lib/validation/rag-features';

// Import types
import { RAGFeatureWithToggle, RAGFeatureCategory, UserRole, OrganizationTreeNode } from '../types/rag-features';

// ==================== MOCK DATA ====================

const mockRAGFeatures: RAGFeatureWithToggle[] = [
  {
    id: '1',
    rag_feature: 'best_practice_kb',
    name: 'Best Practice Knowledge Base',
    description: 'Sales best practices and proven methodologies',
    category: 'sales',
    icon: 'book-open',
    color: 'blue',
    is_active: true,
    enabled: true,
    is_inherited: false,
    inherited_from: undefined,
    source_type: 'own',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    rag_feature: 'performance_analytics',
    name: 'Performance Analytics',
    description: 'Team performance insights and recommendations',
    category: 'manager',
    icon: 'bar-chart',
    color: 'purple',
    is_active: true,
    enabled: false,
    is_inherited: true,
    inherited_from: 'parent-org',
    source_type: 'inherited',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '3',
    rag_feature: 'regulatory_guidance',
    name: 'Regulatory Guidance',
    description: 'Compliance and regulatory information',
    category: 'admin',
    icon: 'shield',
    color: 'red',
    is_active: true,
    enabled: true,
    is_inherited: false,
    inherited_from: undefined,
    source_type: 'own',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

const mockOrganizationHierarchy: OrganizationTreeNode = {
  id: 'org-root',
  name: 'Root Organization',
  parent_organization_id: null,
  children: [
    {
      id: 'org-child-1',
      name: 'Child Organization 1',
      parent_organization_id: 'org-root',
      children: [],
      level: 1,
      path: ['org-root', 'org-child-1'],
      feature_count: 15,
      enabled_features: 12
    }
  ],
  level: 0,
  path: ['org-root'],
  feature_count: 20,
  enabled_features: 18
};

const mockSharingRequests = [
  {
    id: 'req-1',
    source_organization_id: 'org-parent',
    target_organization_id: 'org-child',
    rag_feature: 'best_practice_kb',
    item_id: 'item-1',
    sharing_type: 'hierarchy_down',
    status: 'pending',
    shared_by: 'admin@parent.com',
    shared_at: '2024-01-15T10:30:00Z',
    item_title: 'Q4 Sales Best Practices',
    item_content: 'Key strategies for closing deals in Q4...',
    source_org_name: 'Parent Organization'
  }
];

// ==================== MOCK HOOKS ====================

const mockUseRAGFeatures = vi.fn();
const mockUseRAGFeatureValidation = vi.fn();

vi.mock('../hooks/useRAGFeatures', () => ({
  useRAGFeatures: mockUseRAGFeatures
}));

vi.mock('../lib/validation/rag-features', () => ({
  useRAGFeatureValidation: mockUseRAGFeatureValidation
}));

// ==================== TEST UTILITIES ====================

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
});

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

const mockUser = {
  id: 'user-1',
  organization_id: 'org-root',
  name: 'Test User',
  email: 'test@example.com'
};

const mockUserRoles = ['org_admin'];

// ==================== RAG FEATURE SELECTOR TESTS ====================

describe('RAGFeatureSelector', () => {
  beforeEach(() => {
    mockUseRAGFeatures.mockReturnValue({
      enabledFeatures: mockRAGFeatures.filter(f => f.enabled),
      isLoading: false,
      error: null
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );
    
    expect(screen.getByText('RAG Feature')).toBeInTheDocument();
  });

  it('displays enabled features in dropdown', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );

    const trigger = screen.getByRole('combobox');
    await user.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      expect(screen.getByText('Regulatory Guidance')).toBeInTheDocument();
    });
  });

  it('filters features by category when specified', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
        filterByCategory="sales"
      />
    );

    const trigger = screen.getByRole('combobox');
    await user.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      expect(screen.queryByText('Regulatory Guidance')).not.toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    mockUseRAGFeatures.mockReturnValue({
      enabledFeatures: [],
      isLoading: true,
      error: null
    });

    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );

    expect(screen.getByText('Loading RAG features...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    mockUseRAGFeatures.mockReturnValue({
      enabledFeatures: [],
      isLoading: false,
      error: new Error('Failed to load features')
    });

    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );

    expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
  });

  it('calls onChange when feature is selected', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={onChange}
        organizationId="org-root"
      />
    );

    const trigger = screen.getByRole('combobox');
    await user.click(trigger);

    await waitFor(() => {
      const option = screen.getByText('Best Practice Knowledge Base');
      user.click(option);
    });

    expect(onChange).toHaveBeenCalledWith('best_practice_kb');
  });

  it('disables dropdown when disabled prop is true', () => {
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
        disabled={true}
      />
    );

    const trigger = screen.getByRole('combobox');
    expect(trigger).toBeDisabled();
  });

  it('shows search functionality', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );

    const trigger = screen.getByRole('combobox');
    await user.click(trigger);

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search features...');
      expect(searchInput).toBeInTheDocument();
      
      user.type(searchInput, 'best');
    });

    await waitFor(() => {
      expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      expect(screen.queryByText('Regulatory Guidance')).not.toBeInTheDocument();
    });
  });
});

// ==================== RAG FEATURE TOGGLE CARD TESTS ====================

describe('RAGFeatureToggleCard', () => {
  const mockOnToggle = vi.fn();

  beforeEach(() => {
    mockOnToggle.mockClear();
  });

  it('renders feature information correctly', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[0]}
        onToggle={mockOnToggle}
      />
    );

    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText('Sales best practices and proven methodologies')).toBeInTheDocument();
    expect(screen.getByText('Sales-Focused')).toBeInTheDocument();
  });

  it('shows toggle switch in correct state', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[0]}
        onToggle={mockOnToggle}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeChecked();
  });

  it('calls onToggle when switch is clicked', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[0]}
        onToggle={mockOnToggle}
      />
    );

    const toggle = screen.getByRole('switch');
    await user.click(toggle);

    expect(mockOnToggle).toHaveBeenCalledWith(false);
  });

  it('shows inherited badge for inherited features', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[1]}
        onToggle={mockOnToggle}
        showInheritedBadge={true}
      />
    );

    expect(screen.getByText('Inherited')).toBeInTheDocument();
  });

  it('disables toggle for inherited features', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[1]}
        onToggle={mockOnToggle}
        showInheritedBadge={true}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();
  });

  it('shows override button for inherited features', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[1]}
        onToggle={mockOnToggle}
        showInheritedBadge={true}
      />
    );

    expect(screen.getByText('Override')).toBeInTheDocument();
  });

  it('calls onToggle when override button is clicked', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[1]}
        onToggle={mockOnToggle}
        showInheritedBadge={true}
      />
    );

    const overrideButton = screen.getByText('Override');
    await user.click(overrideButton);

    expect(mockOnToggle).toHaveBeenCalledWith(false);
  });

  it('applies disabled state correctly', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[0]}
        onToggle={mockOnToggle}
        disabled={true}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();
  });

  it('shows category badge with correct color', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[0]}
        onToggle={mockOnToggle}
      />
    );

    const categoryBadge = screen.getByText('Sales-Focused');
    expect(categoryBadge).toBeInTheDocument();
  });
});

// ==================== RAG FEATURE CATEGORY SECTION TESTS ====================

describe('RAGFeatureCategorySection', () => {
  const mockOnToggle = vi.fn();
  const mockOnBulkToggle = vi.fn();

  beforeEach(() => {
    mockOnToggle.mockClear();
    mockOnBulkToggle.mockClear();
  });

  it('renders category header correctly', () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    
    renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
      />
    );

    expect(screen.getByText('Sales-Focused Features')).toBeInTheDocument();
  });

  it('renders all features in category', () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    
    renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
      />
    );

    expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
  });

  it('shows bulk toggle buttons', () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    
    renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
      />
    );

    expect(screen.getByText('Enable All')).toBeInTheDocument();
    expect(screen.getByText('Disable All')).toBeInTheDocument();
  });

  it('calls onBulkToggle when bulk buttons are clicked', async () => {
    const user = userEvent.setup();
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    
    renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
      />
    );

    const enableAllButton = screen.getByText('Enable All');
    await user.click(enableAllButton);

    expect(mockOnBulkToggle).toHaveBeenCalledWith(true);
  });

  it('shows feature count badge', () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    
    renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
      />
    );

    expect(screen.getByText('1')).toBeInTheDocument(); // 1 sales feature
  });

  it('does not render when no features provided', () => {
    const { container } = renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={[]}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('applies disabled state to all toggles', () => {
    const salesFeatures = mockRAGFeatures.filter(f => f.category === 'sales');
    
    renderWithQueryClient(
      <RAGFeatureCategorySection
        category="sales"
        features={salesFeatures}
        onToggle={mockOnToggle}
        onBulkToggle={mockOnBulkToggle}
        disabled={true}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();
  });
});

// ==================== RAG FEATURE MANAGEMENT TESTS ====================

describe('RAGFeatureManagement', () => {
  beforeEach(() => {
    mockUseRAGFeatures.mockReturnValue({
      organizationToggles: mockRAGFeatures,
      globalFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn()
    });
  });

  it('renders management panel correctly', () => {
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    expect(screen.getByText('RAG Feature Management')).toBeInTheDocument();
    expect(screen.getByText('Manage the Retrieval Augmented Generation')).toBeInTheDocument();
  });

  it('shows search functionality', () => {
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    expect(screen.getByPlaceholderText('Search RAG features...')).toBeInTheDocument();
  });

  it('shows category tabs', () => {
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Sales')).toBeInTheDocument();
    expect(screen.getByText('Legal')).toBeInTheDocument();
    expect(screen.getByText('Management')).toBeInTheDocument();
    expect(screen.getByText('Support')).toBeInTheDocument();
  });

  it('shows bulk action buttons', () => {
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    expect(screen.getByText('Bulk Enable All')).toBeInTheDocument();
    expect(screen.getByText('Bulk Disable All')).toBeInTheDocument();
  });

  it('filters features by search term', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    const searchInput = screen.getByPlaceholderText('Search RAG features...');
    await user.type(searchInput, 'best');

    await waitFor(() => {
      expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
      expect(screen.queryByText('Regulatory Guidance')).not.toBeInTheDocument();
    });
  });

  it('switches between category tabs', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    const salesTab = screen.getByText('Sales');
    await user.click(salesTab);

    await waitFor(() => {
      expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    mockUseRAGFeatures.mockReturnValue({
      organizationToggles: [],
      globalFeatures: [],
      isLoading: true,
      error: null,
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn()
    });

    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    expect(screen.getByText('Loading RAG feature settings...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    mockUseRAGFeatures.mockReturnValue({
      organizationToggles: [],
      globalFeatures: [],
      isLoading: false,
      error: new Error('Failed to load features'),
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn()
    });

    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    expect(screen.getByText(/Error loading RAG features/)).toBeInTheDocument();
  });
});

// ==================== ORGANIZATION HIERARCHY TESTS ====================

describe('OrganizationHierarchy', () => {
  const mockOnOrganizationSelect = vi.fn();
  const mockOnFeatureInheritanceView = vi.fn();

  beforeEach(() => {
    mockOnOrganizationSelect.mockClear();
    mockOnFeatureInheritanceView.mockClear();
  });

  it('renders hierarchy tree correctly', () => {
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={mockOnOrganizationSelect}
        onFeatureInheritanceView={mockOnFeatureInheritanceView}
      />
    );

    expect(screen.getByText('Organization Hierarchy')).toBeInTheDocument();
    expect(screen.getByText('Root Organization')).toBeInTheDocument();
  });

  it('shows expand/collapse functionality', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={mockOnOrganizationSelect}
        onFeatureInheritanceView={mockOnFeatureInheritanceView}
      />
    );

    const expandButton = screen.getByRole('button', { name: /expand/i });
    await user.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText('Child Organization 1')).toBeInTheDocument();
    });
  });

  it('calls onOrganizationSelect when organization is clicked', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={mockOnOrganizationSelect}
        onFeatureInheritanceView={mockOnFeatureInheritanceView}
      />
    );

    const viewButton = screen.getByText('View');
    await user.click(viewButton);

    expect(mockOnOrganizationSelect).toHaveBeenCalled();
  });

  it('calls onFeatureInheritanceView when features button is clicked', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={mockOnOrganizationSelect}
        onFeatureInheritanceView={mockOnFeatureInheritanceView}
      />
    );

    const featuresButton = screen.getByText('Features');
    await user.click(featuresButton);

    expect(mockOnFeatureInheritanceView).toHaveBeenCalled();
  });

  it('shows search functionality', () => {
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={mockOnOrganizationSelect}
        onFeatureInheritanceView={mockOnFeatureInheritanceView}
      />
    );

    expect(screen.getByPlaceholderText('Search organizations...')).toBeInTheDocument();
  });

  it('shows feature statistics', () => {
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={mockOnOrganizationSelect}
        onFeatureInheritanceView={mockOnFeatureInheritanceView}
      />
    );

    expect(screen.getByText('20 features')).toBeInTheDocument();
    expect(screen.getByText('18 enabled')).toBeInTheDocument();
  });
});

// ==================== SHARING APPROVALS TESTS ====================

describe('SharingApprovals', () => {
  it('renders sharing approvals interface', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    expect(screen.getByText('Sharing Approvals')).toBeInTheDocument();
    expect(screen.getByText('Manage context sharing requests')).toBeInTheDocument();
  });

  it('shows sharing statistics', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    expect(screen.getByText('1')).toBeInTheDocument(); // Pending count
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('displays pending requests', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    expect(screen.getByText('Q4 Sales Best Practices')).toBeInTheDocument();
    expect(screen.getByText('From: Parent Organization')).toBeInTheDocument();
  });

  it('shows approve and reject buttons', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    expect(screen.getByText('Approve')).toBeInTheDocument();
    expect(screen.getByText('Reject')).toBeInTheDocument();
  });

  it('shows preview functionality', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    const previewButton = screen.getByText('Preview');
    await user.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText('Content Preview')).toBeInTheDocument();
      expect(screen.getByText('Key strategies for closing deals in Q4...')).toBeInTheDocument();
    });
  });

  it('shows search and filter functionality', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    expect(screen.getByPlaceholderText('Search requests...')).toBeInTheDocument();
    expect(screen.getByText('All Status')).toBeInTheDocument();
  });

  it('shows bulk selection functionality', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    expect(screen.getByText('Select All (1)')).toBeInTheDocument();
  });
});

// ==================== RAG FEATURE ERROR BOUNDARY TESTS ====================

describe('RAGFeatureErrorBoundary', () => {
  const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
    if (shouldThrow) {
      throw new Error('Test error');
    }
    return <div>No error</div>;
  };

  it('renders children when no error occurs', () => {
    renderWithQueryClient(
      <RAGFeatureErrorBoundary>
        <ThrowError shouldThrow={false} />
      </RAGFeatureErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('renders error UI when error occurs', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithQueryClient(
      <RAGFeatureErrorBoundary>
        <ThrowError shouldThrow={true} />
      </RAGFeatureErrorBoundary>
    );

    expect(screen.getByText('RAG Feature Error')).toBeInTheDocument();
    expect(screen.getByText('Unknown Error')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('shows retry functionality', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();

    renderWithQueryClient(
      <RAGFeatureErrorBoundary>
        <ThrowError shouldThrow={true} />
      </RAGFeatureErrorBoundary>
    );

    const retryButton = screen.getByText('Try Again');
    await user.click(retryButton);

    // After retry, the error boundary should reset and show children again
    await waitFor(() => {
      expect(screen.getByText('No error')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('shows error details when showDetails is true', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithQueryClient(
      <RAGFeatureErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </RAGFeatureErrorBoundary>
    );

    expect(screen.getByText('Technical Details')).toBeInTheDocument();
    expect(screen.getByText('Copy Details')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('shows custom fallback when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithQueryClient(
      <RAGFeatureErrorBoundary fallback={<div>Custom error message</div>}>
        <ThrowError shouldThrow={true} />
      </RAGFeatureErrorBoundary>
    );

    expect(screen.getByText('Custom error message')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});

// ==================== INTEGRATION TESTS ====================

describe('RAG Feature Integration Tests', () => {
  it('integrates RAGFeatureSelector with RAGFeatureManagement', async () => {
    const user = userEvent.setup();
    
    mockUseRAGFeatures.mockReturnValue({
      organizationToggles: mockRAGFeatures,
      globalFeatures: mockRAGFeatures,
      isLoading: false,
      error: null,
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn()
    });

    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    // Search for a feature
    const searchInput = screen.getByPlaceholderText('Search RAG features...');
    await user.type(searchInput, 'best');

    await waitFor(() => {
      expect(screen.getByText('Best Practice Knowledge Base')).toBeInTheDocument();
    });

    // Click on the feature toggle
    const toggle = screen.getByRole('switch');
    await user.click(toggle);

    // Verify the toggle was called
    expect(mockUseRAGFeatures().updateToggle).toHaveBeenCalled();
  });

  it('integrates OrganizationHierarchy with SharingApprovals', async () => {
    const user = userEvent.setup();
    
    renderWithQueryClient(
      <div>
        <OrganizationHierarchy
          rootOrganizationId="org-root"
          onOrganizationSelect={() => {}}
          onFeatureInheritanceView={() => {}}
        />
        <SharingApprovals organizationId="org-child" />
      </div>
    );

    // Navigate to organization hierarchy
    expect(screen.getByText('Organization Hierarchy')).toBeInTheDocument();
    
    // Navigate to sharing approvals
    expect(screen.getByText('Sharing Approvals')).toBeInTheDocument();
    
    // Verify both components work together
    expect(screen.getByText('Root Organization')).toBeInTheDocument();
    expect(screen.getByText('Q4 Sales Best Practices')).toBeInTheDocument();
  });

  it('handles error propagation through error boundary', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const ErrorComponent = () => {
      throw new Error('Component error');
    };

    renderWithQueryClient(
      <RAGFeatureErrorBoundary>
        <RAGFeatureManagement organizationId="org-root">
          <ErrorComponent />
        </RAGFeatureManagement>
      </RAGFeatureErrorBoundary>
    );

    expect(screen.getByText('RAG Feature Error')).toBeInTheDocument();
    expect(screen.getByText('Component error')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});

// ==================== ACCESSIBILITY TESTS ====================

describe('RAG Feature Accessibility Tests', () => {
  it('RAGFeatureSelector has proper ARIA labels', () => {
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );

    const combobox = screen.getByRole('combobox');
    expect(combobox).toHaveAttribute('aria-label');
  });

  it('RAGFeatureToggleCard has proper ARIA labels', () => {
    renderWithQueryClient(
      <RAGFeatureToggleCard
        feature={mockRAGFeatures[0]}
        onToggle={() => {}}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-label');
  });

  it('OrganizationHierarchy has proper heading structure', () => {
    renderWithQueryClient(
      <OrganizationHierarchy
        rootOrganizationId="org-root"
        onOrganizationSelect={() => {}}
        onFeatureInheritanceView={() => {}}
      />
    );

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('Organization Hierarchy');
  });

  it('SharingApprovals has proper table structure', () => {
    renderWithQueryClient(
      <SharingApprovals organizationId="org-child" />
    );

    // Check for proper button roles
    expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
  });

  it('Error boundary has proper error announcement', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithQueryClient(
      <RAGFeatureErrorBoundary>
        <div>Test</div>
      </RAGFeatureErrorBoundary>
    );

    // Error boundary should be accessible
    expect(screen.getByText('Test')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});

// ==================== PERFORMANCE TESTS ====================

describe('RAG Feature Performance Tests', () => {
  it('RAGFeatureSelector renders efficiently with many features', () => {
    const manyFeatures = Array.from({ length: 100 }, (_, i) => ({
      ...mockRAGFeatures[0],
      id: `feature-${i}`,
      rag_feature: `feature_${i}`,
      name: `Feature ${i}`
    }));

    mockUseRAGFeatures.mockReturnValue({
      enabledFeatures: manyFeatures,
      isLoading: false,
      error: null
    });

    const startTime = performance.now();
    
    renderWithQueryClient(
      <RAGFeatureSelector
        value=""
        onChange={() => {}}
        organizationId="org-root"
      />
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (adjust threshold as needed)
    expect(renderTime).toBeLessThan(100); // 100ms
  });

  it('RAGFeatureManagement handles large feature sets efficiently', () => {
    const largeFeatureSet = Array.from({ length: 50 }, (_, i) => ({
      ...mockRAGFeatures[0],
      id: `feature-${i}`,
      rag_feature: `feature_${i}`,
      name: `Feature ${i}`,
      category: ['sales', 'manager', 'admin'][i % 3] as RAGFeatureCategory
    }));

    mockUseRAGFeatures.mockReturnValue({
      organizationToggles: largeFeatureSet,
      globalFeatures: largeFeatureSet,
      isLoading: false,
      error: null,
      updateToggle: vi.fn(),
      bulkUpdateToggles: vi.fn()
    });

    const startTime = performance.now();
    
    renderWithQueryClient(
      <RAGFeatureManagement organizationId="org-root" />
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time
    expect(renderTime).toBeLessThan(200); // 200ms
  });
});

// ==================== CLEANUP ====================

afterEach(() => {
  vi.clearAllMocks();
});
