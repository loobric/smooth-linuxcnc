# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT

"""LinuxCNC tool table format translator.

Parses and generates LinuxCNC tool table files for bidirectional sync.

LinuxCNC tool table format:
T<number> P<pocket> D<diameter> Z<z_offset> [X<x_offset>] [Y<y_offset>] [A<angle>] [B<angle>] [C<angle>] [U<u_offset>] [V<v_offset>] [W<w_offset>] [Q<orientation>] [I<front_angle>] [J<back_angle>] ;<comment>

Reference: http://wiki.linuxcnc.org/cgi-bin/wiki.pl?ToolTable
"""

import re
from typing import Optional


class LinuxCNCToolTableError(Exception):
    """Error parsing or generating LinuxCNC tool table."""
    pass


def parse_tool_table_line(line: str) -> Optional[dict]:
    """Parse a single line from a LinuxCNC tool table.
    
    Args:
        line: A single line from the tool table
        
    Returns:
        Dictionary with tool data, or None if line is blank/comment
        
    Raises:
        LinuxCNCToolTableError: If line format is invalid
    """
    # Strip whitespace
    line = line.strip()
    
    # Skip blank lines
    if not line:
        return None
    
    # Skip comment-only lines
    if line.startswith(";"):
        return None
    
    # Split on semicolon to separate data from comment
    parts = line.split(";", 1)
    data_part = parts[0].strip()
    comment = parts[1].strip() if len(parts) > 1 else ""
    
    # Parse the data part
    result = {
        "tool_number": None,
        "pocket": None,
        "diameter": None,
        "x_offset": None,
        "y_offset": None,
        "z_offset": None,
        "a_angle": None,
        "b_angle": None,
        "c_angle": None,
        "u_offset": None,
        "v_offset": None,
        "w_offset": None,
        "orientation": None,
        "front_angle": None,
        "back_angle": None,
        "comment": comment
    }
    
    # Extract tool number (required)
    # Check if there's a T followed by non-digits (invalid)
    if re.search(r'T[^\d\s]', data_part):
        raise LinuxCNCToolTableError(f"Invalid tool number in line: {line}")
    
    t_match = re.search(r'T(\d+)', data_part)
    if not t_match:
        raise LinuxCNCToolTableError(f"Missing tool number in line: {line}")
    
    result["tool_number"] = int(t_match.group(1))
    
    # Extract pocket (P parameter)
    p_match = re.search(r'P(\d+)', data_part)
    if p_match:
        result["pocket"] = int(p_match.group(1))
    
    # Extract diameter (D parameter, required for most tools)
    d_match = re.search(r'D([+-]?\d+\.?\d*)', data_part)
    if d_match:
        diameter = float(d_match.group(1))
        if diameter < 0:
            raise LinuxCNCToolTableError(f"Diameter must be positive in line: {line}")
        result["diameter"] = diameter
    
    # Extract X offset
    x_match = re.search(r'X([+-]?\d+\.?\d*)', data_part)
    if x_match:
        result["x_offset"] = float(x_match.group(1))
    
    # Extract Y offset
    y_match = re.search(r'Y([+-]?\d+\.?\d*)', data_part)
    if y_match:
        result["y_offset"] = float(y_match.group(1))
    
    # Extract Z offset
    z_match = re.search(r'Z([+-]?\d+\.?\d*)', data_part)
    if z_match:
        result["z_offset"] = float(z_match.group(1))
    
    # Extract A angle
    a_match = re.search(r'A([+-]?\d+\.?\d*)', data_part)
    if a_match:
        result["a_angle"] = float(a_match.group(1))
    
    # Extract B angle
    b_match = re.search(r'B([+-]?\d+\.?\d*)', data_part)
    if b_match:
        result["b_angle"] = float(b_match.group(1))
    
    # Extract C angle
    c_match = re.search(r'C([+-]?\d+\.?\d*)', data_part)
    if c_match:
        result["c_angle"] = float(c_match.group(1))
    
    # Extract U, V, W offsets
    u_match = re.search(r'U([+-]?\d+\.?\d*)', data_part)
    if u_match:
        result["u_offset"] = float(u_match.group(1))
    
    v_match = re.search(r'V([+-]?\d+\.?\d*)', data_part)
    if v_match:
        result["v_offset"] = float(v_match.group(1))
    
    w_match = re.search(r'W([+-]?\d+\.?\d*)', data_part)
    if w_match:
        result["w_offset"] = float(w_match.group(1))
    
    # Extract orientation (Q parameter)
    q_match = re.search(r'Q(\d+)', data_part)
    if q_match:
        result["orientation"] = int(q_match.group(1))
    
    # Extract front and back angles (I, J parameters)
    i_match = re.search(r'I([+-]?\d+\.?\d*)', data_part)
    if i_match:
        result["front_angle"] = float(i_match.group(1))
    
    j_match = re.search(r'J([+-]?\d+\.?\d*)', data_part)
    if j_match:
        result["back_angle"] = float(j_match.group(1))
    
    return result


def parse_tool_table(content: str) -> list[dict]:
    """Parse a complete LinuxCNC tool table file.
    
    Args:
        content: The complete tool table file content
        
    Returns:
        List of tool dictionaries
        
    Raises:
        LinuxCNCToolTableError: If table format is invalid
    """
    tools = []
    tool_numbers_seen = set()
    
    for line_num, line in enumerate(content.split("\n"), 1):
        try:
            tool = parse_tool_table_line(line)
            if tool:
                # Check for duplicate tool numbers
                if tool["tool_number"] in tool_numbers_seen:
                    raise LinuxCNCToolTableError(
                        f"Duplicate tool number T{tool['tool_number']} at line {line_num}"
                    )
                tool_numbers_seen.add(tool["tool_number"])
                tools.append(tool)
        except LinuxCNCToolTableError as e:
            raise LinuxCNCToolTableError(f"Error at line {line_num}: {e}")
    
    return tools


def generate_tool_table_line(tool: dict) -> str:
    """Generate a single LinuxCNC tool table line.
    
    Args:
        tool: Dictionary with tool data
        
    Returns:
        Formatted tool table line
    """
    parts = []
    
    # Tool number (required)
    parts.append(f"T{tool['tool_number']}")
    
    # Pocket
    pocket = tool.get("pocket", 0)
    parts.append(f"P{pocket}")
    
    # Diameter (format with sign)
    if tool.get("diameter") is not None:
        diameter = tool["diameter"]
        sign = "+" if diameter >= 0 else ""
        parts.append(f"D{sign}{diameter:.6f}")
    
    # X offset
    if tool.get("x_offset") is not None:
        x = tool["x_offset"]
        sign = "+" if x >= 0 else ""
        parts.append(f"X{sign}{x:.6f}")
    
    # Y offset
    if tool.get("y_offset") is not None:
        y = tool["y_offset"]
        sign = "+" if y >= 0 else ""
        parts.append(f"Y{sign}{y:.6f}")
    
    # Z offset
    if tool.get("z_offset") is not None:
        z = tool["z_offset"]
        sign = "+" if z >= 0 else ""
        parts.append(f"Z{sign}{z:.6f}")
    
    # Angles A, B, C
    if tool.get("a_angle") is not None:
        a = tool["a_angle"]
        sign = "+" if a >= 0 else ""
        parts.append(f"A{sign}{a:.6f}")
    
    if tool.get("b_angle") is not None:
        b = tool["b_angle"]
        sign = "+" if b >= 0 else ""
        parts.append(f"B{sign}{b:.6f}")
    
    if tool.get("c_angle") is not None:
        c = tool["c_angle"]
        sign = "+" if c >= 0 else ""
        parts.append(f"C{sign}{c:.6f}")
    
    # U, V, W offsets
    if tool.get("u_offset") is not None:
        u = tool["u_offset"]
        sign = "+" if u >= 0 else ""
        parts.append(f"U{sign}{u:.6f}")
    
    if tool.get("v_offset") is not None:
        v = tool["v_offset"]
        sign = "+" if v >= 0 else ""
        parts.append(f"V{sign}{v:.6f}")
    
    if tool.get("w_offset") is not None:
        w = tool["w_offset"]
        sign = "+" if w >= 0 else ""
        parts.append(f"W{sign}{w:.6f}")
    
    # Orientation
    if tool.get("orientation") is not None:
        parts.append(f"Q{tool['orientation']}")
    
    # Front and back angles
    if tool.get("front_angle") is not None:
        i = tool["front_angle"]
        sign = "+" if i >= 0 else ""
        parts.append(f"I{sign}{i:.6f}")
    
    if tool.get("back_angle") is not None:
        j = tool["back_angle"]
        sign = "+" if j >= 0 else ""
        parts.append(f"J{sign}{j:.6f}")
    
    # Join parts
    line = " ".join(parts)
    
    # Add comment if present
    if tool.get("comment"):
        line += f" ;{tool['comment']}"
    
    return line


def generate_tool_table(tools: list[dict]) -> str:
    """Generate a complete LinuxCNC tool table file.
    
    Args:
        tools: List of tool dictionaries
        
    Returns:
        Formatted tool table content
    """
    if not tools:
        return ""
    
    # Sort by tool number
    sorted_tools = sorted(tools, key=lambda t: t["tool_number"])
    
    lines = [generate_tool_table_line(tool) for tool in sorted_tools]
    return "\n".join(lines)
