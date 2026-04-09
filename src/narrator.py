# src/narrator.py
import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:0.5b-instruct-q4_K_M"

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "text": {"type": "string"},
        "dialogue": {"type": "string"}
    },
    "required": ["title", "text", "dialogue"]
}

def generate_story_block(kind, state, extra=""):
    prompt = f"""
You are adding short dialogue and cutscene text to a fairy-tale adventure game.

Rules:
- Do not change the story outcome.
- Do not invent new items or new quests.
- Keep it short and cinematic.
- This is only a {kind}.
- Current scene: {state.current_scene}
- Health: {state.health}
- Inventory: {state.inventory}
- Flags: {state.flags}
- Extra context: {extra}

Return JSON only.
"""

    fallback = {
        "title": "Story Beat",
        "text": "",
        "dialogue": ""
    }

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "format": SCHEMA,
                "stream": False,
                "options": {"temperature": 0}
            },
            timeout=20,
        )
        r.raise_for_status()
        return json.loads(r.json()["response"])
    except Exception as e:
        print(f"\n[Local narrator unavailable: {e}]")
        return fallback

def print_block(block):
    if not block:
        return

    title = block.get("title", "").strip()
    text = block.get("text", "").strip()
    dialogue = block.get("dialogue", "").strip()

    if title:
        print(f"\n--- {title} ---")
    if text:
        print(text)
    if dialogue:
        print(dialogue)