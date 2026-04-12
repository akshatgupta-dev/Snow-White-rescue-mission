"""
Retro Tkinter UI for the game (Zork-like aesthetic).

Simple window with:
- Black background, green monospace text
- Story scrollable text area
- Input field at bottom
- Minimal buttons (New Game, Quit)
- Typewriter effect on text output

Integrates with GameEngine via input queue.
Game runs in background thread so Tkinter stays responsive.
"""

import contextlib
import queue
import threading
import tkinter as tk
import tkinter.font as tkFont
from tkinter import scrolledtext

from src.game_engine import GameEngine


class GameApp(tk.Tk):
    """Retro terminal-style game window."""

    def __init__(self):
        super().__init__()
        self.title("Cinderella Rescues Snow White")
        self.geometry("800x600")
        self.config(bg="#000000")

        self.engine = GameEngine()
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.typewriter_queue = queue.Queue()  # Queue for typewriter effect
        self.typewriter_active = False  # Flag to prevent overlapping typewriter calls
        self.game_thread = None
        self.game_active = False

        self._setup_ui()
        self.after(40, self._drain_output_queue)
        self.after(25, self._typewriter_loop)  # Fast typewriter effect (25ms per char)
        self.focus()

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

        # Input frame (black bg to match)
        input_frame = tk.Frame(self, bg="#000000")
        input_frame.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(input_frame, text="> ", bg="#000000", fg="#00ff00", font=mono_font).pack(
            side=tk.LEFT
        )
        self.input_field = tk.Entry(
            input_frame, bg="#000000", fg="#00ff00", font=mono_font, insertbackground="#00ff00"
        )
        self.input_field.pack(fill=tk.X, side=tk.LEFT, padx=0)
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

        # Bind keyboard shortcuts
        self.bind("n", lambda e: self._new_game() if not self.game_active else None)
        self.bind("q", lambda e: self._quit_game())

    def _append_text(self, text):
        """Append text to story log from the Tk thread."""
        self.log.config(state=tk.NORMAL)
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
        """Fast typewriter effect - add one character at a time to the log."""
        try:
            char = self.typewriter_queue.get_nowait()
            self._append_text(char)
        except queue.Empty:
            pass
        self.after(25, self._typewriter_loop)  # 25ms per character = fast typing

    def _new_game(self):
        """Start a new game in a background thread."""
        if self.game_active:
            return
        self.log.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.config(state=tk.DISABLED)
        self.input_field.delete(0, tk.END)

        self.engine.new_game()
        self.engine.set_input_queue(self.input_queue)
        self.game_active = True
        self.input_field.focus()

        # Run game in background thread so Tkinter stays responsive
        self.game_thread = threading.Thread(target=self._game_loop, daemon=True)
        self.game_thread.start()

    def _submit_input(self):
        """Submit user input."""
        if not self.game_active:
            return
        user_input = self.input_field.get().strip()
        
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, user_input + "\n", "prompt")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
        
        self.input_field.delete(0, tk.END)
        self.input_queue.put(user_input)

    def _game_loop(self):
        """Main game loop (runs in background thread)."""
        class _QueueStdout:
            def __init__(self, output_queue):
                self.output_queue = output_queue

            def write(self, text):
                if text:
                    self.output_queue.put(text)

            def flush(self):
                return None

        stdout_proxy = _QueueStdout(self.output_queue)
        with contextlib.redirect_stdout(stdout_proxy):
            while self.game_active and self.engine.is_running:
                status, message = self.engine.play_scene()

                if status == "win":
                    print("\n" + "=" * 50)
                    print("YOU WIN!")
                    print("Snow White has been rescued.")
                    print("=" * 50)
                    self.game_active = False
                    break

                elif status == "lose":
                    print("\n" + "=" * 50)
                    print("GAME OVER")
                    if message:
                        print(message)
                    print("=" * 50)
                    self.game_active = False
                    break

                elif status == "error":
                    print(f"\nError: {message}")
                    self.game_active = False
                    break

        self.engine.clear_input_queue()
        # Re-enable input field via safe callback from main thread
        self.after(0, self._game_ended)

    def _game_ended(self):
        """Called when game loop finishes (safely from main thread)."""
        self.input_field.focus()

    def _quit_game(self):
        """Quit the application."""
        self.game_active = False
        self.engine.is_running = False
        self.destroy()


def run():
    """Launch the game."""
    app = GameApp()
    app.mainloop()


if __name__ == "__main__":
    run()
