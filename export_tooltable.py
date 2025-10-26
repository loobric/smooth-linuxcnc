#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT

"""LinuxCNC Tool Table Exporter

Converts Smooth ToolPreset format to LinuxCNC tool table (.tbl) format.

Output format:
T1 P1 D5.000 Z50.000 X0.000 Y0.000 ;5mm Drill HSS
T2 P2 D6.000 Z60.000 X0.000 Y0.000 ;6mm Endmill Carbide
"""

import sys
import json
from typing import Dict, Any, List

# Import existing translator
try:
    from translator import generate_tool_table
except ImportError:
    from clients.linuxcnc.translator import generate_tool_table


def convert_to_linuxcnc_tool(preset: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Smooth ToolPreset to translator.py tool dict format.
    
    Args:
        preset: ToolPreset dictionary from Smooth
        
    Returns:
        Tool dictionary compatible with translator.py
    """
    tool_number = preset.get('tool_number', 0)
    pocket = preset.get('pocket', tool_number)
    description = preset.get('description', f'Tool {tool_number}')
    
    # Extract offsets
    offsets = preset.get('offsets', {})
    
    # Convert units to mm
    def to_mm(value, unit):
        if unit == 'in':
            return value * 25.4
        return value
    
    tool = {
        'tool_number': tool_number,
        'pocket': pocket,
        'comment': description
    }
    
    # Add diameter from metadata
    metadata = preset.get('metadata', {})
    if 'diameter' in metadata:
        diameter = metadata['diameter']
        diameter_unit = metadata.get('diameter_unit', 'mm')
        tool['diameter'] = to_mm(diameter, diameter_unit)
    
    # Add offsets (convert to mm)
    if offsets.get('z') is not None:
        tool['z_offset'] = to_mm(offsets['z'], offsets.get('z_unit', 'mm'))
    if offsets.get('x') is not None:
        tool['x_offset'] = to_mm(offsets['x'], offsets.get('x_unit', 'mm'))
    if offsets.get('y') is not None:
        tool['y_offset'] = to_mm(offsets['y'], offsets.get('y_unit', 'mm'))
    if offsets.get('u') is not None:
        tool['u_offset'] = to_mm(offsets['u'], offsets.get('u_unit', 'mm'))
    if offsets.get('v') is not None:
        tool['v_offset'] = to_mm(offsets['v'], offsets.get('v_unit', 'mm'))
    if offsets.get('w') is not None:
        tool['w_offset'] = to_mm(offsets['w'], offsets.get('w_unit', 'mm'))
    
    # Add orientation
    orientation = preset.get('orientation', {})
    if 'type' in orientation:
        tool['orientation'] = orientation['type']
    if 'front_angle' in orientation:
        tool['front_angle'] = orientation['front_angle']
    if 'back_angle' in orientation:
        tool['back_angle'] = orientation['back_angle']
    
    # Restore any LinuxCNC-specific data from round-trip
    if 'linuxcnc_data' in metadata:
        linuxcnc_data = metadata['linuxcnc_data']
        for key, value in linuxcnc_data.items():
            if key not in tool and value is not None:
                tool[key] = value
    
    return tool


def export_tooltable(presets: List[Dict[str, Any]]) -> str:
    """Export list of ToolPresets to LinuxCNC tool table format.
    
    Args:
        presets: List of ToolPreset dictionaries
        
    Returns:
        Tool table content as string
    """
    # Convert Smooth presets to translator.py format
    tools = [convert_to_linuxcnc_tool(preset) for preset in presets]
    
    # Use existing translator to generate
    return generate_tool_table(tools)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: export_tooltable.py <presets_json>", file=sys.stderr)
        print("       or: cat presets.json | export_tooltable.py -", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Read JSON from argument or stdin
        if sys.argv[1] == '-':
            presets_json = sys.stdin.read()
        else:
            presets_json = sys.argv[1]
        
        # Parse JSON
        data = json.loads(presets_json)
        
        # Handle both list and dict with 'items' key
        if isinstance(data, list):
            presets = data
        elif isinstance(data, dict) and 'items' in data:
            presets = data['items']
        else:
            presets = [data]
        
        # Export to LinuxCNC format
        tool_table = export_tooltable(presets)
        
        print(tool_table, end='')
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error exporting tool table: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
