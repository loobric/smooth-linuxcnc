import pytest
import tempfile
import os
from smooth_linuxcnc.examples.sim.axis.smooth.smooth_handler import on_button_press, backup_tool_table, pull_tool_table

def test_on_button_press():
    """Test the sync button press function reads config and calls sync."""
    ini_content = "[SMOOTH]\nURL=https://api.loobric.com\nTOKEN=abc123\n"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmpfile:
        tmpfile.write(ini_content)
        ini_path = tmpfile.name
    
    # Mock the sync call to verify it's called with correct arguments
    with pytest.mock.patch('smooth_linuxcnc.sync.sync_tools') as mock_sync:
        on_button_press(ini_path)
        mock_sync.assert_called_once_with("https://api.loobric.com", "abc123")
    
    os.remove(ini_path)

def test_backup_tool_table():
    """Test backup_tool_table function.

    Assumptions:
    - backup_tool_table function exists and takes url, token, and tool_table_path as arguments.
    - It sends a POST request to {url}/api/tooltable with the tool table file content using multipart/form-data.
    - Returns True if the request is successful (status code 200), False otherwise.
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.tbl') as tmpfile:
        tmpfile.write("tool data content")
        tmpfile_path = tmpfile.name
    
    with pytest.mock.patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        result = backup_tool_table("https://test.com", "test_token", tmpfile_path)
        assert result == True
        mock_post.assert_called_once_with("https://test.com/api/tooltable", files={'tooltable': open(tmpfile_path, 'rb')}, headers={'Authorization': 'Bearer test_token'})
    
    os.remove(tmpfile_path)

def test_pull_tool_table():
    """Test pull_tool_table function.

    Assumptions:
    - pull_tool_table function exists and takes url, token, and local_path as arguments.
    - It sends a GET request to {url}/api/tooltable with Authorization header.
    - Writes the response content to local_path if status code 200.
    - Returns True if successful, False otherwise.
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmpfile:
        local_path = tmpfile.name
    
    with pytest.mock.patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"tool data content"
        result = pull_tool_table("https://test.com", "test_token", local_path)
        assert result == True
        mock_get.assert_called_once_with("https://test.com/api/tooltable", headers={'Authorization': 'Bearer test_token'})
        with open(local_path, 'rb') as f:
            assert f.read() == b"tool data content"
    
    os.remove(local_path)
