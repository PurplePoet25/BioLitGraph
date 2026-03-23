from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from waitress import serve


def find_free_port(start: int = 5000, stop: int = 5100) -> int:
    for port in range(start, stop + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("Could not find a free local port between 5000 and 5100.")


def open_browser(url: str) -> None:
    time.sleep(1.2)
    webbrowser.open(url)


def _candidate_ca_paths() -> list[Path]:
    candidates: list[Path] = []

    # 1) Whatever certifi thinks, if it actually exists
    try:
        import certifi

        certifi_path = Path(certifi.where())
        candidates.append(certifi_path)
    except Exception:
        pass

    exe_dir = Path(sys.executable).resolve().parent

    # 2) PyInstaller temp/resource dir
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "certifi" / "cacert.pem")

    # 3) Typical onedir bundled locations
    candidates.append(exe_dir / "_internal" / "certifi" / "cacert.pem")
    candidates.append(exe_dir / "certifi" / "cacert.pem")

    # dedupe while preserving order
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)

    return unique


def configure_tls_bundle() -> str:
    checked: list[str] = []

    for path in _candidate_ca_paths():
        checked.append(str(path))
        if path.is_file():
            ca_path = str(path)

            # Make requests / urllib3 / SSL use this exact bundle
            os.environ["SSL_CERT_FILE"] = ca_path
            os.environ["REQUESTS_CA_BUNDLE"] = ca_path
            os.environ["CURL_CA_BUNDLE"] = ca_path

            # Patch certifi too, so anything calling certifi.where() gets the real file
            try:
                import certifi

                certifi.where = lambda: ca_path  # type: ignore[assignment]
                if hasattr(certifi, "core"):
                    certifi.core.where = lambda: ca_path  # type: ignore[attr-defined]
            except Exception:
                pass

            return ca_path

    raise RuntimeError(
        "Could not locate a usable CA certificate bundle for HTTPS requests. "
        "Looked in: " + " | ".join(checked)
    )


def main() -> None:
    configure_tls_bundle()

    # Import app only AFTER TLS bundle is configured
    from app import create_app

    app = create_app()
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    serve(
        app,
        host="127.0.0.1",
        port=port,
        threads=6,
        connection_limit=100,
        cleanup_interval=30,
        channel_timeout=60,
    )


if __name__ == "__main__":
    main()
