#!/usr/bin/env bash
set -euo pipefail

# YeniMenzil Backup Script
# Backs up PostgreSQL database and MinIO media data

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
    if ! command -v pg_dump &>/dev/null; then
        log_error "pg_dump not found. Is PostgreSQL client installed?"
        return 1
    fi
    if ! command -v docker &>/dev/null; then
        log_error "Docker not found. Is Docker running?"
        return 1
    fi
}

backup_db() {
    local backup_name="yenimenzil_pg_backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "Backing up PostgreSQL database..."
    
    docker compose -f "$COMPOSE_FILE" exec db pg_dump -U yenimenzil -d yenimenzil > "/tmp/$backup_name" 2>&1 || {
        log_error "DB backup failed. Trying alternative method..."
        pg_dump -h localhost -U yenimenzil -d yenimenzil > "/tmp/$backup_name" 2>&1 || {
            log_error "All DB backup methods failed."
            return 1
        }
    }
    
    log_info "Database backup saved to /tmp/$backup_name"
    echo "$backup_name"
}

backup_minio() {
    local backup_name="minio_backup_$(date +%Y%m%d_%H%M%S).tar"
    log_info "Backing up MinIO media data..."
    
    # Create tar archive of the MinIO volume
    docker compose -f "$COMPOSE_FILE" exec minio tar czf - /data > "/tmp/$backup_name" 2>&1 || {
        log_warn "MinIO direct backup failed. Using mc mirror if available..."
        # Try with mc if available
        if command -v mc &>/dev/null; then
            mc alias set minio http://localhost:9000 minioadmin minioadmin 2>/dev/null && \
                mc mirror minio/yenimenzil-media "/tmp/minio_media_$(date +%Y%m%d).tar" 2>/dev/null && \
                echo "MinIO media mirrored to /tmp/minio_media_$(date +%Y%m%d).tar"
        fi
        
        log_error "MinIO backup failed."
        return 1
    }
    
    log_info "MinIO backup saved to /tmp/$backup_name"
    echo "$backup_name"
}

full_backup() {
    log_info "Starting full backup of YeniMenzil.az..."
    check_dependencies
    
    local db_backup minio_backup
    
    db_backup=$(backup_db) || log_error "Database backup had issues but continuing..."
    minio_backup=$(backup_minio) || log_error "MinIO backup had issues but continuing..."
    
    log_info "Backup complete!"
    log_info "  Database: $db_backup"
    log_info "  MinIO media: $minio_backup"
    log_info "Backups located in /tmp/"
}

full_backup