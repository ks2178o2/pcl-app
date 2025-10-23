# Real Database Testing Setup Guide

## 🎯 Testing Against Real Supabase Database

You're absolutely right! We should be testing against the real Supabase database instead of mocking it. Here's how to set it up:

### 📋 Prerequisites

1. **Supabase Project**: You have a Supabase project set up
2. **Database Tables**: The required tables exist in your Supabase database
3. **Environment Variables**: Your Supabase credentials are configured

### 🔧 Setup Steps

#### 1. Create Environment File
Create `/Users/krupasrinivas/pcl-product/apps/app-api/.env` with your real Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_ANON_KEY=your-anon-key-here

# OpenAI Configuration (for RAG features)
OPENAI_API_KEY=your-openai-api-key-here
```

#### 2. Required Database Tables
Ensure these tables exist in your Supabase database:

```sql
-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RAG context items table
CREATE TABLE IF NOT EXISTS rag_context_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id TEXT NOT NULL,
    rag_feature TEXT NOT NULL,
    item_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_title TEXT NOT NULL,
    item_content TEXT NOT NULL,
    item_metadata JSONB,
    status TEXT DEFAULT 'included',
    priority INTEGER DEFAULT 1,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    added_by TEXT,
    updated_by TEXT,
    update_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Profiles table (if not exists)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    salesperson_name TEXT,
    organization_id TEXT,
    role TEXT DEFAULT 'salesperson',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. Run Real Database Tests
```bash
cd /Users/krupasrinivas/pcl-product/apps/app-api
python -m pytest __tests__/test_real_database.py -v
```

### 🎯 Benefits of Real Database Testing

1. **Real Data Validation**: Tests actual database constraints and validations
2. **Real Performance**: Tests actual query performance and response times
3. **Real Error Handling**: Tests actual database error conditions
4. **Real Data Integrity**: Tests actual foreign key constraints and relationships
5. **Real Schema Validation**: Tests actual table structures and data types

### 🚨 Important Notes

1. **Test Data**: Use test-specific data (e.g., `test-user-123`, `test-org-123`)
2. **Cleanup**: Consider cleaning up test data after tests complete
3. **Isolation**: Use separate test organizations to avoid conflicts
4. **Rate Limits**: Be aware of Supabase rate limits during testing

### 🔄 Test Categories

1. **Unit Tests**: Test individual service methods with real database
2. **Integration Tests**: Test service interactions with real database
3. **End-to-End Tests**: Test complete workflows with real database
4. **Performance Tests**: Test actual query performance
5. **Error Handling Tests**: Test real database error conditions

### 📊 Expected Test Results

With real database testing, you'll get:
- ✅ Real validation errors
- ✅ Real database constraints
- ✅ Real performance metrics
- ✅ Real data persistence
- ✅ Real error handling

This is much more valuable than mock testing because it tests the actual production behavior!
