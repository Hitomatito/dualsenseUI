import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))


@pytest.fixture
def mock_subprocess():
    with patch('dualsense_ui.backend.subprocess.run') as mock:
        mock.return_value = MagicMock(
            returncode=0,
            stdout='ok',
            stderr='',
        )
        yield mock


@pytest.fixture
def device_serial():
    return 'AA:BB:CC:DD:EE:FF'
