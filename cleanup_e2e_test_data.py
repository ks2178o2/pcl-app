#!/usr/bin/env python3
"""
Cleanup E2E Test Data
Removes all E2E test patients created during testing
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps/app-api"))

from supabase import create_client
from dotenv import load_dotenv

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

print("\n" + "="*80)
print("  CLEANUP E2E TEST DATA")
print("="*80)

# Find all E2E test patients
result = supabase.table('patients').select('id, full_name, email').eq('full_name', 'E2E Test Patient').execute()

if not result.data:
    print("\n✅ No E2E test patients found. Nothing to clean up.")
    sys.exit(0)

print(f"\nFound {len(result.data)} E2E test patients:")
for idx, patient in enumerate(result.data, 1):
    print(f"  {idx}. {patient['id']} ({patient['email']})")

# Ask for confirmation
response = input(f"\n⚠️  Delete all {len(result.data)} E2E test patients? (yes/no): ").strip().lower()

if response not in ['yes', 'y']:
    print("\n❌ Cleanup cancelled.")
    sys.exit(0)

# Delete all E2E test patients
print("\n🗑️  Deleting E2E test patients...")
deleted_count = 0
for patient in result.data:
    try:
        supabase.table('patients').delete().eq('id', patient['id']).execute()
        deleted_count += 1
        print(f"  ✅ Deleted: {patient['id']}")
    except Exception as e:
        print(f"  ❌ Failed to delete {patient['id']}: {e}")

print("\n" + "="*80)
print(f"✅ Cleanup complete! Deleted {deleted_count} E2E test patients.")
print("="*80 + "\n")

