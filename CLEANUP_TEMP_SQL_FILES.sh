#!/bin/bash
# Optional cleanup script - removes temporary SQL diagnostic files
# Keep this script for reference but don't run it automatically

echo "These SQL files were created during migration:"
echo ""
echo "MIGRATION SCRIPTS:"
ls -lh DATABASE_HIERARCHY_MIGRATION.sql ASSIGN_PATIENTS_TO_CENTER.sql ASSIGN_USERS_TO_ORG_CENTERS.sql 2>/dev/null

echo ""
echo "DIAGNOSTIC SCRIPTS:"
ls -lh CHECK_*.sql CLEANUP*.sql DIAGNOSE*.sql FINAL_*.sql RUN_*.sql TEST_*.sql RECREATE*.sql 2>/dev/null

echo ""
echo "To clean up diagnostic files, run:"
echo "rm CHECK_*.sql CLEANUP*.sql DIAGNOSE*.sql FINAL_*.sql RUN_*.sql RECREATE*.sql"
echo ""
echo "Or keep them for future reference!"
