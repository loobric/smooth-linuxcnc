#!/bin/bash
# LinuxCNC Tool Table Sync Script
# Synchronizes tool table between LinuxCNC and Smooth
#
# Usage: sync_tooltable.sh <machine_id>
# Example: sync_tooltable.sh mill01

set -e

# Configuration
CONFIG_FILE="${HOME}/.config/smooth/linuxcnc.conf"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Defaults (override in config file)
SMOOTH_API_URL="${SMOOTH_API_URL:-http://localhost:8000}"
SMOOTH_API_KEY="${SMOOTH_API_KEY:-}"
LOG_DIR="${LOG_DIR:-/tmp/smooth-sync}"
LINUXCNC_INI="${LINUXCNC_INI:-}"

# Get machine ID from argument
MACHINE_ID="${1:-default}"

# Create log directory
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/sync-${MACHINE_ID}-$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $1"
    exit 1
}

# Check if API key is set
if [ -z "$SMOOTH_API_KEY" ]; then
    error "SMOOTH_API_KEY not set. Create ${CONFIG_FILE} or set environment variable."
fi

# Find LinuxCNC tool table
if [ -n "$LINUXCNC_INI" ] && [ -f "$LINUXCNC_INI" ]; then
    # Parse tool table path from INI file
    TOOL_TABLE=$(grep -i "^TOOL_TABLE" "$LINUXCNC_INI" | cut -d= -f2 | tr -d ' ')
    if [ -z "$TOOL_TABLE" ]; then
        error "TOOL_TABLE not found in $LINUXCNC_INI"
    fi
    # Handle relative paths
    if [[ "$TOOL_TABLE" != /* ]]; then
        INI_DIR=$(dirname "$LINUXCNC_INI")
        TOOL_TABLE="${INI_DIR}/${TOOL_TABLE}"
    fi
else
    # Default location
    TOOL_TABLE="${HOME}/linuxcnc/configs/sim/axis/tool.tbl"
fi

if [ ! -f "$TOOL_TABLE" ]; then
    error "Tool table not found: $TOOL_TABLE"
fi

log "Starting sync for machine: $MACHINE_ID"
log "Tool table: $TOOL_TABLE"

# Backup current tool table
BACKUP_FILE="${LOG_DIR}/tool-${MACHINE_ID}-$(date +%Y%m%d-%H%M%S).tbl.bak"
cp "$TOOL_TABLE" "$BACKUP_FILE"
log "Backed up tool table to: $BACKUP_FILE"

# Parse tool table and convert to Smooth format
log "Parsing tool table..."
SCRIPT_DIR=$(dirname "$0")
PARSED_JSON=$(python3 "${SCRIPT_DIR}/parse_tooltable.py" "$TOOL_TABLE" "$MACHINE_ID")

if [ $? -ne 0 ]; then
    error "Failed to parse tool table: $PARSED_JSON"
fi

# Upload to Smooth using generic tool-presets endpoint
log "Uploading tool presets to Smooth..."
UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "${SMOOTH_API_URL}/api/v1/tool-presets" \
    -H "Authorization: Bearer ${SMOOTH_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$PARSED_JSON")

HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$UPLOAD_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ]; then
    error "Upload failed (HTTP $HTTP_CODE): $RESPONSE_BODY"
fi
log "Upload successful"

# Download tool presets from Smooth using generic endpoint
log "Downloading tool presets from Smooth..."
DOWNLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
    "${SMOOTH_API_URL}/api/v1/tool-presets?machine_id=${MACHINE_ID}" \
    -H "Authorization: Bearer ${SMOOTH_API_KEY}")

HTTP_CODE=$(echo "$DOWNLOAD_RESPONSE" | tail -n1)
PRESETS_JSON=$(echo "$DOWNLOAD_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" != "200" ]; then
    error "Download failed (HTTP $HTTP_CODE): $PRESETS_JSON"
fi

# Convert Smooth format to LinuxCNC tool table
log "Converting to LinuxCNC format..."
NEW_TOOL_TABLE=$(python3 "${SCRIPT_DIR}/export_tooltable.py" "$PRESETS_JSON")

if [ $? -ne 0 ]; then
    error "Failed to convert tool table: $NEW_TOOL_TABLE"
fi

# Compare with current tool table
if diff -q <(echo "$NEW_TOOL_TABLE") "$TOOL_TABLE" > /dev/null 2>&1; then
    log "Tool table unchanged, no update needed"
else
    log "Tool table has changes, updating..."
    echo "$NEW_TOOL_TABLE" > "$TOOL_TABLE"
    log "Tool table updated successfully"
fi

log "Sync completed successfully"
