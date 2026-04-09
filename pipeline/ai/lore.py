WORLD_LORE = {
    "premise": (
        "Cinderella arrives at SAMK late at night on a mission to rescue "
        "Snow White. The campus is dark, quiet, and touched by strange "
        "fairytale magic. To succeed, she must move through a series of rooms "
        "and trials across SAMK and Pori, gaining knowledge, direction, and "
        "the means to confront the Evil Queen."
    ),
    "tone": [
        "whimsical",
        "indie fairytale",
        "slightly funny",
        "atmospheric",
        "emotionally grounded",
        "magical but not random",
    ],
    "world_rules": [
        "Narration should follow the established scene facts.",
        "Magic exists, but it usually appears through fairytale logic.",
        "The world is strange and dramatic, but never fully chaotic.",
        "Objects and characters should feel meaningful, not random.",
        "The story mixes humor, tension, and sincerity.",
    ],
    "themes": [
        "kindness matters",
        "wisdom guides progress",
        "effort earns strength",
        "healthy choices restore you",
        "fairytale magic follows emotional logic",
    ],
    "moral": "Be kind. Exercise. Go study. And eat healthy.",
}


CHARACTER_LORE = {
    "Cinderella": {
        "role": "player character",
        "traits": [
            "determined",
            "kind",
            "slightly sarcastic",
            "brave",
            "emotionally grounded",
        ],
        "goal": "Rescue Snow White from the Evil Queen.",
    },
    "Snow White": {
        "role": "the one being rescued",
        "status": "trapped in magic until the final rescue",
        "story_function": "the emotional goal of the quest",
    },
    "Evil Queen": {
        "role": "main antagonist",
        "traits": [
            "dramatic",
            "controlling",
            "theatrical",
            "magical",
        ],
        "story_function": (
            "She controls illusions and false paths, especially in Kirjurinluoto."
        ),
    },
    "Bear": {
        "role": "guardian of Pori and Kirjurinluoto",
        "traits": [
            "hungry",
            "tired",
            "gentle underneath the danger",
        ],
        "story_function": (
            "Tests Cinderella's kindness before allowing passage."
        ),
    },
    "Seven Dwarfs": {
        "role": "guardians of the lightsaber in Agora Hall",
        "traits": [
            "sporty",
            "chaotic",
            "absurdly serious about badminton",
            "comedic",
        ],
        "story_function": (
            "They create a physical challenge that Cinderella must solve through observation."
        ),
    },
}


STORY_FLOW = {
    "library": {
        "purpose": "direction",
        "summary": (
            "Cinderella proves her wisdom at the library, earns the map of Pori, "
            "and learns that the real weapon is in Agora Hall."
        ),
        "reward": "map",
        "lesson": "Knowledge opens the way forward.",
    },
    "agora_hall": {
        "purpose": "earned strength",
        "summary": (
            "Cinderella faces the Seven Dwarfs in a badminton challenge, notices "
            "their weakness, and wins the lightsaber."
        ),
        "reward": "lightsaber",
        "lesson": "Observation and action earn power.",
    },
    "cafeteria": {
        "purpose": "magical transition",
        "summary": (
            "Cinderella finds a pumpkin in the cafeteria. At 10:00 PM it transforms "
            "into a magical carriage and carries her onward."
        ),
        "reward": "carriage",
        "lesson": "Magic often appears when least expected.",
    },
    "bear_bridge": {
        "purpose": "kindness test",
        "summary": (
            "The carriage turns back into a pumpkin. Cinderella gives the pumpkin "
            "to a hungry bear, who then reveals itself as the guardian of the crossing."
        ),
        "reward": "passage to Kirjurinluoto",
        "lesson": "Kindness unlocks the path forward.",
    },
    "kirjurinluoto": {
        "purpose": "final trial",
        "summary": (
            "Cinderella crosses a fog-filled park of illusions, finds the true path, "
            "and reaches the Evil Queen's stage."
        ),
        "reward": "access to final confrontation",
        "lesson": "Clarity matters when the world tries to confuse you.",
    },
    "final": {
        "purpose": "resolution",
        "summary": (
            "Cinderella defeats the Evil Queen, rescues Snow White, and is offered "
            "one final choice with the apple."
        ),
        "reward": "Snow White rescued",
        "lesson": "Restoration comes after courage, kindness, and effort.",
    },
}