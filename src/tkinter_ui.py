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
        
        self.output_queue = queue.Queue()
        self.typewriter_queue = queue.Queue()  # Queue for typewriter effect
        
        # UI State Management
        self.current_packet = None
        self.input_state = "IDLE"  # IDLE, WAITING_FOR_ACTION, WAITING_FOR_TEXT, PROCESSING
        self.pending_action_index = -1
        
        self._setup_ui()
        self.after(40, self._drain_output_queue)
        self.after(5, self._typewriter_loop)  # Very fast typewriter effect (5ms per char)
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

        # Bind keyboard shortcuts
        self.bind("n", lambda e: self._new_game() if self.input_state in ["IDLE", "GAME_OVER"] else None)
        self.bind("q", lambda e: self._quit_game())

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
        try:
            char = self.typewriter_queue.get_nowait()
            self._append_text(char)
        except queue.Empty:
            pass
        self.after(5, self._typewriter_loop)  # 5ms per character

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
        self.destroy()


def run():
    """Launch the game."""
    app = GameApp()
    app.mainloop()


if __name__ == "__main__":
    run()