"""Launcher that picks a free, non-reserved port and starts uvicorn.

Fixes WinError 10013 (Windows reserved port ranges) by trying a list of
candidate ports until one binds successfully.

Usage:
    python run_api.py
"""

from __future__ import annotations

import socket
import sys

import uvicorn

CANDIDATE_PORTS = [8000, 18000, 8080, 9000, 18080, 19000, 21000, 23456]


def find_free_port(candidates: list[int]) -> int:
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError as exc:
                print(f"  port {port}: unavailable ({exc.errno})")
    raise SystemExit("no free port in candidate list; edit CANDIDATE_PORTS in run_api.py")


def main() -> None:
    print("probing ports...")
    port = find_free_port(CANDIDATE_PORTS)
    print(f"\n  bound: http://127.0.0.1:{port}")
    print(f"  docs : http://127.0.0.1:{port}/docs")
    print(f"  stats: http://127.0.0.1:{port}/api/stats\n")
    print(f"  -> if this is not 8000, set API_BASE_URL in .env to http://localhost:{port}\n")

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=port,
        reload="--reload" in sys.argv,
    )


if __name__ == "__main__":
    main()
