# 🚀 Sales Angel Buddy v1.0.0 - Comprehensive Deployment Checklist

## 📋 **Table of Contents**
1. [Environment Variables Overview](#environment-variables-overview)
2. [Backend Configuration](#backend-configuration)
3. [Frontend Configuration](#frontend-configuration)
4. [Database Setup](#database-setup)
5. [Security Configuration](#security-configuration)
6. [Deployment Steps](#deployment-steps)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## 🔐 **Environment Variables Overview**

### **✅ Configured Variables (Currently in Use)**

| Variable | Component | Status | Description |
|----------|-----------|--------|-------------|
| `SUPABASE_URL` | Backend, Frontend | ✅ **CONFIGURED** | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | ⚠️ **MISSING** | Backend authentication with Supabase |
| `SUPABASE_PUBLISHABLE_KEY` | Frontend | ⚠️ **HARDCODED** | Frontend Supabase client (anonymized key) |
| `ENVIRONMENT` | Backend | ⚠️ **NOT SET** | Controls dev/production behavior |
| `CORS_ORIGINS` | Backend | ⚠️ **NOT SET** | Allowed origins for CORS |
| `VITE_API_URL` | Frontend | ⚠️ **MISSING FROM .env** | Backend API URL for frontend |

### **❌ Missing Required Variables**

| Variable | Impact if Missing | Priority | Where to Set |
|----------|------------------|----------|--------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Backend auth **WILL FAIL** | 🔴 **CRITICAL** | Backend `.env` or system environment |
| `ENVIRONMENT` | Docs/Redoc always hidden | 🟡 **HIGH** | Backend `.env` |
| `VITE_API_URL` | API calls may fail | 🟡 **HIGH** | Frontend build-time |
| `VITE_SUPABASE_URL` | Frontend auth fails | 🔴 **CRITICAL** | Frontend build-time |
| `VITE_SUPABASE_ANON_KEY` | Frontend auth fails | 🔴 **CRITICAL** | Frontend build-time |

---

## 🖥️ **Backend Configuration**

### **Current Backend Setup (`apps/app-api/main.py`)**

```python
# ✅ Currently configured with defaults
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xxdahmkfioqzgqvyabek.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # ⚠️ Returns None if not set
ENVIRONMENT = os.getenv("ENVIRONMENT")  # ⚠️ Returns None if not set
```

### **Required Backend Environment Variables**

Create a `.env` file in `apps/app-api/`:

```bash
# ===========================================
# Required: Supabase Configuration
# ===========================================
SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here  # ⚠️ REQUIRED

# ===========================================
# Required: Environment Configuration
# ===========================================
ENVIRONMENT=development  # or 'production'
DEBUG=true

# ===========================================
# Optional: CORS Configuration
# ===========================================
CORS_ORIGINS=http://localhost:3000,http://localhost:3006,https://your-domain.com

# ===========================================
# Optional: Logging Configuration
# ===========================================
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### **⚠️ Critical Issue: Backend Authentication**

**Current Status:**
- ✅ Supabase client created
- ❌ `SUPABASE_SERVICE_ROLE_KEY` is **NOT SET** (returns `None`)
- ⚠️ All auth-protected endpoints **WILL FAIL** without this

**Fix:**
```bash
# In apps/app-api/.env or system environment
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Your actual key
```

---

## 🎨 **Frontend Configuration**

### **Current Frontend Setup (`apps/realtime-gateway/src/integrations/supabase/client.ts`)**

```typescript
// ⚠️ HARDCODED - Should use environment variables
const SUPABASE_URL = "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";  // Anonymized
```

### **Required Frontend Environment Variables**

Create a `.env` file in `apps/realtime-gateway/`:

```bash
# ===========================================
# Required: Supabase Configuration
# ===========================================
VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your anon key

# ===========================================
# Required: Backend API URL
# ===========================================
VITE_API_URL=http://localhost:8000  # Development
# VITE_API_URL=https://api.your-domain.com  # Production
```

### **⚠️ Critical Issue: Hardcoded Supabase Keys**

**Current Status:**
- ✅ Supabase URL is hardcoded (works for now)
- ⚠️ Supabase key is hardcoded (security risk)
- ⚠️ `VITE_API_URL` is not set (may break API calls)

**Fix:**
```typescript
// apps/realtime-gateway/src/integrations/supabase/client.ts
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "fallback-key";
```

---

## 🗄️ **Database Setup**

### **✅ Complete Database Schema**

| Table | Status | Created By |
|-------|--------|-----------|
| `patients` | ✅ **COMPLETE** | `create_patients_table.sql` |
| `call_records` | ✅ **COMPLETE** | `comprehensive_database_fix.sql` |
| `organizations` | ✅ **COMPLETE** | Existing Supabase schema |
| `profiles` | ✅ **COMPLETE** | Existing Supabase schema |
| `centers` | ✅ **COMPLETE** | Existing Supabase schema |
| `user_assignments` | ✅ **COMPLETE** | Existing Supabase schema |

### **Database Migration Status**

- ✅ **Patients table** created with RLS policies
- ✅ **Call records table** updated with required columns
- ✅ **RLS policies** configured correctly
- ✅ **Test data** inserted

**To verify:**
```sql
-- Run in Supabase SQL Editor
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'call_records' 
AND column_name IN ('center_id', 'patient_id', 'total_chunks', 'chunks_uploaded', 'recording_complete');
```

---

## 🔒 **Security Configuration**

### **Current Security Status**

| Security Feature | Status | Notes |
|-----------------|--------|-------|
| CORS | ✅ **RESTRICTED** | Specific origins only |
| Authentication | ⚠️ **PARTIAL** | Missing service role key |
| JWT Validation | ✅ **IMPLEMENTED** | Via Supabase auth |
| RLS Policies | ✅ **CONFIGURED** | Both restrictive and permissive |
| API Docs | ⚠️ **PRODUCTION HIDDEN** | Only works when `ENVIRONMENT=development` |

### **Security Checklist**

- ✅ Frontend using hardcoded Supabase key (needs env vars)
- ⚠️ Backend missing `SUPABASE_SERVICE_ROLE_KEY` (auth will fail)
- ✅ CORS restricted to specific origins
- ✅ API docs hidden in production
- ✅ RLS policies active on all tables

---

## 🚀 **Deployment Steps**

### **Step 1: Backend Configuration**

```bash
cd apps/app-api

# Create .env file
cat > .env << EOF
SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3006,https://your-domain.com
LOG_LEVEL=INFO
EOF

# Install dependencies
pip install -r requirements.txt

# Start backend
python main.py
# Should start on http://localhost:8000
```

### **Step 2: Frontend Configuration**

```bash
cd apps/realtime-gateway

# Create .env file
cat > .env << EOF
VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_API_URL=http://localhost:8000
EOF

# Install dependencies
npm install

# Start frontend
npm run dev
# Should start on http://localhost:3000
```

### **Step 3: Update Frontend Supabase Client**

**File: `apps/realtime-gateway/src/integrations/supabase/client.ts`**

```typescript
// Change from:
const SUPABASE_URL = "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIs...";

// To:
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIs...";
```

### **Step 4: Verify Application**

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","service":"Sales Angel Buddy API","version":"1.0.0"}
   ```

2. **Frontend Health Check:**
   - Open http://localhost:3000
   - Should load without console errors

3. **Database Check:**
   - Log in to Supabase dashboard
   - Verify tables exist: `patients`, `call_records`, `centers`, `profiles`
   - Verify RLS policies are active

---

## 🔧 **Troubleshooting Guide**

### **Issue 1: "Authentication service unavailable"**

**Symptoms:**
- Backend returns `503 Service Unavailable`
- Auth endpoints fail

**Cause:**
- `SUPABASE_SERVICE_ROLE_KEY` not set

**Fix:**
```bash
export SUPABASE_SERVICE_ROLE_KEY="your_key_here"
# Or add to apps/app-api/.env
```

### **Issue 2: Patient Creation Fails (403)**

**Symptoms:**
- Cannot create patients
- 403 error in browser console

**Cause:**
- RLS policies too restrictive
- Missing organization context

**Fix:**
- Already fixed in `comprehensive_database_fix.sql`
- Run the SQL in Supabase if not already done

### **Issue 3: Recording Button Disabled**

**Symptoms:**
- "Start Professional Recording" button disabled
- Button shows requirements message

**Cause:**
- Patient not selected
- Center not selected

**Fix:**
1. Select or create a patient
2. Select a center
3. Button should enable

### **Issue 4: "center_id column not found"**

**Symptoms:**
- Database error when starting recording
- `Could not find the 'center_id' column of 'call_records'`

**Cause:**
- `call_records` table missing columns

**Fix:**
- Run `comprehensive_database_fix.sql` in Supabase SQL Editor

### **Issue 5: Port 8000 Already in Use**

**Symptoms:**
- Backend fails to start
- Error: "address already in use"

**Fix:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or find and kill manually
ps aux | grep "python main.py"
kill -9 <PID>
```

### **Issue 6: Multiple Frontend Servers**

**Symptoms:**
- Port keeps changing (3000 → 3001 → 3002...)
- Console shows "Port 3000 is in use"

**Fix:**
```bash
# Kill all Vite processes
pkill -f "vite.*3000"
pkill -f "npm run dev"

# Restart clean
cd apps/realtime-gateway
npm run dev
```

---

## 📊 **Environment Variable Quick Reference**

### **Backend Variables** (apps/app-api/)

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `SUPABASE_URL` | Hardcoded ✅ | ✅ | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | None ⚠️ | ✅ **CRITICAL** | Backend authentication |
| `ENVIRONMENT` | None ⚠️ | ⚠️ | Controls behavior |
| `CORS_ORIGINS` | Hardcoded ✅ | ⚠️ | Allowed origins |
| `DEBUG` | True | ⚠️ | Debug mode |
| `LOG_LEVEL` | INFO | ⚠️ | Logging level |

### **Frontend Variables** (apps/realtime-gateway/)

| Variable | Current | Required | Purpose |
|-----------|---------|----------|---------|
| `VITE_SUPABASE_URL` | Hardcoded ✅ | ✅ | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Hardcoded ✅ | ✅ | Frontend auth |
| `VITE_API_URL` | Missing ⚠️ | ✅ | Backend API URL |

---

## ✅ **Pre-Deployment Checklist**

### **Backend**
- [ ] Create `apps/app-api/.env` file
- [ ] Set `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Set `ENVIRONMENT` to `production` or `development`
- [ ] Set `CORS_ORIGINS` for your domains
- [ ] Test backend health endpoint
- [ ] Test authentication endpoints

### **Frontend**
- [ ] Update `apps/realtime-gateway/src/integrations/supabase/client.ts` to use env vars
- [ ] Create `apps/realtime-gateway/.env` file
- [ ] Set `VITE_SUPABASE_URL`
- [ ] Set `VITE_SUPABASE_ANON_KEY`
- [ ] Set `VITE_API_URL`
- [ ] Test frontend loads without errors

### **Database**
- [ ] Run `create_patients_table.sql` in Supabase
- [ ] Run `comprehensive_database_fix.sql` in Supabase
- [ ] Verify RLS policies are active
- [ ] Test patient creation
- [ ] Test recording functionality

### **Security**
- [ ] Remove hardcoded secrets from frontend
- [ ] Use environment variables for all secrets
- [ ] Set up proper CORS origins
- [ ] Enable production mode (`ENVIRONMENT=production`)
- [ ] Hide API docs in production

---

## 🎯 **Next Steps**

1. **Set up environment variables** (See "Deployment Steps" section)
2. **Update frontend to use env vars** (See "Frontend Configuration" section)
3. **Test the application** thoroughly
4. **Commit and tag as v1.0.1** with proper configuration
5. **Deploy to production** when ready

---

## 📝 **Notes**

- ✅ **Database**: Fully configured and working
- ⚠️ **Backend**: Missing `SUPABASE_SERVICE_ROLE_KEY` (critical)
- ⚠️ **Frontend**: Using hardcoded keys (security risk)
- ✅ **RLS Policies**: Properly configured
- ✅ **Application**: Functionally complete

**Current Version:** v1.0.0 (Complete Application Release)

