# Database Schema Reference Guide

## 🏗️ Complete Table Relationships

### Main Hierarchy Tables

#### organizations
**Purpose:** Represents a customer company
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    business_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### regions
**Purpose:** Geographic divisions within an organization
```sql
CREATE TABLE regions (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE, -- ✅ ADDED
    network_id UUID REFERENCES networks(id), -- ⚠️ Future use
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### centers
**Purpose:** Individual locations within regions
```sql
CREATE TABLE centers (
    id UUID PRIMARY KEY,
    region_id UUID REFERENCES regions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### patients
**Purpose:** Individuals receiving services
```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE, -- For tenant isolation
    center_id UUID REFERENCES centers(id) ON DELETE SET NULL, -- ✅ ADDED - Primary assignment
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    friendly_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### User Management Tables

#### profiles
**Purpose:** User accounts linked to organizations
```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    organization_id UUID REFERENCES organizations(id), -- Tenant isolation
    salesperson_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### user_assignments
**Purpose:** Where salespeople can work (flexible assignments)
```sql
CREATE TABLE user_assignments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    network_id UUID REFERENCES networks(id), -- Optional: broadest assignment
    region_id UUID REFERENCES regions(id), -- Optional: all centers in region
    center_id UUID REFERENCES centers(id), -- Optional: specific center
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- ✅ CONSTRAINT: At least one must be set
    CHECK (network_id IS NOT NULL OR region_id IS NOT NULL OR center_id IS NOT NULL)
);
```

### Activity Tracking Tables

#### call_records
**Purpose:** Record of customer interactions
```sql
CREATE TABLE call_records (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id), -- Who made the call
    organization_id UUID REFERENCES organizations(id), -- Tenant isolation
    center_id UUID REFERENCES centers(id), -- Where call was made
    patient_id UUID REFERENCES patients(id), -- Who was called
    customer_name TEXT NOT NULL, -- Denormalized
    -- ... (all other call recording fields)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔄 Relationship Flow

```
┌─────────────────┐
│  Organizations  │ ← Customer Company
│   (Customers)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌──▼──────────┐
│Regions │ │  Profiles   │ ← Salespeople
└───┬────┘ │(Salespeople)│
    │      └──┬──────────┘
    │         │
┌───▼────┐    │      ┌─────────────────┐
│Centers │◄───┼──────┤ user_assignments│ ← Where they work
└───┬────┘    │      └─────────────────┘
    │         │
┌───▼────┐    │
│Patients│◄───┘
└────────┘
    │
┌───▼──────────┐
│ Call Records │ ← Activity tracking
└──────────────┘
```

## 📋 Key Relationships Summary

| From Table | To Table | Relationship | Type |
|------------|----------|--------------|------|
| regions | organizations | organization_id | Many-to-One ✅ NEW |
| centers | regions | region_id | Many-to-One |
| patients | centers | center_id | Many-to-One ✅ NEW |
| patients | organizations | organization_id | Many-to-One |
| profiles | organizations | organization_id | Many-to-One |
| user_assignments | centers | center_id | Many-to-One (optional) |
| user_assignments | regions | region_id | Many-to-One (optional) |
| user_assignments | networks | network_id | Many-to-One (optional) |
| call_records | organizations | organization_id | Many-to-One |
| call_records | centers | center_id | Many-to-One |
| call_records | patients | patient_id | Many-to-One |

## 🎯 Common Query Patterns

### Pattern 1: Get Organization Hierarchy
```sql
-- Get all centers for an organization
SELECT c.*, r.name as region_name, o.name as org_name
FROM centers c
JOIN regions r ON c.region_id = r.id
JOIN organizations o ON r.organization_id = o.id
WHERE o.id = $1;
```

### Pattern 2: Get Salesperson's Accessible Centers
```sql
-- All centers a salesperson can access
WITH accessible_centers AS (
    -- Direct center assignments
    SELECT DISTINCT c.* FROM centers c
    JOIN user_assignments ua ON ua.center_id = c.id
    WHERE ua.user_id = $1
    
    UNION
    
    -- Region assignments
    SELECT DISTINCT c.* FROM centers c
    JOIN regions r ON c.region_id = r.id
    JOIN user_assignments ua ON ua.region_id = r.id
    WHERE ua.user_id = $1
    
    UNION
    
    -- Network assignments
    SELECT DISTINCT c.* FROM centers c
    JOIN regions r ON c.region_id = r.id
    JOIN networks n ON r.network_id = n.id
    JOIN user_assignments ua ON ua.network_id = n.id
    WHERE ua.user_id = $1
)
SELECT * FROM accessible_centers;
```

### Pattern 3: Get Patients for a Center
```sql
-- Get all patients at a specific center
SELECT p.*, c.name as center_name, r.name as region_name, o.name as org_name
FROM patients p
JOIN centers c ON p.center_id = c.id
JOIN regions r ON c.region_id = r.id
JOIN organizations o ON r.organization_id = o.id
WHERE c.id = $1;
```

### Pattern 4: Get Salesperson's Patients
```sql
-- Get all patients a salesperson can access
SELECT DISTINCT p.*
FROM patients p
JOIN centers c ON p.center_id = c.id
JOIN (
    -- Get all centers the salesperson can access
    SELECT DISTINCT c.id FROM centers c
    JOIN user_assignments ua ON ua.center_id = c.id
    WHERE ua.user_id = $1
) accessible ON accessible.id = c.id;
```

## ⚙️ Indexes Added

```sql
-- Performance indexes for new relationships
CREATE INDEX idx_regions_organization_id ON regions(organization_id);
CREATE INDEX idx_patients_center_id ON patients(center_id);

-- Additional performance indexes
CREATE INDEX idx_call_records_organization_id ON call_records(organization_id);
CREATE INDEX idx_call_records_center_id ON call_records(center_id);
CREATE INDEX idx_call_records_patient_id ON call_records(patient_id);
CREATE INDEX idx_call_records_user_id ON call_records(user_id);
CREATE INDEX idx_profiles_organization_id ON profiles(organization_id);
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_centers_region_id ON centers(region_id);
```

## 📊 Views Created

### organization_hierarchy_v2
Shows complete org structure with counts
```sql
SELECT * FROM organization_hierarchy_v2;
-- Returns: org_id, org_name, business_type, total_regions, total_centers, total_patients, total_salespeople
```

### salesperson_assignments_view
Shows all salesperson center assignments with context
```sql
SELECT * FROM salesperson_assignments_view;
-- Returns: user_id, profile_id, salesperson_name, org, assignment details, center, region, org
```

### patient_distribution_view
Shows patient distribution across hierarchy
```sql
SELECT * FROM patient_distribution_view;
-- Returns: org, region, center, patient_count, active_salespeople
```

## 🔧 Helper Functions

### migrate_patients_to_centers()
Automatically assigns existing patients to centers based on call history
```sql
SELECT migrate_patients_to_centers();
-- Returns: {success: true, migrated_patients: N}
```

### migrate_regions_to_organizations()
Automatically assigns existing regions to organizations based on user activity
```sql
SELECT migrate_regions_to_organizations();
-- Returns: {success: true, migrated_regions: N}
```

## ✅ Migration Checklist

- [x] Add `organization_id` to regions table
- [x] Add `center_id` to patients table
- [x] Create foreign key constraints
- [x] Create indexes for performance
- [x] Create helpful views
- [x] Create migration helper functions
- [x] Add verification queries
- [x] Update documentation
- [ ] **Run migration on your database**
- [ ] **Run helper functions to migrate existing data**
- [ ] **Test queries**
- [ ] **Update application code to use new relationships**

## 🚀 Next Steps

1. Run `DATABASE_HIERARCHY_MIGRATION.sql` in your Supabase SQL editor
2. Review verification output for any warnings
3. Run `SELECT migrate_regions_to_organizations();` if needed
4. Run `SELECT migrate_patients_to_centers();` if needed
5. Test the views and queries
6. Update your application code to use the new relationships

