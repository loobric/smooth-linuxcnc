import pytest
import tempfile
import os
from smooth_linuxcnc.gui import on_sync_button_press  # This will fail until implemented

def test_on_sync_button_press():
    """Test the sync button press function reads config and calls sync."""
    ini_content = "[SMOOTH]\nURL=https://api.loobric.com\nTOKEN=abc123\n"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmpfile:
        tmpfile.write(ini_content)
        ini_path = tmpfile.name
    
    # Mock the sync call to verify it's called with correct arguments
    with pytest.mock.patch('smooth_linuxcnc.sync.sync_tools') as mock_sync:
        on_sync_button_press(ini_path)
        mock_sync.assert_called_once_with("https://api.loobric.com", "abc123")
    
    os.remove(ini_path)
