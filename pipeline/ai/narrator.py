from ai.prompt_builder import build_narrator_prompt


def generate_narration(
    state,
    prompt_type: str,
    scene_id: str,
    scene_facts,
    player_action: str = "",
) -> str:
    prompt = build_narrator_prompt(
        state=state,
        prompt_type=prompt_type,
        scene_id=scene_id,
        scene_facts=scene_facts,
        player_action=player_action,
    )

    # Replace this section with the real LLM API call later
    return fallback_narration(scene_facts)


def fallback_narration(scene_facts) -> str:
    if not scene_facts:
        return "Something happens, but the moment is strangely difficult to describe."

    return " ".join(scene_facts)