import json
import requests
from pipeline.ai.prompt_builder import build_narrator_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:0.5b-instruct-q4_K_M"

SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"}
    },
    "required": ["text"]
}

def generate_narration(state, prompt_type: str, scene_id: str, scene_facts, player_action: str = "") -> str:
    prompt = build_narrator_prompt(
        state=state,
        prompt_type=prompt_type,
        scene_id=scene_id,
        scene_facts=scene_facts,
        player_action=player_action,
    )

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "format": SCHEMA,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=20,
        )
        r.raise_for_status()
        data = json.loads(r.json()["response"])
        text = data.get("text", "").strip()
        if text:
            return text
    except Exception:
        pass

    return fallback_narration(scene_facts)

def fallback_narration(scene_facts) -> str:
    if not scene_facts:
        return "Something happens, but the moment is strangely difficult to describe."
    return " ".join(scene_facts)