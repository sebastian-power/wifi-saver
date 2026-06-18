"""
wifi_watcher.py
Watches your Wi-Fi connection and reconnects to your preferred AP via
wifiinfoview-x64 whenever you're not on it.

Requirements:
    pip install pystray pillow

Usage:
    python wifi_watcher.py
    -- or double-click it if you associate .py with pythonw.exe
"""

import ctypes
import subprocess
import threading
import time
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

# ── Configuration ────────────────────────────────────────────────────────────
TARGET_SSID = "Aussie Broadband 3997"
TARGET_BSSID = "D0DBB793AC76"
CHECK_INTERVAL = 30

WIFIINFOVIEW_EXE = str(
    Path.home() / "Documents" / "wifiinfoview-x64" / "WifiInfoView.exe"
)
WIFIINFOVIEW_CWD = str(Path.home() / "Documents" / "wifiinfoview-x64")

# ── Globals ───────────────────────────────────────────────────────────────────
status_message = "Starting…"
last_action = ""
tray_icon = None
stop_event = threading.Event()


# ── Wi-Fi helpers ─────────────────────────────────────────────────────────────────────────────────


def _run_netsh(*args) -> str:
    """Run a netsh command and return its output, suppressing any window."""
    result = subprocess.run(
        ["netsh", *args],
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return result.stdout


def get_current_bssid() -> str | None:
    """Return the BSSID of the currently connected Wi-Fi AP, or None."""
    try:
        for line in _run_netsh("wlan", "show", "interfaces").splitlines():
            stripped = line.strip()
            if stripped.startswith("AP BSSID"):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip().replace(":", "").upper()
    except Exception:
        pass
    return None


def is_target_ap_visible() -> bool:
    """Return True if the target SSID/BSSID is visible in a nearby network scan."""
    try:
        output = _run_netsh("wlan", "show", "networks", "mode=bssid")
        for line in output.splitlines():
            normalised = line.strip().replace(":", "").upper()
            if TARGET_BSSID.replace(":", "").upper() in normalised:
                return True
    except Exception:
        pass
    return False


def trigger_connect():
    """Launch wifiinfoview-x64 with the AP arguments (same as the shortcut)."""
    global last_action
    try:
        subprocess.run(
            [WIFIINFOVIEW_EXE, "/ConnectAP", TARGET_SSID, TARGET_BSSID],
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        last_action = time.strftime("Reconnect triggered at %H:%M:%S")
    except Exception as e:
        last_action = f"Error launching: {e}"


# ── Icon drawing ──────────────────────────────────────────────────────────────────────────────────


def make_icon(connected: bool) -> Image.Image:
    """Draw a tiny 64x64 Wi-Fi symbol — green when connected, red when not."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colour = (40, 200, 80, 255) if connected else (220, 50, 50, 255)

    # Draw three arcs as stacked rectangles (simplified Wi-Fi look)
    cx, cy = size // 2, size - 8
    for r, thickness in [(52, 8), (34, 8), (16, 8)]:
        box = [cx - r, cy - r, cx + r, cy + r]
        draw.arc(box, start=210, end=330, fill=colour, width=thickness)

    # Centre dot
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=colour)
    return img


# ── Watcher thread ─────────────────────────────────────────────────────────────────────────────────


def watcher():
    global status_message
    while not stop_event.is_set():
        bssid = get_current_bssid()
        connected = bssid == TARGET_BSSID.replace(":", "").upper()

        if connected:
            status_message = f"✓ Connected to correct AP ({TARGET_BSSID})"
        elif is_target_ap_visible():
            status_message = (
                f"✗ Wrong AP (on: {bssid or 'none'}) — target in range, reconnecting…"
            )
            trigger_connect()
        else:
            status_message = f"⏸ Target AP not in range — standing by"

        # Update tray icon and tooltip
        if tray_icon is not None:
            tray_icon.icon = make_icon(connected)
            tray_icon.title = status_message

        stop_event.wait(CHECK_INTERVAL)


# ── Tray menu ──────────────────────────────────────────────────────────────────────────────────────


def menu_status(icon, item):
    """Show current status in a message box."""
    msg = f"{status_message}\n{last_action}" if last_action else status_message
    ctypes.windll.user32.MessageBoxW(0, msg, "Wi-Fi Watcher", 0x40)


def menu_check_now(icon, item):
    """Force an immediate check."""
    stop_event.set()  # wake the sleep early
    stop_event.clear()
    threading.Thread(target=watcher, daemon=True).start()


def menu_quit(icon, item):
    stop_event.set()
    icon.stop()


# ── Entry point ────────────────────────────────────────────────────────────────────────────────────


def main():
    global tray_icon

    # Start watcher thread
    t = threading.Thread(target=watcher, daemon=True)
    t.start()

    menu = pystray.Menu(
        pystray.MenuItem("Status…", menu_status),
        pystray.MenuItem("Check now", menu_check_now),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", menu_quit),
    )

    tray_icon = pystray.Icon(
        name="wifi_watcher",
        icon=make_icon(False),
        title="Wi-Fi Watcher — starting…",
        menu=menu,
    )
    tray_icon.run()


if __name__ == "__main__":
    main()
