# 🔒 Encryption/Decryption - TODO for Future Implementation

## ⚠️ IMPORTANT REMINDER

The encryption/decryption mechanisms for sensitive data (emails, phone numbers) have been **temporarily disabled** to allow continued testing of other features. They need to be **properly implemented and thoroughly tested** before production use.

## Current Status

- ✅ **Database functions created**: `encrypt_sensitive_data()` and `decrypt_sensitive_data()` exist in the database
- ✅ **Functions tested**: Basic SQL test passed
- ❌ **Code integration**: Encryption/decryption is currently **commented out** in the application code
- ❌ **Production key**: Using auto-generated development key (must be changed for production)

## Files Affected

1. **`apps/realtime-gateway/src/hooks/useAppointments.ts`**
   - Decryption logic is commented out (lines ~146-180)
   - Appointments are currently read without decryption

2. **`apps/realtime-gateway/src/components/AppointmentCreationForm.tsx`**
   - May need encryption on insert (email/phone_number fields)
   - Check if encryption is needed on appointment creation

3. **`apps/realtime-gateway/src/pages/PatientDetails.tsx`**
   - May need encryption when saving contact info (email/phone_number)

4. **`apps/realtime-gateway/src/hooks/useAppointments.ts`** - `uploadAppointments` function
   - May need encryption when uploading appointments from file

## Required Steps Before Production

### 1. Re-enable Decryption on Read
**File**: `apps/realtime-gateway/src/hooks/useAppointments.ts`

- Uncomment the `decryptWithTimeout` function
- Uncomment the decryption logic in `loadAppointments`
- Test that encrypted data decrypts correctly
- Test that unencrypted data (existing records) still works

### 2. Enable Encryption on Insert/Update
**Files to update**:
- `apps/realtime-gateway/src/components/AppointmentCreationForm.tsx`
- `apps/realtime-gateway/src/pages/PatientDetails.tsx`
- `apps/realtime-gateway/src/hooks/useAppointments.ts` (uploadAppointments)

**Implementation pattern**:
```typescript
// Before inserting/updating:
const encryptedEmail = email 
  ? await supabase.rpc('encrypt_sensitive_data', { data: email }).then(({ data }) => data || email)
  : null;

const encryptedPhone = phone
  ? await supabase.rpc('encrypt_sensitive_data', { data: phone }).then(({ data }) => data || phone)
  : null;
```

### 3. Set Production Encryption Key
**IMPORTANT**: The current encryption key is auto-generated for development. You **MUST** set a secure production key.

```sql
-- In Supabase SQL Editor:
-- Generate a secure key: openssl rand -hex 32
UPDATE public.encryption_settings 
SET encryption_key = 'your-generated-32-byte-key-here' 
WHERE id = 1;
```

**Security Notes**:
- Key must be at least 32 bytes (256 bits)
- Store key securely (environment variable, secrets management)
- Never commit the key to version control
- Rotate keys periodically in production

### 4. Test Thoroughly

#### Test Cases:
1. **Create appointment with email/phone** → Verify data is encrypted in database
2. **View appointments** → Verify email/phone decrypts correctly
3. **Update appointment contact info** → Verify encryption on update
4. **Upload appointments file** → Verify encryption on bulk insert
5. **Existing unencrypted data** → Verify graceful handling (should return as-is)
6. **Empty/null values** → Verify doesn't error
7. **Invalid encrypted data** → Verify graceful fallback

#### Database Verification:
```sql
-- Check that data is encrypted (should see base64-like strings)
SELECT id, 
       email, 
       phone_number,
       LENGTH(email) as email_len,
       LENGTH(phone_number) as phone_len
FROM appointments 
WHERE email IS NOT NULL 
LIMIT 5;

-- Test decryption manually
SELECT 
  email,
  decrypt_sensitive_data(email) as decrypted_email
FROM appointments 
WHERE email IS NOT NULL 
LIMIT 5;
```

### 5. Migration Strategy for Existing Data

If you have existing unencrypted data, decide on migration approach:

**Option A: Encrypt existing data**
```sql
-- Encrypt existing unencrypted emails/phones
UPDATE appointments 
SET email = encrypt_sensitive_data(email) 
WHERE email IS NOT NULL 
  AND email NOT LIKE '-----BEGIN%'  -- Not already encrypted
  AND LENGTH(email) < 200;  -- Reasonable email length (encrypted will be longer)

UPDATE appointments 
SET phone_number = encrypt_sensitive_data(phone_number) 
WHERE phone_number IS NOT NULL 
  AND phone_number NOT LIKE '-----BEGIN%'
  AND LENGTH(phone_number) < 50;
```

**Option B: Leave existing data unencrypted, encrypt new data only**
- Simpler, but mixed encrypted/unencrypted data
- Requires code to handle both cases

**Option C: Gradual migration**
- Encrypt on update/access
- Gradually migrate all data

### 6. Error Handling

Ensure robust error handling:
- Function missing → Graceful fallback (don't break app)
- Invalid encrypted data → Return as-is (may be unencrypted)
- Network timeouts → Return original value
- Log errors for monitoring

### 7. Performance Considerations

- Encryption/decryption adds latency
- Consider caching decrypted values (with TTL)
- Batch operations where possible
- Monitor query performance

## Database Functions Reference

**Location**: `create_encryption_functions.sql`

**Functions**:
- `encrypt_sensitive_data(TEXT)` → Returns encrypted base64 string
- `decrypt_sensitive_data(TEXT)` → Returns decrypted plaintext

**Settings Table**: `public.encryption_settings`
- Contains encryption key (RLS protected)
- Service role only access

## Related Documentation

- `create_encryption_functions.sql` - Database function definitions
- Supabase pgcrypto documentation
- Security best practices for encryption keys

## Checklist Before Production

- [ ] Re-enable decryption on read (useAppointments.ts)
- [ ] Enable encryption on insert (AppointmentCreationForm.tsx)
- [ ] Enable encryption on update (PatientDetails.tsx)
- [ ] Enable encryption on bulk upload (useAppointments.ts uploadAppointments)
- [ ] Set production encryption key
- [ ] Test all create/read/update flows
- [ ] Test with existing unencrypted data
- [ ] Test error scenarios
- [ ] Performance test with large datasets
- [ ] Document key rotation procedure
- [ ] Set up monitoring/alerts for encryption failures
- [ ] Security review of encryption implementation

---

**Last Updated**: 2025-01-27  
**Status**: ⚠️ Encryption disabled - requires implementation and testing

