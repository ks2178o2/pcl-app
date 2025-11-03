#!/usr/bin/env python3
"""
Seed Dashboard Data
Creates sample data for testing the v1.0.6 Sales Dashboard UI
"""

import os
from datetime import datetime, timedelta
from supabase import create_client, Client

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_sample_appointments():
    """Create sample appointments for the schedule page"""
    print("\n📅 Creating sample appointments...")
    
    # Get current user (you'll need to adjust this based on your auth setup)
    user_id = "cfc2f7f8-cf3a-4962-99bc-7168bf0622de"  # From console logs
    
    # Create appointments for the next few days
    appointments = [
        {
            "user_id": user_id,
            "customer_name": "Sarah Connor",
            "appointment_date": (datetime.now() + timedelta(hours=2)).isoformat(),
            "email": "sarah.connor@email.com",
            "phone_number": "(555) 987-6543",
            "created_at": datetime.now().isoformat(),
        },
        {
            "user_id": user_id,
            "customer_name": "Alex Murphy",
            "appointment_date": (datetime.now() + timedelta(hours=5)).isoformat(),
            "email": "alex.murphy@example.com",
            "phone_number": "(555) 123-4567",
            "created_at": datetime.now().isoformat(),
        },
        {
            "user_id": user_id,
            "customer_name": "Jennifer Martinez",
            "appointment_date": (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
            "email": "jennifer.m@email.com",
            "phone_number": "(555) 456-7890",
            "created_at": datetime.now().isoformat(),
        },
    ]
    
    for apt in appointments:
        try:
            result = supabase.table("appointments").insert(apt).execute()
            print(f"  ✅ Created appointment: {apt['customer_name']} at {apt['appointment_date']}")
        except Exception as e:
            print(f"  ⚠️  Error creating appointment: {e}")

def create_sample_call_records():
    """Create sample call records for activity feed"""
    print("\n📞 Creating sample call records...")
    
    user_id = "cfc2f7f8-cf3a-4962-99bc-7168bf0622de"
    
    calls = [
        {
            "user_id": user_id,
            "customer_name": "Sarah Connor",
            "duration_seconds": 450,  # 7.5 minutes
            "is_active": True,
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "user_id": user_id,
            "customer_name": "Alex Murphy",
            "duration_seconds": 300,  # 5 minutes
            "is_active": True,
            "created_at": (datetime.now() - timedelta(hours=3)).isoformat(),
        },
        {
            "user_id": user_id,
            "customer_name": "Michael Chen",
            "duration_seconds": 600,  # 10 minutes
            "is_active": True,
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        },
        {
            "user_id": user_id,
            "customer_name": "Emily Johnson",
            "duration_seconds": 120,  # 2 minutes
            "is_active": True,
            "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        },
    ]
    
    for call in calls:
        try:
            result = supabase.table("call_records").insert(call).execute()
            print(f"  ✅ Created call record: {call['customer_name']} ({call['duration_seconds']}s)")
        except Exception as e:
            print(f"  ⚠️  Error creating call record: {e}")

def create_sample_patients():
    """Create sample patients"""
    print("\n👥 Creating sample patients...")
    
    # Get organization_id from your profile
    # This assumes you have an organization set up
    
    patients = [
        {
            "full_name": "Sarah Connor",
            "email": "sarah.connor@email.com",
            "phone": "(555) 987-6543",
            "friendly_id": "P001",
        },
        {
            "full_name": "Alex Murphy",
            "email": "alex.murphy@example.com",
            "phone": "(555) 123-4567",
            "friendly_id": "P002",
        },
        {
            "full_name": "Michael Chen",
            "email": "michael.chen@email.com",
            "phone": "(555) 234-5678",
            "friendly_id": "P003",
        },
    ]
    
    for patient in patients:
        try:
            result = supabase.table("patients").insert(patient).execute()
            print(f"  ✅ Created patient: {patient['full_name']}")
        except Exception as e:
            print(f"  ⚠️  Error creating patient: {e}")

def create_sample_call_analyses():
    """Create sample call analyses for patient insights"""
    print("\n🧠 Creating sample call analyses...")
    
    # This would require getting call_record_ids from the calls we just created
    # For now, this is a placeholder
    
    analyses = [
        {
            "call_record_id": None,  # Will need to fetch actual ID
            "analysis_data": {
                "customerPersonality": {
                    "motivationCategory": "confidence-esteem",
                    "communicationStyle": {
                        "preferredTone": "supportive",
                        "informationDepth": "detailed",
                        "decisionSpeed": "deliberate"
                    },
                    "psychographics": {
                        "riskTolerance": "moderate",
                        "socialInfluence": "medium",
                        "qualityFocus": "value"
                    }
                },
                "objections": [
                    {
                        "type": "cost-value",
                        "text": "Patient expressed concerns about the price of the treatment."
                    }
                ]
            },
        }
    ]
    
    print("  ⚠️  Call analyses require call_record_ids from actual calls")
    print("  This should be populated after calls are created")

def main():
    """Main function to seed all data"""
    print("=" * 60)
    print("🌱 Seeding Dashboard Data for v1.0.6")
    print("=" * 60)
    
    try:
        create_sample_appointments()
        create_sample_call_records()
        create_sample_patients()
        create_sample_call_analyses()
        
        print("\n" + "=" * 60)
        print("🎉 Dashboard data seeding complete!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        raise

if __name__ == "__main__":
    main()

