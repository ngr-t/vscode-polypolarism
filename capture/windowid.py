"""Print the CGWindowID of the test VS Code (Extension Development Host)
window, so `screencapture -l <id>` grabs exactly that window regardless of
which Space/app is frontmost. Exits non-zero if not found."""

import sys

import Quartz


def find_window_id():
    opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    windows = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []
    fallback = None  # (id, area) largest Code/Electron window if title match fails
    for w in windows:
        name = w.get("kCGWindowName", "") or ""
        owner = w.get("kCGWindowOwnerName", "") or ""
        num = w.get("kCGWindowNumber")
        b = w.get("kCGWindowBounds", {}) or {}
        area = (b.get("Width", 0) or 0) * (b.get("Height", 0) or 0)
        if "Extension Development Host" in name:
            return num
        if owner in ("Code", "Electron", "Visual Studio Code") and area > 100_000:
            if fallback is None or area > fallback[1]:
                fallback = (num, area)
    return fallback[0] if fallback else None


wid = find_window_id()
if wid is None:
    sys.exit(1)
print(int(wid))
