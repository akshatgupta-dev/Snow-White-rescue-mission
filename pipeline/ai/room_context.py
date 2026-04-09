from game_foundation import (
    SCENE_LIBRARY,
    SCENE_AGORA,
    SCENE_CAFETERIA,
    SCENE_BEAR_BRIDGE,
    SCENE_KIRJURINLUOTO,
    SCENE_FINAL,
    CHAR_CINDERELLA,
    CHAR_SNOW_WHITE,
    CHAR_EVIL_QUEEN,
    CHAR_BEAR,
    CHAR_SEVEN_DWARFS,
)


ROOM_CONTEXT = {
    SCENE_LIBRARY: {
        "display_name": "The Library",
        "room_purpose": "direction",
        "mood": [
            "silent",
            "dusty",
            "magical",
            "academic",
            "slightly intimidating",
        ],
        "focus": [
            "wisdom",
            "proving belonging",
            "finding direction",
            "first trial",
        ],
        "important_objects": [
            "holographic guardian",
            "glowing map of Pori",
            "locked library passage",
        ],
        "characters_present": [
            CHAR_CINDERELLA,
        ],
        "challenge_type": "knowledge_test",
        "success_feeling": [
            "earned access",
            "clarity",
            "forward momentum",
        ],
        "failure_feeling": [
            "embarrassment",
            "magical sting",
            "blocked progress",
        ],
        "narrator_guidance": [
            "Emphasize that the library gives direction, not power.",
            "Keep the tone mysterious but fair.",
            "The guardian should feel magical, formal, and slightly theatrical.",
            "The room should feel like the beginning of a larger quest.",
        ],
        "penalty_flavor": [
            "dark magical energy",
            "sharp humiliation",
            "a brief sense of being judged by the room itself",
        ],
        "hint_style": [
            "gentle academic clue",
            "knowledge-based guidance",
        ],
    },

    SCENE_AGORA: {
        "display_name": "Agora Hall",
        "room_purpose": "earned_strength",
        "mood": [
            "playful",
            "chaotic",
            "sporty",
            "absurd",
            "energetic",
        ],
        "focus": [
            "observation",
            "timing",
            "physical challenge",
            "comic tension",
        ],
        "important_objects": [
            "badminton court",
            "lightsaber on display stand",
            "matching badminton outfits",
        ],
        "characters_present": [
            CHAR_CINDERELLA,
            CHAR_SEVEN_DWARFS,
        ],
        "challenge_type": "pattern_recognition_physical_challenge",
        "success_feeling": [
            "earned victory",
            "comic triumph",
            "gaining real power",
        ],
        "failure_feeling": [
            "awkwardness",
            "frustration",
            "being outplayed by chaos",
        ],
        "narrator_guidance": [
            "Treat the dwarfs as absurd but sincere opponents.",
            "Keep the humor dry and slightly theatrical.",
            "The lightsaber should feel ridiculous in context, but still important.",
            "Emphasize that Cinderella wins by noticing a pattern, not by brute force.",
        ],
        "penalty_flavor": [
            "stumbled rally",
            "awkward sports failure",
            "momentary loss of confidence",
        ],
        "hint_style": [
            "subtle tactical clue",
            "attention to court positioning",
        ],
    },

    SCENE_CAFETERIA: {
        "display_name": "SAMK Cafeteria",
        "room_purpose": "magical_transition",
        "mood": [
            "quiet",
            "eerie",
            "funny",
            "empty",
            "suspicious",
        ],
        "focus": [
            "hunger",
            "temptation",
            "strange stillness",
            "fairytale transformation",
        ],
        "important_objects": [
            "perfect pumpkin",
            "empty cafeteria tables",
            "buzzing overhead lights",
        ],
        "characters_present": [
            CHAR_CINDERELLA,
        ],
        "challenge_type": "temptation_or_environmental_event",
        "success_feeling": [
            "surprise",
            "wonder",
            "movement into the next stage of the quest",
        ],
        "failure_feeling": [
            "confusion",
            "wasted time",
            "hunger and uncertainty",
        ],
        "narrator_guidance": [
            "The cafeteria should feel unnaturally quiet.",
            "The pumpkin should seem both inviting and suspicious.",
            "Keep the humor understated, especially when magic suddenly becomes normal.",
            "This room should feel like a threshold between ordinary campus space and stronger fairytale logic.",
        ],
        "penalty_flavor": [
            "hunger pangs",
            "weird cafeteria unease",
            "the sense that time is behaving strangely",
        ],
        "hint_style": [
            "environmental clue",
            "food and magic symbolism",
        ],
    },

    SCENE_BEAR_BRIDGE: {
        "display_name": "Bear Bridge",
        "room_purpose": "kindness_test",
        "mood": [
            "foggy",
            "quiet",
            "tense",
            "emotional",
            "gentle underneath the danger",
        ],
        "focus": [
            "kindness",
            "sacrifice",
            "hesitation",
            "earning passage",
        ],
        "important_objects": [
            "bridge crossing",
            "pumpkin",
            "river fog",
            "hungry bear",
        ],
        "characters_present": [
            CHAR_CINDERELLA,
            CHAR_BEAR,
        ],
        "challenge_type": "moral_choice",
        "success_feeling": [
            "warmth",
            "earned trust",
            "quiet heroism",
        ],
        "failure_feeling": [
            "selfishness",
            "guilt",
            "blocked crossing",
        ],
        "narrator_guidance": [
            "The bear should feel dangerous at first, but clearly suffering.",
            "Emphasize emotional tension over action.",
            "This is a kindness test, not a combat scene.",
            "The bridge should feel like an important turning point in the story.",
        ],
        "penalty_flavor": [
            "cold fog",
            "hunger",
            "emotional discomfort",
            "the weight of refusing kindness",
        ],
        "hint_style": [
            "gentle moral clue",
            "sympathy-focused guidance",
        ],
    },

    SCENE_KIRJURINLUOTO: {
        "display_name": "Kirjurinluoto",
        "room_purpose": "final_trial",
        "mood": [
            "magical",
            "foggy",
            "confusing",
            "theatrical",
            "unsettling",
        ],
        "focus": [
            "false paths",
            "illusions",
            "staying calm",
            "finding the truth",
        ],
        "important_objects": [
            "fog-filled paths",
            "illusion-covered park",
            "the Evil Queen's stage",
        ],
        "characters_present": [
            CHAR_CINDERELLA,
            CHAR_EVIL_QUEEN,
        ],
        "challenge_type": "navigation_and_final_confrontation",
        "success_feeling": [
            "clarity",
            "approaching the truth",
            "readiness for the final fight",
        ],
        "failure_feeling": [
            "disorientation",
            "drained confidence",
            "being trapped by illusion",
        ],
        "narrator_guidance": [
            "This room should feel like a dream that is trying to mislead the player.",
            "The false paths should feel tempting, not random.",
            "Build a sense of approaching climax.",
            "The Evil Queen's presence should be felt before the confrontation fully begins.",
        ],
        "penalty_flavor": [
            "fog-induced confusion",
            "illusion backlash",
            "wandering in circles",
        ],
        "hint_style": [
            "calm navigational clue",
            "truth-versus-illusion guidance",
        ],
    },

    SCENE_FINAL: {
        "display_name": "Final Chamber",
        "room_purpose": "resolution",
        "mood": [
            "relieved",
            "warm",
            "slightly funny",
            "emotionally complete",
        ],
        "focus": [
            "rescue",
            "release from magic",
            "recovery",
            "final moral choice",
        ],
        "important_objects": [
            "broken magical prison",
            "Snow White",
            "shiny apple",
        ],
        "characters_present": [
            CHAR_CINDERELLA,
            CHAR_SNOW_WHITE,
        ],
        "challenge_type": "final_choice",
        "success_feeling": [
            "closure",
            "comfort",
            "renewed strength",
        ],
        "failure_feeling": [
            "mostly mild hesitation rather than tragedy",
        ],
        "narrator_guidance": [
            "Let the tension soften here after the confrontation.",
            "The emotional reunion should matter, but the ending can still be playful.",
            "The apple choice should feel small but meaningful.",
            "End with warmth and a fairytale moral.",
        ],
        "penalty_flavor": [
            "lingering tiredness",
            "post-battle hunger",
        ],
        "hint_style": [
            "gentle closing guidance",
            "healthy-choice symbolism",
        ],
    },
}