# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT

"""Tests for Smooth format conversion (parse_tooltable.py and export_tooltable.py).

Tests conversion between LinuxCNC tool table format and Smooth ToolPreset format.
"""

import pytest
import json
from pathlib import Path
from clients.linuxcnc.parse_tooltable import parse_tooltable, convert_to_smooth_preset
from clients.linuxcnc.export_tooltable import export_tooltable, convert_to_linuxcnc_tool


class TestConvertToSmoothPreset:
    """Test conversion from LinuxCNC tool dict to Smooth ToolPreset."""
    
    def test_basic_conversion(self):
        """Test basic tool conversion."""
        tool = {
            'tool_number': 1,
            'pocket': 0,
            'diameter': 5.0,
            'z_offset': -50.0,
            'comment': '5mm Drill'
        }
        
        preset = convert_to_smooth_preset(tool, 'mill01')
        
        assert preset['machine_id'] == 'mill01'
        assert preset['tool_number'] == 1
        assert preset['pocket'] == 0
        assert preset['description'] == '5mm Drill'
        assert preset['offsets']['z'] == -50.0
        assert preset['offsets']['z_unit'] == 'mm'
        assert preset['metadata']['diameter'] == 5.0
        assert preset['metadata']['diameter_unit'] == 'mm'
    
    def test_all_offsets(self):
        """Test conversion with all offset types."""
        tool = {
            'tool_number': 2,
            'pocket': 2,
            'diameter': 6.0,
            'x_offset': 1.5,
            'y_offset': -2.3,
            'z_offset': -60.0,
            'u_offset': 0.1,
            'v_offset': 0.2,
            'w_offset': 0.3,
            'comment': 'Tool with all offsets'
        }
        
        preset = convert_to_smooth_preset(tool, 'mill01')
        
        assert preset['offsets']['x'] == 1.5
        assert preset['offsets']['y'] == -2.3
        assert preset['offsets']['z'] == -60.0
        assert preset['offsets']['u'] == 0.1
        assert preset['offsets']['v'] == 0.2
        assert preset['offsets']['w'] == 0.3
    
    def test_orientation(self):
        """Test conversion with orientation data."""
        tool = {
            'tool_number': 3,
            'pocket': 3,
            'diameter': 10.0,
            'orientation': 5,
            'front_angle': 45.0,
            'back_angle': 135.0,
            'comment': 'Oriented tool'
        }
        
        preset = convert_to_smooth_preset(tool, 'mill01')
        
        assert preset['orientation']['type'] == 5
        assert preset['orientation']['front_angle'] == 45.0
        assert preset['orientation']['back_angle'] == 135.0
    
    def test_no_comment(self):
        """Test conversion without comment."""
        tool = {
            'tool_number': 10,
            'pocket': 10,
            'diameter': 3.0
        }
        
        preset = convert_to_smooth_preset(tool, 'lathe01')
        
        assert preset['description'] == 'Tool 10'
    
    def test_linuxcnc_data_preserved(self):
        """Test that LinuxCNC-specific data is preserved for round-trip."""
        tool = {
            'tool_number': 5,
            'pocket': 5,
            'diameter': 8.0,
            'z_offset': -40.0,
            'a_angle': 10.0,
            'b_angle': 20.0,
            'c_angle': 30.0,
            'comment': 'Complex tool'
        }
        
        preset = convert_to_smooth_preset(tool, 'mill01')
        
        # Check that all data is in metadata
        linuxcnc_data = preset['metadata']['linuxcnc_data']
        assert linuxcnc_data['tool_number'] == 5
        assert linuxcnc_data['a_angle'] == 10.0
        assert linuxcnc_data['b_angle'] == 20.0
        assert linuxcnc_data['c_angle'] == 30.0


class TestConvertToLinuxCNCTool:
    """Test conversion from Smooth ToolPreset to LinuxCNC tool dict."""
    
    def test_basic_conversion(self):
        """Test basic preset conversion."""
        preset = {
            'machine_id': 'mill01',
            'tool_number': 1,
            'pocket': 0,
            'description': '5mm Drill',
            'offsets': {
                'z': -50.0,
                'z_unit': 'mm'
            },
            'metadata': {
                'source': 'linuxcnc',
                'diameter': 5.0,
                'diameter_unit': 'mm'
            }
        }
        
        tool = convert_to_linuxcnc_tool(preset)
        
        assert tool['tool_number'] == 1
        assert tool['pocket'] == 0
        assert tool['comment'] == '5mm Drill'
        assert tool['diameter'] == 5.0
        assert tool['z_offset'] == -50.0
    
    def test_unit_conversion_imperial(self):
        """Test conversion from imperial units."""
        preset = {
            'tool_number': 2,
            'description': '1/4 inch drill',
            'offsets': {
                'z': 2.0,
                'z_unit': 'in'
            },
            'metadata': {
                'diameter': 0.25,
                'diameter_unit': 'in'
            }
        }
        
        tool = convert_to_linuxcnc_tool(preset)
        
        # Should be converted to mm
        assert tool['diameter'] == pytest.approx(6.35, rel=0.01)
        assert tool['z_offset'] == pytest.approx(50.8, rel=0.01)
    
    def test_all_offsets(self):
        """Test conversion with all offset types."""
        preset = {
            'tool_number': 3,
            'description': 'Complex tool',
            'offsets': {
                'x': 1.5, 'x_unit': 'mm',
                'y': -2.3, 'y_unit': 'mm',
                'z': -60.0, 'z_unit': 'mm',
                'u': 0.1, 'u_unit': 'mm',
                'v': 0.2, 'v_unit': 'mm',
                'w': 0.3, 'w_unit': 'mm'
            },
            'metadata': {'diameter': 6.0, 'diameter_unit': 'mm'}
        }
        
        tool = convert_to_linuxcnc_tool(preset)
        
        assert tool['x_offset'] == 1.5
        assert tool['y_offset'] == -2.3
        assert tool['z_offset'] == -60.0
        assert tool['u_offset'] == 0.1
        assert tool['v_offset'] == 0.2
        assert tool['w_offset'] == 0.3
    
    def test_orientation(self):
        """Test conversion with orientation."""
        preset = {
            'tool_number': 4,
            'description': 'Oriented tool',
            'orientation': {
                'type': 5,
                'front_angle': 45.0,
                'back_angle': 135.0
            },
            'metadata': {'diameter': 10.0, 'diameter_unit': 'mm'}
        }
        
        tool = convert_to_linuxcnc_tool(preset)
        
        assert tool['orientation'] == 5
        assert tool['front_angle'] == 45.0
        assert tool['back_angle'] == 135.0
    
    def test_round_trip_data_restoration(self):
        """Test that LinuxCNC data is restored from metadata."""
        preset = {
            'tool_number': 5,
            'description': 'Round-trip tool',
            'offsets': {'z': -40.0, 'z_unit': 'mm'},
            'metadata': {
                'diameter': 8.0,
                'diameter_unit': 'mm',
                'linuxcnc_data': {
                    'tool_number': 5,
                    'a_angle': 10.0,
                    'b_angle': 20.0,
                    'c_angle': 30.0
                }
            }
        }
        
        tool = convert_to_linuxcnc_tool(preset)
        
        # LinuxCNC-specific data should be restored
        assert tool['a_angle'] == 10.0
        assert tool['b_angle'] == 20.0
        assert tool['c_angle'] == 30.0


class TestParseTooltable:
    """Test parsing complete tool table files."""
    
    def test_parse_simple_table(self, tmp_path):
        """Test parsing simple tool table."""
        table_content = """T1 P0 D+5.000000 Z-50.000000 ;5mm Drill
T2 P0 D+6.000000 Z-60.000000 ;6mm Endmill
T3 P0 D+3.000000 ;3mm Probe"""
        
        table_file = tmp_path / "tools.tbl"
        table_file.write_text(table_content)
        
        presets = parse_tooltable(str(table_file), 'mill01')
        
        assert len(presets) == 3
        assert presets[0]['tool_number'] == 1
        assert presets[0]['description'] == '5mm Drill'
        assert presets[0]['machine_id'] == 'mill01'
        assert presets[1]['tool_number'] == 2
        assert presets[2]['tool_number'] == 3


class TestExportTooltable:
    """Test exporting to LinuxCNC tool table format."""
    
    def test_export_simple_presets(self):
        """Test exporting simple presets."""
        presets = [
            {
                'tool_number': 1,
                'pocket': 0,
                'description': '5mm Drill',
                'offsets': {'z': -50.0, 'z_unit': 'mm'},
                'metadata': {'diameter': 5.0, 'diameter_unit': 'mm'}
            },
            {
                'tool_number': 2,
                'pocket': 0,
                'description': '6mm Endmill',
                'offsets': {'z': -60.0, 'z_unit': 'mm'},
                'metadata': {'diameter': 6.0, 'diameter_unit': 'mm'}
            }
        ]
        
        table = export_tooltable(presets)
        
        assert 'T1 P0' in table
        assert 'T2 P0' in table
        assert '5mm Drill' in table
        assert '6mm Endmill' in table
        assert 'D+5.000000' in table
        assert 'Z-50.000000' in table


class TestRoundTrip:
    """Test round-trip conversion LinuxCNC -> Smooth -> LinuxCNC."""
    
    def test_round_trip_simple(self, tmp_path):
        """Test that data survives round-trip conversion."""
        original_content = """T1 P0 D+5.000000 Z-50.000000 ;5mm Drill
T2 P0 D+6.000000 Z-60.000000 X+1.500000 ;6mm Endmill
T3 P0 D+3.000000 ;Probe"""
        
        table_file = tmp_path / "original.tbl"
        table_file.write_text(original_content)
        
        # Parse to Smooth format
        presets = parse_tooltable(str(table_file), 'mill01')
        
        # Export back to LinuxCNC format
        exported_content = export_tooltable(presets)
        
        # Parse both versions and compare
        from clients.linuxcnc.translator import parse_tool_table
        
        original_tools = parse_tool_table(original_content)
        exported_tools = parse_tool_table(exported_content)
        
        assert len(original_tools) == len(exported_tools)
        
        for orig, exp in zip(original_tools, exported_tools):
            assert orig['tool_number'] == exp['tool_number']
            assert orig['diameter'] == pytest.approx(exp['diameter'])
            if orig.get('z_offset'):
                assert orig['z_offset'] == pytest.approx(exp['z_offset'])
            if orig.get('x_offset'):
                assert orig['x_offset'] == pytest.approx(exp['x_offset'])
            assert orig['comment'] == exp['comment']
