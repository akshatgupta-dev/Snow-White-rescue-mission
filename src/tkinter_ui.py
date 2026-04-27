"""
Retro Tkinter UI for the game (Zork-like aesthetic).

Simple window with:
- Black background, green monospace text
- Story scrollable text area
- Input field at bottom
- Minimal buttons (New Game, Quit)
- Typewriter effect on text output

Integrates with GameEngine using packet-based calls.
Engine execution runs in background threads so Tkinter stays responsive.
"""

import queue
import threading
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
from tkinter import scrolledtext

from src.game_engine import GameEngine


class GameApp(tk.Tk):
    """Retro terminal-style game window."""

    def __init__(self):
        super().__init__()
        self.title("Cinderella Rescues Snow White")
        self.geometry("800x600")
        self.config(bg="#000000")

        self.engine = None

        self._wsl_runtime = self._is_wsl()
        self._safe_mode = os.environ.get("UI_SAFE_MODE", "").lower() in {"1", "true", "yes", "on"}
        # WSL/Xwayland sessions in this project frequently start Tk windows iconified.
        # Default to safe mode under WSL unless explicitly overridden.
        if self._wsl_runtime and os.environ.get("UI_FORCE_SAFE_WSL", "").lower() in {"1", "true", "yes", "on"}:
            self._safe_mode = True
        self._aggressive_wm = (
            os.environ.get("UI_AGGRESSIVE_WM", "").lower() in {"1", "true", "yes", "on"}
        ) and (not self._safe_mode)
        
        self.output_queue = queue.Queue()
        self.typewriter_queue = queue.Queue()  # Queue for typewriter effect
        self.tts_queue = queue.Queue()
        self.tts_stop_event = threading.Event()
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
        self.llm_enabled = False
        self.llm_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b-instruct-q4_K_M")
        self.cursor_options = self._build_cursor_options()
        self.cursor_index = 0
        self._video_path = Path(__file__).resolve().parent / "assets" / "Vietnamese_Jedi_with_Red_Lightsaber.mp4"
        self._video_capture = None
        self._video_after_id = None
        self._video_photo = None
        self._video_label = None
        self._video_enabled = False
        video_default = "0" if self._safe_mode else "1"
        self._video_requested = False
        self._video_frame_interval_ms = 95
        self._video_darkness = 0.18
        self._video_cv2 = None
        self._video_image_cls = None
        self._video_image_tk = None
        self._video_preflight_queue = queue.Queue()
        self._video_preflight_pending = False
        self._wm_fallback_applied = False
        self._safe_window_mode_applied = False
        cursor_default = "0" if self._safe_mode else "1"
        self._custom_cursor_enabled = (
            os.environ.get("UI_CUSTOM_CURSOR", cursor_default).lower() in {"1", "true", "yes", "on"}
        )
        self._cursor_selector_keys_bound = False
        
        # UI State Management
        self.current_packet = None
        self.input_state = "IDLE"  # IDLE, WAITING_FOR_ACTION, WAITING_FOR_TEXT, PROCESSING
        self.pending_action_index = -1
        
        # --- Minimal Known-Good Startup Sequence ---
        self._setup_ui()

        self._video_requested = False
        self.llm_enabled = False

        self.after(0, lambda: self._append_text("UI booted successfully.\n", "system"))
        self.after(100, self._show_window)
        if self._custom_cursor_enabled:
            self.after(200, self._show_cursor_selector)
        else:
            self.after(200, self._new_game)
        self.after(40, self._drain_output_queue)
        self.after(5, self._typewriter_loop)

    def _apply_safe_window_mode(self):
        """Force an always-mapped borderless window for fragile WSL/Xwayland sessions."""
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
            # self.overrideredirect(True)
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
        """Ensure the root window is not left minimized/withdrawn by the WM."""
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
        """Return True when the window is still effectively hidden/unmapped."""
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
        """Fallback for sessions where the WM keeps Tk windows iconified/unmapped."""
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

            # Prefer a primary-screen friendly position instead of virtual-desktop center.
            pos_x = 60
            pos_y = 60
            if pos_x > screen_w - 120:
                pos_x = max(20, (screen_w - win_w) // 2)
            if pos_y > screen_h - 120:
                pos_y = max(20, (screen_h - win_h) // 2)

            # Force direct mapping without relying on WM decorations.
            # self.overrideredirect(True)
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

        # Filter out cursor options whose bitmap files are not present (common in
        # partially-packaged builds). Keep built-ins.
        available = []
        for option in options:
            cursor_file = option.get("cursor_file")
            if cursor_file and (not Path(cursor_file).exists()):
                continue
            available.append(option)

        if not available:
            return [{"name": "Classic Arrow", "description": "Default arrow cursor.", "builtin": "arrow"}]

        return available

    def _bind_cursor_selector_keys(self):
        if self._cursor_selector_keys_bound:
            return

        self.bind_all("<Left>", lambda e: self._cursor_prev())
        self.bind_all("<Right>", lambda e: self._cursor_next())
        self.bind_all("<Return>", lambda e: self._select_cursor_and_start())
        self.bind_all("<KP_Enter>", lambda e: self._select_cursor_and_start())
        self.bind_all("<Escape>", lambda e: self._select_cursor_and_start())
        self._cursor_selector_keys_bound = True

    def _unbind_cursor_selector_keys(self):
        if not getattr(self, "_cursor_selector_keys_bound", False):
            return

        for sequence in ("<Left>", "<Right>", "<Return>", "<KP_Enter>", "<Escape>"):
            try:
                self.unbind_all(sequence)
            except tk.TclError:
                pass

        self._cursor_selector_keys_bound = False

    def _show_cursor_selector(self):
        """Show startup carousel for cursor selection."""
        if hasattr(self, "cursor_overlay") and self.cursor_overlay.winfo_exists():
            self.cursor_overlay.lift()
            self._bind_cursor_selector_keys()
            return

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
        option = self.cursor_options[self.cursor_index]
        self._apply_cursor_option(option)
        self.output_queue.put(f"\nCursor selected: {option['name']}\n")
        if hasattr(self, "cursor_overlay") and self.cursor_overlay.winfo_exists():
            self._unbind_cursor_selector_keys()
            self.cursor_overlay.destroy()
        self.after(60, self._new_game)

    def _report_llm_status(self):
        """Report Ollama status when LLM narration is enabled."""
        if not self.llm_enabled:
            return

        def _worker():
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
        if not hasattr(self, "llm_status_var"):
            return
        self.after(0, lambda m=message: self.llm_status_var.set(m))

    def _toggle_llm(self):
        self.llm_enabled = not self.llm_enabled
        os.environ["USE_LLM_NARRATOR"] = "1" if self.llm_enabled else "0"
        self.llm_button.configure(text=f"LLM: {'ON' if self.llm_enabled else 'OFF'}")
        if self.llm_enabled:
            self.output_queue.put("\nLLM enabled.\n")
        else:
            self.output_queue.put("\nLLM disabled (deterministic narration).\n")
        self._refresh_llm_status()

    def _refresh_llm_status(self):
        if not self.llm_enabled:
            self._update_llm_status_label("LLM: Off")
            return
        self._report_llm_status()

    def _open_ollama_download(self):
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
        """Bring the game window to the front on startup."""
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

        # If WM still refuses to map the window, attempt fallback quickly.
        self.after(40, self._apply_wm_fallback_if_needed)

    def _ensure_on_screen(self):
        """Force the window to a visible position if the WM places it off-screen."""
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
        """Initialize optional text-to-speech worker thread."""
        if self._safe_mode:
            return

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
        """Return True when running under Windows Subsystem for Linux."""
        return bool(os.environ.get("WSL_DISTRO_NAME"))

    def _prepare_tts_segments(self, text):
        """Normalize and split narration into short chunks for smoother playback."""
        cleaned = " ".join((text or "").split())
        if not cleaned:
            return []

        if len(cleaned) > self._tts_max_chars:
            cleaned = cleaned[: self._tts_max_chars].rsplit(" ", 1)[0] + "."

        # Windows SAPI is launched via subprocess, so one chunk per narration is smoother.
        if self._tts_backend in ("windows-sapi", "edge-tts"):
            return [cleaned]

        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", cleaned) if p.strip()]
        if not parts:
            return [cleaned]
        return parts

    def _discover_edge_voice(self):
        """Pick the best available Edge neural voice from a preferred shortlist."""
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
        """Speak via Windows SAPI with preferred voices when running in WSL."""
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
        """Convert a WSL path to a Windows-readable file URI via \\wsl$ share."""
        distro = os.environ.get("WSL_DISTRO_NAME", "Ubuntu")
        path_text = str(Path(linux_path).resolve())
        unc_path = f"\\\\wsl$\\{distro}{path_text.replace('/', '\\')}"
        return "file://" + unc_path.replace("\\", "/")

    def _synthesize_edge_audio_file(self, text):
        """Synthesize narration to mp3 using Edge Neural TTS."""
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
        """Play media URI on Windows audio stack and wait until playback finishes."""
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
        """Return True when Linux has either ALSA cards or a WSLg Pulse socket."""
        pulse_server = (os.environ.get("PULSE_SERVER") or "").strip()
        if pulse_server.startswith("unix:/mnt/wslg/"):
            pulse_socket = pulse_server.replace("unix:", "", 1)
            if Path(pulse_socket).exists():
                return True

        if not shutil.which("aplay"):
            # Other players may still work; only hard-check ALSA if aplay exists.
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

        # Require at least one listed card when querying ALSA device list.
        return "card " in combined

    def _tts_worker(self):
        """Background speech loop so UI remains responsive during narration playback."""
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
                # If speech fails once, keep the game playable and silently continue.
                continue

        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass

    def _queue_tts(self, text):
        """Queue narration text for voice playback."""
        if not self.tts_enabled or not self.tts_available:
            return

        segments = self._prepare_tts_segments(text)
        if not segments:
            return

        # Keep only the latest narration to avoid long speech backlog.
        while True:
            try:
                self.tts_queue.get_nowait()
            except queue.Empty:
                break

        for segment in segments:
            self.tts_queue.put(segment)

    def _toggle_tts(self):
        """Enable or disable narration voice."""
        self.tts_enabled = not self.tts_enabled
        state_label = "ON" if self.tts_enabled else "OFF"
        self.tts_button.configure(text=f"TTS: {state_label}")

        if self.tts_enabled:
            self.output_queue.put("\nTTS enabled.\n")
        else:
            self.output_queue.put("\nTTS muted.\n")

    def _apply_cursor_option(self, option):
        """Apply a cursor option from the carousel."""
        cursor_candidates = []

        builtin = option.get("builtin")
        if builtin:
            cursor_candidates.append(builtin)
        else:
            cursor_file = option.get("cursor_file")
            mask_file = option.get("mask_file")
            fg = option.get("fg", "white")
            bg = option.get("bg", "black")

            if cursor_file and Path(cursor_file).exists():
                if mask_file and Path(mask_file).exists():
                    cursor_candidates.append(f"@{cursor_file} {mask_file} {fg} {bg}")

                cursor_candidates.append(f"@{cursor_file} {fg} {bg}")
                cursor_candidates.append(f"@{cursor_file}")

        cursor_candidates.append("arrow")

        for cursor_spec in cursor_candidates:
            try:
                # Validate cursor on the root first; then apply broadly.
                self.configure(cursor=cursor_spec)
                self.option_add("*cursor", cursor_spec)
                self._set_cursor_recursive(self, cursor_spec)
                return
            except tk.TclError:
                continue

    def _set_cursor_recursive(self, widget, cursor_spec):
        """Apply a cursor to the widget tree so existing controls match the root cursor."""
        try:
            widget.configure(cursor=cursor_spec)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_cursor_recursive(child, cursor_spec)

    def _start_background_video(self):
        """Start asynchronous preflight for optional background video."""
        if not self._video_requested or self._video_preflight_pending:
            return

        self._video_preflight_pending = True
        threading.Thread(target=self._background_video_worker, daemon=True).start()
        self.after(40, self._poll_background_video_preflight)

    def _background_video_worker(self):
        """Run dependency checks off the Tk main thread, then notify UI thread."""
        healthy = self._video_dependencies_healthy()
        self._video_preflight_queue.put(healthy)

    def _poll_background_video_preflight(self):
        """Poll worker result from the Tk thread, then continue setup safely."""
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
        """Create a dark looping background video layer behind all UI widgets."""
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
        """Probe video imports in a subprocess so native crashes cannot kill the UI process."""
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
        """Internal background video setup implementation."""
        self._video_label = tk.Label(self, bg="#000000", bd=0, highlightthickness=0)
        self._video_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._video_label.lower()

        if not self._video_path.exists():
            return

        try:
            cv2_mod = importlib.import_module("cv2")
            pil_image = importlib.import_module("PIL.Image")
            pil_imagetk = importlib.import_module("PIL.ImageTk")
        except Exception:
            self.output_queue.put(
                "\nVideo background disabled: install pillow and opencv-python-headless to enable it. "
                "Set UI_BG_VIDEO=0 to disable this warning.\n"
            )
            return

        capture = cv2_mod.VideoCapture(str(self._video_path))
        if not capture.isOpened():
            capture.release()
            self.output_queue.put("\nVideo background disabled: unable to open background video file.\n")
            return

        self._video_cv2 = cv2_mod
        self._video_image_cls = pil_image
        self._video_image_tk = pil_imagetk
        self._video_capture = capture
        self._video_enabled = True
        self.after(80, self._render_video_frame)

    def _render_video_frame(self):
        """Render one frame of the background video, darkened for readability."""
        if not self._video_enabled or self._video_capture is None:
            return

        try:
            ok, frame = self._video_capture.read()
            if not ok:
                self._video_capture.set(self._video_cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._video_capture.read()

            if ok:
                target_w = max(1, self.winfo_width())
                target_h = max(1, self.winfo_height())

                frame = self._video_cv2.resize(
                    frame,
                    (target_w, target_h),
                    interpolation=self._video_cv2.INTER_AREA,
                )

                gray = self._video_cv2.cvtColor(frame, self._video_cv2.COLOR_BGR2GRAY)
                frame = self._video_cv2.cvtColor(gray, self._video_cv2.COLOR_GRAY2BGR)
                frame = self._video_cv2.convertScaleAbs(frame, alpha=self._video_darkness, beta=0)
                rgb = self._video_cv2.cvtColor(frame, self._video_cv2.COLOR_BGR2RGB)

                image = self._video_image_cls.fromarray(rgb)
                self._video_photo = self._video_image_tk.PhotoImage(image=image)
                self._video_label.configure(image=self._video_photo)
                self._video_label.lower()
        except Exception:
            self._video_enabled = False
            return

        self._video_after_id = self.after(self._video_frame_interval_ms, self._render_video_frame)

    def _stop_background_video(self):
        """Stop frame loop and release media resources."""
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

    def _setup_ui(self):
        """Build minimal retro UI."""
        # Story log (green-on-black, monospace)
        mono_font = tkFont.Font(family="Monospace", size=11)
        self.log = scrolledtext.ScrolledText(
            self,
            bg="#000000",
            fg="#00ff00",
            font=mono_font,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Configure text tags for styling
        self.log.tag_config("prompt", foreground="#ffff00")  # Yellow for user input
        self.log.tag_config("system", foreground="#00ffff")  # Cyan for system messages

        # Input frame (black bg to match)
        input_frame = tk.Frame(self, bg="#000000")
        input_frame.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(input_frame, text="> ", bg="#000000", fg="#00ff00", font=mono_font).pack(
            side=tk.LEFT
        )
        self.input_field = tk.Entry(
            input_frame, bg="#000000", fg="#00ff00", font=mono_font, insertbackground="#00ff00"
        )
        self.input_field.pack(fill=tk.X, side=tk.LEFT, padx=0, expand=True)
        self.input_field.bind("<Return>", lambda e: self._submit_input())

        # Button frame (minimal)
        button_frame = tk.Frame(self, bg="#000000")
        button_frame.pack(fill=tk.X, padx=2, pady=2)

        tk.Button(
            button_frame, text="[N]ew Game", command=self._new_game, bg="#1a1a1a", fg="#00ff00", 
            font=("Monospace", 9), relief=tk.FLAT, padx=3, pady=1
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame, text="[Q]uit", command=self._quit_game, bg="#1a1a1a", fg="#00ff00",
            font=("Monospace", 9), relief=tk.FLAT, padx=3, pady=1
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
            text=f"Download Model",
            command=self._pull_ollama_model,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Monospace", 9),
            relief=tk.FLAT,
            padx=3,
            pady=1,
        ).pack(side=tk.LEFT, padx=2)

        self.llm_status_var = tk.StringVar(value="LLM: Off" if not self.llm_enabled else "LLM: Checking...")
        tk.Label(
            llm_frame,
            textvariable=self.llm_status_var,
            bg="#000000",
            fg="#00ff00",
            font=("Monospace", 9),
        ).pack(side=tk.LEFT, padx=6)

        # Bind keyboard shortcuts
        self.bind("n", lambda e: self._new_game() if self.input_state in ["IDLE", "GAME_OVER"] else None)
        self.bind("q", lambda e: self._quit_game())
        self.bind("<Control-t>", lambda e: self._toggle_tts())
        self.bind("<Control-T>", lambda e: self._toggle_tts())

    def _append_text(self, text, tag=None):
        """Append text to story log from the Tk thread."""
        self.log.config(state=tk.NORMAL)
        if tag:
            self.log.insert(tk.END, text, tag)
        else:
            self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _drain_output_queue(self):
        """Move queued stdout text into the typewriter queue."""
        while True:
            try:
                chunk = self.output_queue.get_nowait()
            except queue.Empty:
                break
            # Queue for typewriter effect
            for char in chunk:
                self.typewriter_queue.put(char)
        self.after(40, self._drain_output_queue)

    def _typewriter_loop(self):
        """Very fast typewriter effect - add one character at a time to the log."""
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
        """Start a new game in a background thread."""
        if self.input_state == "PROCESSING":
            return
            
        self.log.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.config(state=tk.DISABLED)
        self.input_field.delete(0, tk.END)

        self._append_text("Initializing game...\n", "system")
        self.input_state = "PROCESSING"
        
        threading.Thread(target=self._run_new_game_thread, daemon=True).start()
        self.input_field.focus()

    def _run_new_game_thread(self):
        """Background thread for creating a new game."""
        try:
            if self.engine is None:
                self.engine = GameEngine()
            packet = self.engine.new_game()
            self.after(0, self._handle_engine_response, packet)
        except Exception as e:
            self.output_queue.put(f"\nEngine Error: {str(e)}\n")
            self.input_state = "GAME_OVER"

    def _submit_input(self):
        """Handle user hitting enter based on the current state."""
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
            
            # Check if this action requires a second step
            if chosen_action.get("input_required"):
                self.pending_action_index = action_index
                self.input_state = "WAITING_FOR_TEXT"
                hint = chosen_action.get("input_hint", "Enter input:")
                self.output_queue.put(f"\n{hint}\n")
                return
                
            # Otherwise, submit immediately
            self.input_state = "PROCESSING"
            self.output_queue.put("\nProcessing...\n")
            threading.Thread(
                target=self._run_submit_choice_thread, 
                args=(action_index, None), 
                daemon=True
            ).start()

        elif self.input_state == "WAITING_FOR_TEXT":
            self.input_state = "PROCESSING"
            self.output_queue.put("\nProcessing...\n")
            threading.Thread(
                target=self._run_submit_choice_thread, 
                args=(self.pending_action_index, user_input), 
                daemon=True
            ).start()

    def _run_submit_choice_thread(self, action_index, user_input):
        """Background thread for executing an action."""
        try:
            packet = self.engine.submit_choice(action_index, user_input=user_input)
            self.after(0, self._handle_engine_response, packet)
        except Exception as e:
            self.output_queue.put(f"\nEngine Error: {str(e)}\n")
            self.input_state = "GAME_OVER"

    def _handle_engine_response(self, packet):
        """Receives packet from background thread safely in the main thread."""
        self.current_packet = packet
        display_text = self._format_packet(packet)
        self.output_queue.put(display_text)
        self._queue_tts(packet.get("narration", ""))
        
        if packet.get("game_over") or packet.get("game_complete") or packet.get("health", 0) <= 0:
            self.input_state = "GAME_OVER"
        else:
            self.input_state = "WAITING_FOR_ACTION"

    def _format_packet(self, packet):
        """Formats the game state and narration into Zork-like text."""
        lines = ["\n" + "-" * 50]
        
        # Status Header
        scene_id = packet.get("scene_id", "Unknown")
        health = packet.get("health", 0)
        inv = packet.get("inventory", [])
        inv_str = ", ".join(inv) if inv else "empty"
        
        lines.append(f"Scene: {scene_id} | Health: {health}")
        lines.append(f"Inventory: {inv_str}")
        lines.append("-" * 50 + "\n")
        
        # Main Narration
        if packet.get("narration"):
            lines.append(packet["narration"] + "\n")

        # Short status updates (damage/heal context)
        for status_line in packet.get("status_lines", []):
            lines.append(status_line)

        if packet.get("status_lines"):
            lines.append("")
            
        # Win/Loss Evaluation
        if packet.get("health", 0) <= 0 or packet.get("game_over"):
            lines.append("\nGAME OVER")
            lines.append("=" * 50 + "\n")
        elif packet.get("game_complete"):
            lines.append("\nYOU WIN!")
            lines.append("Snow White has been rescued.")
            lines.append("=" * 50 + "\n")
        else:
            # Action Listing
            actions = packet.get("actions", [])
            if actions:
                lines.append("Actions:")
                for i, action in enumerate(actions, start=1):
                    lines.append(f"{i}. {action.get('label', 'Unknown Action')}")
            else:
                lines.append("No available actions. You are stuck.")
                
        return "\n".join(lines) + "\n"

    def _quit_game(self):
        """Quit the application."""
        self._stop_background_video()
        self.tts_stop_event.set()
        self.tts_queue.put(None)
        self.destroy()


def run():
    """Launch the game."""
    app = GameApp()
    app.mainloop()


if __name__ == "__main__":
    run()