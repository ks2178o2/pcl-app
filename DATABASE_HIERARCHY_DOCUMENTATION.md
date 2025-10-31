# Complete Database Hierarchy Documentation

## ✅ Hierarchy Structure

```
Organizations (Customers)
  ├── Regions
  │     └── Centers
  │           └── Patients
  └── Profiles (Salespeople)
        └── User Assignments (Can span multiple centers)
```

## 📊 Complete Relationship Map

### 1. Organization → Region → Center → Patient Chain

**organizations** (Customer company)
- `id` (PK)
- `name`
- `business_type`
- `created_at`, `updated_at`

**regions** (Geographic divisions within organization)
- `id` (PK)
- `organization_id` (FK → organizations.id) **← ADDED**
- `network_id` (FK → networks.id) *[kept for future use]*
- `name`
- `created_at`, `updated_at`

**centers** (Individual locations within regions)
- `id` (PK)
- `region_id` (FK → regions.id)
- `name`
- `address`
- `created_at`, `updated_at`

**patients** (Individuals receiving services)
- `id` (PK)
- `organization_id` (FK → organizations.id) *[for tenant isolation]*
- `center_id` (FK → centers.id) **← ADDED**
- `full_name`
- `email`, `phone`
- `friendly_id`
- `created_at`, `updated_at`

### 2. Salesperson Assignment Chain

**profiles** (User accounts linked to organizations)
- `id` (PK)
- `user_id` (FK → auth.users.id)
- `organization_id` (FK → organizations.id)
- `salesperson_name`
- `created_at`, `updated_at`

**user_assignments** (Where salespeople can work)
- `id` (PK)
- `user_id` (FK → auth.users.id via profiles)
- `network_id` (FK → networks.id) *[optional]*
- `region_id` (FK → regions.id) *[optional]*
- `center_id` (FK → centers.id) *[optional]*
- **Constraint:** At least ONE of network_id, region_id, or center_id must be set
- `created_at`, `updated_at`

### 3. Activity Recording

**call_records** (Customer interactions)
- `id` (PK)
- `user_id` (FK → auth.users.id) *[who made the call]*
- `organization_id` (FK → organizations.id) *[tenant isolation]*
- `center_id` (FK → centers.id) *[where call was made]*
- `patient_id` (FK → patients.id) *[who was called]*
- `customer_name` *[denormalized for easier queries]*
- All call recording fields...

## 🔗 Relationship Summary

### Direct Links Created:
1. ✅ `regions.organization_id` → `organizations.id`
2. ✅ `patients.center_id` → `centers.id`
3. ✅ `centers.region_id` → `regions.id` (already existed)
4. ✅ `regions.network_id` → `networks.id` (kept for future)

### Existing Links Maintained:
5. ✅ `profiles.organization_id` → `organizations.id`
6. ✅ `patients.organization_id` → `organizations.id`
7. ✅ `user_assignments.center_id` → `centers.id`
8. ✅ `user_assignments.region_id` → `regions.id`
9. ✅ `user_assignments.network_id` → `networks.id`
10. ✅ `call_records.user_id` → `auth.users.id`
11. ✅ `call_records.organization_id` → `organizations.id`
12. ✅ `call_records.center_id` → `centers.id`
13. ✅ `call_records.patient_id` → `patients.id`

## 🎯 Query Examples

### Get all centers for an organization:
```sql
SELECT c.* 
FROM centers c
JOIN regions r ON c.region_id = r.id
WHERE r.organization_id = 'org-uuid-here';
```

### Get all patients for a specific center:
```sql
SELECT * 
FROM patients 
WHERE center_id = 'center-uuid-here';
```

### Get all centers a salesperson can access:
```sql
SELECT DISTINCT c.*
FROM centers c
JOIN user_assignments ua ON ua.center_id = c.id
WHERE ua.user_id = 'user-uuid-here'
UNION
SELECT DISTINCT c.*
FROM centers c
JOIN regions r ON c.region_id = r.id
JOIN user_assignments ua ON ua.region_id = r.id
WHERE ua.user_id = 'user-uuid-here'
UNION
SELECT DISTINCT c.*
FROM centers c
JOIN regions r ON c.region_id = r.id
JOIN networks n ON r.network_id = n.id
JOIN user_assignments ua ON ua.network_id = n.id
WHERE ua.user_id = 'user-uuid-here';
```

### Get organization hierarchy with counts:
```sql
SELECT * FROM organization_hierarchy_v2;
```

### Get all salesperson assignments:
```sql
SELECT * FROM salesperson_assignments_view;
```

### Get patient distribution:
```sql
SELECT * FROM patient_distribution_view;
```

## 🔍 Views Created

1. **organization_hierarchy_v2** - Complete org structure with counts
2. **salesperson_assignments_view** - All salesperson center assignments
3. **patient_distribution_view** - Patient distribution with metrics

## 🛠️ Helper Functions

1. **migrate_patients_to_centers()** - Auto-assign patients to centers based on call history
2. **migrate_regions_to_organizations()** - Auto-assign regions to orgs based on user activity

## ⚠️ Important Notes

- **Tenant Isolation**: `organization_id` is kept on multiple tables for RLS and query performance
- **Flexible Assignments**: Salespeople can be assigned at network, region, OR center level
- **Patients Belong to ONE Center**: This is the primary assignment
- **Call Records**: Record the full context (user, organization, center, patient) for audit trail

