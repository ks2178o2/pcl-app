# v1.0.4 Deployment Guide

This guide walks you through deploying the v1.0.4 authentication and security enhancements.

---

## Prerequisites

1. Access to Supabase dashboard
2. Backend server access
3. Frontend deployment environment
4. Database admin privileges

---

## Deployment Process

### Phase 1: Database Setup (5 minutes)

1. **Open Supabase SQL Editor**
   - Navigate to your project
   - Go to "SQL Editor"

2. **Run Migration Script**
   - Open `V1_0_4_AUTH_DATABASE_SCHEMA.sql`
   - Copy entire contents
   - Paste into SQL Editor
   - Click "Run"

3. **Verify Migration**
   ```sql
   -- Check tables were created
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('user_invitations', 'login_audit', 'user_devices');
   
   -- Check profiles table was altered
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'profiles' 
   AND column_name IN ('two_factor_enabled', 'two_factor_secret', 'last_login_ip');
   ```

4. **Expected Results**
   - All 3 new tables created
   - 5 new columns in profiles
   - Views created successfully
   - Functions and triggers installed

---

### Phase 2: OAuth Configuration (10 minutes)

1. **Enable Google OAuth**
   - Supabase Dashboard → Authentication → Providers
   - Enable "Google"
   - Add Client ID and Secret
   - Authorized redirect URLs: `https://yourdomain.com/auth/callback`

2. **Enable Apple OAuth** (Optional)
   - Enable "Apple"
   - Configure Apple Developer credentials
   - Authorized redirect URLs: `https://yourdomain.com/auth/callback`

3. **Test OAuth Flow**
   - Navigate to login page
   - Click "Sign in with Google"
   - Verify redirect works
   - Complete authentication

---

### Phase 3: Backend Deployment (5 minutes)

1. **Update Dependencies**
   ```bash
   cd apps/app-api
   pip install -r requirements.txt
   ```

2. **Verify Installation**
   ```bash
   pip list | grep -E "(pyotp|qrcode)"
   # Should show:
   # pyotp 2.9.0
   # qrcode 7.4.2
   ```

3. **Restart Application**
   ```bash
   # If using systemd
   sudo systemctl restart your-app-api
   
   # If using Docker
   docker restart your-api-container
   
   # If running manually
   pkill -f "uvicorn main:app"
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Verify Backend Health**
   ```bash
   curl http://localhost:8000/health
   # Should return 200 OK
   ```

5. **Check API Documentation**
   ```
   Open: http://localhost:8000/docs
   Verify new routes appear:
   - /api/invitations/*
   - /api/auth/*
   - /api/auth/2fa/*
   ```

---

### Phase 4: Frontend Deployment (5 minutes)

1. **Update Dependencies**
   ```bash
   cd apps/realtime-gateway
   npm install
   ```

2. **Verify Installation**
   ```bash
   npm list react-icons
   # Should show react-icons@5.0.0
   ```

3. **Build Application**
   ```bash
   npm run build
   ```

4. **Deploy**
   ```bash
   # Copy dist/ to your web server
   # Restart nginx/apache
   # Or deploy to your CDN/static hosting
   ```

5. **Verify Frontend**
   - Navigate to login page
   - Verify OAuth buttons appear
   - Check for console errors

---

### Phase 5: Testing (15 minutes)

#### Test 1: User Invitation
1. Log in as admin
2. Go to User Management
3. Click "Invite User"
4. Enter email and select role
5. Send invitation
6. Check email for invitation link
7. Click link and verify acceptance page loads
8. Create account
9. Verify login works

#### Test 2: OAuth Login
1. Go to login page
2. Click "Sign in with Google"
3. Complete Google authentication
4. Verify redirected back
5. Verify profile created automatically

#### Test 3: 2FA Setup
1. Log in as test user
2. Navigate to security settings
3. Click "Enable 2FA"
4. Scan QR code with authenticator app
5. Enter verification code
6. Verify 2FA enabled

#### Test 4: Login Audit
1. Log in as user
2. Navigate to security settings
3. View login history
4. Verify recent login appears
5. Check device information captured

---

## Rollback Procedure

If issues occur, rollback using these steps:

1. **Backend Rollback**
   ```bash
   # Revert main.py to previous version
   git checkout v1.0.3 apps/app-api/main.py
   
   # Restart application
   sudo systemctl restart your-app-api
   ```

2. **Frontend Rollback**
   ```bash
   # Revert to previous build
   git checkout v1.0.3
   npm run build
   # Deploy previous build
   ```

3. **Database Rollback** (if needed)
   ```sql
   -- Drop new tables
   DROP TABLE IF EXISTS user_devices CASCADE;
   DROP TABLE IF EXISTS login_audit CASCADE;
   DROP TABLE IF EXISTS user_invitations CASCADE;
   
   -- Drop views
   DROP VIEW IF EXISTS recent_logins;
   DROP VIEW IF EXISTS active_invitations;
   
   -- Remove columns from profiles
   ALTER TABLE profiles 
   DROP COLUMN IF EXISTS two_factor_enabled,
   DROP COLUMN IF EXISTS two_factor_secret,
   DROP COLUMN IF EXISTS verified_devices,
   DROP COLUMN IF EXISTS last_login_ip,
   DROP COLUMN IF EXISTS last_login_at;
   ```

---

## Post-Deployment Checklist

- [ ] Database migration completed successfully
- [ ] OAuth providers configured
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend application restarted
- [ ] Frontend deployed
- [ ] User invitation tested
- [ ] OAuth login tested
- [ ] 2FA setup tested
- [ ] Login audit working
- [ ] No console errors
- [ ] No API errors
- [ ] Performance acceptable

---

## Monitoring

After deployment, monitor:

1. **Error Logs**
   - Backend: Check application logs
   - Frontend: Check browser console
   - Database: Check Supabase logs

2. **Performance**
   - API response times
   - Authentication latency
   - Database query times

3. **Security**
   - Failed login attempts
   - Unusual IP addresses
   - Device registrations

4. **User Feedback**
   - OAuth login issues
   - 2FA setup difficulties
   - Invitation email delivery

---

## Troubleshooting

### Issue: OAuth not working
**Solution:**
1. Check redirect URLs in Supabase
2. Verify OAuth credentials
3. Check browser console for errors
4. Ensure HTTPS is used (OAuth requirement)

### Issue: 2FA QR code not generating
**Solution:**
1. Verify pyotp and qrcode installed
2. Check PIL (Pillow) is installed
3. Review backend logs for errors
4. Test API endpoint directly

### Issue: Invitation emails not sending
**Solution:**
1. Implement email sending function
2. Configure SMTP settings
3. Check Supabase Edge Functions
4. Verify email templates

### Issue: Database errors
**Solution:**
1. Check migration script ran fully
2. Verify foreign key constraints
3. Check RLS policies
4. Review Supabase logs

---

## Support

For deployment issues:
1. Check logs first
2. Review this guide
3. Contact development team
4. Open GitHub issue with details

---

**Deployment Time:** ~40 minutes  
**Estimated Downtime:** None (zero-downtime deployment)  
**Risk Level:** Low

