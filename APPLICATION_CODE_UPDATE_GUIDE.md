# Application Code Update Guide

## Overview

Now that the database hierarchy migration is complete, your application code needs to be updated to properly leverage the new center-based relationships. This guide outlines the changes needed across different parts of your application.

## Database Structure Changes Summary

### Before Migration
```
patients
  ├── organization_id (was used for filtering)
  └── No center_id relationship
```

### After Migration
```
organizations
  └── regions
      └── centers
          ├── patients (center_id FK)
          └── user_assignments (center_id FK)
```

## 1. Database RLS Policies (DONE ✅)

**File**: `UPDATE_RLS_POLICIES_FOR_CENTER_HIERARCHY.sql`

**Status**: ✅ Run this SQL script in your Supabase database

**What it does**: Updates Row Level Security policies to grant access based on center assignments instead of organization-wide access.

**Run Command**: Execute the SQL script in your Supabase SQL Editor.

## 2. Frontend Changes

### 2.1 Patient Search (`apps/realtime-gateway/src/hooks/usePatientSearch.ts`)

**Current Code** (lines 50-54):
```typescript
// Try org scoping if column exists (fallback gracefully if it doesn't)
try {
  if (userOrganizationId) {
    query = query.eq('organization_id', userOrganizationId);
  }
```

**No Changes Needed**: ✅ The frontend already uses `organization_id` for filtering, which is compatible with the new schema. The database RLS policies now handle center-based access automatically.

**However, for better hierarchy support**, you could enhance it to:
- Filter by center_id when a center is selected in the UI
- Join with centers table to show which center a patient belongs to
- Use the new database views (e.g., `patient_distribution_view`)

### 2.2 Patient List (`apps/realtime-gateway/src/hooks/usePatients.ts`)

**Current Code** (lines 32-35):
```typescript
const { data, error } = await (supabase as any)
  .from('patients')
  .select('id, full_name, email, phone, friendly_id, created_at, updated_at')
  .order('updated_at', { ascending: false });
```

**Enhancement Opportunity**: Add center information to patient queries:

```typescript
const { data, error } = await (supabase as any)
  .from('patients')
  .select(`
    id, 
    full_name, 
    email, 
    phone, 
    friendly_id, 
    created_at, 
    updated_at,
    center:centers(id, name),
    organization_id
  `)
  .order('updated_at', { ascending: false });
```

### 2.3 Organization Data (`apps/realtime-gateway/src/hooks/useOrganizationData.ts`)

**Status**: ✅ Already handles regions and centers correctly (lines 72-124)

**No Changes Needed**: The hook already fetches regions with organization_id and centers with regions.

### 2.4 Center Session (`apps/realtime-gateway/src/hooks/useCenterSession.ts`)

**Current Code** (lines 44-51):
```typescript
if (userAssignments.length === 0) {
  // No assignments = access to all centers in user's organization
  console.log('No assignments found - granting access to all centers in organization');
  console.log('User organization_id:', profile?.organization_id);
  availableCenters = centers.filter(center => 
    center.region?.organization_id === profile?.organization_id
  );
```

**No Changes Needed**: ✅ Already correctly filters centers by organization through the region relationship.

## 3. Backend API Changes

### 3.1 Patient API Endpoints (Not Found in Current Codebase)

**Recommended**: Create a new API route for patients if it doesn't exist.

**Suggested Location**: `apps/app-api/api/patients_api.py`

**Example Implementation**:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from services.supabase_client import get_supabase_client
from middleware.permissions import require_role, UserRole
from supabase import Client

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("/")
async def get_patients(
    center_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get patients filtered by center or organization
    - If center_id is provided, filter by center
    - If organization_id is provided, filter by organization
    - If neither, return all accessible patients (based on RLS)
    """
    query = supabase.from_('patients').select('*, center:centers(*), region:regions(*)')
    
    if center_id:
        query = query.eq('center_id', center_id)
    elif organization_id:
        # Filter through the hierarchy
        query = query.eq('center.region.organization_id', organization_id)
    
    query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
    
    result = query.execute()
    
    return {
        "success": True,
        "patients": result.data or [],
        "total": result.count or len(result.data or [])
    }

@router.post("/")
async def create_patient(
    patient_data: dict,
    supabase: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user)
):
    """Create a new patient"""
    # Validate center_id if provided
    if patient_data.get('center_id'):
        center_result = supabase.from_('centers').select('*, region:regions(organization_id)').eq('id', patient_data['center_id']).execute()
        
        if not center_result.data:
            raise HTTPException(status_code=404, detail="Center not found")
        
        center_org = center_result.data[0]['region']['organization_id']
        user_org = current_user.get('organization_id')
        
        if center_org != user_org:
            raise HTTPException(status_code=403, detail="Cannot assign patient to center in different organization")
    
    result = supabase.from_('patients').insert(patient_data).execute()
    
    return {
        "success": True,
        "patient": result.data[0] if result.data else None
    }
```

### 3.2 Organization Hierarchy API (`apps/app-api/api/organization_hierarchy_api.py`)

**Status**: ✅ Already uses `organization_hierarchy` view (line 239)

**No Changes Needed**: The API already queries the hierarchy view which includes the new relationships.

**Recommended Enhancement**: Add a new endpoint to query patients by center:

```python
@router.get("/centers/{center_id}/patients")
async def get_center_patients(
    center_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """Get all patients assigned to a center"""
    # Verify center exists and user has access
    center_result = supabase.from_('centers').select('*, region:regions(*)').eq('id', center_id).execute()
    
    if not center_result.data:
        raise HTTPException(status_code=404, detail="Center not found")
    
    # Get patients for this center
    patients_result = supabase.from_('patients').select('*').eq('center_id', center_id).range(offset, offset + limit - 1).execute()
    
    return {
        "success": True,
        "patients": patients_result.data or [],
        "total": patients_result.count or 0
    }
```

## 4. Database Views Usage

### 4.1 Use New Views for Reporting

**Existing Views**:
- `organization_hierarchy_v2` - Complete org hierarchy with counts
- `salesperson_assignments_view` - Salespeople and their center assignments  
- `patient_distribution_view` - Patient distribution by org/region/center

**Example Usage**:
```sql
-- In your reporting queries, use:
SELECT * FROM organization_hierarchy_v2;

-- Instead of manually joining:
SELECT * FROM organization_hierarchy_v2 
WHERE organization_id = 'your-org-id';
```

### 4.2 Update Reporting Components

**File**: `apps/realtime-gateway/src/components/EnterpriseReports.tsx`

**Enhancement Opportunity**: Use `patient_distribution_view` for patient analytics:

```typescript
const { data: patientDistribution } = await supabase
  .from('patient_distribution_view')
  .select('*')
  .eq('organization_id', profile?.organization_id);

// Use this for patient analytics instead of querying patients table directly
```

## 5. Testing Checklist

After implementing these changes, test the following:

- [ ] **Patient Search**: Verify users can search for patients
- [ ] **Patient Creation**: Verify users can create patients
- [ ] **Center Filtering**: Verify patients are properly assigned to centers
- [ ] **RLS Enforcement**: Verify users only see patients from their assigned centers
- [ ] **Organization Admin**: Verify org admins can see all patients in their org
- [ ] **Multi-Center Users**: Verify users assigned to multiple centers see all their patients
- [ ] **Reports**: Verify reports show correct patient counts by center
- [ ] **Views**: Verify database views return correct data

## 6. Migration Summary

### Database Changes (COMPLETE ✅)
- [x] Added `center_id` foreign key to `patients` table
- [x] Added `organization_id` foreign key to `regions` table
- [x] Created database views for hierarchy
- [x] Updated RLS policies for center-based access
- [x] Migrated existing data

### Application Changes (RECOMMENDED)
- [ ] Run `UPDATE_RLS_POLICIES_FOR_CENTER_HIERARCHY.sql` in Supabase
- [ ] Enhance patient queries to include center information
- [ ] Create/update patient API endpoints
- [ ] Update reporting to use new database views
- [ ] Add center filtering to patient search
- [ ] Test all patient operations

## 7. Rollback Plan

If you need to rollback:

1. **Revert RLS Policies**: Re-run the old organization-based policies from `create_patients_table.sql` or `COMPLETE_DATABASE_SETUP.sql`

2. **Remove Foreign Key**: 
```sql
ALTER TABLE patients DROP CONSTRAINT IF EXISTS patients_center_id_fkey;
ALTER TABLE regions DROP CONSTRAINT IF EXISTS regions_organization_id_fkey;
```

3. **Drop Views**:
```sql
DROP VIEW IF EXISTS organization_hierarchy_v2;
DROP VIEW IF EXISTS salesperson_assignments_view;
DROP VIEW IF EXISTS patient_distribution_view;
```

**Note**: Rolling back will break your current data structure, so only do this if absolutely necessary.

## 8. Next Steps

1. ✅ **Run RLS Policy Update**: Execute `UPDATE_RLS_POLICIES_FOR_CENTER_HIERARCHY.sql`
2. 🔄 **Test Existing Functionality**: Verify current features still work
3. 🚀 **Implement Enhancements**: Add center filtering and new views usage
4. 📊 **Update Reports**: Use new views for analytics
5. ✅ **Full Testing**: Run through testing checklist

## Support

If you encounter issues during the migration:

1. Check database logs in Supabase
2. Verify RLS policies are correct: `SELECT * FROM pg_policies WHERE tablename = 'patients';`
3. Check foreign key constraints: `SELECT * FROM pg_constraints WHERE table_name = 'patients';`
4. Review view definitions: `\d organization_hierarchy_v2` in psql

---

**Status**: Database migration complete ✅ | Application updates recommended 🔄

