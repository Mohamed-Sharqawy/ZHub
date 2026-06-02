"""Flask server lifecycle manager for desktop mode.

Starts the Flask application via Waitress (production WSGI) in a background
daemon thread so PyWebView can run on the main thread.
"""

import logging
import socket
import threading
import time
from urllib.request import urlopen
from urllib.error import URLError

log = logging.getLogger(__name__)


def find_free_port(host: str = '127.0.0.1') -> int:
    """Find an available TCP port on *host*."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


class FlaskServer:
    """Manages the Flask app running inside a Waitress WSGI server."""

    def __init__(self, host: str = '127.0.0.1', port: int = 0):
        self.host = host
        self.port = port or find_free_port(host)
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f'http://{self.host}:{self.port}'

    def start(self):
        """Create the Flask app and serve it in a daemon thread."""
        from waitress import serve
        from website import create_app

        app = create_app()
        # Suppress Flask/Waitress logging to avoid console noise
        app.logger.setLevel(logging.WARNING)
        logging.getLogger('waitress').setLevel(logging.WARNING)

        def _run():
            log.info('Starting Waitress on %s:%s', self.host, self.port)
            serve(app, host=self.host, port=self.port, _quiet=True)

        self._thread = threading.Thread(target=_run, daemon=True, name='flask-server')
        self._thread.start()

    def wait_ready(self, timeout: float = 15.0, interval: float = 0.25) -> bool:
        """Poll the server until it responds or *timeout* seconds elapse."""
        health_url = f'{self.url}/login'
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                resp = urlopen(health_url, timeout=2)
                if resp.status == 200:
                    log.info('Server ready at %s', self.url)
                    return True
            except (URLError, OSError):
                pass
            time.sleep(interval)
        log.error('Server failed to start within %.1fs', timeout)
        return False
