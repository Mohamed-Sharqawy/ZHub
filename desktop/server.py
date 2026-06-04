"""
desktop/server.py — Waitress WSGI server management for ZHub desktop.

Responsibilities:
  1. Accept the data_dir path from main.py.
  2. Set ZHUB_DATA_DIR in the environment BEFORE importing the Flask app,
     so that config.py picks up the correct writable path.
  3. Discover a free TCP port dynamically to avoid conflicts.
  4. Create the Flask application via website.create_app().
     create_app() calls db.create_all() internally, which provisions the
     SQLite database automatically on first run.
  5. Start Waitress in a background daemon thread and return the port.
"""
import os
import socket
import threading


def _find_free_port():
    """
    Bind a socket to port 0 so the OS assigns a free port, record it,
    then close the socket. The port is free for Waitress to use
    immediately after this function returns.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def start(data_dir):
    """
    Set the data directory, build the Flask app, and serve it with
    Waitress on a free localhost port in a background daemon thread.

    Parameters
    ----------
    data_dir : str
        Absolute path to the writable directory returned by
        desktop.paths.get_data_dir().

    Returns
    -------
    int
        The TCP port number Waitress is listening on.
    """
    # Set ZHUB_DATA_DIR *before* importing website so config.py reads it.
    os.environ['ZHUB_DATA_DIR'] = data_dir

    # These imports must happen AFTER the env var is set.
    from website import create_app
    from waitress import serve

    port = _find_free_port()
    app  = create_app()

    # daemon=True ensures this thread is killed automatically when the
    # main process exits (i.e. when the pywebview window is closed).
    server_thread = threading.Thread(
        target=serve,
        kwargs={
            'app':  app,
            'host': '127.0.0.1',
            'port': port,
        },
        daemon=True,
        name='zhub-waitress',
    )
    server_thread.start()
    return port
