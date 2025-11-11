"""Configuration handling for smooth-linuxcnc integration."""
import configparser
from typing import Dict, Optional

def read_smooth_config(ini_path: str) -> Dict[str, str]:
    """Read SMOOTH section from LinuxCNC INI file.
    
    Args:
        ini_path: Path to the LinuxCNC INI file
        
    Returns:
        Dict containing the configuration from the SMOOTH section
        
    Raises:
        configparser.Error: If there's an error reading the INI file
        KeyError: If the SMOOTH section is missing
    """
    config = configparser.ConfigParser()
    config.read(ini_path)
    
    if 'SMOOTH' not in config:
        raise KeyError("No [SMOOTH] section found in INI file")
        
    return dict(config['SMOOTH'])
