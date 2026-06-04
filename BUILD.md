# ZHub — Desktop Application Build Guide

## Running as a desktop app without building (recommended for development)

Open a terminal in the project root and run:
python run_desktop.py

This launches ZHub in a native desktop window using your current Python
environment. No build step is required. Data is stored in the project root,
identical to running `python app.py`.

---

## Building a standalone .exe for Windows

Follow these steps **in order** every time you want to produce a new build.

### Prerequisites

Install PyInstaller into your virtual environment (one-time only):
pip install pyinstaller

All other dependencies are already listed in requirements.txt and must be
installed before building:
pip install -r requirements.txt

### Step 1 — Generate the application icon (one-time only)
python create_icon.py

This creates `desktop/zhub.ico`. You only need to run this once unless
you want to change the icon.

### Step 2 — Build the executable
pyinstaller zhub.spec

PyInstaller will create two directories:
- `build/`  — intermediate files (safe to delete after a successful build)
- `dist/ZHub/` — the finished application

### Step 3 — Locate the output

The distributable application is in:
dist/ZHub/

The entry point executable is:
dist/ZHub/ZHub.exe

Double-click `ZHub.exe` to launch the application.

### Step 4 — Distribute to another machine

Copy the entire `dist/ZHub/` folder to the target machine.
Do NOT copy just `ZHub.exe` — it requires all the other files
in that folder to run.

The target machine does NOT need Python installed.

---

## Where does data go on each machine?

Each machine that runs ZHub has its own independent database and
generated files. Data is never shared between machines automatically.

| Platform | Data location |
|----------|---------------|
| Windows  | `%LOCALAPPDATA%\ZHub\` (e.g. `C:\Users\Ahmed\AppData\Local\ZHub\`) |
| macOS    | `~/Library/Application Support/ZHub/` |
| Linux    | `~/.local/share/ZHub/` |

Inside that folder:
- `instance/zhub.db` — the SQLite database (all students, courses, etc.)
- `data/qrcodes/` — generated QR code images
- `data/certificates/` — generated certificate PDFs
- `data/student_photos/` — uploaded student photos
- `data/project_media/` — portfolio project files

The database and all tables are created automatically on first launch.
A default admin account is also created automatically:
  Email:    admin@zhub.com
  Password: admin123
Change this password immediately after first login.

---

## Windows WebView2 requirement

ZHub's desktop window uses Microsoft Edge WebView2, which is built into
Windows 11 and available as a free download for Windows 10.

If the window fails to open on Windows 10, the user must install the
WebView2 Runtime from:
  https://developer.microsoft.com/en-us/microsoft-edge/webview2/

---

## Rebuilding after code changes

After making any change to Python files or templates:
pyinstaller zhub.spec

Re-running the icon generator is not necessary unless you changed
`create_icon.py`.
