import pytest
import tempfile
import os
from smooth_linuxcnc.config import read_smooth_config

def test_read_smooth_config():
    """Test reading SMOOTH section from .ini file."""
    # Test with valid config
    ini_content = """[SMOOTH]
URL=https://api.loobric.com
TOKEN=abc123
MACHINE_ID=123
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmpfile:
        tmpfile.write(ini_content)
        ini_path = tmpfile.name
    
    try:
        config = read_smooth_config(ini_path)
        assert config['URL'] == "https://api.loobric.com"
        assert config['TOKEN'] == "abc123"
        assert config['MACHINE_ID'] == "123"
    finally:
        os.remove(ini_path)

def test_missing_smooth_section():
    """Test handling of missing SMOOTH section."""
    ini_content = "[OTHER_SECTION]\nKEY=value\n"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmpfile:
        tmpfile.write(ini_content)
        ini_path = tmpfile.name
    
    try:
        with pytest.raises(KeyError, match="No \[SMOOTH\] section found"):
            read_smooth_config(ini_path)
    finally:
        os.remove(ini_path)

def test_empty_smooth_section():
    """Test handling of empty SMOOTH section."""
    ini_content = "[SMOOTH]\n"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmpfile:
        tmpfile.write(ini_content)
        ini_path = tmpfile.name
    
    try:
        config = read_smooth_config(ini_path)
        assert config == {}
    finally:
        os.remove(ini_path)

def test_special_characters():
    """Test handling of special characters in values."""
    special_token = "abc123!@#$%^&*()_+-=[]{}|;:,.<>?"
    ini_content = f"""[SMOOTH]
URL=https://api.loobric.com
TOKEN={special_token}
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmpfile:
        tmpfile.write(ini_content)
        ini_path = tmpfile.name
    
    try:
        config = read_smooth_config(ini_path)
        assert config['TOKEN'] == special_token
    finally:
        os.remove(ini_path)
