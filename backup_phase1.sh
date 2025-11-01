#!/bin/bash
# Phase 1 Code Cleanup - Backup Script
# Backs up 10 redundant system startup scripts before deletion

set -e  # Exit on error

echo "=========================================="
echo "Phase 1 Backup Script - Starting"
echo "=========================================="

# Create backup directory if not exists
mkdir -p _archived

# List of 10 redundant files to backup
files_to_backup=(
    "complete_project_system.py"
    "secure_complete_system.py"
    "unified_quant_system.py"
    "simple_dashboard.py"
    "enhanced_interactive_dashboard.py"
    "test_system_startup.py"
    "system_status_report.py"
    "run_complete_macro_analysis.py"
    "demo_real_data_backtest.py"
    "demo_verification_system.py"
)

echo "Backing up files..."
backed_up_count=0

for file in "${files_to_backup[@]}"; do
    if [ -f "$file" ]; then
        echo "  Backing up: $file"
        cp "$file" "_archived/"
        backed_up_count=$((backed_up_count + 1))
    else
        echo "  ⚠️  File not found: $file (skipping)"
    fi
done

echo ""
echo "=========================================="
echo "✅ Backup Complete"
echo "=========================================="
echo "Backed up: $backed_up_count files"
echo "Location: _archived/"
echo ""
echo "Next steps:"
echo "1. Verify backups: ls -lh _archived/"
echo "2. Run tasks 1.2.1 to 1.2.10 to delete the files"
echo "3. Verify deletion and imports"
