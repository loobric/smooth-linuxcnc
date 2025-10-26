# Smooth LinuxCNC Integration

> Bidirectional tool table synchronization between LinuxCNC and Smooth tool management system.

## What is smooth-linuxcnc?

A client-side integration that synchronizes tool data between LinuxCNC controllers and a Smooth server, providing:
- **Bidirectional sync** - Upload tool tables to Smooth, download updates back to LinuxCNC
- **Automated sync script** - Periodic synchronization via cron or manual trigger
- **Automatic backups** - Backs up tool table before every sync
- **Change detection** - Only updates if tool table has changed
- **Comprehensive logging** - All operations logged with timestamps
- **Multiple integration options** - Manual, cron-based, HAL, or event-driven

## Features

- Parses LinuxCNC tool table (`.tbl`) format
- Converts to/from Smooth ToolPreset entities
- Preserves all LinuxCNC parameters (T, P, D, Z, X, Y, Q, etc.)
- Round-trip conversion tested
- Machine-specific synchronization
- Configuration file for easy setup

## Quick Start

### 1. Install Dependencies

```bash
# Python requests library (if not already installed)
pip install requests
```

### 2. Configure

Create `~/.config/smooth/linuxcnc.conf`:
```bash
# Smooth API configuration
SMOOTH_API_URL="http://localhost:8000"
SMOOTH_API_KEY="your-api-key-here"

# LinuxCNC configuration
LINUXCNC_INI="/home/user/linuxcnc/configs/mill/mill.ini"

# Logging
LOG_DIR="/tmp/smooth-sync"
```

### 3. Run Sync

```bash
# Manual sync
./sync_tooltable.sh mill01

# Output:
# [2025-10-25 12:00:00] Starting sync for machine: mill01
# [2025-10-25 12:00:00] Tool table: /home/user/linuxcnc/configs/mill/tool.tbl
# [2025-10-25 12:00:00] Backed up tool table to: /tmp/smooth-sync/tool-mill01-20251025-120000.tbl.bak
# [2025-10-25 12:00:01] Parsing tool table...
# [2025-10-25 12:00:01] Uploading tool presets to Smooth...
# [2025-10-25 12:00:02] Upload successful
# [2025-10-25 12:00:02] Downloading tool presets from Smooth...
# [2025-10-25 12:00:03] Converting to LinuxCNC format...
# [2025-10-25 12:00:03] Tool table has changes, updating...
# [2025-10-25 12:00:03] Tool table updated successfully
# [2025-10-25 12:00:03] Sync completed successfully
```

## How It Works

### LinuxCNC → Smooth

1. **Locate** - Find tool table from LinuxCNC INI file
2. **Backup** - Create timestamped backup before changes
3. **Parse** - Read `.tbl` file and extract tool data
4. **Convert** - Transform to Smooth ToolPreset format
5. **Upload** - Send to Smooth via REST API (`POST /api/v1/tool-presets`)

### Smooth → LinuxCNC

1. **Download** - Fetch ToolPresets from Smooth (`GET /api/v1/tool-presets?machine_id=...`)
2. **Convert** - Transform to LinuxCNC format
3. **Compare** - Check if different from current tool table
4. **Update** - Write new tool table only if changed
5. **Log** - Record all operations

## LinuxCNC Tool Table Format

### Example Tool Table
```
T1 P0 D+5.000000 Z-50.000000 ;5mm Drill HSS
T2 P0 D+6.000000 Z-60.000000 X+1.500000 ;6mm Endmill Carbide
T3 P0 D+3.000000 Z-40.000000 ;3mm Probe
T10 P0 D+12.700000 Z-25.000000 ;1/2" Face Mill
```

### Parameters
- **T** - Tool number (required)
- **P** - Pocket number (usually 0)
- **D** - Diameter (mm or inches)
- **Z** - Z offset (length)
- **X, Y** - X, Y offsets (optional)
- **U, V, W** - Additional offsets for multi-axis (optional)
- **Q** - Orientation (optional)
- **;comment** - Tool description

### Conversion to Smooth

LinuxCNC entry:
```
T1 P0 D+5.000000 Z-50.000000 ;5mm Drill HSS
```

Becomes Smooth ToolPreset:
```json
{
  "machine_id": "mill01",
  "tool_number": 1,
  "description": "5mm Drill HSS",
  "offsets": {
    "z": -50.0,
    "z_unit": "mm"
  },
  "metadata": {
    "source": "linuxcnc",
    "diameter": 5.0,
    "diameter_unit": "mm",
    "pocket": 0
  }
}
```

## Integration Options

### Option 1: Manual Sync (Testing/Development)
Run sync script when needed:
```bash
./sync_tooltable.sh mill01
```

### Option 2: Cron-Based (Recommended for Production)
Periodic background sync every 5-15 minutes:
```bash
# Edit crontab
crontab -e

# Add line for sync every 5 minutes
*/5 * * * * /path/to/smooth-linuxcnc/sync_tooltable.sh mill01 >> /var/log/smooth-sync.log 2>&1
```

### Option 3: HAL Integration
Sync on machine startup/shutdown:
```hal
# In your postgui.hal file
loadusr -w /path/to/smooth-linuxcnc/sync_tooltable.sh mill01
```

### Option 4: Event-Driven (Advanced - Future)
Python HAL component that syncs on tool changes:
```python
import hal
import subprocess

h = hal.component("smooth-sync")
h.ready()

# Sync on tool changes
while True:
    if tool_changed():
        subprocess.run(["/path/to/sync_tooltable.sh", "mill01"])
```

## Components

### 1. Low-Level Translator (`translator.py`)
Parses and generates LinuxCNC tool table format.

**Functions:**
- `parse_tool_table_line(line)` - Parse single tool entry
- `parse_tool_table(content)` - Parse complete file
- `generate_tool_table_line(tool)` - Generate single entry
- `generate_tool_table(tools)` - Generate complete file

### 2. Parser Script (`parse_tooltable.py`)
Converts LinuxCNC → Smooth ToolPreset format.

**Usage:**
```bash
./parse_tooltable.py /path/to/tool.tbl machine_id
```

**Output:** JSON ready for Smooth API

### 3. Export Script (`export_tooltable.py`)
Converts Smooth ToolPreset → LinuxCNC format.

**Usage:**
```bash
cat presets.json | ./export_tooltable.py -
```

**Output:** LinuxCNC `.tbl` format

### 4. Sync Script (`sync_tooltable.sh`)
Orchestrates complete bidirectional sync.

**Features:**
- Automatic backup before changes
- Change detection (only updates if different)
- Comprehensive logging
- Error handling and rollback
- Configuration file support

## Testing

### Unit Tests
```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_translator.py
pytest tests/test_smooth_conversion.py

# With coverage
pytest --cov=. --cov-report=html
```

**Test coverage:** 42+ tests passing

### Manual Testing

**Parse a tool table:**
```bash
./parse_tooltable.py sample_tool.tbl mill01 | jq
```

**Generate a tool table:**
```bash
echo '{"items": [{"tool_number": 1, "description": "Test", "metadata": {"diameter": 5.0}}]}' | ./export_tooltable.py -
```

**Full sync test:**
```bash
./sync_tooltable.sh mill01
cat /tmp/smooth-sync/sync-mill01-$(date +%Y%m%d).log
```

## File Locations

**LinuxCNC tool tables:**
- Defined in machine INI file: `[EMCIO]` section, `TOOL_TABLE` parameter
- Common location: `~/linuxcnc/configs/{machine}/tool.tbl`

**Configuration:**
- `~/.config/smooth/linuxcnc.conf`

**Logs:**
- `$LOG_DIR/sync-{machine_id}-{date}.log`

**Backups:**
- `$LOG_DIR/tool-{machine_id}-{timestamp}.tbl.bak`

## Architecture

```
LinuxCNC Controller
       │
       └─ Tool Table (.tbl file)
              │
              ▼
    ┌─────────────────────┐
    │  Smooth LinuxCNC    │
    │  (Client-side)      │
    │  • Parse .tbl       │
    │  • Convert data     │
    │  • Sync via API     │
    └─────────────────────┘
              │
              ▼ REST API
    ┌─────────────────────┐
    │   Smooth Core       │
    │   (Server)          │
    │   • ToolPreset      │
    │   • Version track   │
    │   • Multi-machine   │
    └─────────────────────┘
```

**Client-side conversion** keeps Smooth Core application-agnostic.

## Troubleshooting

**Sync fails with "API key not set":**
- Check `~/.config/smooth/linuxcnc.conf` exists
- Verify `SMOOTH_API_KEY` is set correctly
- Ensure no extra whitespace in config file

**Tool table not found:**
- Check `LINUXCNC_INI` points to correct `.ini` file
- Verify INI file has `[EMCIO]` section with `TOOL_TABLE` parameter
- Check file permissions

**Network errors:**
- Verify Smooth server: `curl http://localhost:8000/api/health`
- Check firewall settings
- Ensure API URL is correct

**Tool data mismatch:**
- Check unit consistency (mm vs inches in LinuxCNC INI)
- Verify tool table format is correct
- Review sync logs for parsing errors

**Permission errors:**
- Ensure sync script is executable: `chmod +x sync_tooltable.sh`
- Check write permissions on tool table file
- Verify log directory exists and is writable

## Production Considerations

- ✅ **Automatic backups** - Every sync creates timestamped backup
- ✅ **Logging** - All operations logged with timestamps
- ✅ **Change detection** - Only updates when data changes
- ⚠️ **Conflict resolution** - Currently last-write-wins
- ⚠️ **Network resilience** - Add retry logic for unreliable networks
- ⚠️ **Notifications** - Consider alerting on sync failures
- ⚠️ **Monitoring** - Set up health checks for cron jobs

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for:
- Component architecture details
- LinuxCNC format specification
- Testing procedures
- Contributing guidelines

## Documentation

- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Development guide
- **[../DEVELOPMENT.md](../DEVELOPMENT.md)** - Cross-project principles
- **LinuxCNC Docs** - http://linuxcnc.org/docs/html/gcode/tool-compensation.html

## Contributing

Contributions welcome! Please:
1. Test with real LinuxCNC configurations
2. Ensure round-trip conversion works
3. Follow TDD (tests before implementation)
4. Update docstrings
5. Follow functional programming style

## License

[License information to be added]

## Support

- GitHub Issues: [Link to issues]
- LinuxCNC Forum: [Link to thread]
- Documentation: [Link to docs]
