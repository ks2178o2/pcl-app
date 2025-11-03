# Database Schema Analysis & Clarification Questions

## Current Schema Overview

From the codebase, I can see the following tables exist:

### Main Hierarchy Tables:
1. **organizations** (id, name, business_type, created_at, updated_at)
2. **regions** (id, name, network_id, created_at, updated_at)
3. **centers** (id, name, region_id, address, created_at, updated_at)
4. **networks** (id, name, created_at, updated_at) - NOT CLEAR WHERE THIS FITS

### User/Patient Tables:
5. **profiles** (id, user_id, organization_id, salesperson_name, created_at, updated_at)
6. **patients** (id, organization_id, full_name, email, phone, friendly_id, created_at, updated_at)
7. **user_assignments** (id, user_id, network_id, region_id, center_id, created_at, updated_at)

### Other Tables:
8. **call_records** (id, user_id, organization_id, center_id, patient_id, customer_name, ...)
9. (Many other tables for RAG features, contexts, etc.)

## YOUR STATED HIERARCHY

"**Each customer is their own organization. Each organization can define their own regions and each region will have their own centers. Similarly, each patient is associated with a center through their salesperson. A salesperson in an organization may be associated with one or more centers across regions.**"

## CRITICAL CLARIFICATION QUESTIONS

### Question 1: Organizations
- You said "each customer is their own organization"
- But in the schema, I see organizations have a `network_id` connection through regions
- **CLARIFY**: Should "Organization" = "Customer"? Or is there a separate customer concept?

### Question 2: Networks Table
- The schema has a `networks` table that regions reference
- **CLARIFY**: What is a "network"? Is this like a franchise group? Or should we remove this?

### Question 3: Patient-Center Association
- You said patients are "associated with a center through their salesperson"
- Current schema: `patients` → `organization_id`
- Current schema: `call_records` → `center_id`, `patient_id`
- **CLARIFY**: Should patients have a direct `center_id`? Or only through salesperson assignments?

### Question 4: Salesperson-Center Association
- Current schema: `user_assignments` allows network_id, region_id, OR center_id
- **CLARIFY**: 
  - Can a salesperson be assigned to multiple centers?
  - Can a salesperson be assigned to a full region (all centers)?
  - Can a salesperson be assigned to a full network (all regions/centers)?

### Question 5: Missing Relationships Found

**MISSING RELATIONSHIPS I NOTICED:**

1. **regions → organizations**: No direct link! Regions currently link to "networks"
2. **centers → organizations**: No direct link! Centers only link to regions
3. **patients → center_id**: Missing direct link
4. **profiles (salespeople) → role field**: Missing! How do we know if someone is a salesperson vs admin?

## Current Relationships:
```
networks (id)
  └── regions (network_id)
        └── centers (region_id)
              └── user_assignments (center_id)

organizations (id)
  └── profiles (organization_id)
  └── patients (organization_id)
  └── call_records (organization_id)

profiles (user_id)
  └── user_assignments (user_id)
```

## Missing Relationships That Should Exist Based on Your Description:

```
organizations (id) ← CUSTOMER
  ├── regions (organization_id) ← MISSING!
  │     └── centers (region_id)
  │           └── patients (center_id) ← MISSING!
  └── profiles (organization_id) ← salespeople
        └── user_assignments (user_id, center_id)
```

## PROPOSED CORRECTIONS

Please answer the questions above, and I will provide a migration script to fix all the relationships.
