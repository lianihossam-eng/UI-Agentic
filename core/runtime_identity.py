"""Content-address the actual runtime used by browser proof gates.

On the declared Linux CI domain, Playwright's default headless Chromium uses a
separate headless-shell binary. BrowserType.executable_path is therefore not
trusted as evidence of the process actually launched. We identify the live
browser process through /proc and hash /proc/<pid>/exe while it is running.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import pathlib
import subprocess
import sys

from playwright.sync_api import sync_playwright

FONT_PATTERNS = ("system-ui", "sans-serif", "serif", "monospace")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _ppid(pid: int) -> int | None:
    try:
        for line in pathlib.Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("PPid:"):
                return int(line.split(":", 1)[1].strip())
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        return None
    return None


def _descendants(root_pid: int) -> set[int]:
    parent_of = {}
    for entry in pathlib.Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        parent = _ppid(pid)
        if parent is not None:
            parent_of[pid] = parent
    descendants = set()
    changed = True
    while changed:
        changed = False
        for pid, parent in parent_of.items():
            if pid in descendants:
                continue
            if parent == root_pid or parent in descendants:
                descendants.add(pid)
                changed = True
    return descendants


def _cmdline(pid: int) -> list[str]:
    try:
        raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return []
    return [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]


def actual_browser_process(root_pid: int) -> tuple[int, pathlib.Path, list[str]]:
    candidates = []
    for pid in sorted(_descendants(root_pid)):
        args = _cmdline(pid)
        if not args or "--remote-debugging-pipe" not in args:
            continue
        if any(arg.startswith("--type=") for arg in args):
            continue
        exe_link = pathlib.Path(f"/proc/{pid}/exe")
        try:
            target = pathlib.Path(os.readlink(exe_link))
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        candidates.append((pid, target, args))
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected exactly one live Playwright browser root process, found {len(candidates)}"
        )
    return candidates[0]


def _font_identity(pattern: str) -> dict:
    proc = subprocess.run(
        ["fc-match", "-f", "%{file}\n", pattern],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"fc-match failed for {pattern}: {proc.stderr.strip()}")
    first = next((line.strip() for line in proc.stdout.splitlines() if line.strip()), None)
    if not first:
        raise RuntimeError(f"fc-match returned no font for {pattern}")
    path = pathlib.Path(first)
    if not path.is_file():
        raise RuntimeError(f"resolved font does not exist for {pattern}: {path}")
    return {
        "file_name": path.name,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def capture_runtime_identity() -> dict:
    if not pathlib.Path("/proc").is_dir():
        raise RuntimeError("runtime identity requires Linux /proc in the declared CI domain")

    parent_pid = os.getpid()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            pid, executable_target, _ = actual_browser_process(parent_pid)
            executable_proc_path = pathlib.Path(f"/proc/{pid}/exe")
            browser_identity = {
                "version": browser.version,
                "executable_name": executable_target.name,
                "size": executable_proc_path.stat().st_size,
                "sha256": sha256_file(executable_proc_path),
            }
        finally:
            browser.close()

    python_path = pathlib.Path(sys.executable)
    python_identity = {
        "version": sys.version.split()[0],
        "executable_name": python_path.name,
        "size": python_path.stat().st_size,
        "sha256": sha256_file(python_path),
    }
    fonts = {pattern: _font_identity(pattern) for pattern in FONT_PATTERNS}
    stable = {
        "browser": browser_identity,
        "python": python_identity,
        "playwright_version": importlib.metadata.version("playwright"),
        "fonts": fonts,
    }
    return {
        **stable,
        "runtime_identity_root": sha256_json(stable),
        "runtime_identity_algo": "sha256",
    }
