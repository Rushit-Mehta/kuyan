#!/bin/bash

# KUYAN Restore Script
# Restores database from a backup file

BACKUP_DIR="backups"
DB_FILE="kuyan.db"

echo "Available backups:"
echo "=================="
ls -lht "$BACKUP_DIR"/*.db 2>/dev/null | awk '{print NR". "$9" ("$6" "$7" "$8")"}'

if [ $? -ne 0 ]; then
    echo "No backups found in $BACKUP_DIR/"
    exit 1
fi

echo ""
echo "Enter the number of the backup to restore (or 'q' to quit):"
read -r choice

if [ "$choice" = "q" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Get the selected backup file
BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null | sed -n "${choice}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "Invalid selection"
    exit 1
fi

echo "Selected backup: $BACKUP_FILE"
echo "This will OVERWRITE your current database!"
echo "Type 'YES' to confirm:"
read -r confirm

if [ "$confirm" != "YES" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Backup current database before restoring
if [ -f "$DB_FILE" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    SAFETY_BACKUP="$BACKUP_DIR/pre_restore_backup_$TIMESTAMP.db"
    cp "$DB_FILE" "$SAFETY_BACKUP"
    echo "Current database backed up to: $SAFETY_BACKUP"
fi

# Restore the backup
cp "$BACKUP_FILE" "$DB_FILE"

echo "Database restored from: $BACKUP_FILE"
echo "Restore completed successfully!"
