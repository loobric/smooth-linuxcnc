# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT

"""LinuxCNC tool table import/export API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Annotated

from smooth.database.schema import ToolPreset, User
from smooth.api.auth import get_db, require_auth
from clients.linuxcnc.translator import (
    parse_tool_table,
    generate_tool_table,
    LinuxCNCToolTableError
)
from smooth.audit import create_audit_log

router = APIRouter(prefix="/api/v1/linuxcnc", tags=["linuxcnc"])


@router.post("/import")
async def import_tool_table(
    file: UploadFile = File(...),
    machine_id: str = "default",
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Import LinuxCNC tool table file.
    
    Creates or updates ToolPresets based on the tool table.
    Matches tools by tool_number for the given machine_id.
    
    Args:
        file: Uploaded tool table file
        machine_id: Machine identifier (default: "default")
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Summary of import operation
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse tool table
        tools = parse_tool_table(content_str)
        
        if not tools:
            raise HTTPException(status_code=400, detail="Tool table is empty")
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for tool in tools:
            try:
                tool_number = tool["tool_number"]
                
                # Check if preset already exists for this machine/tool_number
                existing = db.query(ToolPreset).filter(
                    ToolPreset.user_id == current_user.id,
                    ToolPreset.machine_id == machine_id,
                    ToolPreset.tool_number == tool_number
                ).first()
                
                # Build offsets JSON
                offsets = {}
                if tool.get("z_offset") is not None:
                    offsets["length"] = {
                        "geometry": tool["z_offset"],
                        "wear": 0.0,
                        "total": tool["z_offset"]
                    }
                if tool.get("diameter") is not None:
                    offsets["diameter"] = {
                        "geometry": tool["diameter"],
                        "wear": 0.0,
                        "total": tool["diameter"]
                    }
                
                # Build orientation JSON
                orientation = {}
                if tool.get("orientation") is not None:
                    orientation["orientation"] = tool["orientation"]
                
                # Build limits JSON (empty for now)
                limits = {}
                
                if existing:
                    # Update existing preset
                    existing.pocket = tool.get("pocket")
                    existing.offsets = offsets if offsets else None
                    existing.orientation = orientation if orientation else None
                    existing.updated_by = current_user.id
                    existing.version += 1
                    
                    create_audit_log(
                        session=db,
                        user_id=current_user.id,
                        operation="UPDATE",
                        entity_type="ToolPreset",
                        entity_id=existing.id,
                        changes={"source": "linuxcnc_import"},
                        result="success"
                    )
                    updated_count += 1
                else:
                    # Create new preset
                    from uuid import uuid4
                    new_preset = ToolPreset(
                        id=str(uuid4()),
                        user_id=current_user.id,
                        machine_id=machine_id,
                        tool_number=tool_number,
                        instance_id=None,  # No instance mapping yet
                        pocket=tool.get("pocket"),
                        offsets=offsets if offsets else None,
                        orientation=orientation if orientation else None,
                        limits=limits if limits else None,
                        created_by=current_user.id,
                        updated_by=current_user.id
                    )
                    db.add(new_preset)
                    
                    create_audit_log(
                        session=db,
                        user_id=current_user.id,
                        operation="CREATE",
                        entity_type="ToolPreset",
                        entity_id=new_preset.id,
                        changes={"source": "linuxcnc_import"},
                        result="success"
                    )
                    created_count += 1
                    
            except Exception as e:
                errors.append({
                    "tool_number": tool.get("tool_number"),
                    "error": str(e)
                })
        
        db.commit()
        
        return {
            "success": True,
            "machine_id": machine_id,
            "created_count": created_count,
            "updated_count": updated_count,
            "total_tools": len(tools),
            "errors": errors
        }
        
    except LinuxCNCToolTableError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tool table format: {str(e)}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/export", response_class=PlainTextResponse)
async def export_tool_table(
    machine_id: str = "default",
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Export ToolPresets to LinuxCNC tool table format.
    
    Args:
        machine_id: Machine identifier (default: "default")
        current_user: Authenticated user
        db: Database session
        
    Returns:
        LinuxCNC tool table as plain text
    """
    try:
        # Get all presets for this machine
        presets = db.query(ToolPreset).filter(
            ToolPreset.user_id == current_user.id,
            ToolPreset.machine_id == machine_id
        ).order_by(ToolPreset.tool_number).all()
        
        if not presets:
            raise HTTPException(
                status_code=404,
                detail=f"No tool presets found for machine '{machine_id}'"
            )
        
        # Convert presets to LinuxCNC format
        tools = []
        for preset in presets:
            tool = {
                "tool_number": preset.tool_number,
                "pocket": preset.pocket if preset.pocket else 0,
            }
            
            # Extract diameter and Z offset from offsets JSON
            if preset.offsets:
                if "diameter" in preset.offsets:
                    diameter_data = preset.offsets["diameter"]
                    if isinstance(diameter_data, dict):
                        tool["diameter"] = diameter_data.get("total") or diameter_data.get("geometry")
                    else:
                        tool["diameter"] = diameter_data
                
                if "length" in preset.offsets:
                    length_data = preset.offsets["length"]
                    if isinstance(length_data, dict):
                        tool["z_offset"] = length_data.get("total") or length_data.get("geometry")
                    else:
                        tool["z_offset"] = length_data
            
            # Add orientation if present
            if preset.orientation and "orientation" in preset.orientation:
                tool["orientation"] = preset.orientation["orientation"]
            
            # Use instance_id as comment if available, otherwise use T-number
            if preset.instance_id:
                tool["comment"] = f"Instance: {preset.instance_id[:8]}"
            else:
                tool["comment"] = f"Tool {preset.tool_number}"
            
            tools.append(tool)
        
        # Generate tool table
        tool_table = generate_tool_table(tools)
        
        # Log export
        create_audit_log(
            session=db,
            user_id=current_user.id,
            operation="EXPORT",
            entity_type="ToolPreset",
            entity_id=machine_id,
            changes={"tool_count": len(tools), "source": "linuxcnc_export"},
            result="success"
        )
        db.commit()
        
        return tool_table
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
