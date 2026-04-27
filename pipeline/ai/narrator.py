import os
import json
import re
import requests
from pipeline.ai.room_context import ROOM_CONTEXT
from pipeline.ai.prompt_builder import build_narrator_prompt

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_URL = os.environ.get("OLLAMA_URL", f"{OLLAMA_BASE_URL}/api/generate")
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b-instruct-q4_K_M")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "20"))
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.25"))
OLLAMA_TOP_P = float(os.environ.get("OLLAMA_TOP_P", "0.9"))
OLLAMA_REPEAT_PENALTY = float(os.environ.get("OLLAMA_REPEAT_PENALTY", "1.15"))
OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "160"))
_OLLAMA_STATUS = {"checked": False, "ok": False, "message": "", "key": ""}


def use_llm_narrator() -> bool:
    return os.environ.get("USE_LLM_NARRATOR", "").lower() in {"1", "true", "yes", "on"}

SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"}
    },
    "required": ["text"]
}


def _normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned[0].upper() + cleaned[1:]


def _dedupe_facts(scene_facts) -> list[str]:
    if not scene_facts:
        return []

    if isinstance(scene_facts, str):
        scene_facts = [scene_facts]

    unique_facts = []
    seen = set()
    for fact in scene_facts:
        cleaned = _normalize_text(fact)
        if not cleaned:
            continue

        key = re.sub(r"[^a-z0-9]+", "", cleaned.lower())
        if key in seen:
            continue

        seen.add(key)
        unique_facts.append(cleaned)

    return unique_facts


def _scene_name(scene_id: str) -> str:
    room = ROOM_CONTEXT.get(scene_id, {})
    display_name = room.get("display_name")
    if display_name:
        return display_name
    return scene_id.replace("_", " ").title()


def _deterministic_narration(prompt_type: str, scene_id: str, scene_facts, player_action: str = "") -> str:
    facts = _dedupe_facts(scene_facts)
    if not facts:
        return "Something happens, but the moment is hard to describe."

    openings = {
        "scene_intro": f"Cinderella enters {_scene_name(scene_id)}.",
        "action_reaction": "The result lands immediately.",
        "penalty_event": "The moment turns against Cinderella.",
        "success_transition": "The scene shifts in Cinderella's favor.",
        "hint_text": "A clue becomes easier to see.",
    }

    opening = openings.get(prompt_type, "The moment settles into place.")

    if prompt_type == "scene_intro":
        return " ".join(facts)

    if prompt_type == "action_reaction":
        return " ".join([opening] + facts)

    if prompt_type == "penalty_event":
        return " ".join([opening] + facts)

    if prompt_type == "success_transition":
        return " ".join([opening] + facts)

    if prompt_type == "hint_text":
        return " ".join([opening] + facts)

    return " ".join(facts)


def _looks_like_prompt_leak(text: str) -> bool:
    if not text:
        return False

    lowered = text.lower()
    leak_phrases = [
        "scene name:",
        "room purpose:",
        "room mood:",
        "room focus:",
        "important objects:",
        "characters present:",
        "narrator guidance:",
        "current game state:",
        "scene facts:",
        "success feeling:",
        "penalty flavor:",
        "hint style:",
        "keep the tone",
        "this room should",
        "should feel",
        "should seem",
        "should be",
    ]

    return any(phrase in lowered for phrase in leak_phrases)


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _dedupe_sentences(sentences: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for sentence in sentences:
        key = re.sub(r"[^a-z0-9]+", "", sentence.lower())
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(sentence)
    return deduped


def _max_sentences_for_prompt(prompt_type: str) -> int:
    if prompt_type == "hint_text":
        return 2
    return 4


def _clean_llm_text(text: str, prompt_type: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""

    sentences = _split_sentences(cleaned)
    if not sentences:
        sentences = [cleaned]

    sentences = _dedupe_sentences(sentences)
    max_sentences = _max_sentences_for_prompt(prompt_type)
    cleaned = " ".join(sentences[:max_sentences]).strip()

    if len(cleaned) > 700:
        return ""

    return cleaned


def check_ollama_status(force: bool = False) -> dict:
    current_key = f"{OLLAMA_BASE_URL}|{OLLAMA_MODEL}"
    if _OLLAMA_STATUS.get("key") != current_key:
        _OLLAMA_STATUS.update({"checked": False, "ok": False, "message": "", "key": current_key})

    if _OLLAMA_STATUS["checked"] and not force:
        return _OLLAMA_STATUS

    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = {model.get("name") for model in models if model.get("name")}

        if OLLAMA_MODEL not in model_names:
            _OLLAMA_STATUS.update(
                {
                    "checked": True,
                    "ok": False,
                    "message": f"Model '{OLLAMA_MODEL}' not found in Ollama.",
                }
            )
            return _OLLAMA_STATUS

        _OLLAMA_STATUS.update(
            {
                "checked": True,
                "ok": True,
                "message": f"Connected to Ollama with model '{OLLAMA_MODEL}'.",
            }
        )
        return _OLLAMA_STATUS
    except Exception:
        _OLLAMA_STATUS.update(
            {
                "checked": True,
                "ok": False,
                "message": f"Ollama not reachable at {OLLAMA_BASE_URL}.",
            }
        )
        return _OLLAMA_STATUS

def generate_narration(state, prompt_type: str, scene_id: str, scene_facts, player_action: str = "") -> str:
    if not use_llm_narrator():
        return _deterministic_narration(prompt_type, scene_id, scene_facts, player_action)

    status = check_ollama_status()
    if not status.get("ok"):
        return _deterministic_narration(prompt_type, scene_id, scene_facts, player_action)

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
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": SCHEMA,
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMPERATURE,
                    "top_p": OLLAMA_TOP_P,
                    "repeat_penalty": OLLAMA_REPEAT_PENALTY,
                    "num_predict": OLLAMA_NUM_PREDICT,
                },
            },
            timeout=OLLAMA_TIMEOUT,
        )
        r.raise_for_status()
        data = json.loads(r.json()["response"])
        text = data.get("text", "").strip()
        if text:
            if _looks_like_prompt_leak(text):
                return _deterministic_narration(prompt_type, scene_id, scene_facts, player_action)
            cleaned_text = _clean_llm_text(text, prompt_type)
            if not cleaned_text or _looks_like_prompt_leak(cleaned_text):
                return _deterministic_narration(prompt_type, scene_id, scene_facts, player_action)
            return cleaned_text
    except Exception:
        pass

    return _deterministic_narration(prompt_type, scene_id, scene_facts, player_action)

def fallback_narration(scene_facts) -> str:
    return _deterministic_narration("scene_intro", "", scene_facts)