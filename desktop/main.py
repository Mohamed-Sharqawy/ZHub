"""
desktop/main.py — ZHub Desktop Application Entry Point.

This file is referenced as the Analysis entry point in zhub.spec.

Usage
-----
Development (no build required):
    python run_desktop.py              ← recommended convenience wrapper
    python -m desktop.main             ← alternative from project root

Production:
    Double-click  dist/ZHub/ZHub.exe   ← after PyInstaller build
"""
import os
import sys
import time
import socket


def _bootstrap_sys_path():
    """
    Ensure the project root is on sys.path so that `from desktop.X import Y`
    and `from website import create_app` resolve correctly when this file is
    executed in development mode.

    In frozen mode PyInstaller adds sys._MEIPASS to sys.path automatically,
    so this function is a no-op in that case.
    """
    if getattr(sys, 'frozen', False):
        return  # PyInstaller handles path setup automatically.

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


# Run immediately so every subsequent import can resolve correctly.
_bootstrap_sys_path()


def _wait_for_server(port, timeout=30):
    """
    Poll 127.0.0.1:port every 100 ms until a TCP connection is accepted
    or `timeout` seconds elapse.

    Returns True if the server became ready, False on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    return False


def main():
    from desktop.paths  import get_data_dir
    from desktop.server import start as start_server

    # ── 1. Resolve and create the writable data directory ───────────────────
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)

    # ── 2. Start the Waitress server in a background daemon thread ──────────
    port = start_server(data_dir)

    # ── 3. Import pywebview after the server thread has started ─────────────
    #       (avoids rare import-order issues on some platforms)
    import webview

    # ── 4. Wait up to 30 s for Waitress to accept connections ───────────────
    server_ready = _wait_for_server(port, timeout=30)

    if not server_ready:
        # Show a minimal error window so the user is not left with nothing.
        webview.create_window(
            title='ZHub — Startup Error',
            html=(
                '<body style="font-family:system-ui,sans-serif;'
                'padding:48px;background:#fff;color:#212529;">'
                '<h2 style="color:#dc3545;">&#10060; ZHub could not start</h2>'
                '<p>The internal server did not respond within 30 seconds.</p>'
                '<p>Please close this window and try launching ZHub again.</p>'
                '<p style="color:#6c757d;font-size:0.85rem;">'
                'If the problem persists, check that no other application is '
                'blocking localhost connections.</p>'
                '</body>'
            ),
            width=540,
            height=280,
            resizable=False,
        )
        webview.start()
        return

    # ── 5. Open the main application window ─────────────────────────────────
    #
    # text_select=True  — lets the user select and copy text in the UI.
    # min_size          — prevents the window from being resized so small
    #                     that the Bootstrap layout breaks.
    # The window points at the Flask app running on localhost.
    # Flask-Login will redirect to /login on the first request because
    # no session cookie exists yet. This is the correct expected behaviour.
    webview.create_window(
        title='ZHub Course Center',
        url=f'http://127.0.0.1:{port}/',
        width=1280,
        height=800,
        min_size=(900, 600),
        resizable=True,
        text_select=True,
    )

    # webview.start() blocks until the window is closed by the user.
    # When it returns the process exits, killing the daemon Waitress thread.
    webview.start()


if __name__ == '__main__':
    main()
