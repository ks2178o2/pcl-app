#!/usr/bin/env python3
"""
Show Database Contents
Displays current data in all tables
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps/app-api"))

from supabase import create_client
from dotenv import load_dotenv

# Load env
env_path = project_root / "apps" / "app-api" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing credentials")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def show_orgs():
    print_section("ORGANIZATIONS")
    result = supabase.table('organizations').select('*').execute()
    for org in result.data:
        print(f"  {org['name']} ({org['id']})")
        print(f"    Type: {org.get('business_type', 'N/A')}")
    print(f"\n  Total: {len(result.data)} organizations")

def show_regions():
    print_section("REGIONS")
    result = supabase.table('regions').select('id, name, organization_id').execute()
    for region in result.data:
        org_result = supabase.table('organizations').select('name').eq('id', region['organization_id']).single().execute()
        print(f"  {region['name']} ({region['id']})")
        print(f"    Organization: {org_result.data['name'] if org_result.data else 'N/A'}")
    print(f"\n  Total: {len(result.data)} regions")

def show_centers():
    print_section("CENTERS")
    result = supabase.table('centers').select('id, name, region_id').execute()
    for center in result.data:
        region_result = supabase.table('regions').select('name, organization_id').eq('id', center['region_id']).single().execute()
        region = region_result.data if region_result.data else {}
        org_result = supabase.table('organizations').select('name').eq('id', region.get('organization_id')).single().execute() if region.get('organization_id') else None
        print(f"  {center['name']} ({center['id']})")
        print(f"    Region: {region.get('name', 'N/A')}")
        print(f"    Organization: {org_result.data['name'] if org_result and org_result.data else 'N/A'}")
    print(f"\n  Total: {len(result.data)} centers")

def show_patients():
    print_section("PATIENTS")
    result = supabase.table('patients').select('id, full_name, email, phone, center_id, friendly_id').execute()
    for patient in result.data:
        print(f"  {patient['full_name']} ({patient['id']})")
        if patient.get('center_id'):
            center_result = supabase.table('centers').select('name, region_id').eq('id', patient['center_id']).single().execute()
            if center_result.data:
                center = center_result.data
                region_result = supabase.table('regions').select('name, organization_id').eq('id', center['region_id']).single().execute() if center.get('region_id') else None
                if region_result and region_result.data:
                    region = region_result.data
                    org_result = supabase.table('organizations').select('name').eq('id', region['organization_id']).single().execute() if region.get('organization_id') else None
                    print(f"    Center: {center['name']}")
                    print(f"    Region: {region['name']}")
                    print(f"    Organization: {org_result.data['name'] if org_result and org_result.data else 'N/A'}")
        else:
            print(f"    ⚠️  NO CENTER ASSIGNED")
        if patient.get('email'):
            print(f"    Email: {patient['email']}")
    print(f"\n  Total: {len(result.data)} patients")

def show_users():
    print_section("USER ASSIGNMENTS")
    result = supabase.table('user_assignments').select('id, user_id, center_id, role, is_active').execute()
    for assignment in result.data:
        profile_result = supabase.table('profiles').select('salesperson_name').eq('user_id', assignment['user_id']).single().execute()
        name = profile_result.data['salesperson_name'] if profile_result.data else 'Unknown'
        
        if assignment.get('center_id'):
            center_result = supabase.table('centers').select('name').eq('id', assignment['center_id']).single().execute()
            center_name = center_result.data['name'] if center_result.data else 'N/A'
        else:
            center_name = 'N/A'
            
        print(f"  {name}")
        print(f"    Center: {center_name}")
        print(f"    Role: {assignment['role']}")
        print(f"    Active: {assignment.get('is_active', 'N/A')}")
    print(f"\n  Total: {len(result.data)} assignments")

def show_summary():
    print_section("SUMMARY COUNTS")
    orgs = supabase.table('organizations').select('id', count='exact').execute()
    regions = supabase.table('regions').select('id', count='exact').execute()
    centers = supabase.table('centers').select('id', count='exact').execute()
    patients = supabase.table('patients').select('id', count='exact').execute()
    users = supabase.table('profiles').select('id', count='exact').execute()
    assignments = supabase.table('user_assignments').select('id', count='exact').execute()
    
    print(f"  Organizations:    {orgs.count}")
    print(f"  Regions:          {regions.count}")
    print(f"  Centers:          {centers.count}")
    print(f"  Patients:         {patients.count}")
    print(f"  Users:            {users.count}")
    print(f"  Assignments:      {assignments.count}")

def show_hierarchy():
    print_section("ORGANIZATION HIERARCHY")
    result = supabase.table('organization_hierarchy_v2').select('*').execute()
    for org in result.data:
        print(f"\n  {org['organization_name']}")
        print(f"    Regions:  {org['total_regions']}")
        print(f"    Centers:  {org['total_centers']}")
        print(f"    Patients: {org['total_patients']}")
        print(f"    Users:    {org['total_salespeople']}")

print("\n" + "="*80)
print("  DATABASE CONTENTS VIEWER")
print("="*80)

try:
    show_orgs()
    show_regions()
    show_centers()
    show_patients()
    show_users()
    show_summary()
    show_hierarchy()
    
    print("\n" + "="*80)
    print("  ✅ Done!")
    print("="*80 + "\n")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
