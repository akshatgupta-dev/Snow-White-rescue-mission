"""
retro tkinter UI for the game.

simple window with:
- black background, green monospace text
- story scrollable text area
- input field at bottom
- Minimal buttons (New Game, Quit)
- typewriter effect on text output

Integrates with GameEngine using packet-based calls.
Engine execution runs in background threads so Tkinter stays responsive.
"""

import queue
import threading
import textwrap
import tkinter as tk
import tkinter.font as tkFont
import asyncio
import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

from src.game_engine import GameEngine


class GameApp(tk.Tk):
    """Retro terminal-style game window."""

    _BOOL_TRUE = {"1", "true", "yes", "on"}

    def __init__(self):
        super().__init__()
        self.title("Cinderella Rescues Snow White")
        self.geometry("800x600")
        self.config(bg="#000000")

        # engine starts later so teh UI can open first
        self.engine = None

        # these flags help when running inside WSL, bc windows can be weird there
        self._wsl_runtime = self._is_wsl()
        self._safe_mode = os.environ.get("UI_SAFE_MODE", "").lower() in {"1", "true", "yes", "on"}
        if self._wsl_runtime and os.environ.get("UI_FORCE_SAFE_WSL", "").lower() in {"1", "true", "yes", "on"}:
            self._safe_mode = True
        self._aggressive_wm = (
            os.environ.get("UI_AGGRESSIVE_WM", "").lower() in {"1", "true", "yes", "on"}
        ) and (not self._safe_mode)

        # queues are used so background threads dont touch tkinter directly
        self.output_queue = queue.Queue()
        self.typewriter_queue = queue.Queue()
        self.tts_queue = queue.Queue()
        self.tts_stop_event = threading.Event()
        # output_queue is for normal text, typewriter_queue is for printing it slowly
        # tts_queue is seperate becuase voice can be slower than the game text

        # tts setup values, it is off in safe mode so it doesnt crash the UI
        self.tts_enabled = not self._safe_mode
        self.tts_available = False
        self._pyttsx3 = None
        self._edge_tts = None
        self._tts_backend = None
        self._tts_rate = 175
        self._tts_max_chars = 420
        self._windows_voice_rate = -2
        self._edge_voice_candidates = [
            "en-US-AvaMultilingualNeural",
            "en-US-AvaNeural",
            "en-US-JennyNeural",
            "en-US-AriaNeural",
            "en-US-GuyNeural",
        ]
        self._edge_voice = self._edge_voice_candidates[0]
        self._edge_rate = "-8%"
        self._edge_pitch = "+0Hz"
        self._edge_volume = "+0%"

        # LLM is kept off by default because normal game should still work alone
        self.llm_enabled = False
        self.llm_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b-instruct-q4_K_M")

        # cursor stuff for the start screen carousel
        self.cursor_options = self._build_cursor_options()
        self.cursor_index = 0

        # background video config, can be controled from env vars
        self._video_path = Path(__file__).resolve().parent / "assets" / "Vietnamese_Jedi_with_Red_Lightsaber.mp4"
        self._video_capture = None
        self._video_after_id = None
        self._video_photo = None
        self._video_label = None
        self._video_enabled = False
        video_default = "0" if self._safe_mode else "1"
        self._video_requested = os.environ.get("UI_BG_VIDEO", video_default).lower() in self._BOOL_TRUE

        # alpha and darkness are from env vars so i can test visibility without editing code
        alpha_text = (os.environ.get("UI_BG_VIDEO_ALPHA") or "").strip()
        try:
            alpha_value = float(alpha_text) if alpha_text else 0.88
        except ValueError:
            alpha_value = 0.88
        self._video_overlay_alpha = min(1.0, max(0.75, alpha_value))

        self._video_window = None
        self._video_configure_bound = False
        self._video_geometry_sync_pending = False
        self._video_frame_interval_ms = 140

        # video darknes works more like brightness here, higher is brighter
        darkness_text = (os.environ.get("UI_BG_VIDEO_DARKNESS") or "").strip()
        try:
            darkness_value = float(darkness_text) if darkness_text else 0.75
        except ValueError:
            darkness_value = 0.65
        self._video_darkness = min(1.0, max(0.05, darkness_value))

        # blur makes the video less distracting behind the green terminal text
        blur_text = (os.environ.get("UI_BG_VIDEO_BLUR") or "").strip()
        try:
            blur_value = int(blur_text) if blur_text else 11
        except ValueError:
            blur_value = 11
        blur_value = min(31, max(0, blur_value))
        if blur_value != 0 and (blur_value % 2 == 0):
            blur_value += 1
        self._video_blur_ksize = blur_value

        # video modules are imported later after checking they are safe
        self._video_cv2 = None
        self._video_image_cls = None
        self._video_image_tk = None
        self._video_preflight_queue = queue.Queue()
        self._video_preflight_pending = False

        self._wm_fallback_applied = False
        self._safe_window_mode_applied = False

        # cursor is optional bc custom bitmap cursor can fail on some linux setups
        cursor_default = "0" if self._safe_mode else "1"
        self._custom_cursor_enabled = (
            os.environ.get("UI_CUSTOM_CURSOR", cursor_default).lower() in {"1", "true", "yes", "on"}
        )
        self._cursor_selector_keys_bound = False

        # this tells what kind of user input the game is waiting for
        self.current_packet = None
        self.input_state = "IDLE"
        self.pending_action_index = -1
        # current_packet keeps the last engine response so the typed number can map to an action

        # build the UI first, then start the slower stuff after tkinter is alive
        self._setup_ui()
        # self.after(500, self._debug_cursor_test)
        self.llm_enabled = False

        # after() is used here because tkinter should do UI changes inside its own loop
        self.after(0, lambda: self._append_text("UI booted successfully.", "system"))
        self.after(100, self._show_window)
        if self._video_requested:
            self.after(160, self._start_background_video)
        if self._custom_cursor_enabled:
            self.after(200, self._show_cursor_selector)
        else:
            self.after(200, self._new_game)
        self.after(40, self._drain_output_queue)
        self.after(5, self._typewriter_loop)

    def _place_video_behind_root(self):
        # this is for the older helper-window video mode
        if self._video_window is None:
            return

        try:
            if not self._video_window.winfo_exists():
                return

            self._video_window.deiconify()
            # lift it once first, then lower it exactly below the main window
            # this avoids sending it behind the desktop by accident
            self._video_window.lift()
            self._video_window.lower(self)
            self.lift()
        except tk.TclError:
            pass

    def _apply_safe_window_mode(self):
        # safe window mode makes a normal visible window when WSL acts broken
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
        except tk.TclError:
            return

        win_w = 1000
        win_h = 700
        if win_w > screen_w - 40:
            win_w = max(640, screen_w - 40)
        if win_h > screen_h - 40:
            win_h = max(480, screen_h - 40)

        pos_x = 60
        pos_y = 60
        if pos_x > screen_w - 120:
            pos_x = 20
        if pos_y > screen_h - 120:
            pos_y = 20

        try:
            self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
            self.deiconify()
            self.update_idletasks()
            self.lift()
            self.attributes("-topmost", True)
            self.after(500, lambda: self.attributes("-topmost", False))
            self._safe_window_mode_applied = True
        except tk.TclError:
            pass

    def _normalize_window_state(self):
        # make sure window is not stuck minimized or hidden. ahd some problems in that so i ahd to hardcode to not be irritating to other people too
        try:
            current_state = self.state()
        except tk.TclError:
            return

        if current_state in ("iconic", "withdrawn"):
            try:
                self.deiconify()
            except tk.TclError:
                pass
            try:
                self.state("normal")
            except tk.TclError:
                pass

    def _window_mapping_failed(self):
        # returns true if tkinter says window exists but user cant really see it
        try:
            state = self.state()
            mapped = bool(self.winfo_ismapped())
            viewable = bool(self.winfo_viewable())
            width = self.winfo_width()
            height = self.winfo_height()
        except tk.TclError:
            return False

        if state in ("iconic", "withdrawn"):
            return True

        if not mapped or not viewable:
            return True

        if width < 100 or height < 100:
            return True

        return False

    def _apply_wm_fallback_if_needed(self):
        # last try if the window manager keeps the app invisible. it was a problem in my linux setup but redundancies are always good to ahve
        if self._safe_mode:
            return

        if self._wm_fallback_applied:
            return

        self._normalize_window_state()

        try:
            self.update_idletasks()
        except tk.TclError:
            return

        if not self._window_mapping_failed():
            return

        try:
            win_w = self.winfo_width()
            win_h = self.winfo_height()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

            if win_w < 200:
                win_w = 800
            if win_h < 200:
                win_h = 600

            pos_x = 60
            pos_y = 60
            if pos_x > screen_w - 120:
                pos_x = max(20, (screen_w - win_w) // 2)
            if pos_y > screen_h - 120:
                pos_y = max(20, (screen_h - win_h) // 2)

            self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
            self.deiconify()
            self.update_idletasks()
            try:
                self.lift()
                if self._aggressive_wm:
                    self.focus_force()
            except tk.TclError:
                pass

            self._wm_fallback_applied = True
            self.output_queue.put(
                "\nDisplay fallback enabled: window manager mapping failed, "
                "using borderless mode. Press Q or use [Q]uit to close.\n"
            )
        except tk.TclError:
            pass

    def _build_cursor_options(self):
        # Windows Tkinter does not reliably support custom XBM cursors.
        # Use built-in cursors on Windows so the packaged .exe works.
        if sys.platform.startswith("win"):
            return [
                {
                    "name": "Magic Crosshair",
                    "description": "Precise magical aiming cursor.",
                    "builtin": "crosshair",
                },
                {
                    "name": "Hand",
                    "description": "Simple clickable hand cursor.",
                    "builtin": "hand2",
                },
                {
                    "name": "Watch",
                    "description": "Retro waiting cursor.",
                    "builtin": "watch",
                },
                {
                    "name": "Classic Arrow",
                    "description": "Default Windows cursor.",
                    "builtin": "arrow",
                },
            ]

        # Linux / WSL / X11 custom XBM cursors
        assets_dir = Path(__file__).resolve().parent / "assets"

        options = [
            {
                "name": "Lightsaber",
                "description": "Classic glowing blade cursor.",
                "cursor_file": assets_dir / "lightsaber_cursor.xbm",
                "mask_file": assets_dir / "lightsaber_cursor_mask.xbm",
                "fg": "white",
                "bg": "red",
            },
            {
                "name": "Cinderella",
                "description": "Literally a Cinderella-shaped cursor.",
                "cursor_file": assets_dir / "cinderella_cursor.xbm",
                "mask_file": assets_dir / "cinderella_cursor_mask.xbm",
                "fg": "white",
                "bg": "deepskyblue",
            },
            {
                "name": "Pumpkin",
                "description": "A fairytale pumpkin charm cursor.",
                "cursor_file": assets_dir / "pumpkin_cursor.xbm",
                "mask_file": assets_dir / "pumpkin_cursor_mask.xbm",
                "fg": "orange",
                "bg": "black",
            },
            {
                "name": "Magic Wand",
                "description": "Sparkly wand cursor for magical choices.",
                "cursor_file": assets_dir / "wand_cursor.xbm",
                "mask_file": assets_dir / "wand_cursor_mask.xbm",
                "fg": "gold",
                "bg": "black",
            },
            {
                "name": "Classic Arrow",
                "description": "Default arrow cursor for precision.",
                "builtin": "arrow",
            },
        ]

        available = []

        for option in options:
            cursor_file = option.get("cursor_file")
            mask_file = option.get("mask_file")

            if cursor_file and not Path(cursor_file).exists():
                continue

            if mask_file and not Path(mask_file).exists():
                continue

            available.append(option)

        if not available:
            return [{"name": "Classic Arrow", "description": "Default arrow cursor.", "builtin": "arrow"}]

        return available

    def _debug_cursor_test(self):
        self.output_queue.put("\nCursor debug test started.\n")

        test_cursors = ["crosshair", "hand2", "watch", "pirate", "arrow"]

        def apply_test(index=0):
            cursor_name = test_cursors[index % len(test_cursors)]

            try:
                self.configure(cursor=cursor_name)
                self.input_field.configure(cursor=cursor_name)
                self.log.configure(cursor=cursor_name)
                self.output_queue.put(f"Trying built-in cursor: {cursor_name}\n")
            except tk.TclError as exc:
                self.output_queue.put(f"Built-in cursor failed: {cursor_name} -> {exc}\n")

            if index + 1 < len(test_cursors):
                self.after(1200, lambda: apply_test(index + 1))

        apply_test()

    def _bind_cursor_selector_keys(self):
        # arrow keys are only for cursor menu while it is open
        if self._cursor_selector_keys_bound:
            return

        self.bind_all("<Left>", lambda e: self._cursor_prev())
        self.bind_all("<Right>", lambda e: self._cursor_next())
        self.bind_all("<Return>", lambda e: self._select_cursor_and_start())
        self.bind_all("<KP_Enter>", lambda e: self._select_cursor_and_start())
        self.bind_all("<Escape>", lambda e: self._select_cursor_and_start())
        self._cursor_selector_keys_bound = True

    def _unbind_cursor_selector_keys(self):
        # remove global binds so they dont mess with the actual game input
        if not getattr(self, "_cursor_selector_keys_bound", False):
            return

        for sequence in ("<Left>", "<Right>", "<Return>", "<KP_Enter>", "<Escape>"):
            try:
                self.unbind_all(sequence)
            except tk.TclError:
                pass

        self._cursor_selector_keys_bound = False

    def _show_cursor_selector(self):
        # first screen where player picks teh mouse cursor
        if hasattr(self, "cursor_overlay") and self.cursor_overlay.winfo_exists():
            self.cursor_overlay.lift()
            self._bind_cursor_selector_keys()
            return

        # overlay covers the normal game UI until player chooses cursor
        self.cursor_overlay = tk.Frame(self, bg="#030303")
        self.cursor_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        title_font = tkFont.Font(family="Monospace", size=18, weight="bold")
        body_font = tkFont.Font(family="Monospace", size=11)

        tk.Label(
            self.cursor_overlay,
            text="Choose Your Cursor",
            bg="#030303",
            fg="#00ff00",
            font=title_font,
        ).pack(pady=(45, 10))

        tk.Label(
            self.cursor_overlay,
            text="Use the arrows to browse cursor styles, then select one to begin.",
            bg="#030303",
            fg="#9cff9c",
            font=body_font,
        ).pack(pady=(0, 24))

        carousel = tk.Frame(self.cursor_overlay, bg="#030303")
        carousel.pack(pady=8)

        tk.Button(
            carousel,
            text="<",
            command=self._cursor_prev,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 14, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT, padx=12)

        info_frame = tk.Frame(carousel, bg="#050505", highlightbackground="#00ff00", highlightthickness=1)
        info_frame.pack(side=tk.LEFT, padx=8)

        self.cursor_name_var = tk.StringVar(value="")
        self.cursor_desc_var = tk.StringVar(value="")
        self.cursor_index_var = tk.StringVar(value="")

        tk.Label(
            info_frame,
            textvariable=self.cursor_name_var,
            bg="#050505",
            fg="#00ff00",
            font=("Monospace", 14, "bold"),
            width=30,
        ).pack(pady=(16, 8), padx=16)

        tk.Label(
            info_frame,
            textvariable=self.cursor_desc_var,
            bg="#050505",
            fg="#9cff9c",
            font=("Monospace", 10),
            width=46,
            wraplength=420,
            justify="center",
        ).pack(pady=(0, 8), padx=16)

        tk.Label(
            info_frame,
            textvariable=self.cursor_index_var,
            bg="#050505",
            fg="#6bff6b",
            font=("Monospace", 9),
        ).pack(pady=(0, 16))

        tk.Button(
            carousel,
            text=">",
            command=self._cursor_next,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 14, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT, padx=12)

        tk.Button(
            self.cursor_overlay,
            text="Select Cursor & Start",
            command=self._select_cursor_and_start,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 11, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(pady=(28, 6))

        self._refresh_cursor_selector()
        self._bind_cursor_selector_keys()
        self.cursor_overlay.lift()
        try:
            self.cursor_overlay.focus_set()
        except tk.TclError:
            pass

    def _refresh_cursor_selector(self):
        # refresh labels and also try the cursor live
        option = self.cursor_options[self.cursor_index]
        self.cursor_name_var.set(option["name"])
        self.cursor_desc_var.set(option["description"])
        self.cursor_index_var.set(f"{self.cursor_index + 1} / {len(self.cursor_options)}")
        self._apply_cursor_option(option)

    def _cursor_next(self):
        self.cursor_index = (self.cursor_index + 1) % len(self.cursor_options)
        self._refresh_cursor_selector()

    def _cursor_prev(self):
        self.cursor_index = (self.cursor_index - 1) % len(self.cursor_options)
        self._refresh_cursor_selector()

    def _select_cursor_and_start(self):
        # after picking cursor, close overlay and start game
        option = self.cursor_options[self.cursor_index]
        self._apply_cursor_option(option)
        self.output_queue.put(f"\nCursor selected: {option['name']}\n")
        if hasattr(self, "cursor_overlay") and self.cursor_overlay.winfo_exists():
            self._unbind_cursor_selector_keys()
            self.cursor_overlay.destroy()
        self.after(60, self._new_game)

    def _report_llm_status(self):
        # checks Ollama without freezing the interface
        if not self.llm_enabled:
            return

        def _worker():
            # import inside worker so missing narrator code doesnt break the whole UI at startup
            try:
                from pipeline.ai.narrator import check_ollama_status
                status = check_ollama_status(force=True)
                message = status.get("message", "LLM status unknown.")
                self.output_queue.put(f"\nLLM: {message}\n")
                self._update_llm_status_label(message)
            except Exception:
                self.output_queue.put("\nLLM: Unable to check Ollama status.\n")
                self._update_llm_status_label("LLM: Unable to check Ollama status.")

        threading.Thread(target=_worker, daemon=True).start()

    def _update_llm_status_label(self, message: str):
        # update label from tkinter thread only
        if not hasattr(self, "llm_status_var"):
            return
        self.after(0, lambda m=message: self.llm_status_var.set(m))

    def _toggle_llm(self):
        # flips narrator mode and update button text
        self.llm_enabled = not self.llm_enabled
        os.environ["USE_LLM_NARRATOR"] = "1" if self.llm_enabled else "0"
        self.llm_button.configure(text=f"LLM: {'ON' if self.llm_enabled else 'OFF'}")
        if self.llm_enabled:
            self.output_queue.put("\nLLM enabled.\n")
        else:
            self.output_queue.put("\nLLM disabled (deterministic narration).\n")
        self._refresh_llm_status()

    def _refresh_llm_status(self):
        # show useful LLM state under buttons
        if not self.llm_enabled:
            self._update_llm_status_label("LLM: Off")
            return
        self._report_llm_status()

    def _open_ollama_download(self):
        # open Ollama website in the right browser for WSL or normal OS
        url = "https://ollama.com/download"

        if self._is_wsl():
            if shutil.which("wslview"):
                subprocess.Popen(["wslview", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return

            if shutil.which("powershell.exe"):
                subprocess.Popen(
                    ["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{url}'"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            if shutil.which("cmd.exe"):
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            self.output_queue.put(f"\nOpen this URL in Windows: {url}\n")
            return

        try:
            if not webbrowser.open(url):
                self.output_queue.put(f"\nOpen this URL in your browser: {url}\n")
        except Exception:
            self.output_queue.put(f"\nOpen this URL in your browser: {url}\n")

    def _start_ollama(self):
        # start local Ollama server if it is installed
        if not shutil.which("ollama"):
            self.output_queue.put("\nLLM: Ollama CLI not found. Install Ollama first.\n")
            return

        def _worker():
            try:
                kwargs = {
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL,
                }
                if sys.platform.startswith("win"):
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(["ollama", "serve"], **kwargs)
                self.output_queue.put("\nLLM: Ollama server started.\n")
            except Exception:
                self.output_queue.put("\nLLM: Unable to start Ollama.\n")
            self._refresh_llm_status()

        threading.Thread(target=_worker, daemon=True).start()

    def _pull_ollama_model(self):
        # downloads teh model used by the narrator
        if not shutil.which("ollama"):
            self.output_queue.put("\nLLM: Ollama CLI not found. Install Ollama first.\n")
            return

        model = self.llm_model
        self.output_queue.put(f"\nLLM: Downloading model '{model}'...\n")

        def _worker():
            try:
                result = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True,
                    text=True,
                    timeout=900,
                    check=False,
                )
                if result.returncode == 0:
                    self.output_queue.put("\nLLM: Model download complete.\n")
                else:
                    stderr = (result.stderr or "").strip()
                    self.output_queue.put(
                        f"\nLLM: Model download failed ({stderr or 'unknown error'}).\n"
                    )
            except Exception:
                self.output_queue.put("\nLLM: Model download failed.\n")

            self._refresh_llm_status()

        threading.Thread(target=_worker, daemon=True).start()

    def _show_window(self):
        # puts game window somewhere sane and visible at startup
        if self._safe_mode:
            self._apply_safe_window_mode()
            return

        self._normalize_window_state()

        try:
            self.deiconify()
            self.state("normal")
        except tk.TclError:
            pass

        try:
            self.update_idletasks()
        except tk.TclError:
            pass

        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            win_w = self.winfo_width()
            win_h = self.winfo_height()
            pos_x = self.winfo_x()
            pos_y = self.winfo_y()

            if win_w < 200:
                win_w = 800
            if win_h < 200:
                win_h = 600

            if pos_x < 0 or pos_y < 0 or pos_x > screen_w - 100 or pos_y > screen_h - 100:
                new_x = max(20, (screen_w - win_w) // 2)
                new_y = max(20, (screen_h - win_h) // 2)
                self.geometry(f"{win_w}x{win_h}+{new_x}+{new_y}")
                self.update_idletasks()
        except tk.TclError:
            pass

        try:
            if self._aggressive_wm:
                self.lift()
                self.focus_force()
                self.attributes("-topmost", True)
                self.after(600, lambda: self.attributes("-topmost", False))
        except tk.TclError:
            pass

        self.after(40, self._apply_wm_fallback_if_needed)

    def _ensure_on_screen(self):
        # can be called after resize/move if window gets lost off screen
        if self._safe_mode:
            self._apply_safe_window_mode()
            return

        self._normalize_window_state()

        try:
            self.update_idletasks()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            win_w = self.winfo_width()
            win_h = self.winfo_height()
            pos_x = self.winfo_x()
            pos_y = self.winfo_y()

            if win_w < 200:
                win_w = 800
            if win_h < 200:
                win_h = 600

            if pos_x < 0 or pos_y < 0 or pos_x > screen_w - 100 or pos_y > screen_h - 100:
                new_x = max(20, (screen_w - win_w) // 2)
                new_y = max(20, (screen_h - win_h) // 2)
                self.geometry(f"{win_w}x{win_h}+{new_x}+{new_y}")
                self.update_idletasks()
        except tk.TclError:
            pass

        try:
            if self._aggressive_wm:
                self.lift()
                self.focus_force()
        except tk.TclError:
            pass

    def _setup_tts(self):
        # setup voice stuff, all optional so game should run without it
        if self._safe_mode:
            return

        # in WSL the Windows sound system is usually easier than linux audio
        if self._is_wsl() and shutil.which("powershell.exe"):
            try:
                self._edge_tts = importlib.import_module("edge_tts")
                self._tts_backend = "edge-tts"
                threading.Thread(target=self._tts_worker, daemon=True).start()
                return
            except Exception:
                self._tts_backend = "windows-sapi"
                threading.Thread(target=self._tts_worker, daemon=True).start()
                return

        if sys.platform.startswith("linux"):
            has_player = any(
                shutil.which(cmd) for cmd in ("aplay", "paplay", "pw-play", "play")
            )
            if not has_player:
                self.output_queue.put(
                    "\nTTS disabled: no Linux audio playback tool found. "
                    "Install alsa-utils (provides aplay).\n"
                )
                return

            if not self._linux_audio_device_available():
                self.output_queue.put(
                    "\nTTS disabled: no default audio device detected. "
                    "ALSA cannot open output in this environment.\n"
                )
                return

            if shutil.which("espeak-ng"):
                self._tts_backend = "espeak-ng"
                threading.Thread(target=self._tts_worker, daemon=True).start()
                return

        try:
            self._pyttsx3 = importlib.import_module("pyttsx3")
            self._tts_backend = "pyttsx3"
        except Exception:
            self.output_queue.put(
                "\nTTS disabled: install pyttsx3 or espeak-ng to enable narration voice.\n"
            )
            return

        threading.Thread(target=self._tts_worker, daemon=True).start()

    def _is_wsl(self):
        # WSL sets this env var, so this is enough for our case
        return bool(os.environ.get("WSL_DISTRO_NAME"))

    def _prepare_tts_segments(self, text):
        # clean narration and split it so voice queue does not get massive
        cleaned = " ".join((text or "").split())
        if not cleaned:
            return []

        if len(cleaned) > self._tts_max_chars:
            # cut long narration, otherwise voice keeps talking after player moved on
            cleaned = cleaned[: self._tts_max_chars].rsplit(" ", 1)[0] + "."

        if self._tts_backend in ("windows-sapi", "edge-tts"):
            return [cleaned]

        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", cleaned) if p.strip()]
        if not parts:
            return [cleaned]
        return parts

    def _discover_edge_voice(self):
        # tries to use best Edge voice from my prefered list
        default_voice = self._edge_voice_candidates[0]

        async def _list_voice_names():
            voices = await self._edge_tts.list_voices()
            names = []
            for voice in voices:
                short_name = voice.get("ShortName") or voice.get("Name") or ""
                if short_name:
                    names.append(short_name)
            return names

        try:
            available_names = set(asyncio.run(_list_voice_names()))
        except Exception:
            return default_voice

        for candidate in self._edge_voice_candidates:
            if candidate in available_names:
                return candidate

        return default_voice

    def _speak_windows_sapi(self, text):
        # use Windows built in voice from WSL, it is more reliable sometimes
        ps_script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$s.Volume=100;"
            f"$s.Rate={self._windows_voice_rate};"
            "$prefs=@('Microsoft Aria','Microsoft Jenny','Microsoft Zira','Microsoft Hazel','Microsoft David');"
            "$voices=$s.GetInstalledVoices()|ForEach-Object{$_.VoiceInfo.Name};"
            "$pick=$null;"
            "foreach($p in $prefs){$m=$voices|Where-Object{$_ -like \"*$p*\"}|Select-Object -First 1;if($m){$pick=$m;break}};"
            "if(-not $pick -and $voices.Count -gt 0){$pick=$voices[0]};"
            "if($pick){$s.SelectVoice($pick)};"
            "$t=[Console]::In.ReadToEnd();"
            "if($t){$s.Speak($t)}"
        )
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            input=text,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )

    def _wsl_path_to_windows_file_uri(self, linux_path):
        # converts linux path into a Windows file uri so Windows can play it
        distro = os.environ.get("WSL_DISTRO_NAME", "Ubuntu")
        path_text = str(Path(linux_path).resolve())
        windows_path = path_text.replace("/", "\\")
        unc_path = f"\\\\wsl$\\{distro}{windows_path}"
        return "file://" + unc_path.replace("\\", "/")

    def _synthesize_edge_audio_file(self, text):
        # edge tts writes a temp mp3, then Windows media player plays it
        if self._edge_tts is None:
            return None

        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        async def _run_synth():
            communicate = self._edge_tts.Communicate(
                text=text,
                voice=self._edge_voice,
                rate=self._edge_rate,
                pitch=self._edge_pitch,
                volume=self._edge_volume,
            )
            await communicate.save(temp_path)

        asyncio.run(_run_synth())
        return temp_path

    def _play_windows_media_uri(self, media_uri):
        # play generated mp3 on Windows audio stack and wait till it finishes
        ps_script = (
            "Add-Type -AssemblyName PresentationCore;"
            "$u=$args[0];"
            "$p=New-Object System.Windows.Media.MediaPlayer;"
            "$p.Open([Uri]$u);"
            "$p.Volume=1.0;"
            "$p.Play();"
            "$sw=[Diagnostics.Stopwatch]::StartNew();"
            "while(-not $p.NaturalDuration.HasTimeSpan -and $sw.ElapsedMilliseconds -lt 8000){Start-Sleep -Milliseconds 50};"
            "if($p.NaturalDuration.HasTimeSpan){$ms=[int]$p.NaturalDuration.TimeSpan.TotalMilliseconds+120; if($ms -gt 0){Start-Sleep -Milliseconds $ms}}"
            "else{Start-Sleep -Seconds 3};"
            "$p.Stop();"
            "$p.Close();"
        )
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script, media_uri],
            capture_output=True,
            text=True,
            timeout=50,
            check=False,
        )

    def _linux_audio_device_available(self):
        # basic audio check so linux tts doesnt spam errors
        pulse_server = (os.environ.get("PULSE_SERVER") or "").strip()
        if pulse_server.startswith("unix:/mnt/wslg/"):
            pulse_socket = pulse_server.replace("unix:", "", 1)
            if Path(pulse_socket).exists():
                return True

        if not shutil.which("aplay"):
            return True

        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except Exception:
            return False

        combined = (result.stdout + "\n" + result.stderr).lower()
        if "no soundcards found" in combined:
            return False

        return "card " in combined

    def _tts_worker(self):
        # real speech loop, running away from tkinter thread
        engine = None
        if self._tts_backend == "edge-tts":
            self.tts_available = True
            self.output_queue.put(
                f"\nTTS ready (Edge Neural voice: {self._edge_voice}). Press Ctrl+T to toggle narration voice.\n"
            )
        elif self._tts_backend == "windows-sapi":
            self.tts_available = True
            self.output_queue.put(
                "\nTTS ready (Windows voice). Press Ctrl+T to toggle narration voice.\n"
            )
        elif self._tts_backend == "espeak-ng":
            self.tts_available = True
            self.output_queue.put(
                "\nTTS ready (espeak-ng). Press Ctrl+T to toggle narration voice. "
                "(Reads text aloud; does not transcribe speech input.)\n"
            )
        else:
            try:
                engine = self._pyttsx3.init()
                engine.setProperty("rate", 185)
                self.tts_available = True
                self.output_queue.put(
                    "\nTTS ready. Press Ctrl+T to toggle narration voice. "
                    "(Reads text aloud; does not transcribe speech input.)\n"
                )
            except Exception as exc:
                self.output_queue.put(f"\nTTS disabled: {exc}\n")
                return

        while not self.tts_stop_event.is_set():
            # timeout lets the thread check stop_event often, so quit doesnt hang
            try:
                text = self.tts_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if text is None:
                break

            if not self.tts_enabled:
                continue

            try:
                if self._tts_backend == "edge-tts":
                    audio_path = self._synthesize_edge_audio_file(text)
                    if not audio_path:
                        continue
                    media_uri = self._wsl_path_to_windows_file_uri(audio_path)
                    result = self._play_windows_media_uri(media_uri)
                    try:
                        Path(audio_path).unlink(missing_ok=True)
                    except Exception:
                        pass
                    if result.returncode != 0:
                        stderr = (result.stderr or "").strip()
                        self.output_queue.put(
                            f"\nTTS warning: Edge Neural playback failed ({stderr or 'unknown error'}).\n"
                        )
                elif self._tts_backend == "windows-sapi":
                    result = self._speak_windows_sapi(text)
                    if result.returncode != 0:
                        stderr = (result.stderr or "").strip()
                        self.output_queue.put(
                            f"\nTTS warning: Windows voice failed ({stderr or 'unknown error'}).\n"
                        )
                elif self._tts_backend == "espeak-ng":
                    result = subprocess.run(
                        ["espeak-ng", "-s", str(self._tts_rate), "-v", "en-us", text],
                        capture_output=True,
                        text=True,
                        timeout=12,
                        check=False,
                    )
                    if result.returncode != 0:
                        stderr = (result.stderr or "").strip()
                        self.output_queue.put(
                            f"\nTTS warning: espeak-ng failed ({stderr or 'unknown error'}).\n"
                        )
                else:
                    engine.say(text)
                    engine.runAndWait()
            except Exception:
                continue

        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass

    def _queue_tts(self, text):
        # put latest narration into tts queue and clear old text
        if not self.tts_enabled or not self.tts_available:
            return

        segments = self._prepare_tts_segments(text)
        if not segments:
            return

        while True:
            try:
                self.tts_queue.get_nowait()
            except queue.Empty:
                break

        for segment in segments:
            self.tts_queue.put(segment)
    def _is_frozen_app(self):
        return bool(getattr(sys, "frozen", False))
    
    def _toggle_tts(self):
        # mute or unmute narration voice
        self.tts_enabled = not self.tts_enabled
        state_label = "ON" if self.tts_enabled else "OFF"
        self.tts_button.configure(text=f"TTS: {state_label}")

        if self.tts_enabled:
            self.output_queue.put("\nTTS enabled.\n")
        else:
            self.output_queue.put("\nTTS muted.\n")

    def _apply_cursor_option(self, option):
        cursor_candidates = []

        builtin = option.get("builtin")
        if builtin:
            cursor_candidates.append(builtin)
        else:
            cursor_file = option.get("cursor_file")
            mask_file = option.get("mask_file")
            fg = option.get("fg", "white")
            bg = option.get("bg", "black")

            if cursor_file:
                cursor_file = str(Path(cursor_file).resolve())

            if mask_file:
                mask_file = str(Path(mask_file).resolve())

            if cursor_file and Path(cursor_file).exists():
                if mask_file and Path(mask_file).exists():
                    cursor_candidates.append(f"@{cursor_file} {mask_file} {fg} {bg}")

                cursor_candidates.append(f"@{cursor_file} {fg} {bg}")
                cursor_candidates.append(f"@{cursor_file}")

        cursor_candidates.append("arrow")

        for cursor_spec in cursor_candidates:
            try:
                self.configure(cursor=cursor_spec)
                self.option_add("*cursor", cursor_spec)
                self._set_cursor_recursive(self, cursor_spec)
                return
            except tk.TclError:
                continue

        self.configure(cursor="arrow")
        self.option_add("*cursor", "arrow")
        self._set_cursor_recursive(self, "arrow")

    def _set_cursor_recursive(self, widget, cursor_spec):
        # apply cursor to every child widget, or some buttons keep old cursor
        try:
            widget.configure(cursor=cursor_spec)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_cursor_recursive(child, cursor_spec)

    def _start_background_video(self):
        # starts video check in seperate thread so bad cv2 doesnt freeze start
        if not self._video_requested or self._video_preflight_pending:
            return

        self._video_preflight_pending = True
        threading.Thread(target=self._background_video_worker, daemon=True).start()
        self.after(40, self._poll_background_video_preflight)

    def _background_video_worker(self):
        # only checks if imports are safe, real tkinter work happens later
        healthy = self._video_dependencies_healthy()
        self._video_preflight_queue.put(healthy)

    def _poll_background_video_preflight(self):
        # wait for video test result without blocking mainloop
        if not self._video_preflight_pending:
            return

        try:
            healthy = self._video_preflight_queue.get_nowait()
        except queue.Empty:
            self.after(40, self._poll_background_video_preflight)
            return

        self._video_preflight_pending = False
        self._setup_background_video(healthy)

    def _setup_background_video(self, dependencies_ok=True):
        # only setup video if checks passed
        if not self._video_requested:
            return

        if not dependencies_ok:
            return

        try:
            self._setup_background_video_impl()
        except Exception:
            self.output_queue.put(
                "\nVideo background disabled due to startup error. "
                "Set UI_BG_VIDEO=0 to force-disable it.\n"
            )
            self._stop_background_video()

    def _video_dependencies_healthy(self):
        # In a PyInstaller app, sys.executable points to the .exe itself.
        # Do not run [sys.executable, "-c", ...] because it can relaunch the app repeatedly.
        if self._is_frozen_app():
            try:
                importlib.import_module("cv2")
                importlib.import_module("PIL.Image")
                importlib.import_module("PIL.ImageTk")
                return True
            except Exception:
                self.output_queue.put(
                    "\nVideo background disabled: OpenCV/Pillow unavailable in packaged app.\n"
                )
                return False

        probe_cmd = [
            sys.executable,
            "-c",
            "import cv2; from PIL import Image, ImageTk; print('ok')",
        ]

        try:
            result = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except Exception:
            self.output_queue.put(
                "\nVideo background disabled: dependency preflight failed. "
                "Set UI_BG_VIDEO=0 to silence this message.\n"
            )
            return False

        if result.returncode != 0:
            self.output_queue.put(
                "\nVideo background disabled: OpenCV/Pillow check failed in this environment. "
                "Set UI_BG_VIDEO=0 to silence this message.\n"
            )
            return False

        return True

    def _setup_background_video_impl(self):
        # setup video frames inside the canvas, not as a seperate window
        if not self._video_path.exists():
            self.output_queue.put(
                f"\nVideo background disabled: file not found:\n{self._video_path}\n"
            )
            return

        try:
            cv2_mod = importlib.import_module("cv2")
            pil_image = importlib.import_module("PIL.Image")
            pil_imagetk = importlib.import_module("PIL.ImageTk")
        except Exception as exc:
            self.output_queue.put(
                f"\nVideo background disabled: missing dependency: {exc}\n"
                "Install with: pip install pillow opencv-python\n"
            )
            return

        # OpenCV reads the mp4 frame by frame and later PIL converts it for tkinter
        capture = cv2_mod.VideoCapture(str(self._video_path))

        if not capture.isOpened():
            capture.release()
            self.output_queue.put(
                f"\nVideo background disabled: OpenCV could not open:\n{self._video_path}\n"
            )
            return

        self._video_cv2 = cv2_mod
        self._video_image_cls = pil_image
        self._video_image_tk = pil_imagetk
        self._video_capture = capture
        self._video_enabled = True

        self.output_queue.put("\nVideo background ready.\n")
        self.after(50, self._render_video_frame)

    def _on_root_configure_video(self, _event=None):
        # debounce resize events for the older video window mode
        if not self._video_requested or not self._video_enabled:
            return
        if self._video_geometry_sync_pending:
            return
        self._video_geometry_sync_pending = True
        self.after(15, self._sync_video_window_geometry)

    def _sync_video_window_geometry(self):
        # keep helper video window same size as root when using that mode
        self._video_geometry_sync_pending = False

        if self._video_window is None:
            return

        try:
            if not self._video_window.winfo_exists():
                return
        except tk.TclError:
            return

        try:
            state = self.state()
        except tk.TclError:
            state = "normal"

        if state in ("iconic", "withdrawn"):
            try:
                self._video_window.withdraw()
            except tk.TclError:
                pass
            return

        try:
            self.update_idletasks()
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
        except tk.TclError:
            return

        if w < 80 or h < 80:
            return

        try:
            self._video_window.geometry(f"{w}x{h}+{x}+{y}")
            self._place_video_behind_root()
        except tk.TclError:
            pass

    def _render_video_frame(self):
        # draw one video frame behind terminal text, then schedule next frame
        if not self._video_enabled or self._video_capture is None:
            return

        try:
            ok, frame = self._video_capture.read()
            if not ok:
                self._video_capture.set(self._video_cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._video_capture.read()

            if ok:
                target_widget = self._video_window if self._video_window is not None else self
                target_w = max(1, target_widget.winfo_width())
                target_h = max(1, target_widget.winfo_height())

                frame = self._video_cv2.resize(
                    frame,
                    (target_w, target_h),
                    interpolation=self._video_cv2.INTER_AREA,
                )

                # convert to gray so background looks more retro and not too noisy
                gray = self._video_cv2.cvtColor(frame, self._video_cv2.COLOR_BGR2GRAY)
                frame = self._video_cv2.cvtColor(gray, self._video_cv2.COLOR_GRAY2BGR)

                blur_ksize = getattr(self, "_video_blur_ksize", 0)
                if blur_ksize and blur_ksize >= 3:
                    frame = self._video_cv2.GaussianBlur(frame, (blur_ksize, blur_ksize), 0)

                frame = self._video_cv2.convertScaleAbs(frame, alpha=self._video_darkness, beta=0)
                rgb = self._video_cv2.cvtColor(frame, self._video_cv2.COLOR_BGR2RGB)

                image = self._video_image_cls.fromarray(rgb)
                self._video_photo = self._video_image_tk.PhotoImage(image=image)

                if self._video_canvas_image_id is None:
                    # first frame creates the canvas image, next frames only replace image data
                    self._video_canvas_image_id = self.log.create_image(
                        0,
                        0,
                        anchor="nw",
                        image=self._video_photo,
                        tags=(self._video_bg_tag,),
                    )
                else:
                    self.log.itemconfig(
                        self._video_canvas_image_id,
                        image=self._video_photo,
                    )

                self.log.tag_lower(self._video_bg_tag)
                self.log.tag_raise(self._terminal_text_tag)

        except Exception as exc:
            self.output_queue.put(
                f"\nVideo background crashed: {type(exc).__name__}: {exc}\n"
            )
            self._video_enabled = False
            return

        self._video_after_id = self.after(self._video_frame_interval_ms, self._render_video_frame)

    def _stop_background_video(self):
        # cleanup video resources before closing app
        self._video_enabled = False
        self._video_preflight_pending = False

        if self._video_after_id is not None:
            try:
                self.after_cancel(self._video_after_id)
            except Exception:
                pass
            self._video_after_id = None

        if self._video_capture is not None:
            try:
                self._video_capture.release()
            except Exception:
                pass
            self._video_capture = None

        self._video_canvas_image_id = None

    def _setup_ui(self):
        # main terminal uses canvas so video can sit under text
        self._terminal_font = tkFont.Font(family="Monospace", size=11)
        self._terminal_line_height = self._terminal_font.metrics("linespace") + 3
        self._terminal_lines = [("", None)]
        self._terminal_text_items = []
        self._terminal_margin = 10
        self._video_canvas_image_id = None

        self.log = tk.Canvas(
            self,
            bg="#000000",
            highlightthickness=0,
            bd=0,
        )
        # canvas acts like a fake terminal, because ScrolledText cant have video behind it
        self.log.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self._terminal_font = tkFont.Font(family="Monospace", size=11)
        self._terminal_line_height = self._terminal_font.metrics("linespace") + 3
        self._terminal_lines = [("", None)]
        self._terminal_text_items = []
        self._terminal_margin = 10

        self._video_canvas_image_id = None
        self._terminal_text_tag = "terminal_text"
        self._video_bg_tag = "video_bg"
        # tags make z-order easy: video goes down and text comes up
        self.log.bind("<Configure>", lambda _e: self._redraw_terminal_text())

        # bottom input box where player types action number or text
        input_frame = tk.Frame(self, bg="#000000")
        input_frame.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(
            input_frame,
            text="> ",
            bg="#000000",
            fg="#00ff00",
            font=self._terminal_font,
        ).pack(side=tk.LEFT)

        self.input_field = tk.Entry(
            input_frame,
            bg="#000000",
            fg="#00ff00",
            font=self._terminal_font,
            insertbackground="#00ff00",
        )
        self.input_field.pack(fill=tk.X, side=tk.LEFT, padx=0, expand=True)
        self.input_field.bind("<Return>", lambda e: self._submit_input())

        # small controls, keeping them ugly-retro on purpose
        button_frame = tk.Frame(self, bg="#000000")
        button_frame.pack(fill=tk.X, padx=2, pady=2)

        tk.Button(
            button_frame,
            text="[N]ew Game",
            command=self._new_game,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="[Q]uit",
            command=self._quit_game,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        ).pack(side=tk.LEFT, padx=2)

        self.tts_button = tk.Button(
            button_frame,
            text="TTS: ON",
            command=self._toggle_tts,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        )
        self.tts_button.pack(side=tk.LEFT, padx=2)

        # LLM helper controls for Ollama narrator
        llm_frame = tk.Frame(self, bg="#000000")
        llm_frame.pack(fill=tk.X, padx=2, pady=2)

        self.llm_button = tk.Button(
            llm_frame,
            text=f"LLM: {'ON' if self.llm_enabled else 'OFF'}",
            command=self._toggle_llm,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        )
        self.llm_button.pack(side=tk.LEFT, padx=2)

        tk.Button(
            llm_frame,
            text="Install Ollama",
            command=self._open_ollama_download,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            llm_frame,
            text="Start Ollama",
            command=self._start_ollama,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            llm_frame,
            text="Download Model",
            command=self._pull_ollama_model,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        ).pack(side=tk.LEFT, padx=2)

        self.llm_status_var = tk.StringVar(
            value="LLM: Off" if not self.llm_enabled else "LLM: Checking..."
        )

        tk.Label(
            llm_frame,
            textvariable=self.llm_status_var,
            bg="#000000",
            fg="#00ff00",
            font=("Monospace", 9),
        ).pack(side=tk.LEFT, padx=6)

        # keyboard shortcuts for faster testing
        self.bind("n", lambda e: self._new_game() if self.input_state in ["IDLE", "GAME_OVER"] else None)
        self.bind("q", lambda e: self._quit_game())
        self.bind("<Control-t>", lambda e: self._toggle_tts())
        self.bind("<Control-T>", lambda e: self._toggle_tts())

    def _color_for_tag(self, tag):
        # colors by message type, default is normal terminal green
        if tag == "prompt":
            return "#ffff00"
        if tag == "system":
            return "#00ffff"
        return "#00ff00"

    def _clear_terminal(self):
        # clear only terminal text, video background can stay alive
        self._terminal_lines = [("", None)]

        try:
            self.log.delete(self._terminal_text_tag)
        except tk.TclError:
            pass

        self._terminal_text_items.clear()
        self._redraw_terminal_text()

    def _append_text(self, text, tag=None):
        # add text to our fake terminal buffer char by char
        if not hasattr(self, "_terminal_lines"):
            return

        for char in text:
            if char == "\n":
                self._terminal_lines.append(("", tag))
            else:
                current_text, current_tag = self._terminal_lines[-1]

                if current_text == "":
                    current_tag = tag

                self._terminal_lines[-1] = (current_text + char, current_tag)

        if len(self._terminal_lines) > 500:
            self._terminal_lines = self._terminal_lines[-500:]

        self._redraw_terminal_text()

    def _redraw_terminal_text(self):
        # redraw visible wrapped lines on top of video every time text changes
        if not hasattr(self, "log"):
            return

        try:
            self.log.delete(self._terminal_text_tag)
            self._terminal_text_items.clear()

            width = max(100, self.log.winfo_width() - self._terminal_margin * 2)
            height = max(100, self.log.winfo_height() - self._terminal_margin * 2)

            char_width = max(1, self._terminal_font.measure("M"))
            max_chars = max(10, width // char_width)

            visual_lines = []

            # convert logical lines into wrapped screen lines based on current canvas width
            for raw_line, tag in self._terminal_lines:
                if raw_line == "":
                    visual_lines.append(("", tag))
                    continue

                wrapped = textwrap.wrap(
                    raw_line,
                    width=max_chars,
                    replace_whitespace=False,
                    drop_whitespace=False,
                )

                for part in wrapped:
                    visual_lines.append((part, tag))

            max_visible = max(1, height // self._terminal_line_height)
            # only draw last lines, like terminal scrollback staying at bottom
            visible_lines = visual_lines[-max_visible:]

            y = self._terminal_margin

            for line, tag in visible_lines:
                color = self._color_for_tag(tag)

                # black shadow helps readability when the video background is bright
                shadow = self.log.create_text(
                    self._terminal_margin + 2,
                    y + 2,
                    anchor="nw",
                    text=line,
                    fill="#000000",
                    font=self._terminal_font,
                    tags=(self._terminal_text_tag,),
                )

                item = self.log.create_text(
                    self._terminal_margin,
                    y,
                    anchor="nw",
                    text=line,
                    fill=color,
                    font=self._terminal_font,
                    tags=(self._terminal_text_tag,),
                )

                self._terminal_text_items.extend([shadow, item])
                y += self._terminal_line_height

            if self._video_canvas_image_id is not None:
                self.log.tag_lower(self._video_bg_tag)

            self.log.tag_raise(self._terminal_text_tag)

        except tk.TclError:
            pass

    def _drain_output_queue(self):
        # move thread output into typewriter queue for smooth terminal effect
        while True:
            try:
                chunk = self.output_queue.get_nowait()
            except queue.Empty:
                break
            # split into chars here so _typewriter_loop can control the speed
            for char in chunk:
                self.typewriter_queue.put(char)
        self.after(40, self._drain_output_queue)

    def _typewriter_loop(self):
        # prints few chars at a time, fast enough but still looks alive
        chunk = []
        for _ in range(8):
            try:
                chunk.append(self.typewriter_queue.get_nowait())
            except queue.Empty:
                break

        if chunk:
            self._append_text("".join(chunk))

        self.after(5, self._typewriter_loop)

    def _new_game(self):
        # reset screen and start fresh game in background thread
        if self.input_state == "PROCESSING":
            return

        self._clear_terminal()
        self.input_field.delete(0, tk.END)

        self._append_text("Initializing game...\n", "system")
        self.input_state = "PROCESSING"

        threading.Thread(target=self._run_new_game_thread, daemon=True).start()
        self.input_field.focus_set()

    def _run_new_game_thread(self):
        # engine work is seperate so tkinter doesnt become unresponsive
        try:
            if self.engine is None:
                self.engine = GameEngine()
            packet = self.engine.new_game()
            self.after(0, self._handle_engine_response, packet)
        except Exception as e:
            self.output_queue.put(f"\nEngine Error: {str(e)}\n")
            self.input_state = "GAME_OVER"

    def _submit_input(self):
        # handles Enter key based on what the game is asking for
        # strip removes random spaces so typing ' 1 ' still works
        user_input = self.input_field.get().strip()
        if not user_input or self.input_state not in ["WAITING_FOR_ACTION", "WAITING_FOR_TEXT"]:
            return

        self._append_text(f"> {user_input}\n", "prompt")
        self.input_field.delete(0, tk.END)

        if self.input_state == "WAITING_FOR_ACTION":
            if not user_input.isdigit():
                self.output_queue.put("Please enter a valid action number.\n")
                return

            choice_num = int(user_input)
            actions = self.current_packet.get("actions", [])

            if not (1 <= choice_num <= len(actions)):
                self.output_queue.put("That number is not one of the available actions.\n")
                return

            action_index = choice_num - 1
            chosen_action = actions[action_index]

            # some actions need extra text, like entering a name or answer
            if chosen_action.get("input_required"):
                self.pending_action_index = action_index
                self.input_state = "WAITING_FOR_TEXT"
                hint = chosen_action.get("input_hint", "Enter input:")
                self.output_queue.put(f"\n{hint}\n")
                return

            self.input_state = "PROCESSING"
            self.output_queue.put("\nProcessing...\n")
            threading.Thread(
                target=self._run_submit_choice_thread,
                args=(action_index, None),
                daemon=True,
            ).start()

        elif self.input_state == "WAITING_FOR_TEXT":
            self.input_state = "PROCESSING"
            self.output_queue.put("\nProcessing...\n")
            threading.Thread(
                target=self._run_submit_choice_thread,
                args=(self.pending_action_index, user_input),
                daemon=True,
            ).start()

    def _run_submit_choice_thread(self, action_index, user_input):
        # send selected action to engine outside the UI thread
        try:
            packet = self.engine.submit_choice(action_index, user_input=user_input)
            self.after(0, self._handle_engine_response, packet)
        except Exception as e:
            self.output_queue.put(f"\nEngine Error: {str(e)}\n")
            self.input_state = "GAME_OVER"

    def _handle_engine_response(self, packet):
        # engine packet comes back here and UI decides next state
        self.current_packet = packet
        display_text = self._format_packet(packet)
        self.output_queue.put(display_text)
        self._queue_tts(packet.get("narration", ""))

        # decide if the game should still accept choices after this packet
        if packet.get("game_over") or packet.get("game_complete") or packet.get("health", 0) <= 0:
            self.input_state = "GAME_OVER"
        else:
            self.input_state = "WAITING_FOR_ACTION"

    def _format_packet(self, packet):
        # convert engine data into old-school terminal text
        lines = ["" + "-" * 50]
        # this list is joined at the end, easier than making one huge string

        scene_id = packet.get("scene_id", "Unknown")
        health = packet.get("health", 0)
        inv = packet.get("inventory", [])
        inv_str = ", ".join(inv) if inv else "empty"

        lines.append(f"Scene: {scene_id} | Health: {health}")
        lines.append(f"Inventory: {inv_str}")
        lines.append("-" * 50 + "\n")

        if packet.get("narration"):
            lines.append(packet["narration"] + "\n")

        for status_line in packet.get("status_lines", []):
            lines.append(status_line)

        if packet.get("status_lines"):
            lines.append("")

        # end screens are formatted here instead of inside engine so UI controls the look
        if packet.get("health", 0) <= 0 or packet.get("game_over"):
            lines.append("\nGAME OVER")
            lines.append("=" * 50 + "\n")
        elif packet.get("game_complete"):
            lines.append("\nYOU WIN!")
            lines.append("Snow White has been rescued.")
            lines.append("=" * 50 + "\n")
        else:
            actions = packet.get("actions", [])
            if actions:
                lines.append("Actions:")
                for i, action in enumerate(actions, start=1):
                    lines.append(f"{i}. {action.get('label', 'Unknown Action')}")
            else:
                lines.append("No available actions. You are stuck.")

        return "\n".join(lines) + "\n"

    def _quit_game(self):
        # stop bg workers and close the window cleanly
        self._stop_background_video()
        self.tts_stop_event.set()
        self.tts_queue.put(None)
        self.destroy()


def run():
    # small launcher function so main_ui.py can import it
    app = GameApp()
    app.mainloop()


if __name__ == "__main__":
    run()
