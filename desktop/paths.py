"""
desktop/paths.py — Writable data-directory resolution for ZHub.

Works identically in three environments:
  1. Development:  python run_desktop.py          → project root
  2. Built .exe:   ZHub.exe on Windows            → %LOCALAPPDATA%\ZHub
  3. Built app:    ZHub.app on macOS              → ~/Library/Application Support/ZHub
"""
import os
import sys


def get_data_dir():
    """
    Return the absolute path of the directory where ZHub is allowed to
    write files: the SQLite database, QR code images, certificates,
    student photos, and project media.

    In frozen mode (PyInstaller .exe/.app) the project source files live
    inside a read-only extraction archive (sys._MEIPASS). All writable
    output must go to a user-owned directory outside that archive.

    In development mode the project root is writable, so it is used directly,
    which mirrors the existing behaviour of the plain Flask web server.
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller-built executable.
        # Choose a platform-appropriate user data directory.
        if sys.platform == 'win32':
            # Windows: C:\\Users\\<name>\\AppData\\Local\\ZHub
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            # macOS: /Users/<name>/Library/Application Support/ZHub
            base = os.path.expanduser('~/Library/Application Support')
        else:
            # Linux / other UNIX: /home/<name>/.local/share/ZHub
            base = os.path.expanduser('~/.local/share')
        return os.path.join(base, 'ZHub')

    # Development mode: use the project root directory.
    # __file__ is <project_root>/desktop/paths.py so go up one level.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
