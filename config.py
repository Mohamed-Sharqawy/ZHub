import os
import sys

# ---------------------------------------------------------------------------
# Base directory: where the source code / bundled data lives.
# In development this is the project root. When frozen by PyInstaller it is
# sys._MEIPASS (a temporary extraction directory).
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Data directory: writable location for the database and generated files.
# When the desktop launcher sets ZHUB_DATA_DIR (e.g. %LOCALAPPDATA%/ZHub)
# that value is used. Otherwise falls back to BASE_DIR for normal dev use.
# ---------------------------------------------------------------------------
DATA_DIR = os.environ.get('ZHUB_DATA_DIR', BASE_DIR)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'zhub-dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(DATA_DIR, 'instance', 'zhub.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Writable asset paths for generated files (QR codes, certificates)
    STATIC_DIR = os.path.join(DATA_DIR, 'data')
    QR_CODES_DIR = os.path.join(STATIC_DIR, 'qrcodes')
    CERTIFICATES_DIR = os.path.join(STATIC_DIR, 'certificates')

