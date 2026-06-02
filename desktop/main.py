"""ZHub Desktop Application — main entry point.

Orchestrates:
  1. Single-instance detection (lock file)
  2. Runtime directory setup
  3. Flask server startup in background thread
  4. PyWebView window creation
  5. Clean shutdown when window closes
"""

import logging
import os
import sys

# ---------------------------------------------------------------------------
# Bootstrap: ensure the project root is on sys.path so that 'website' and
# 'config' modules can be imported regardless of working directory.
# ---------------------------------------------------------------------------
from desktop.paths import get_base_dir, get_data_dir, ensure_data_dirs, is_frozen

_project_root = get_base_dir()
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Set environment variable so config.py picks up the correct data directory
os.environ['ZHUB_DATA_DIR'] = get_data_dir()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
ensure_data_dirs()

_log_file = os.path.join(get_data_dir(), 'logs', 'zhub.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),
    ],
)
log = logging.getLogger('zhub.desktop')

# ---------------------------------------------------------------------------
# Single-instance lock
# ---------------------------------------------------------------------------
_LOCK_FILE = os.path.join(get_data_dir(), 'zhub.lock')


def _acquire_lock() -> bool:
    """Create a lock file. Returns False if another instance is running."""
    if os.path.exists(_LOCK_FILE):
        # Check if the PID in the lock file is still alive
        try:
            with open(_LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            # On Windows, check if process exists
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x0400, False, old_pid)  # PROCESS_QUERY_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return False  # Process still running
        except (ValueError, OSError, AttributeError):
            pass  # Lock file is stale, continue

    with open(_LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True


def _release_lock():
    """Remove the lock file."""
    try:
        os.remove(_LOCK_FILE)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info('ZHub Desktop starting (PID %d)', os.getpid())

    if not _acquire_lock():
        log.warning('Another instance is already running. Exiting.')
        # Show a message to the user
        try:
            import webview
            webview.create_window(
                'ZHub',
                html='<h2 style="font-family:sans-serif;text-align:center;margin-top:80px;">'
                     'ZHub is already running.</h2>',
                width=400, height=200,
            )
            webview.start()
        except Exception:
            pass
        sys.exit(1)

    try:
        from desktop.server import FlaskServer

        server = FlaskServer()
        log.info('Starting Flask server on port %d', server.port)
        server.start()

        if not server.wait_ready(timeout=20):
            log.error('Flask server did not become ready. Aborting.')
            _release_lock()
            sys.exit(2)

        # Launch the desktop window
        import webview

        log.info('Opening PyWebView window → %s', server.url)
        webview.create_window(
            title='ZHub Course Center',
            url=server.url,
            width=1280,
            height=800,
            min_size=(900, 600),
            text_select=True,
        )
        # webview.start() blocks until the window is closed
        webview.start()

        log.info('Window closed. Shutting down.')

    except Exception:
        log.exception('Fatal error in desktop launcher')
    finally:
        _release_lock()
        log.info('ZHub Desktop exited.')


if __name__ == '__main__':
    main()
