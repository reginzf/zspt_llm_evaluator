#!/bin/bash

# AI-KEN Code Synchronization Script (前后端分离版本)
# 用于同步代码并重启 ai-ken-backend 和 ai-ken-frontend 服务

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to backup configuration files before pulling
backup_configs() {
    log_step "Backing up configuration files..."
    
    if [ -d "configs" ]; then
        cp -r configs configs_backup_$(date +%Y%m%d_%H%M%S)
        log_info "Configuration files backed up"
    else
        log_warn "configs directory not found, skipping backup"
    fi
    
    # Backup other important files/directories
    important_dirs=("logs" "data" "models" "reports/report_data")
    for dir in "${important_dirs[@]}"; do
        if [ -d "$dir" ]; then
            cp -r "$dir" "${dir}_backup_$(date +%Y%m%d_%H%M%S)"
            log_info "$dir backed up"
        fi
    done
}

# Function to restore configuration files after pulling
restore_configs() {
    log_step "Restoring configuration files..."
    
    # Find the latest backup configs directory
    latest_backup=$(ls -td configs_backup_* 2>/dev/null | head -n1)
    if [ -n "$latest_backup" ] && [ -d "$latest_backup" ]; then
        # Restore settings.toml specifically to preserve environment configuration
        if [ -f "$latest_backup/settings.toml" ]; then
            mkdir -p configs
            cp "$latest_backup/settings.toml" configs/settings.toml
            log_info "settings.toml restored from backup"
        fi
        
        # Also restore other config files if they don't exist
        for file in "$latest_backup"/*; do
            filename=$(basename "$file")
            if [ ! -f "configs/$filename" ] && [ "$filename" != "settings.toml" ]; then
                cp "$file" "configs/"
                log_info "$filename restored from backup"
            fi
        done
        
        # Clean up backup
        rm -rf "$latest_backup"
        log_info "Backup cleaned up"
    else
        log_warn "No configuration backup found to restore"
    fi
    
    # Restore other important directories
    important_dirs=("logs" "data" "models" "reports/report_data")
    for dir in "${important_dirs[@]}"; do
        backup_dir="${dir}_backup_$(ls -td ${dir}_backup_* 2>/dev/null | head -n1 | xargs basename 2>/dev/null || echo '')"
        if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
            # Move files back, preserving existing content
            if [ -d "$dir" ]; then
                rsync -av "$backup_dir/" "$dir/" --ignore-existing
            else
                mv "$backup_dir" "$dir"
            fi
            log_info "$dir restored from backup"
            rm -rf "$backup_dir"  # Clean up backup
        fi
    done
}

# Function to restart backend service
restart_backend() {
    log_step "Restarting ai-ken-backend service..."
    
    sudo systemctl restart ai-ken-backend
    
    # Wait a moment for service to restart
    sleep 3
    
    if systemctl is-active --quiet ai-ken-backend; then
        log_info "ai-ken-backend service restarted successfully"
    else
        log_error "Failed to restart ai-ken-backend service"
        sudo journalctl -u ai-ken-backend --no-pager -n 20
        return 1
    fi
}

# Function to restart frontend service
restart_frontend() {
    log_step "Restarting ai-ken-frontend service..."
    
    sudo systemctl restart ai-ken-frontend
    
    # Wait a moment for service to restart
    sleep 2
    
    if systemctl is-active --quiet ai-ken-frontend; then
        log_info "ai-ken-frontend service restarted successfully"
    else
        log_error "Failed to restart ai-ken-frontend service"
        sudo journalctl -u ai-ken-frontend --no-pager -n 20
        return 1
    fi
}

# Function to restart services (both backend and frontend)
restart_services() {
    log_step "Restarting services..."
    
    # Restart backend first
    restart_backend
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Note: Frontend is built and deployed by deploy_prod.sh to /var/www/ai-ken/
    # We skip rebuilding frontend here to avoid dependency issues on server
    log_info "Skipping frontend build (managed by deploy_prod.sh)"

    # Restart frontend (Nginx)
    restart_frontend
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    log_info "All services restarted successfully"
}

# Function to show service status
show_status() {
    log_step "Service status:"
    echo ""
    echo "=== Backend Service ==="
    sudo systemctl status ai-ken-backend --no-pager -l
    echo ""
    echo "=== Frontend Service ==="
    sudo systemctl status ai-ken-frontend --no-pager -l
}

# Main function
main() {
    log_info "Starting code synchronization process..."
    log_info "Mode: 前后端分离部署"
    
    # Check if we're in a git repository
    if [ ! -d ".git" ] && [ ! -f ".git" ]; then
        log_error "Not in a git repository directory"
        exit 1
    fi
    
    # Get current branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -z "$current_branch" ]; then
        # If in detached HEAD state, get the current commit hash
        current_commit=$(git rev-parse HEAD 2>/dev/null)
        if [ -z "$current_commit" ]; then
            log_error "Could not determine current branch or commit"
            exit 1
        fi
        log_warn "In detached HEAD state at commit: $current_commit"
        current_branch="HEAD"
    else
        log_info "Current branch: $current_branch"
    fi
    
    # Store current directory
    PROJECT_ROOT=$(pwd)
    log_info "Project root: $PROJECT_ROOT"
    
    # Backup configuration files
    backup_configs
    
    # Get the current remote URL
    remote_url=$(git remote get-url origin 2>/dev/null)
    if [ $? -ne 0 ]; then
        log_error "Failed to get remote URL. Not in a git repository?"
        exit 1
    fi
    
    log_info "Current remote URL: $remote_url"
    
    # Fetch from the origin remote directly since credentials are configured
    log_step "Fetching latest code from remote repository..."
    if git fetch origin; then
        log_info "Successfully fetched from remote repository"
    else
        log_error "Failed to fetch from remote repository"
        exit 1
    fi
    
    # Reset to the latest commit from the origin remote
    log_step "Resetting to latest commit on $current_branch..."
    if git reset --hard origin/$current_branch; then
        log_info "Successfully reset to latest commit"
    else
        log_error "Failed to reset to latest commit"
        exit 1
    fi
    
    # Restore configuration files
    restore_configs
    
    # Restart services (backend + frontend)
    restart_services
    if [ $? -ne 0 ]; then
        log_error "Service restart failed"
        exit 1
    fi
    
    # Show final status
    show_status
    
    log_info "Code synchronization completed successfully!"
    log_info ""
    log_info "Services status:"
    log_info "  - Backend (ai-ken-backend): http://127.0.0.1:5001"
    log_info "  - Frontend (ai-ken-frontend): http://<server_ip>:5002"
    log_info ""
    log_info "Tips:"
    log_info "  - Use 'sudo journalctl -u ai-ken-backend -f' to view backend logs"
    log_info "  - Use 'sudo journalctl -u ai-ken-frontend -f' to view frontend logs"
}

# Run main function with error handling
main "$@"
