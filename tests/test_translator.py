# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT

"""Tests for LinuxCNC tool table translator.

LinuxCNC tool table format:
T<number> P<pocket> D<diameter> Z<z_offset> [X<x_offset>] [Y<y_offset>] [A<angle>] [B<angle>] [C<angle>] [U<u_offset>] [V<v_offset>] [W<w_offset>] [Q<orientation>] [I<front_angle>] [J<back_angle>] ;<comment>

Reference: http://wiki.linuxcnc.org/cgi-bin/wiki.pl?ToolTable
"""

import pytest
from clients.linuxcnc.translator import (
    parse_tool_table_line,
    parse_tool_table,
    generate_tool_table_line,
    generate_tool_table,
    LinuxCNCToolTableError
)


class TestParseToolTableLine:
    """Test parsing individual LinuxCNC tool table lines."""
    
    def test_parse_simple_tool(self):
        """Test parsing a basic tool with T, P, D, Z."""
        line = "T1 P0 D+2.997200 Z-41.031000 ;Probe"
        result = parse_tool_table_line(line)
        
        assert result["tool_number"] == 1
        assert result["pocket"] == 0
        assert result["diameter"] == 2.997200
        assert result["z_offset"] == -41.031000
        assert result["comment"] == "Probe"
    
    def test_parse_tool_diameter_only(self):
        """Test parsing tool with only diameter."""
        line = "T20 P0 D+1.000000 ;Drill"
        result = parse_tool_table_line(line)
        
        assert result["tool_number"] == 20
        assert result["pocket"] == 0
        assert result["diameter"] == 1.000000
        assert result["z_offset"] is None
        assert result["comment"] == "Drill"
    
    def test_parse_tool_no_comment(self):
        """Test parsing tool without comment."""
        line = "T5 P0 D+11.112500 Z-34.227900"
        result = parse_tool_table_line(line)
        
        assert result["tool_number"] == 5
        assert result["diameter"] == 11.112500
        assert result["z_offset"] == -34.227900
        assert result["comment"] == ""
    
    def test_parse_tool_with_spaces(self):
        """Test parsing with various spacing."""
        line = "T3   P0   D+3.175000 Z-48.107441 ;1/8\" 2 Flute"
        result = parse_tool_table_line(line)
        
        assert result["tool_number"] == 3
        assert result["comment"] == '1/8" 2 Flute'
    
    def test_parse_blank_line(self):
        """Test that blank lines return None."""
        assert parse_tool_table_line("") is None
        assert parse_tool_table_line("   ") is None
        assert parse_tool_table_line("\n") is None
    
    def test_parse_comment_line(self):
        """Test that comment-only lines return None."""
        assert parse_tool_table_line(";This is a comment") is None
    
    def test_parse_invalid_tool_number(self):
        """Test error on invalid tool number."""
        with pytest.raises(LinuxCNCToolTableError, match="Invalid tool number"):
            parse_tool_table_line("TABC P0 D+1.0")
    
    def test_parse_missing_tool_number(self):
        """Test error on missing tool number."""
        with pytest.raises(LinuxCNCToolTableError, match="Missing tool number"):
            parse_tool_table_line("P0 D+1.0")
    
    def test_parse_negative_diameter(self):
        """Test that negative diameters are rejected."""
        with pytest.raises(LinuxCNCToolTableError, match="Diameter must be positive"):
            parse_tool_table_line("T1 P0 D-5.0")
    
    def test_parse_tool_with_all_offsets(self):
        """Test parsing tool with X, Y, Z offsets."""
        line = "T1 P0 D+10.0 X+1.5 Y-2.3 Z-50.0 ;Complete offsets"
        result = parse_tool_table_line(line)
        
        assert result["tool_number"] == 1
        assert result["diameter"] == 10.0
        assert result["x_offset"] == 1.5
        assert result["y_offset"] == -2.3
        assert result["z_offset"] == -50.0


class TestParseToolTable:
    """Test parsing complete LinuxCNC tool tables."""
    
    def test_parse_multiple_tools(self):
        """Test parsing a complete tool table."""
        table = """
T1   P0   D+2.997200 ;Probe 
T2   P0   D+3.175000 Z-41.031000 ;Spot Drill 
T3   P0   D+3.175000 Z-48.107441 ;1/8" 2 Flute 
"""
        tools = parse_tool_table(table)
        
        assert len(tools) == 3
        assert tools[0]["tool_number"] == 1
        assert tools[1]["tool_number"] == 2
        assert tools[2]["tool_number"] == 3
    
    def test_parse_with_blank_lines(self):
        """Test parsing table with blank lines."""
        table = """
T1 P0 D+2.0 ;Tool 1

T2 P0 D+3.0 ;Tool 2

"""
        tools = parse_tool_table(table)
        assert len(tools) == 2
    
    def test_parse_empty_table(self):
        """Test parsing empty table."""
        assert parse_tool_table("") == []
        assert parse_tool_table("\n\n") == []
    
    def test_parse_duplicate_tool_numbers(self):
        """Test that duplicate tool numbers raise error."""
        table = """
T1 P0 D+2.0 ;First
T1 P0 D+3.0 ;Duplicate
"""
        with pytest.raises(LinuxCNCToolTableError, match="Duplicate tool number"):
            parse_tool_table(table)


class TestGenerateToolTableLine:
    """Test generating LinuxCNC tool table lines."""
    
    def test_generate_simple_line(self):
        """Test generating basic tool line."""
        tool = {
            "tool_number": 1,
            "pocket": 0,
            "diameter": 2.997200,
            "z_offset": -41.031000,
            "comment": "Probe"
        }
        line = generate_tool_table_line(tool)
        assert line == "T1 P0 D+2.997200 Z-41.031000 ;Probe"
    
    def test_generate_diameter_only(self):
        """Test generating line with only diameter."""
        tool = {
            "tool_number": 20,
            "pocket": 0,
            "diameter": 1.0,
            "comment": "Drill"
        }
        line = generate_tool_table_line(tool)
        assert line == "T20 P0 D+1.000000 ;Drill"
    
    def test_generate_no_comment(self):
        """Test generating line without comment."""
        tool = {
            "tool_number": 5,
            "pocket": 0,
            "diameter": 11.112500,
            "z_offset": -34.227900
        }
        line = generate_tool_table_line(tool)
        assert line == "T5 P0 D+11.112500 Z-34.227900"
    
    def test_generate_with_all_offsets(self):
        """Test generating line with X, Y, Z offsets."""
        tool = {
            "tool_number": 1,
            "pocket": 0,
            "diameter": 10.0,
            "x_offset": 1.5,
            "y_offset": -2.3,
            "z_offset": -50.0,
            "comment": "Complete"
        }
        line = generate_tool_table_line(tool)
        assert "X+1.500000" in line
        assert "Y-2.300000" in line
        assert "Z-50.000000" in line


class TestGenerateToolTable:
    """Test generating complete LinuxCNC tool tables."""
    
    def test_generate_multiple_tools(self):
        """Test generating complete tool table."""
        tools = [
            {"tool_number": 1, "pocket": 0, "diameter": 2.0, "comment": "Tool 1"},
            {"tool_number": 2, "pocket": 0, "diameter": 3.0, "z_offset": -40.0, "comment": "Tool 2"},
            {"tool_number": 3, "pocket": 0, "diameter": 4.0, "comment": "Tool 3"}
        ]
        table = generate_tool_table(tools)
        
        lines = table.strip().split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("T1 ")
        assert lines[1].startswith("T2 ")
        assert lines[2].startswith("T3 ")
    
    def test_generate_empty_table(self):
        """Test generating empty table."""
        assert generate_tool_table([]) == ""
    
    def test_generate_sorts_by_tool_number(self):
        """Test that tools are sorted by tool number."""
        tools = [
            {"tool_number": 5, "pocket": 0, "diameter": 2.0},
            {"tool_number": 1, "pocket": 0, "diameter": 3.0},
            {"tool_number": 3, "pocket": 0, "diameter": 4.0}
        ]
        table = generate_tool_table(tools)
        lines = table.strip().split("\n")
        
        assert lines[0].startswith("T1 ")
        assert lines[1].startswith("T3 ")
        assert lines[2].startswith("T5 ")


class TestRoundTripConversion:
    """Test that parsing and generating are inverse operations."""
    
    def test_round_trip_simple(self):
        """Test round-trip conversion of simple tools."""
        original = """T1 P0 D+2.997200 ;Probe
T2 P0 D+3.175000 Z-41.031000 ;Spot Drill
T3 P0 D+6.350000 Z-21.642200 ;1/4" 2 Flute"""
        
        tools = parse_tool_table(original)
        regenerated = generate_tool_table(tools)
        
        # Parse again to compare data structures
        tools_original = parse_tool_table(original)
        tools_regenerated = parse_tool_table(regenerated)
        
        assert len(tools_original) == len(tools_regenerated)
        for orig, regen in zip(tools_original, tools_regenerated):
            assert orig["tool_number"] == regen["tool_number"]
            assert orig["diameter"] == pytest.approx(regen["diameter"])
            if orig.get("z_offset"):
                assert orig["z_offset"] == pytest.approx(regen["z_offset"])
    
    def test_round_trip_preserves_comments(self):
        """Test that comments are preserved through round-trip."""
        original = "T1 P0 D+10.0 ;This is a test comment"
        tools = parse_tool_table(original)
        regenerated = generate_tool_table(tools)
        
        assert "This is a test comment" in regenerated
