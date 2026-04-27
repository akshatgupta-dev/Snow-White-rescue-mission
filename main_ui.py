#!/usr/bin/env python3
"""
Entry point for the Cinderella game UI.

Run this to launch the game window:
    python main_ui.py

If Tk/X display startup is not healthy in this session, the launcher can
fall back to the interactive terminal version when GUI startup fails.

Environment overrides:
    UI_FORCE_CLI=1            Force the terminal game.
    UI_SKIP_PREFLIGHT=1       Skip the Tk display preflight.
    UI_DISPLAY_PREFLIGHT_TIMEOUT=10
                              Set the preflight timeout in seconds.
"""

import os
import subprocess
import sys
import traceback

def _as_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_wsl() -> bool:
    return bool(os.environ.get("WSL_DISTRO_NAME"))


def _display_preflight(timeout_seconds: int = 5):
    """Check whether Tk can start in this display session."""
    probe_code = (
        "import tkinter as tk\n"
        "r = tk.Tk()\n"
        "r.withdraw()\n"
        "r.update_idletasks()\n"
        "print('ok')\n"
        "r.destroy()\n"
    )

    try:
        result = subprocess.run(
            [sys.executable, "-c", probe_code],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (
            False,
            f"display preflight timed out after {timeout_seconds}s (Tk did not respond)",
        )
    except Exception as exc:
        return False, f"display preflight failed to run ({exc})"

    if result.returncode != 0:
        err = (result.stderr or "").strip() or (result.stdout or "").strip() or "unknown error"
        return False, f"display preflight failed ({err})"

    output = (result.stdout or "").strip().splitlines()
    last = output[-1] if output else ""
    if last != "ok":
        return False, "display preflight returned unexpected output"

    return True, "ok"


def _run_cli_fallback(reason: str):
    """Run interactive terminal game when GUI launch is unavailable."""
    print("\nGUI launch unavailable.")
    print(f"Reason: {reason}")

    if _is_wsl():
        display = os.environ.get("DISPLAY", "").strip() or "(unset)"
        wayland = os.environ.get("WAYLAND_DISPLAY", "").strip() or "(unset)"
        print(
            "\nWSL detected. If GUI apps are not opening in this session, "
            "WSLg/Xwayland is likely stuck.\n"
            "Try this from Windows PowerShell:  wsl --shutdown\n"
            "Then reopen your distro and run the game again.\n"
            "(From inside WSL you can also run:  /mnt/c/Windows/System32/wsl.exe --shutdown)\n"
            "If it still fails:  wsl --update  (then reboot Windows if needed)\n"
            "(From inside WSL:  /mnt/c/Windows/System32/wsl.exe --update)\n"
            f"(DISPLAY={display}, WAYLAND_DISPLAY={wayland})\n"
            "Tip: to attempt GUI even when preflight fails, run:  UI_SKIP_PREFLIGHT=1 python3 main_ui.py\n"
        )

    print("Starting terminal game fallback...\n")

    from pipeline.runner import main as cli_main

    cli_main()


def main():
    force_cli = _as_bool(os.environ.get("UI_FORCE_CLI", "0"))
    skip_preflight = _as_bool(os.environ.get("UI_SKIP_PREFLIGHT", "0"))
    timeout_text = os.environ.get("UI_DISPLAY_PREFLIGHT_TIMEOUT", "5").strip()
    try:
        preflight_timeout = max(1, int(timeout_text))
    except ValueError:
        preflight_timeout = 5
    use_preflight = (not skip_preflight) and (
        _as_bool(os.environ.get("UI_GUI_PREFLIGHT", "0")) or _is_wsl()
    )

    if force_cli:
        _run_cli_fallback("UI_FORCE_CLI is enabled")
        return

    if use_preflight:
        ok, detail = _display_preflight(preflight_timeout)
        if not ok:
            _run_cli_fallback(detail)
            return

    try:
        from src.tkinter_ui import run

        run()
    except Exception as exc:
        traceback.print_exc()
        _run_cli_fallback(f"GUI startup error ({exc})")

if __name__ == "__main__":
    main()
