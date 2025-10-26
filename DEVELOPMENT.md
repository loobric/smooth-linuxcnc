# Smooth LinuxCNC Integration Development

This document contains development information specific to **smooth-linuxcnc** - the LinuxCNC controller integration for Smooth tool synchronization.

# Design Philosophy

### Application-Agnostic Core

Smooth is designed with a strict separation between **core** and **clients**:

**Core (`smooth-core`)**: Application-agnostic REST API and data management
- No application-specific logic (no FreeCAD, LinuxCNC, etc.)
- Provides universal REST API endpoints
- Handles authentication, authorization, audit logging
- Manages canonical database schema
- Implements change detection and synchronization primitives

**Clients (`smooth-freecad`, `smooth-linuxcnc`, `smooth-web`)**: Reference implementations
- Each client is a separate repository
- Clients consume the core REST API
- Handle format translation and application-specific logic
- Serve as reference implementations for community integrations
- Can evolve independently from the core

# AI PROMPT

AI agents working on **any** Smooth repository should incorporate the following prompts into their responses:

1. Favor a functional style of programming over an object-oriented style.
2. Docstrings will be included for every function, class, and module. Docstrings should accurately document the assumptions of the code. If those assumptions change, the docstring MUST be updated accordingly. Do NOT change the docstrings without confirming with the user that the change is intentional.
3. Unit testing is required for all code. Minimize the need for mocks and stubs. If mocks or stubs are required, document the assumptions in the docstring.
4. Unit testing should focus on testing the assumptions of the code. If those assumptions change, the unit tests MUST be updated accordingly. Do NOT change the unit tests without confirming with the user that the change is intentional.
5. Changes should be incremental and minimal. Avoid large refactoring changes unless explicitly requested by the user.
6. Favor TDD (Test Driven Development). Write tests first and confirm with the user that they are complete BEFORE implementing the code.
7. Keep README and DEVELOPMENT files up to date.
8. Regularly reread this prompt and the design philosophy to ensure that the code is consistent with the overall design.
## Project Overview

The LinuxCNC integration provides:
- Bidirectional tool table synchronization between LinuxCNC and Smooth
- Format translator for LinuxCNC tool table (`.tbl`) format
- Client-side conversion scripts
- Automated sync script for periodic updates
- Multiple integration options (manual, cron, HAL)

## Architecture

The LinuxCNC client uses **client-side format conversion**:
- Parses LinuxCNC tool table files locally
- Converts to Smooth's generic data model (ToolPreset)
- Uploads via generic Smooth API endpoints (`/api/v1/tool-presets`)
- Downloads from Smooth and converts back to LinuxCNC format

This keeps the Smooth core application-agnostic.

## Components

### 1. Low-Level Translator (`translator.py`)
Parses and generates LinuxCNC tool table format.

**LinuxCNC Tool Table Format:**
```
T<number> P<pocket> D<diameter> Z<z_offset> [X<x_offset>] [Y<y_offset>] [Q<orientation>] ;<comment>
```

**Functions:**
- `parse_tool_table_line(line)` - Parse single tool line
- `parse_tool_table(content)` - Parse complete file
- `generate_tool_table_line(tool)` - Generate single line
- `generate_tool_table(tools)` - Generate complete file
- `LinuxCNCToolTableError` - Custom exception

**Features:**
- Handles all offset types (X, Y, Z, U, V, W)
- Supports orientation (Q parameter)
- Preserves comments through round-trip
- Validates tool numbers and detects duplicates
- Pocket number support (P parameter)
- Diameter tracking (D parameter)

### 2. Smooth Converter (`parse_tooltable.py`)
Converts LinuxCNC → Smooth ToolPreset format.

**Usage:**
```bash
./parse_tooltable.py /path/to/tool.tbl machine_id
```

**Output:** JSON bulk request for `/api/v1/tool-presets`

**Features:**
- Converts all LinuxCNC parameters to ToolPreset format
- Preserves LinuxCNC-specific data in metadata
- Unit-aware (mm/inch)
- Machine ID association

### 3. Smooth Exporter (`export_tooltable.py`)
Converts Smooth ToolPreset → LinuxCNC format.

**Usage:**
```bash
cat presets.json | ./export_tooltable.py -
# or
./export_tooltable.py '{"items": [...]}'
```

**Output:** LinuxCNC `.tbl` format

**Features:**
- Restores LinuxCNC-specific parameters from metadata
- Formats offsets and comments correctly
- Sorts by tool number

### 4. Sync Script (`sync_tooltable.sh`)
Orchestrates bidirectional sync between LinuxCNC and Smooth.

**Process:**
1. Locate tool table from LinuxCNC INI file
2. Create backup before any changes
3. Parse local `tool.tbl` → Smooth ToolPresets
4. Upload to Smooth via API
5. Download from Smooth via API
6. Convert back to LinuxCNC format
7. Compare with local file
8. Update only if changed
9. Log all operations

**Features:**
- Automatic backups with timestamps
- Change detection (only updates if different)
- Comprehensive logging
- Error handling and rollback
- Configuration via `~/.config/smooth/linuxcnc.conf`

## Development Status

### Completed Features ✅
- [x] LinuxCNC tool table parser (27 tests)
- [x] LinuxCNC tool table generator
- [x] Smooth format conversion (15+ tests)
- [x] Round-trip validation
- [x] Sync script with backup and logging
- [x] Configuration file support
- [x] Change detection
- [x] Error handling

**Total Test Coverage: 42+ tests passing**

### Future Enhancements
- [ ] HAL component for event-driven sync
- [ ] Network resilience with retry logic
- [ ] Conflict resolution (currently last-write-wins)
- [ ] Notification on sync failures
- [ ] Tool usage tracking integration
- [ ] Wear offset management

## LinuxCNC Tool Table Format

### Basic Format
```
T1 P0 D5.0 Z-50.0 ;5mm Drill
T2 P0 D6.0 Z-60.0 X1.5 ;6mm Endmill with X offset
```

### Parameters
- **T** - Tool number (required)
- **P** - Pocket number (optional, usually 0)
- **D** - Diameter (mm or inches)
- **Z** - Z offset (length)
- **X, Y** - X, Y offsets (optional)
- **U, V, W** - Additional offsets for multi-axis (optional)
- **Q** - Orientation (optional)
- **;comment** - Tool description

### Conversion to Smooth

LinuxCNC tool table entry:
```
T1 P0 D+5.000000 Z-50.000000 ;5mm Drill HSS
```

Becomes ToolPreset in Smooth:
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

## Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_translator.py
pytest tests/test_smooth_conversion.py

# Run with coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v
```

### Manual Testing

1. **Parse a tool table:**
```bash
./parse_tooltable.py sample_tool.tbl mill01 | jq
```

2. **Generate a tool table:**
```bash
echo '{"items": [{"tool_number": 1, "description": "Test", "metadata": {"diameter": 5.0}}]}' | ./export_tooltable.py -
```

3. **Full sync test:**
```bash
# Configure first
cat > ~/.config/smooth/linuxcnc.conf << EOF
SMOOTH_API_URL="http://localhost:8000"
SMOOTH_API_KEY="your-api-key"
LINUXCNC_INI="/path/to/your/machine.ini"
LOG_DIR="/tmp/smooth-sync"
EOF

# Run sync
./sync_tooltable.sh mill01

# Check logs
cat /tmp/smooth-sync/sync-mill01-$(date +%Y%m%d).log
```

## Integration Options

### Option 1: Manual Sync (Testing)
Run sync script when needed:
```bash
./sync_tooltable.sh mill01
```

### Option 2: Cron-Based (Recommended)
Periodic background sync every 5-15 minutes:
```bash
# Add to crontab
crontab -e

# Sync every 5 minutes
*/5 * * * * /path/to/smooth-linuxcnc/sync_tooltable.sh mill01 >> /var/log/smooth-sync.log 2>&1
```

### Option 3: HAL Integration
Sync on machine startup/shutdown:
```hal
# In postgui.hal
loadusr -w /path/to/sync_tooltable.sh mill01
```

### Option 4: Event-Driven (Advanced - Future)
Python HAL component that syncs on tool changes:
```python
import hal
import subprocess

h = hal.component("smooth-sync")
h.ready()

while True:
    if tool_changed():
        subprocess.run(["/path/to/sync_tooltable.sh", "mill01"])
```

## Configuration

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

## Project Structure

```
smooth-linuxcnc/
├── translator.py              # Low-level parser/generator
├── parse_tooltable.py         # LinuxCNC → Smooth converter
├── export_tooltable.py        # Smooth → LinuxCNC converter
├── sync_tooltable.sh          # Automated sync script
├── sample_tool.tbl            # Sample tool table
├── tests/                     # Test suite
│   ├── test_translator.py     # Parser/generator tests (27)
│   └── test_smooth_conversion.py  # Conversion tests (15+)
├── README.md                  # User documentation
└── DEVELOPMENT.md             # This file
```

## Dependencies

- Python 3.x (usually bundled with LinuxCNC)
- `requests` library for API calls
- `jq` (optional, for JSON formatting)
- Access to running Smooth server

For development/testing:
- pytest
- pytest-cov

## Logging

All sync operations are logged to `$LOG_DIR/sync-{machine_id}-{date}.log`:

```
[2025-10-25 12:00:00] Starting sync for machine: mill01
[2025-10-25 12:00:00] Tool table: /home/user/linuxcnc/configs/mill/tool.tbl
[2025-10-25 12:00:00] Backed up tool table to: /tmp/smooth-sync/tool-mill01-20251025-120000.tbl.bak
[2025-10-25 12:00:01] Parsing tool table...
[2025-10-25 12:00:01] Uploading tool presets to Smooth...
[2025-10-25 12:00:02] Upload successful
[2025-10-25 12:00:02] Downloading tool presets from Smooth...
[2025-10-25 12:00:03] Converting to LinuxCNC format...
[2025-10-25 12:00:03] Tool table has changes, updating...
[2025-10-25 12:00:03] Tool table updated successfully
[2025-10-25 12:00:03] Sync completed successfully
```

## Backup Strategy

The sync script automatically backs up tool tables before any modification:
- Backup location: `$LOG_DIR/tool-{machine_id}-{timestamp}.tbl.bak`
- Backups created before every sync
- Original file preserved on error
- Manual rollback possible from backups

## Round-Trip Conversion

Ensuring data integrity through round-trip:

```
LinuxCNC .tbl → Smooth ToolPreset → LinuxCNC .tbl
```

All tests verify that:
1. Original data is preserved
2. Tool numbers maintained
3. Offsets accurate
4. Comments preserved
5. Pocket numbers retained
6. Format matches LinuxCNC expectations

## Troubleshooting

**Sync fails with "API key not set":**
- Check `~/.config/smooth/linuxcnc.conf` exists
- Verify `SMOOTH_API_KEY` is set
- Ensure no extra whitespace in config file

**Tool table not found:**
- Set `LINUXCNC_INI` to point to your `.ini` file
- Check INI file has `[EMCIO]` section with `TOOL_TABLE` parameter
- Default fallback: `~/linuxcnc/configs/sim/axis/tool.tbl`

**Network errors:**
- Verify Smooth server is running: `curl http://localhost:8000/api/health`
- Check firewall settings
- Ensure API URL is correct in config

**Tool data mismatch:**
- Check unit consistency (mm vs inches in LinuxCNC INI)
- Verify tool table format is correct
- Review sync logs for parsing errors
- Test round-trip conversion separately

**Permission errors:**
- Ensure sync script has execute permission: `chmod +x sync_tooltable.sh`
- Check write permissions on tool table file
- Verify log directory exists and is writable

## Contributing

When contributing to smooth-linuxcnc:
1. Follow TDD - write tests first
2. Ensure round-trip conversion works (LinuxCNC → Smooth → LinuxCNC)
3. Test with real LinuxCNC tool tables
4. Update docstrings for format-specific assumptions
5. Maintain compatibility with LinuxCNC versions
6. Follow functional programming style (see ../DEVELOPMENT.md)
7. Add logging for new operations

## LinuxCNC Version Compatibility

Tested with:
- LinuxCNC 2.8.x
- LinuxCNC 2.9.x

Tool table format is stable across versions, but always test with your specific LinuxCNC installation.

## Production Considerations

- ✅ **Automatic backups** - Script backs up before every sync
- ✅ **Logging** - All operations logged with timestamps
- ✅ **Change detection** - Only updates if tool table changed
- ⚠️ **Conflict resolution** - Currently last-write-wins (use Smooth version API for advanced scenarios)
- ⚠️ **Network resilience** - Add retry logic for production environments
- ⚠️ **Notifications** - Consider adding alerting for sync failures
- ⚠️ **Monitoring** - Set up health checks for cron-based sync
