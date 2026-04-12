"""
Input abstraction layer.

Allows scenes to call input() without knowing if input comes from:
- Tkinter window (via queue)
- Terminal (fallback to stdlib)
- Test harness (injected queue)

This is a monkey-patch approach: scene code is unchanged.
"""

import builtins
import queue

_input_queue = None
_original_input = builtins.input


def set_input_source(q):
    """
    Inject a queue as the input source.
    Subsequent input() calls in scenes will read from this queue.
    """
    global _input_queue
    _input_queue = q


def clear_input_source():
    """Remove the injected input source. Revert to stdlib input()."""
    global _input_queue
    _input_queue = None


def _patched_input(prompt=""):
    """
    Replacement for builtin input().
    If a queue is set, block and wait for input from it.
    Otherwise, fall back to stdlib input().
    """
    if _input_queue is not None:
        # Block until UI provides input
        return _input_queue.get()
    else:
        # Fallback: use original input() for CLI mode
        return _original_input(prompt)


def activate_queue_input():
    """Patch builtins.input to use the queue-based version."""
    builtins.input = _patched_input


def deactivate_queue_input():
    """Restore original builtins.input."""
    builtins.input = _original_input
