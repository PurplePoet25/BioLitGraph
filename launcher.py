
from __future__ import annotations

import socket
import threading
import time
import webbrowser

from waitress import serve

from app import create_app


def find_free_port(start: int = 5000, stop: int = 5100) -> int:
    for port in range(start, stop + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError('Could not find a free local port between 5000 and 5100.')


def open_browser(url: str) -> None:
    time.sleep(1.2)
    webbrowser.open(url)


def main() -> None:
    app = create_app()
    port = find_free_port()
    url = f'http://127.0.0.1:{port}'

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    serve(
        app,
        host='127.0.0.1',
        port=port,
        threads=6,
        connection_limit=100,
        cleanup_interval=30,
        channel_timeout=60,
    )


if __name__ == '__main__':
    main()
