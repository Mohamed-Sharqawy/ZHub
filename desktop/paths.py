"""Runtime path resolution for both development and PyInstaller-frozen modes.

In development:
    BASE_DIR  = project root (where app.py lives)
    DATA_DIR  = same as BASE_DIR (so instance/zhub.db works as before)

When frozen (PyInstaller .exe):
    BASE_DIR  = sys._MEIPASS  (temporary bundle extraction, read-only)
    DATA_DIR  = %LOCALAPPDATA%/ZHub  (writable, persists across updates)
"""

import os
import sys


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller bundle."""
    return getattr(sys, 'frozen', False)


def get_base_dir() -> str:
    """Return the directory containing the application source/data.

    - Frozen:  sys._MEIPASS  (PyInstaller extraction directory)
    - Normal:  the project root (parent of this file's package)
    """
    if is_frozen():
        return sys._MEIPASS
    # desktop/ is one level below project root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_data_dir() -> str:
    """Return the writable user-data directory.

    - Frozen:  %LOCALAPPDATA%/ZHub
    - Normal:  project root (existing behavior for development)
    """
    if is_frozen():
        local_app_data = os.environ.get(
            'LOCALAPPDATA',
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local'),
        )
        return os.path.join(local_app_data, 'ZHub')
    return get_base_dir()


def ensure_data_dirs():
    """Create all writable directories needed at runtime."""
    data = get_data_dir()
    dirs = [
        os.path.join(data, 'instance'),
        os.path.join(data, 'data', 'qrcodes'),
        os.path.join(data, 'data', 'certificates'),
        os.path.join(data, 'logs'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
