# RAG Feature Management - Architecture Decisions

## Decision Record - Multi-Tenant RAG Implementation

**Date**: 2025-10-23
**Status**: APPROVED

---

## 1. User Role Permissions

**Decision**: System Admin can manage all RAG features globally; Org Admin can manage RAG features for their organization; Salespeople can only view/use enabled features

### Role Definitions:
- **System Admin** (`system_admin`):
  - Manage global RAG feature catalog
  - Set system-wide defaults
  - View all organization settings
  - Override organization settings if needed

- **Organization Admin** (`org_admin`):
  - Enable/disable RAG features for their organization
  - Manage feature settings within their org
  - View usage statistics for their org
  - Cannot see or affect other organizations

- **Salesperson/User** (`user`, `salesperson`):
  - View only enabled RAG features
  - Use enabled features for uploads/context management
  - No management capabilities
  - No visibility into disabled features

### Permission Matrix:
| Action | System Admin | Org Admin | Salesperson |
|--------|--------------|-----------|-------------|
| View Global RAG Catalog | ✅ | ✅ (read-only) | ❌ |
| Enable/Disable RAG Features (Own Org) | ✅ | ✅ | ❌ |
| Enable/Disable RAG Features (Other Orgs) | ✅ | ❌ | ❌ |
| Use Enabled RAG Features | ✅ | ✅ | ✅ |
| View Feature Usage Stats (Own Org) | ✅ | ✅ | ❌ |
| View Feature Usage Stats (All Orgs) | ✅ | ❌ | ❌ |

---

## 2. RAG Feature Toggle Control Levels

**Decision**: Both global and organization level - system admins set global features, orgs can enable/disable from that set

### Implementation:
- **Global Level** (System Admin):
  - Define the master catalog of 20 RAG features
  - Set feature metadata (name, description, category)
  - Define which features are available to organizations
  - Cannot be modified by org admins

- **Organization Level** (Org Admin):
  - Enable/disable features from the global catalog
  - Only enabled features are visible to org users
  - Each organization maintains independent toggle state
  - Settings are isolated per organization (tenant)

### Data Flow:
```
Global RAG Catalog (System Admin)
    ↓ (20 features defined)
Organization RAG Toggles (Org Admin)
    ↓ (subset enabled per org)
User RAG Feature Selection (Salesperson)
    ↓ (only sees enabled features)
Context Items / Uploads
```

### Toggle State:
- If feature is disabled at org level → NOT available to org users
- If feature is enabled at org level → Available to org users
- Changes take effect immediately for all org users

---

## 3. Salesperson RAG Feature Usage

**Decision**: Select from only the RAG features enabled for their organization

### User Experience:
- Salespeople see **dropdown menus** with enabled features only
- No text input for feature names (prevents errors)
- Validation ensures only enabled features can be selected
- Clear visual indication when no features are enabled

### Implementation Details:
- API fetches enabled features for user's organization
- Frontend filters dropdown to show only `enabled: true` features
- Form validation blocks submission with disabled features
- Graceful error handling if feature is disabled mid-session

### Benefits:
- Prevents invalid feature assignments
- Reduces user errors
- Ensures compliance with org policies
- Clear user experience

---

## 4. RAG Feature Categories

**Decision**: By user role: Sales-specific, Manager-specific, Admin-specific

### Category Definitions:

#### **Sales-Focused Features**
*Available to: Salespeople, Managers, Admins*
- `customer_insight_rag` - Customer intelligence and history
- `success_pattern_rag` - Successful sales patterns
- `content_personalization_rag` - Personalized content generation
- `live_call_coaching_rag` - Real-time call assistance
- `unified_customer_view_rag` - 360° customer view
- `best_practice_kb` - Sales best practices

#### **Manager-Focused Features**
*Available to: Managers, Admins*
- `performance_improvement_rag` - Team performance insights
- `predictive_analytics_rag` - Sales forecasting
- `performance_benchmarking_rag` - Team benchmarking
- `trend_analysis_rag` - Market trend analysis
- `knowledge_sharing_rag` - Cross-team knowledge sharing
- `best_practice_transfer_rag` - Best practice distribution
- `resource_optimization_rag` - Resource allocation

#### **Admin-Focused Features**
*Available to: Admins only*
- `regulatory_guidance_rag` - Compliance and regulations
- `legal_knowledge_rag` - Legal documentation
- `scheduling_intelligence_rag` - Team scheduling
- `dynamic_content_rag` - Dynamic content management
- `multi_channel_optimization_rag` - Channel optimization
- `document_intelligence_integration` - Document processing
- `historical_context_rag` - Historical data analysis

### UI Organization:
- Features grouped by role in the toggle management UI
- Color-coded categories for easy identification
- Role badges on each feature
- Filter by category in dropdown menus

---

## 5. RAG Feature Access Model

**Decision**: Hierarchical - parent orgs can share features with child orgs

### Organizational Hierarchy:
```
System Level (Platform)
    ↓
Parent Organization (Reseller / Enterprise)
    ↓
Child Organizations (Departments / Teams)
    ↓
Users (Salespeople / Managers)
```

### Access Rules:

#### **Parent → Child Sharing**:
- Parent orgs can enable features for child orgs
- Child orgs inherit parent's enabled features
- Child orgs can restrict (disable) inherited features
- Child orgs cannot enable features not enabled by parent

#### **Data Isolation**:
- Each org's RAG context items are isolated
- No automatic cross-org data access
- Explicit sharing required for cross-org context

#### **Sharing Mechanisms**:
1. **Inheritance**: Child orgs automatically get parent's feature toggles
2. **Explicit Sharing**: Parent can share specific context items with children
3. **Approval Required**: Child must approve shared context items

### Example Scenarios:

**Scenario 1: Enterprise Rollout**
- Parent Org (Acme Corp) enables `customer_insight_rag`
- Child Org 1 (Sales Team A) inherits and uses it
- Child Org 2 (Sales Team B) disables it for their team
- Child Org 3 (Sales Team C) inherits and uses it

**Scenario 2: Best Practice Sharing**
- Parent Org creates best practice content
- Shares with Child Org 1 and Child Org 2
- Child Org 1 approves and adds to their RAG
- Child Org 2 reviews before approving

### Implementation:
- `parent_organization_id` field in organization table
- Recursive feature toggle inheritance
- Override mechanism at each level
- Audit trail for sharing activities

---

## 6. Multi-Tenant Isolation Guarantees

### Tenant Boundaries:
- **Organization ID** is the primary tenant identifier
- All RAG operations scoped to `organization_id`
- Database row-level security enforced
- No cross-tenant data leakage

### Isolation Points:
1. **RAG Feature Toggles**: Per-organization toggle state
2. **Context Items**: `organization_id` foreign key required
3. **Upload Logs**: Scoped to organization
4. **Sharing Requests**: Explicit source/target organizations
5. **Access Grants**: Organization-specific permissions

### Security:
- API validates user's `organization_id` on every request
- Middleware enforces tenant isolation
- No user can access other organization's data
- Audit logging for all cross-org operations

---

## 7. Implementation Priorities

### Phase 1: Foundation (Week 1-2)
- RAG feature toggle API endpoints
- Role-based permission checks
- Organization-level toggle management

### Phase 2: UI Components (Week 3-4)
- RAG feature toggle management panel (Org Admin)
- RAG feature selector dropdown (All Users)
- Category-based organization

### Phase 3: Hierarchy & Sharing (Week 5-6)
- Parent-child organization relationships
- Feature inheritance mechanism
- Context sharing with approval workflow

### Phase 4: Analytics & Optimization (Week 7-8)
- Usage tracking per feature
- Role-based analytics
- Performance optimization

---

## Summary

This architecture ensures:
- ✅ **Secure multi-tenancy** with complete data isolation
- ✅ **Role-based access control** appropriate to each user type
- ✅ **Hierarchical sharing** for enterprise scenarios
- ✅ **Flexible management** at both global and org levels
- ✅ **User-friendly experience** with dropdown menus and validation
- ✅ **Scalable design** supporting future enhancements

All decisions prioritize security, usability, and maintainability while supporting the platform's multi-tenant architecture.

