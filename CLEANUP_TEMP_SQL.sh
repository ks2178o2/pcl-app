#!/bin/bash
# Cleanup temporary diagnostic SQL files

echo "Cleaning up temporary SQL diagnostic files..."

rm -f CHECK_ASSIGNMENTS_AFTER_CLEANUP.sql
rm -f CHECK_DUPLICATE_PROFILES.sql
rm -f CHECK_EXISTING_ASSIGNMENTS_ROLES.sql
rm -f CHECK_ROLES.sql
rm -f CHECK_ROLE_ENUM.sql
rm -f CHECK_USER_ASSIGNMENTS.sql
rm -f CHECK_USER_ASSIGNMENTS_SCHEMA.sql
rm -f CLEANUP_DUPLICATES.sql
rm -f CLEANUP_DUPLICATE_PROFILES.sql
rm -f DIAGNOSE_ASSIGNMENTS.sql
rm -f FINAL_CHECK.sql
rm -f RECREATE_ASSIGNMENTS_FROM_SCRATCH.sql
rm -f RUN_CLEANUP.sql
rm -f CLEANUP_TEMP_SQL_FILES.sh

echo "✅ Cleanup complete!"
echo ""
echo "Keeping essential SQL files:"
ls -1 *.sql 2>/dev/null
