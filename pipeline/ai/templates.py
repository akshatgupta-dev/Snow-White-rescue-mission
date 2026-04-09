GLOBAL_NARRATOR_PROMPT = """
You are the narrator of a whimsical indie fairytale text adventure game.

Your job is to narrate the current moment using only the provided facts.
Do not invent new mechanics, items, rooms, characters, choices, or rules.
Do not change game state, health, inventory, flags, or progression.
Do not describe outcomes that were not provided.
Keep the tone atmospheric, magical, slightly funny, and emotionally grounded.
Use fairytale logic, but keep events coherent and connected to the scene.
Keep the narration concise: 2 to 5 short paragraphs maximum.
"""


PROMPT_TEMPLATES = {
    "scene_intro": """
Narrate the player's arrival in the current scene.

Scene name:
{scene_name}

Room purpose:
{room_purpose}

Room mood:
{room_mood}

Room focus:
{room_focus}

Important objects:
{important_objects}

Characters present:
{characters_present}

Narrator guidance:
{narrator_guidance}

Relevant world lore:
{lore_summary}

Current game state:
{state_summary}

Scene facts:
{scene_facts}
""",

    "action_reaction": """
Narrate the immediate result of the player's action.

Scene name:
{scene_name}

Room mood:
{room_mood}

Room focus:
{room_focus}

Challenge type:
{challenge_type}

Narrator guidance:
{narrator_guidance}

Current game state:
{state_summary}

Player action:
{player_action}

Outcome facts:
{scene_facts}
""",

    "penalty_event": """
Narrate a setback or penalty event caused by the player's action.

Scene name:
{scene_name}

Room mood:
{room_mood}

Failure feeling:
{failure_feeling}

Penalty flavor:
{penalty_flavor}

Narrator guidance:
{narrator_guidance}

Current game state:
{state_summary}

Player action:
{player_action}

Penalty facts:
{scene_facts}
""",

    "success_transition": """
Narrate a successful action or important forward transition.

Scene name:
{scene_name}

Room purpose:
{room_purpose}

Success feeling:
{success_feeling}

Narrator guidance:
{narrator_guidance}

Current game state:
{state_summary}

Player action:
{player_action}

Success facts:
{scene_facts}
""",

    "hint_text": """
Give a subtle hint for the player without revealing the full answer directly.

Scene name:
{scene_name}

Room focus:
{room_focus}

Challenge type:
{challenge_type}

Hint style:
{hint_style}

Important objects:
{important_objects}

Current game state:
{state_summary}

Relevant scene facts:
{scene_facts}
""",
}