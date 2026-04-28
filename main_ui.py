#!/usr/bin/env python3

import os
import subprocess
import sys
import traceback


def _as_bool(value: str) -> bool:
    # small helper so env vars like 1, true, yes all work the same
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_wsl() -> bool:
    # WSL sets this env var, so this is the quickest check for it
    return bool(os.environ.get("WSL_DISTRO_NAME"))


def _display_preflight(timeout_seconds: int = 5):
    # this checks if Tk can even open before loading the full game UI
    probe_code = (
        "import tkinter as tk\n"
        "r = tk.Tk()\n"
        "r.withdraw()\n"
        "r.update_idletasks()\n"
        "print('ok')\n"
        "r.destroy()\n"
    )

    try:
        # run Tk test in a seperate process because display problems can hang badly
        result = subprocess.run(
            [sys.executable, "-c", probe_code],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # if it takes too long, assume GUI is broken in this session
        return (
            False,
            f"display preflight timed out after {timeout_seconds}s (Tk did not respond)",
        )
    except Exception as exc:
        # this catches weird subprocess errors, not actual game errors
        return False, f"display preflight failed to run ({exc})"

    if result.returncode != 0:
        # use stderr first because Tk normally writes display errors there
        err = (result.stderr or "").strip() or (result.stdout or "").strip() or "unknown error"
        return False, f"display preflight failed ({err})"

    output = (result.stdout or "").strip().splitlines()
    last = output[-1] if output else ""
    if last != "ok":
        # means the test ran but didnt return the exact thing expected
        return False, "display preflight returned unexpected output"

    return True, "ok"


def _run_cli_fallback(reason: str):
    # if GUI is dead, start terminal game instead of just crashing
    print("\nGUI launch unavailable.")
    print(f"Reason: {reason}")

    if _is_wsl():
        # showing DISPLAY values helps debug WSLg/Xwayland issues later
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

    # import here only when needed, so normal GUI startup does not load CLI stuff
    from pipeline.runner import main as cli_main

    cli_main()


def main():
    # env flags make it easy to test GUI/CLI without changing the file
    force_cli = _as_bool(os.environ.get("UI_FORCE_CLI", "0"))
    skip_preflight = _as_bool(os.environ.get("UI_SKIP_PREFLIGHT", "0"))
    timeout_text = os.environ.get("UI_DISPLAY_PREFLIGHT_TIMEOUT", "5").strip()

    try:
        # timeout should never go below 1, otherwise subprocess timeout gets silly
        preflight_timeout = max(1, int(timeout_text))
    except ValueError:
        preflight_timeout = 5

    # WSL uses preflight by default because display problems happened there alot
    use_preflight = (not skip_preflight) and (
        _as_bool(os.environ.get("UI_GUI_PREFLIGHT", "0")) or _is_wsl()
    )

    if force_cli:
        # direct terminal mode, useful for testing game logic without Tkinter
        _run_cli_fallback("UI_FORCE_CLI is enabled")
        return

    if use_preflight:
        # quick Tk probe before launching the real UI
        ok, detail = _display_preflight(preflight_timeout)
        if not ok:
            _run_cli_fallback(detail)
            return

    try:
        # actual GUI import happens late so CLI fallback can still work if Tk UI breaks
        from src.tkinter_ui import run

        run()
    except Exception as exc:
        # print full traceback for debugging, then still give user playable terminal game
        traceback.print_exc()
        _run_cli_fallback(f"GUI startup error ({exc})")


if __name__ == "__main__":
    main()
