"""
run_desktop.py — Launch ZHub as a desktop window without building an .exe.

Run from the project root:
    python run_desktop.py

Requirements: all packages in requirements.txt must be installed.
No PyInstaller build is needed. Uses your current Python environment.
The application data (database, QR codes, etc.) will be stored in the
project root directory, identical to running the plain Flask web server.
"""
import sys
import os

# Guarantee the project root is importable regardless of the working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop.main import main

if __name__ == '__main__':
    main()
