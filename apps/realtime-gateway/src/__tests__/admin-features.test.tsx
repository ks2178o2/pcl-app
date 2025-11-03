/**
 * Comprehensive Test Suite for Enhanced Admin Features
 * 
 * This test file covers:
 * 1. RAG Feature Management
 * 2. RBAC Permissions Management
 * 3. Knowledge Base Management
 * 4. Enhanced System Health Checks
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import SystemAdmin from '@/pages/SystemAdmin';
import { useAuth } from '@/hooks/useAuth';
import { useOrganizationData } from '@/hooks/useOrganizationData';

// Mock hooks
vi.mock('@/hooks/useAuth');
vi.mock('@/hooks/useOrganizationData');
vi.mock('@/hooks/useUserRoles');

describe('Enhanced Admin Features - SystemAdmin Integration', () => {
  const mockUser = {
    id: 'user-123',
    email: 'admin@test.com',
    roles: ['system_admin']
  };

  const mockOrganizationId = 'org-123';

  beforeEach(() => {
    (useAuth as any).mockReturnValue({
      user: mockUser,
      session: { access_token: 'mock-token' }
    });
    (useOrganizationData as any).mockReturnValue({
      organizationId: mockOrganizationId
    });
  });

  describe('1. RAG Feature Management Tab', () => {
    it('should display RAG Feature Management tab', () => {
      render(<SystemAdmin />);
      expect(screen.getByText('RAG Features')).toBeInTheDocument();
    });

    it('should show feature toggles when tab is clicked', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Features');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/RAG Feature Management/i)).toBeInTheDocument();
      });
    });

    it('should allow toggling features on and off', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Features');
      fireEvent.click(tab);
      
      await waitFor(() => {
        const toggle = screen.getByLabelText(/sales intelligence/i);
        expect(toggle).toBeInTheDocument();
      });

      const toggle = screen.getByLabelText(/sales intelligence/i);
      fireEvent.click(toggle);
      
      await waitFor(() => {
        expect(toggle).toBeChecked();
      });
    });

    it('should filter features by category', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Features');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/sales/i)).toBeInTheDocument();
      });

      const categoryFilter = screen.getByRole('combobox', { name: /category/i });
      fireEvent.change(categoryFilter, { target: { value: 'sales' } });
      
      await waitFor(() => {
        expect(screen.getByText(/sales/i)).toBeInTheDocument();
      });
    });

    it('should support bulk operations', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Features');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Enable All/i)).toBeInTheDocument();
      });

      const bulkButton = screen.getByText(/Enable All/i);
      fireEvent.click(bulkButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Saving changes/i)).toBeInTheDocument();
      });
    });
  });

  describe('2. RBAC Permissions Management Tab', () => {
    it('should display RAG Permissions tab', () => {
      render(<SystemAdmin />);
      expect(screen.getByText('RAG Permissions')).toBeInTheDocument();
    });

    it('should show role selection when tab is clicked', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Select Role/i)).toBeInTheDocument();
      });
    });

    it('should display all available roles', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/System Admin/i)).toBeInTheDocument();
        expect(screen.getByText(/Org Admin/i)).toBeInTheDocument();
        expect(screen.getByText(/Salesperson/i)).toBeInTheDocument();
      });
    });

    it('should load default permissions for selected role', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        const roleSelect = screen.getByRole('combobox');
        fireEvent.click(roleSelect);
      });

      const salespersonOption = screen.getByText(/Salesperson/i);
      fireEvent.click(salespersonOption);
      
      await waitFor(() => {
        expect(screen.getByText(/sales_intelligence/i)).toBeInTheDocument();
      });
    });

    it('should allow customizing permissions per feature', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        const roleSelect = screen.getByRole('combobox');
        fireEvent.click(roleSelect);
      });

      const salespersonOption = screen.getByText(/Salesperson/i);
      fireEvent.click(salespersonOption);
      
      await waitFor(() => {
        const toggle = screen.getByLabelText(/sales_intelligence/i);
        expect(toggle).toBeInTheDocument();
      });

      const toggle = screen.getByLabelText(/sales_intelligence/i);
      fireEvent.click(toggle);
      
      await waitFor(() => {
        expect(screen.getByText(/Unsaved changes/i)).toBeInTheDocument();
      });
    });

    it('should save permission changes', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        const roleSelect = screen.getByRole('combobox');
        fireEvent.click(roleSelect);
      });

      const salespersonOption = screen.getByText(/Salesperson/i);
      fireEvent.click(salespersonOption);
      
      await waitFor(() => {
        const toggle = screen.getByLabelText(/sales_intelligence/i);
        fireEvent.click(toggle);
      });

      const saveButton = screen.getByText(/Save Changes/i);
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(screen.queryByText(/Unsaved changes/i)).not.toBeInTheDocument();
      });
    });

    it('should show permission summary for each role', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Role Permissions Summary/i)).toBeInTheDocument();
        expect(screen.getByText(/System Admin/i)).toBeInTheDocument();
        expect(screen.getByText(/Org Admin/i)).toBeInTheDocument();
      });
    });
  });

  describe('3. Knowledge Base Management Tab', () => {
    it('should display Knowledge Base tab', () => {
      render(<SystemAdmin />);
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
    });

    it('should show Knowledge Base Management component', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('Knowledge Base');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Knowledge Base Management/i)).toBeInTheDocument();
      });
    });

    it('should show Upload Manager component', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('Knowledge Base');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Upload Manager/i)).toBeInTheDocument();
      });
    });

    it('should display organization context', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('Knowledge Base');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(new RegExp(mockOrganizationId))).toBeInTheDocument();
      });
    });
  });

  describe('4. Enhanced System Health Checks', () => {
    it('should display System Check tab for system admins', () => {
      render(<SystemAdmin />);
      expect(screen.getByText('System Check')).toBeInTheDocument();
    });

    it('should run all health checks on load', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Supabase Connection/i)).toBeInTheDocument();
        expect(screen.getByText(/Authentication/i)).toBeInTheDocument();
        expect(screen.getByText(/Patients Table/i)).toBeInTheDocument();
      });
    });

    it('should check RAG-related tables', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/RAG Features Table/i)).toBeInTheDocument();
        expect(screen.getByText(/Organization RAG Toggles/i)).toBeInTheDocument();
        expect(screen.getByText(/Global Context Items/i)).toBeInTheDocument();
      });
    });

    it('should check AI service endpoints', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/AI Service: OpenAI API/i)).toBeInTheDocument();
        expect(screen.getByText(/AI Service: Deepgram API/i)).toBeInTheDocument();
        expect(screen.getByText(/AI Service: AssemblyAI API/i)).toBeInTheDocument();
      });
    });

    it('should show auto-refresh toggle', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Auto Refresh/i)).toBeInTheDocument();
      });
    });

    it('should enable/disable auto-refresh', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        const autoRefreshButton = screen.getByText(/Auto Refresh/i);
        expect(autoRefreshButton).toBeInTheDocument();
        fireEvent.click(autoRefreshButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/Auto Refresh/i).parentElement).toHaveClass('variant-outline');
      });
    });

    it('should display last checked timestamp', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Last checked:/i)).toBeInTheDocument();
      });
    });

    it('should allow manual refresh', async () => {
      render(<SystemAdmin />);
      const tab = screen.getByText('System Check');
      fireEvent.click(tab);
      
      await waitFor(() => {
        const runCheckButton = screen.getByText(/Run Check Now/i);
        expect(runCheckButton).toBeInTheDocument();
        fireEvent.click(runCheckButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/Last checked:/i)).toBeInTheDocument();
      });
    });
  });

  describe('5. SystemAdmin Tab Integration', () => {
    it('should display all tabs for system admin', () => {
      render(<SystemAdmin />);
      expect(screen.getByText('Organizations')).toBeInTheDocument();
      expect(screen.getByText('Management')).toBeInTheDocument();
      expect(screen.getByText('Users')).toBeInTheDocument();
      expect(screen.getByText('RAG Features')).toBeInTheDocument();
      expect(screen.getByText('RAG Permissions')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
      expect(screen.getByText('Timeout Settings')).toBeInTheDocument();
    });

    it('should show system-level tabs only for system admins', () => {
      render(<SystemAdmin />);
      expect(screen.getByText('System Analytics')).toBeInTheDocument();
      expect(screen.getByText('System Check')).toBeInTheDocument();
    });

    it('should not show system-level tabs for org admins', () => {
      (useAuth as any).mockReturnValue({
        user: { ...mockUser, roles: ['org_admin'] }
      });
      
      render(<SystemAdmin />);
      expect(screen.queryByText('Organizations')).not.toBeInTheDocument();
      expect(screen.queryByText('System Analytics')).not.toBeInTheDocument();
    });
  });

  describe('6. Error Handling', () => {
    it('should handle API errors gracefully in RAG Features', async () => {
      // Mock API error
      global.fetch = vi.fn().mockRejectedValue(new Error('API Error'));
      
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Features');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/Error/i)).toBeInTheDocument();
      });
    });

    it('should handle permission loading errors', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Permission Error'));
      
      render(<SystemAdmin />);
      const tab = screen.getByText('RAG Permissions');
      fireEvent.click(tab);
      
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe('7. Access Control', () => {
    it('should deny access to non-admin users', () => {
      (useAuth as any).mockReturnValue({
        user: { ...mockUser, roles: ['salesperson'] }
      });
      
      render(<SystemAdmin />);
      expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
    });

    it('should allow access for system admins', () => {
      render(<SystemAdmin />);
      expect(screen.getByText(/System Administration/i)).toBeInTheDocument();
    });

    it('should allow access for org admins', () => {
      (useAuth as any).mockReturnValue({
        user: { ...mockUser, roles: ['org_admin'] }
      });
      
      render(<SystemAdmin />);
      expect(screen.getByText(/Organization Administration/i)).toBeInTheDocument();
    });
  });
});

