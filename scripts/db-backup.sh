#!/bin/bash

# KUYAN Backup Script
# Backs up your database to a timestamped file

BACKUP_DIR="backups"
DB_FILE="kuyan.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/kuyan_backup_$TIMESTAMP.db"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file $DB_FILE not found!"
    exit 1
fi

# Copy database file
cp "$DB_FILE" "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"
echo "Database size: $(ls -lh $DB_FILE | awk '{print $5}')"
echo "Backup size: $(ls -lh $BACKUP_FILE | awk '{print $5}')"

# Optional: Keep only last 30 backups
cd "$BACKUP_DIR"
ls -t kuyan_backup_*.db | tail -n +31 | xargs -r rm
echo "Old backups cleaned (keeping last 30)"
