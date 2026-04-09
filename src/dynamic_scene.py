import json
import requests

from src.game_foundation import DYNAMIC_SCENE
from src.input_utils import match_text

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:0.5b-instruct-q4_K_M"

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "intro": {"type": "string"},
        "choices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "effect": {"type": "string"},
                    "result": {"type": "string"},
                },
                "required": ["label", "effect", "result"],
            },
        },
    },
    "required": ["title", "intro", "choices"],
}

ALLOWED_EFFECTS = {"none", "lose_5_health", "gain_5_health", "flavor_only"}


def generate_dynamic_scene(state, return_scene, extra_context=""):
    prompt = f"""
You are generating a very short side scene for an existing fairy-tale game.

Strict rules:
- This is a temporary side scene between main story scenes.
- It must NOT replace the main story.
- After this scene, Cinderella MUST continue to: {return_scene}
- Never invent major plot changes.
- Never invent permanent items.
- Never defeat villains.
- Never rescue Snow White.
- Never change the destination scene.
- Use only these effects: none, lose_5_health, gain_5_health, flavor_only
- Use only known world elements from the story.
- Keep it short.
- Provide exactly 2 choices.

Choice rules:
- Choices must be immediate player actions that make sense in this exact moment.
- Choices must be written like normal player options, not code.
- Do NOT use underscores.
- Do NOT use variable-style names like walk_forward or eat_apple.
- Do NOT mention items unless they are clearly present in the current moment.
- Do NOT mention the apple unless the apple is explicitly present in this scene.
- The choices should fit this exact context: {extra_context}
- Good examples: "Study the glowing map", "Keep walking toward Agora Hall"
- Bad examples: "walk_forward", "eat_apple", "label1", "do_action"

Each choice must contain only:
- label
- effect
- result

The destination after the scene is always {return_scene}.

Current scene: {state.current_scene}
Inventory: {state.inventory}
Flags: {state.flags}
Extra context: {extra_context}

Return JSON only.
"""

    fallback = {
        "title": "A Brief Detour",
        "intro": "Cinderella takes a brief detour, gathers herself, and continues onward.",
        "choices": [
            {
                "label": "Keep moving",
                "effect": "none",
                "result": "She stays focused and continues the journey.",
            },
            {
                "label": "Pause for a moment",
                "effect": "flavor_only",
                "result": "She takes a breath, then resumes the journey.",
            },
        ],
    }

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "format": SCHEMA,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 160,
                },
            },
            timeout=25,
        )
        r.raise_for_status()
        data = json.loads(r.json()["response"])

        if "choices" not in data or not isinstance(data["choices"], list) or len(data["choices"]) < 2:
            return fallback

        cleaned_choices = []
        fallback_choices = fallback_choices_for_return_scene(return_scene)

        for i, choice in enumerate(data["choices"][:2], start=1):
            effect = str(choice.get("effect", "none"))
            if effect not in ALLOWED_EFFECTS:
                effect = "none"

            raw_label = str(choice.get("label", "")).strip()
            raw_result = str(choice.get("result", "Cinderella continues onward.")).strip()

            if is_bad_choice_label(raw_label):
                cleaned_choices.append(fallback_choices[i - 1])
            else:
                cleaned_choices.append(
                    {
                        "id": str(i),
                        "label": raw_label,
                        "effect": effect,
                        "result": raw_result,
                    }
                )

        return {
            "title": str(data.get("title", "A Brief Detour")).strip(),
            "intro": str(data.get("intro", "Cinderella encounters a short interruption on the road.")).strip(),
            "choices": cleaned_choices,
        }

    except Exception as e:
        print(f"\n[Dynamic scene unavailable: {e}]")
        return {
            "title": "A Brief Detour",
            "intro": "Cinderella takes a brief detour, gathers herself, and continues onward.",
            "choices": fallback_choices_for_return_scene(return_scene),
        }


def queue_dynamic_scene(state, return_scene, extra_context=""):
    state.pending_return_scene = return_scene
    state.dynamic_scene_data = generate_dynamic_scene(
        state,
        return_scene=return_scene,
        extra_context=extra_context,
    )
    state.current_scene = DYNAMIC_SCENE


def is_bad_choice_label(label: str) -> bool:
    label = label.strip().lower()

    if not label:
        return True

    # reject code-like labels
    if "_" in label:
        return True

    if label in {"label1", "label2", "choice1", "choice2", "option1", "option2"}:
        return True

    # reject obviously unrelated or forbidden actions
    forbidden_phrases = {
        "eat apple",
        "eat the apple",
        "rescue snow white",
        "defeat queen",
        "take lightsaber",
        "win game",
    }
    if label in forbidden_phrases:
        return True

    # too short / not natural
    if len(label.split()) < 2:
        return True

    return False


def fallback_choices_for_return_scene(return_scene: str):
    if return_scene == "agora_hall":
        return [
            {
                "id": "1",
                "label": "Study the glowing map",
                "effect": "flavor_only",
                "result": "Cinderella checks the glowing map and steadies herself before continuing.",
            },
            {
                "id": "2",
                "label": "Keep walking toward Agora Hall",
                "effect": "none",
                "result": "Cinderella keeps moving and soon reaches Agora Hall.",
            },
        ]

    if return_scene == "cafeteria":
        return [
            {
                "id": "1",
                "label": "Look around the corridor",
                "effect": "flavor_only",
                "result": "Cinderella takes in her surroundings, then continues onward.",
            },
            {
                "id": "2",
                "label": "Head straight toward the cafeteria",
                "effect": "none",
                "result": "Cinderella stays focused and heads for the cafeteria.",
            },
        ]

    if return_scene == "bear_bridge":
        return [
            {
                "id": "1",
                "label": "Listen to the night around her",
                "effect": "flavor_only",
                "result": "She pauses briefly, then continues through the night.",
            },
            {
                "id": "2",
                "label": "Ride onward toward Bear Bridge",
                "effect": "none",
                "result": "The journey continues toward Bear Bridge.",
            },
        ]

    if return_scene == "kirjurinluoto":
        return [
            {
                "id": "1",
                "label": "Thank the bear once more",
                "effect": "flavor_only",
                "result": "Cinderella gives a quiet nod of thanks before moving on.",
            },
            {
                "id": "2",
                "label": "Cross toward Kirjurinluoto",
                "effect": "none",
                "result": "Cinderella crosses ahead toward the final area.",
            },
        ]

    return [
        {
            "id": "1",
            "label": "Pause for a moment",
            "effect": "flavor_only",
            "result": "Cinderella takes a breath, then continues.",
        },
        {
            "id": "2",
            "label": "Keep moving",
            "effect": "none",
            "result": "Cinderella continues onward.",
        },
    ]

def apply_dynamic_effect(state, effect):
    if effect == "lose_5_health":
        state.health = max(0, state.health - 5)
    elif effect == "gain_5_health":
        state.health = min(100, state.health + 5)


def play_dynamic_scene(state):
    scene = state.dynamic_scene_data

    if not scene:
        if state.pending_return_scene:
            state.current_scene = state.pending_return_scene
            state.pending_return_scene = None
        return

    print(f"\n--- {scene['title']} ---")
    print(scene["intro"])

    print("\nChoices:")
    for choice in scene["choices"]:
        print(f"{choice['id']}. {choice['label']}")

    selected = None
    labels = [choice["label"] for choice in scene["choices"]]

    while selected is None:
        user_choice = input("> ").strip()

        # allow 1 or 2 directly
        selected = next((c for c in scene["choices"] if c["id"] == user_choice), None)

        # also allow fuzzy text match on the choice label
        if selected is None:
            ok, matched = match_text(user_choice, labels, cutoff=0.75)
            if ok:
                selected = next((c for c in scene["choices"] if c["label"] == matched), None)

        if selected is None:
            print("Invalid choice. Pick 1 or 2.")

    print("\n" + selected["result"])
    apply_dynamic_effect(state, selected["effect"])

    return_scene = state.pending_return_scene
    state.dynamic_scene_data = None
    state.pending_return_scene = None

    if return_scene:
        state.current_scene = return_scene