#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT

"""LinuxCNC Tool Table Parser

Parses LinuxCNC tool table (.tbl) files and converts to Smooth ToolPreset format.

LinuxCNC tool table format:
T1 P1 D5.000 Z50.000 X0.000 Y0.000 ;5mm Drill HSS
T2 P2 D6.000 Z60.000 X0.000 Y0.000 ;6mm Endmill Carbide
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Import existing translator
try:
    from translator import parse_tool_table
except ImportError:
    from clients.linuxcnc.translator import parse_tool_table

def convert_to_smooth_preset(tool_data: Dict[str, Any], machine_id: str) -> Dict[str, Any]:
    """Convert LinuxCNC tool data to Smooth ToolPreset format.
    
    Args:
        tool_data: Parsed tool data from translator.py
        machine_id: Machine identifier
        
    Returns:
        Dictionary in Smooth ToolPreset format
    """
    preset = {
        "machine_id": machine_id,
        "tool_number": tool_data['tool_number'],
        "description": tool_data.get('comment', f"Tool {tool_data['tool_number']}"),
        "metadata": {
            "source": "linuxcnc"
        }
    }
    
    # Add pocket if present
    if tool_data.get('pocket') is not None:
        preset['pocket'] = tool_data['pocket']
    
    # Build offsets
    offsets = {}
    if tool_data.get('z_offset') is not None:
        offsets['z'] = tool_data['z_offset']
        offsets['z_unit'] = 'mm'
    if tool_data.get('x_offset') is not None:
        offsets['x'] = tool_data['x_offset']
        offsets['x_unit'] = 'mm'
    if tool_data.get('y_offset') is not None:
        offsets['y'] = tool_data['y_offset']
        offsets['y_unit'] = 'mm'
    if tool_data.get('u_offset') is not None:
        offsets['u'] = tool_data['u_offset']
        offsets['u_unit'] = 'mm'
    if tool_data.get('v_offset') is not None:
        offsets['v'] = tool_data['v_offset']
        offsets['v_unit'] = 'mm'
    if tool_data.get('w_offset') is not None:
        offsets['w'] = tool_data['w_offset']
        offsets['w_unit'] = 'mm'
    
    if offsets:
        preset['offsets'] = offsets
    
    # Build orientation
    orientation = {}
    if tool_data.get('orientation') is not None:
        orientation['type'] = tool_data['orientation']
    if tool_data.get('front_angle') is not None:
        orientation['front_angle'] = tool_data['front_angle']
    if tool_data.get('back_angle') is not None:
        orientation['back_angle'] = tool_data['back_angle']
    
    if orientation:
        preset['orientation'] = orientation
    
    # Store diameter in metadata (should eventually link to ToolItem)
    # TODO: Find or create ToolItem with this diameter
    if tool_data.get('diameter') is not None:
        preset['metadata']['diameter'] = tool_data['diameter']
        preset['metadata']['diameter_unit'] = 'mm'
    
    # Store all LinuxCNC-specific data for round-trip
    preset['metadata']['linuxcnc_data'] = {
        k: v for k, v in tool_data.items() 
        if v is not None and k not in ['comment']
    }
    
    return preset


def parse_tooltable(file_path: str, machine_id: str) -> List[Dict[str, Any]]:
    """Parse LinuxCNC tool table file.
    
    Args:
        file_path: Path to .tbl file
        machine_id: Machine identifier
        
    Returns:
        List of ToolPreset dictionaries
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Use existing translator to parse
    tools = parse_tool_table(content)
    
    # Convert to Smooth ToolPresets
    presets = [convert_to_smooth_preset(tool, machine_id) for tool in tools]
    
    return presets


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: parse_tooltable.py <tool_table_file> <machine_id>", file=sys.stderr)
        sys.exit(1)
    
    tool_table_file = sys.argv[1]
    machine_id = sys.argv[2]
    
    try:
        presets = parse_tooltable(tool_table_file, machine_id)
        
        # Output as bulk request format
        output = {
            "items": presets
        }
        
        print(json.dumps(output, indent=2))
        
    except FileNotFoundError:
        print(f"Error: Tool table file not found: {tool_table_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing tool table: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
