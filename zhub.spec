# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for ZHub Course Center desktop application.

Build command:
    pyinstaller zhub.spec

Output:
    dist/ZHub/ZHub.exe   (one-directory mode)
"""

import os

block_cipher = None

# Project root (where this .spec file lives)
ROOT = os.path.abspath('.')

a = Analysis(
    ['desktop/main.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # Flask templates and static assets (read-only, bundled)
        ('website/templates', 'website/templates'),
        ('website/static', 'website/static'),
        # Config module
        ('config.py', '.'),
    ],
    hiddenimports=[
        # Flask and extensions
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_wtf',
        'flask_migrate',
        'wtforms',
        'wtforms.validators',
        'wtforms.fields',
        # Email validator (used by WTForms)
        'email_validator',
        # Jinja2
        'jinja2',
        'jinja2.ext',
        # SQLAlchemy dialects
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        # Alembic (for Flask-Migrate)
        'alembic',
        # WSGI server
        'waitress',
        # QR code generation
        'qrcode',
        'qrcode.image.pil',
        # PDF generation
        'reportlab',
        'reportlab.lib',
        'reportlab.pdfgen',
        # Image processing
        'PIL',
        'PIL.Image',
        # Desktop window
        'webview',
        # Application modules
        'website',
        'website.auth',
        'website.admin',
        'website.students',
        'website.instructors',
        'website.courses',
        'website.payments',
        'website.attendance',
        'website.certificates',
        'website.qr',
        'desktop',
        'desktop.paths',
        'desktop.server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ZHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='desktop/zhub.ico',
    version_info=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ZHub',
)
