import ctypes
import subprocess
import time
from pathlib import Path

import tracker_gui


PROJECT_ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"
WINDOW_BOOT_DELAY_SECONDS = 0.6
VIEW_SWITCH_DELAY_SECONDS = 0.35


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def slugify(label):
    allowed = []
    for char in label.lower():
        if char.isalnum():
            allowed.append(char)
        else:
            allowed.append("_")
    slug = "".join(allowed)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def ensure_output_dir():
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    return SCREENSHOT_DIR


def bring_window_to_front(app):
    app.deiconify()
    app.lift()
    app.attributes("-topmost", True)
    app.focus_force()
    app.update_idletasks()
    app.update()
    time.sleep(0.1)
    app.attributes("-topmost", False)
    app.update_idletasks()
    app.update()


def get_window_rect(app):
    rect = RECT()
    hwnd = app.winfo_id()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("Could not read tracker window bounds.")
    return rect.left, rect.top, rect.right, rect.bottom


def capture_rect_to_png(left, top, right, bottom, output_path):
    width = right - left
    height = bottom - top
    escaped_path = str(output_path).replace("'", "''")

    powershell_script = f"""
Add-Type -AssemblyName System.Drawing
$bitmap = New-Object System.Drawing.Bitmap {width}, {height}
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen({left}, {top}, 0, 0, $bitmap.Size)
$bitmap.Save('{escaped_path}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
"""

    subprocess.run(
        ["powershell", "-NoProfile", "-Command", powershell_script],
        check=True,
    )


def capture_app_window(app, filename):
    output_dir = ensure_output_dir()
    output_path = output_dir / filename
    bring_window_to_front(app)
    time.sleep(VIEW_SWITCH_DELAY_SECONDS)
    left, top, right, bottom = get_window_rect(app)
    capture_rect_to_png(left, top, right, bottom, output_path)
    return output_path


def get_capture_targets(app, payload):
    capture_targets = []

    for view_key, config in tracker_gui.VIEW_CONFIG.items():
        filename = f"{len(capture_targets) + 1:02d}_{slugify(config['label'])}.png"
        capture_targets.append(
            (
                config["label"],
                filename,
                lambda key=view_key: app.show_view(key),
            )
        )

    for server_name in sorted(payload.get("server_stats", {})):
        filename = f"{len(capture_targets) + 1:02d}_server_{slugify(server_name)}.png"
        capture_targets.append(
            (
                f"{server_name} Server",
                filename,
                lambda name=server_name: app.show_server_view(name),
            )
        )

    return capture_targets


def main():
    ctypes.windll.user32.SetProcessDPIAware()
    payload = tracker_gui.load_stats_payload()
    app = tracker_gui.TrackerStatsApp(payload=payload)

    try:
        app.attributes("-fullscreen", True)
        app.update_idletasks()
        app.update()
        time.sleep(WINDOW_BOOT_DELAY_SECONDS)

        saved_paths = []
        for label, filename, activate_view in get_capture_targets(app, payload):
            activate_view()
            app.update_idletasks()
            app.update()
            saved_path = capture_app_window(app, filename)
            saved_paths.append(saved_path)
            print(f"Saved {label}: {saved_path}")
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
