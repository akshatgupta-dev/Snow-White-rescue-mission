from pipeline.ai.lore import WORLD_LORE, STORY_FLOW
from pipeline.ai.room_context import ROOM_CONTEXT
from pipeline.ai.state_formatter import format_state_summary
from pipeline.ai.templates import GLOBAL_NARRATOR_PROMPT, PROMPT_TEMPLATES


def _format_list(value):
    if not value:
        return "none"

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    return str(value)


def _build_lore_summary(scene_id: str) -> str:
    premise = WORLD_LORE.get("premise", "")
    themes = _format_list(WORLD_LORE.get("themes", []))
    moral = WORLD_LORE.get("moral", "")

    story_step = STORY_FLOW.get(scene_id, {})
    room_summary = story_step.get("summary", "No room summary available.")

    return (
        f"Premise: {premise}\n"
        f"Story role of this room: {room_summary}\n"
        f"Themes: {themes}\n"
        f"Moral: {moral}"
    )


def build_narrator_prompt(
    state,
    prompt_type: str,
    scene_id: str,
    scene_facts: list[str],
    player_action: str = "",
) -> str:
    room = ROOM_CONTEXT.get(scene_id)
    if room is None:
        raise ValueError(f"No room context found for scene_id='{scene_id}'")

    template = PROMPT_TEMPLATES.get(prompt_type)
    if template is None:
        raise ValueError(f"No prompt template found for prompt_type='{prompt_type}'")

    state_summary = format_state_summary(state)
    lore_summary = _build_lore_summary(scene_id)

    filled_template = template.format(
        scene_name=room.get("display_name", scene_id),
        room_purpose=room.get("room_purpose", "unknown"),
        room_mood=_format_list(room.get("mood", [])),
        room_focus=_format_list(room.get("focus", [])),
        important_objects=_format_list(room.get("important_objects", [])),
        characters_present=_format_list(room.get("characters_present", [])),
        narrator_guidance=_format_list(room.get("narrator_guidance", [])),
        challenge_type=room.get("challenge_type", "unknown"),
        success_feeling=_format_list(room.get("success_feeling", [])),
        failure_feeling=_format_list(room.get("failure_feeling", [])),
        penalty_flavor=_format_list(room.get("penalty_flavor", [])),
        hint_style=_format_list(room.get("hint_style", [])),
        lore_summary=lore_summary,
        state_summary=state_summary,
        player_action=player_action or "none",
        scene_facts=_format_list(scene_facts),
    )

    return f"{GLOBAL_NARRATOR_PROMPT.strip()}\n\n{filled_template.strip()}"