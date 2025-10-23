# Enhanced RAG Context Management System

## Overview

The Enhanced RAG Context Management System provides comprehensive capabilities for managing RAG (Retrieval Augmented Generation) context across multiple tenants with advanced features including app-wide knowledge bases, cross-tenant sharing, enhanced upload mechanisms, and tenant isolation policies.

## Architecture

### Core Components

1. **Enhanced Context Manager** (`enhanced_context_manager.py`)
   - App-wide context management
   - Tenant access control
   - Cross-tenant knowledge sharing
   - Enhanced upload mechanisms

2. **Tenant Isolation Service** (`tenant_isolation_service.py`)
   - Tenant isolation policies
   - Quota management
   - RAG feature toggles
   - Security monitoring

3. **API Endpoints** (`enhanced_context_api.py`)
   - RESTful API for all enhanced features
   - Authentication and authorization
   - Audit logging integration

4. **Frontend Components**
   - Enhanced Context Management Dashboard
   - Upload Manager with multiple upload types
   - Tenant access control interface

## Features

### 1. App-Wide Context Management

**Global Knowledge Base**
- System-wide knowledge items accessible to all tenants
- Centralized management by system administrators
- Global item deduplication and validation

**Key Methods:**
```python
# Add global context item
await context_manager.add_global_context_item({
    "rag_feature": "best_practice_kb",
    "item_id": "global-knowledge-123",
    "item_type": "knowledge_chunk",
    "item_title": "Global Best Practice",
    "item_content": "This is global knowledge",
    "priority": 1,
    "confidence_score": 0.9,
    "tags": ["sales", "best-practice"]
})

# Get global context items
await context_manager.get_global_context_items(
    rag_feature="best_practice_kb",
    organization_id="org-123"
)
```

### 2. Tenant Access Management

**Access Control**
- Granular control over which tenants can access global RAG features
- Multiple access levels: read, write, admin
- Dynamic access granting and revocation

**Key Methods:**
```python
# Grant tenant access
await context_manager.grant_tenant_access(
    organization_id="org-123",
    rag_feature="best_practice_kb",
    access_level="read"
)

# Revoke tenant access
await context_manager.revoke_tenant_access(
    organization_id="org-123",
    rag_feature="best_practice_kb"
)
```

### 3. Cross-Tenant Knowledge Sharing

**Knowledge Sharing**
- Share context items between tenants
- Approval workflow for sharing requests
- Read-only and collaborative sharing modes

**Key Methods:**
```python
# Share context item
await context_manager.share_context_item(
    source_org_id="org-123",
    target_org_id="org-456",
    rag_feature="best_practice_kb",
    item_id="knowledge-123",
    sharing_type="read_only",
    shared_by="user-123"
)

# Approve sharing request
await context_manager.approve_sharing_request(
    sharing_id="sharing-123",
    approved_by="user-123"
)
```

### 4. Enhanced Upload Mechanisms

**File Upload**
- Support for multiple file types (PDF, DOCX, TXT, MD)
- Automatic content extraction and processing
- Batch processing with progress tracking

**Web Scraping**
- Scrape content from web pages
- Automatic knowledge extraction
- URL-based content ingestion

**Bulk API Upload**
- JSON-based bulk item uploads
- Batch processing with error handling
- Flexible item metadata support

**Key Methods:**
```python
# File upload
await context_manager.upload_file_content(
    file_content=file_content,
    file_type="pdf",
    organization_id="org-123",
    rag_feature="best_practice_kb",
    uploaded_by="user-123"
)

# Web scraping
await context_manager.scrape_web_content(
    url="https://example.com/article",
    organization_id="org-123",
    rag_feature="industry_insights",
    uploaded_by="user-123"
)

# Bulk API upload
await context_manager.bulk_api_upload(
    items=[...],  # Array of items
    organization_id="org-123",
    rag_feature="customer_insights",
    uploaded_by="user-123"
)
```

### 5. Quota Management

**Organization Quotas**
- Context items limit
- Global access features limit
- Sharing requests limit
- Real-time usage tracking

**Key Methods:**
```python
# Check quota limits
await tenant_isolation_service.check_quota_limits(
    organization_id="org-123",
    operation_type="context_items",
    quantity=10
)

# Update quota usage
await tenant_isolation_service.update_quota_usage(
    organization_id="org-123",
    operation_type="context_items",
    quantity=5,
    operation="increment"
)
```

### 6. Tenant Isolation Policies

**Security Policies**
- Data access isolation
- Cross-tenant access control
- Resource sharing policies
- API access restrictions

**Key Methods:**
```python
# Enforce tenant isolation
await tenant_isolation_service.enforce_tenant_isolation(
    user_id="user-123",
    organization_id="org-123",
    resource_type="context_item",
    resource_id="item-123"
)

# Create isolation policy
await tenant_isolation_service.create_isolation_policy({
    "organization_id": "org-123",
    "policy_type": "data_access",
    "policy_name": "Strict Data Isolation",
    "policy_rules": {...}
})
```

### 7. RAG Feature Toggles

**Feature Management**
- Organization-level RAG feature toggles
- Granular control over available features
- Bulk toggle management

**Key Methods:**
```python
# Get RAG feature toggles
await tenant_isolation_service.get_rag_feature_toggles("org-123")

# Update RAG feature toggle
await tenant_isolation_service.update_rag_feature_toggle(
    organization_id="org-123",
    rag_feature="best_practice_kb",
    enabled=False
)

# Bulk update toggles
await tenant_isolation_service.bulk_update_rag_toggles(
    organization_id="org-123",
    toggle_updates={
        "best_practice_kb": True,
        "customer_insight_rag": False
    }
)
```

## Database Schema

### Core Tables

1. **global_context_items** - App-wide knowledge items
2. **tenant_context_access** - Tenant access control
3. **context_sharing** - Cross-tenant sharing
4. **organization_context_quotas** - Quota management
5. **context_upload_logs** - Upload tracking
6. **tenant_isolation_policies** - Security policies
7. **cross_tenant_permissions** - Cross-tenant access
8. **organization_rag_toggles** - Feature toggles
9. **quota_usage_logs** - Quota usage tracking
10. **isolation_violation_logs** - Security monitoring

### Key Features

- **Row Level Security (RLS)** - Automatic tenant isolation
- **Audit Logging** - Complete action tracking
- **Quota Functions** - Database-level quota management
- **Indexing** - Optimized query performance

## API Endpoints

### Global Context
- `POST /api/enhanced-context/global/add` - Add global context item
- `GET /api/enhanced-context/global/items` - Get global context items

### Tenant Access
- `POST /api/enhanced-context/access/grant` - Grant tenant access
- `POST /api/enhanced-context/access/revoke` - Revoke tenant access

### Knowledge Sharing
- `POST /api/enhanced-context/sharing/share` - Share context item
- `POST /api/enhanced-context/sharing/approve/{sharing_id}` - Approve sharing
- `GET /api/enhanced-context/sharing/received` - Get shared items

### Enhanced Uploads
- `POST /api/enhanced-context/upload/file` - File upload
- `POST /api/enhanced-context/upload/web-scrape` - Web scraping
- `POST /api/enhanced-context/upload/bulk` - Bulk API upload

### Quota Management
- `GET /api/enhanced-context/quotas/{organization_id}` - Get quotas
- `PUT /api/enhanced-context/quotas/{organization_id}` - Update quotas

## Frontend Components

### Enhanced Context Management Dashboard
- Global context item management
- Tenant access control interface
- Knowledge sharing management
- Quota monitoring

### Enhanced Upload Manager
- File upload with progress tracking
- Web scraping interface
- Bulk API upload with JSON editor
- Upload results and history

## Security Features

### Tenant Isolation
- Automatic data isolation by organization
- Cross-tenant access controls
- Resource-level permissions

### Audit Logging
- Complete action tracking
- User activity monitoring
- Security violation logging

### Quota Enforcement
- Real-time quota checking
- Automatic limit enforcement
- Usage tracking and reporting

## Usage Examples

### 1. Setting Up Global Knowledge Base

```python
# System admin adds global knowledge
global_item = {
    "rag_feature": "best_practice_kb",
    "item_id": "sales-best-practice-001",
    "item_type": "knowledge_chunk",
    "item_title": "Effective Sales Techniques",
    "item_content": "Key techniques for successful sales...",
    "priority": 1,
    "confidence_score": 0.95,
    "tags": ["sales", "techniques", "best-practice"]
}

result = await context_manager.add_global_context_item(global_item)
```

### 2. Granting Tenant Access

```python
# Grant access to specific tenant
await context_manager.grant_tenant_access(
    organization_id="org-123",
    rag_feature="best_practice_kb",
    access_level="read"
)
```

### 3. Bulk Knowledge Upload

```python
# Upload multiple knowledge items
bulk_items = [
    {
        "item_id": "customer-insight-001",
        "item_type": "customer_insight",
        "item_title": "Customer Behavior Analysis",
        "item_content": "Analysis of customer behavior patterns...",
        "priority": 1,
        "confidence_score": 0.9
    },
    {
        "item_id": "customer-insight-002",
        "item_type": "customer_insight",
        "item_title": "Purchase Decision Factors",
        "item_content": "Key factors influencing purchase decisions...",
        "priority": 2,
        "confidence_score": 0.85
    }
]

result = await context_manager.bulk_api_upload(
    items=bulk_items,
    organization_id="org-123",
    rag_feature="customer_insights",
    uploaded_by="user-123"
)
```

### 4. Cross-Tenant Knowledge Sharing

```python
# Share knowledge between tenants
await context_manager.share_context_item(
    source_org_id="org-123",
    target_org_id="org-456",
    rag_feature="best_practice_kb",
    item_id="sales-best-practice-001",
    sharing_type="read_only",
    shared_by="user-123"
)

# Approve sharing request
await context_manager.approve_sharing_request(
    sharing_id="sharing-123",
    approved_by="user-456"
)
```

## Testing

### Test Coverage
- Unit tests for all services
- Integration tests for workflows
- End-to-end tests for complete scenarios
- Error handling and validation tests

### Test Files
- `test_enhanced_context_management.py` - Comprehensive test suite
- `test_real_database.py` - Real database integration tests

## Deployment

### Database Setup
1. Run `enhanced_rag_context_schema.sql` to create core tables
2. Run `tenant_isolation_schema.sql` to create additional tables
3. Configure RLS policies
4. Set up audit logging

### Service Configuration
1. Update environment variables
2. Configure Supabase connection
3. Set up authentication
4. Enable audit logging

### Frontend Integration
1. Add enhanced components to admin dashboard
2. Configure API endpoints
3. Set up user permissions
4. Test upload mechanisms

## Monitoring and Maintenance

### Quota Monitoring
- Real-time quota usage tracking
- Automated alerts for quota limits
- Usage analytics and reporting

### Security Monitoring
- Isolation violation logging
- Cross-tenant access monitoring
- Audit log analysis

### Performance Optimization
- Database indexing
- Query optimization
- Caching strategies

## Future Enhancements

### Planned Features
- Advanced file processing (OCR, NLP)
- Machine learning-based content categorization
- Automated knowledge extraction
- Advanced analytics and reporting
- API rate limiting and throttling
- Multi-language support

### Scalability Improvements
- Horizontal scaling support
- Caching layer implementation
- CDN integration for file uploads
- Microservices architecture migration

This enhanced RAG context management system provides a comprehensive solution for managing knowledge across multiple tenants with advanced security, scalability, and usability features.
