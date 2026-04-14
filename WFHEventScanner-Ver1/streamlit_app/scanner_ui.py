"""Streamlit UI port of the React frontend (Scanner, Scan Log, Stats).

Deploy target: Streamlit Community Cloud.
Mirrors WFHEventScanner-Ver1/frontend/src pages using the same FastAPI backend.
"""

from __future__ import annotations

import io
import os
import sys
import socket
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# Make repo root importable so `from api.main import app` works on Streamlit Cloud
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass


# --------------------------------------------------------- Embedded FastAPI
# On Streamlit Cloud only the Streamlit process runs, so we start uvicorn in a
# background thread inside this same process and talk to it over localhost.
EMBED_API = os.getenv("EMBED_API", "1") == "1"
EMBED_API_PORT = int(os.getenv("EMBED_API_PORT", "0"))  # 0 = auto-pick free port


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@st.cache_resource(show_spinner=False)
def _start_embedded_api(port: int) -> str:
    """Start FastAPI via uvicorn in a daemon thread. Runs once per process."""
    if port == 0 or _port_in_use(port):
        port = _pick_free_port() if port == 0 else port
    if _port_in_use(port):
        return f"http://127.0.0.1:{port}"

    import uvicorn
    from api.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app, host="127.0.0.1", port=port, log_level="warning", loop="asyncio"
    )
    server = uvicorn.Server(config)

    t = threading.Thread(target=server.run, daemon=True, name="embedded-uvicorn")
    t.start()

    # Wait up to ~10s for the server to come up
    for _ in range(100):
        if _port_in_use(port):
            break
        time.sleep(0.1)

    return f"http://127.0.0.1:{port}"


def _resolve_api_base() -> str:
    # Embedded mode wins by default — run `EMBED_API=0` to use an external API.
    if EMBED_API:
        return _start_embedded_api(EMBED_API_PORT)
    override = os.getenv("API_BASE_URL")
    if not override and hasattr(st, "secrets"):
        try:
            override = st.secrets.get("API_BASE_URL")
        except Exception:
            override = None
    return override or "http://localhost:8000"


API_BASE = _resolve_api_base()

SCAN_COOLDOWN_MS = 2000
POLL_SECONDS = 5


def api_post(path: str, json: dict):
    r = requests.post(f"{API_BASE}{path}", json=json, timeout=10)
    if r.status_code >= 400:
        try:
            err = r.json().get("error") or r.text
        except Exception:
            err = r.text
        raise RuntimeError(err)
    return r.json()


def api_get(path: str, params: dict | None = None):
    r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=10)
    r.raise_for_status()
    return r.json()


def post_scan(payload: str, scanned_by: str = "staff"):
    return api_post("/api/scan", {"payload": payload, "scanned_by": scanned_by})


# ------------------------------------------------------------------ QR decode
def decode_qr_from_image(image_bytes: bytes) -> str | None:
    """Try pyzbar first (fast, multi-symbol); fall back to opencv."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode
        img = Image.open(io.BytesIO(image_bytes))
        results = zbar_decode(img)
        if results:
            return results[0].data.decode("utf-8", errors="replace")
    except Exception:
        pass
    try:
        import cv2
        import numpy as np
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        return data or None
    except Exception:
        return None


# ------------------------------------------------------------------ Scanner
def scanner_page():
    st.header("Scan entry pass")

    scanned_by = st.text_input("Scanned by", value=st.session_state.get("scanned_by", "staff"))
    st.session_state["scanned_by"] = scanned_by

    tab_camera, tab_upload, tab_manual = st.tabs(["Camera", "Upload image", "Manual entry"])

    payload: str | None = None

    with tab_camera:
        st.caption("Point your camera at the QR code and take a photo.")
        shot = st.camera_input("Capture QR")
        if shot is not None:
            data = decode_qr_from_image(shot.getvalue())
            if data:
                payload = data
                st.success(f"Decoded: {data}")
            else:
                st.warning("No QR detected — try again with better lighting.")

    with tab_upload:
        up = st.file_uploader("QR image", type=["png", "jpg", "jpeg", "webp"])
        if up is not None:
            data = decode_qr_from_image(up.getvalue())
            if data:
                payload = data
                st.success(f"Decoded: {data}")
            else:
                st.error("Could not decode QR from image.")

    with tab_manual:
        manual = st.text_input("Paste QR payload")
        if st.button("Submit", type="primary", disabled=not manual.strip()):
            payload = manual.strip()

    # cooldown guard (prevents same payload re-submitting from a reloaded camera snapshot)
    last = st.session_state.get("last_scan")
    now_ms = time.time() * 1000
    if payload and last and payload == last["payload"] and (now_ms - last["ts"]) < SCAN_COOLDOWN_MS:
        payload = None

    if payload:
        st.session_state["last_scan"] = {"payload": payload, "ts": now_ms}
        try:
            result = post_scan(payload, scanned_by=scanned_by or "staff")
            render_attendee_card(result)
        except Exception as exc:
            st.error(f"Check-in failed: {exc}")


def render_attendee_card(result: dict):
    a = result.get("attendee") or {}
    duplicate = bool(result.get("duplicate"))
    color_bg = "#fff3cd" if duplicate else "#d1e7dd"
    border = "#ffc107" if duplicate else "#198754"
    title = "Already checked in" if duplicate else "Checked in"
    icon = "⚠" if duplicate else "✓"

    swatch = ""
    if a.get("color"):
        swatch = (
            f'<span style="display:inline-block;width:14px;height:14px;'
            f'border-radius:3px;background:{a["color"].lower()};'
            f'margin-right:8px;vertical-align:middle;border:1px solid #0003;"></span>'
        )

    html = f"""
    <div style="background:{color_bg};border:2px solid {border};
                border-radius:12px;padding:24px;text-align:center;
                box-shadow:0 2px 8px #0001;margin-top:16px;">
      <h3 style="margin:0 0 12px;">{icon} {title}</h3>
      <div style="font-size:2rem;font-weight:600;margin:8px 0;">
        {a.get('first_name','')} {a.get('last_name','')}
      </div>
      <div style="margin:4px 0;">{swatch}<strong>Table: {a.get('color','—')}</strong></div>
      <div style="color:#555;margin-top:4px;">{a.get('event_name','')}</div>
      {'<div style="margin-top:8px;"><span style="background:#6c757d;color:#fff;padding:2px 10px;border-radius:10px;font-size:0.8rem;">duplicate scan</span></div>' if duplicate else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ------------------------------------------------------------------- Scan Log
def scan_log_page():
    st.header("Scan log")
    c1, c2 = st.columns([3, 1])
    limit = c1.slider("Rows", 20, 500, 100, 20)
    auto = c2.toggle("Auto-refresh", value=False)

    try:
        rows = api_get("/api/scans", params={"limit": limit})
    except Exception as exc:
        st.error(f"Failed to load: {exc}")
        return

    if not rows:
        st.info("no scans yet")
    else:
        df = pd.DataFrame(rows)
        if "scanned_at" in df.columns:
            df["scanned_at"] = pd.to_datetime(df["scanned_at"], errors="coerce")
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export CSV",
            data=csv,
            file_name=f"scan_log_{datetime.now():%Y%m%d_%H%M%S}.csv",
            mime="text/csv",
        )

    if auto:
        time.sleep(POLL_SECONDS)
        st.rerun()


# ----------------------------------------------------------------------- Stats
def stats_page():
    st.header("Stats")
    auto = st.toggle("Auto-refresh", value=False)

    try:
        s = api_get("/api/stats")
    except Exception as exc:
        st.error(f"Error: {exc}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", s.get("total", 0))
    c2.metric("Pending", s.get("pending", 0))
    c3.metric("Sent", s.get("sent", 0))
    c4.metric("Checked in", s.get("checked_in", 0))

    total = s.get("total") or 0
    checked = s.get("checked_in") or 0
    pct = round((checked / total) * 100) if total else 0

    st.subheader("Attendance")
    st.progress(pct / 100, text=f"{pct}%")
    st.caption(f"Scans today: {s.get('scans_today', 0)}")

    if auto:
        time.sleep(POLL_SECONDS)
        st.rerun()


# ---------------------------------------------------------------------- Router
st.set_page_config(page_title="WFH Event Scanner", layout="centered")

st.sidebar.title("Event Scanner")
page = st.sidebar.radio("Navigate", ["Scanner", "Scan Log", "Stats"])
st.sidebar.caption(f"API: {API_BASE}")

if page == "Scanner":
    scanner_page()
elif page == "Scan Log":
    scan_log_page()
else:
    stats_page()
