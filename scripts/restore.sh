#!/usr/bin/env bash
set -euo pipefail

# YeniMenzil Restore Script
# Restores PostgreSQL database and MinIO media data from backups

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_dependencies() {
    if ! command -v docker &>/dev/null; then
        log_error "Docker not found. Is Docker running?"
        return 1
    fi
}

restore_db() {
    local backup_file="$1"
    if [[ ! -f "/tmp/$backup_file" ]]; then
        log_error "Backup file /tmp/$backup_file not found."
        return 1
    fi
    
    log_info "Restoring PostgreSQL database from $backup_file..."
    
    # Stop the app first to avoid conflicts
    docker compose -f "$COMPOSE_FILE" stop api worker 2>/dev/null || true
    
    # Restore via docker exec
    cat "/tmp/$backup_file" | docker compose -f "$COMPOSE_FILE" exec db psql -U yenimenzil -d yenimenzil 2>&1 || {
        log_error "DB restore via docker exec failed. Trying direct method..."
        psql -h localhost -U yenimenzil -d yenimenzil < "/tmp/$backup_file" 2>&1 || {
            log_error "All DB restore methods failed."
            return 1
        }
    }
    
    log_info "Database restored successfully from $backup_file"
}

restore_minio() {
    local backup_file="$1"
    if [[ ! -f "/tmp/$backup_file" ]]; then
        log_error "Backup file /tmp/$backup_file not found."
        return 1
    fi
    
    log_info "Restoring MinIO media data from $backup_file..."
    
    # Stop minio briefly during restore
    docker compose -f "$COMPOSE_FILE" stop minio 2>/dev/null || true
    
    # Restore from tar archive
    docker compose -f "$COMPOSE_FILE" exec minio tar xzf - -C /data < "/tmp/$backup_file" 2>&1 || {
        log_error "MinIO tar restore failed. Trying mc mirror..."
        
        # Try with mc if available
        if command -v mc &>/dev/null; then
            mc alias set minio http://localhost:9000 minioadmin minioadmin 2>/dev/null && \
                mc mirror "/tmp/minio_media_$(date +%Y%m%d).tar" minio/yenimenzil-media 2>/dev/null && \
                log_info "MinIO media mirrored from backup."
        fi
        
        log_error "MinIO restore failed."
        return 1
    }
    
    log_info "MinIO media restored successfully from $backup_file"
    
    # Restart minio
    docker compose -f "$COMPOSE_FILE" start minio 2>/dev/null || true
}

full_restore() {
    log_info "Starting full restore of YeniMenzil.az..."
    check_dependencies
    
    # List available backups
    echo "Available database backups in /tmp/:"
    ls /tmp/pg_backup_*.sql 2>/dev/null || echo "  None found"
    echo "Available MinIO backups in /tmp/:"
    ls /tmp/minio_backup_*.tar 2>/dev/null || echo "  None found"
    
    # Ask for backup files to restore
    read -p "Enter database backup filename (e.g. pg_backup_20240101_120000.sql): " db_backup
    read -p "Enter MinIO backup filename (e.g. minio_backup_20240101_120000.tar): " minio_backup
    
    if [[ -z "$db_backup" ]]; then
        log_error "No database backup specified. Aborting."
        return 1
    fi
    
    restore_db "$db_backup" || return 1
    restore_minio "$minio_backup" || return 1
    
    log_info "Restore complete! YeniMenzil.az is back up."
}

full_restore