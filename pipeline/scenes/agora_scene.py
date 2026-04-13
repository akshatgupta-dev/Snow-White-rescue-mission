from src.game_foundation import (
    SCENE_AGORA,
    SCENE_CAFETERIA,
    ITEM_LIGHTSABER,
    STATE_HAS_LIGHTSABER,
    STATE_AGORA_CHALLENGE_STARTED,
    STATE_AGORA_RALLY_ACTIVE,
    STATE_AGORA_CHALLENGE_RESOLVED,
    STATE_AGORA_CHALLENGE_WON,
    STATE_AGORA_STUDIED_FORMATION,
    add_item,
    has_item,
    set_flag,
    get_flag,
    damage_player,
)


def get_agora_intro():
    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_AGORA,
        "scene_facts": [
            "Cinderella arrives in Agora Hall.",
            "The hall feels strangely sporty, theatrical, and full of chaotic energy.",
            "The Seven Dwarfs stand together in matching badminton outfits.",
            "A lightsaber rests behind them on a display stand.",
            "The dwarfs challenge Cinderella to win one badminton round if she wants the weapon.",
        ],
    }


def get_agora_actions(state):
    if has_item(state, ITEM_LIGHTSABER):
        return [
            {
                "action_id": "leave_with_lightsaber",
                "label": "Leave Agora Hall with the lightsaber",
                "input_required": False,
            }
        ]

    if get_flag(state, STATE_AGORA_CHALLENGE_RESOLVED):
        if get_flag(state, STATE_AGORA_CHALLENGE_WON):
            return [
                {
                    "action_id": "catch_breath",
                    "label": "Catch your breath",
                    "input_required": False,
                },
                {
                    "action_id": "claim_lightsaber",
                    "label": "Claim the lightsaber",
                    "input_required": False,
                },
            ]

        return [
            {
                "action_id": "retry_rally",
                "label": "Try another rally",
                "input_required": False,
            },
            {
                "action_id": "study_formation_again",
                "label": "Study the dwarfs' formation again",
                "input_required": False,
            },
            {
                "action_id": "taunt_dwarfs",
                "label": "Try to throw the dwarfs off their game",
                "input_required": False,
            },
        ]

    if get_flag(state, STATE_AGORA_RALLY_ACTIVE):
        return [
            {
                "action_id": "smash_front",
                "label": "Smash straight at the front line",
                "input_required": False,
            },
            {
                "action_id": "drop_shot",
                "label": "Try a soft drop shot near the net",
                "input_required": False,
            },
            {
                "action_id": "send_behind",
                "label": "Send the shuttle behind all seven dwarfs",
                "input_required": False,
            },
            {
                "action_id": "hesitate",
                "label": "Hesitate for a moment",
                "input_required": False,
            },
        ]

    if get_flag(state, STATE_AGORA_CHALLENGE_STARTED):
        return [
            {
                "action_id": "start_rally",
                "label": "Start the badminton rally",
                "input_required": False,
            },
            {
                "action_id": "study_formation",
                "label": "Study the dwarfs' formation",
                "input_required": False,
            },
            {
                "action_id": "taunt_dwarfs",
                "label": "Try to distract the dwarfs first",
                "input_required": False,
            },
        ]

    return [
        {
            "action_id": "study_dwarfs",
            "label": "Study the Seven Dwarfs and their formation",
            "input_required": False,
        },
        {
            "action_id": "ask_about_weapon",
            "label": "Ask why they are guarding a lightsaber",
            "input_required": False,
        },
        {
            "action_id": "accept_challenge",
            "label": "Accept the badminton challenge",
            "input_required": False,
        },
    ]


def handle_agora_action(state, action_id, user_input=None):
    if has_item(state, ITEM_LIGHTSABER):
        if action_id == "leave_with_lightsaber":
            state.current_scene = SCENE_CAFETERIA
            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_AGORA,
                "scene_facts": [
                    "Cinderella leaves Agora Hall with the lightsaber in hand.",
                    "The absurd sports challenge is behind her now.",
                    "She moves onward toward the next stage of her quest.",
                ],
                "next_scene": SCENE_CAFETERIA,
            }

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella already holds the lightsaber.",
                "There is nothing left to prove in Agora Hall.",
            ],
            "next_scene": None,
        }

    if get_flag(state, STATE_AGORA_CHALLENGE_RESOLVED):
        return _handle_resolved_state(state, action_id)

    if get_flag(state, STATE_AGORA_RALLY_ACTIVE):
        return _resolve_rally(state, action_id)

    if get_flag(state, STATE_AGORA_CHALLENGE_STARTED):
        return _handle_started_state(state, action_id)

    return _handle_intro_state(state, action_id)


def _handle_intro_state(state, action_id):
    if action_id == "study_dwarfs":
        set_flag(state, STATE_AGORA_STUDIED_FORMATION, True)
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella watches the Seven Dwarfs carefully.",
                "They are energetic and aggressive, crowding the front of the court whenever they prepare to attack.",
                "Their formation leaves open space behind them.",
            ],
            "next_scene": None,
        }

    if action_id == "ask_about_weapon":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella asks why the dwarfs are guarding a lightsaber.",
                "Their answer is deeply unhelpful but extremely sincere.",
                "The challenge remains simple: win one badminton round, and the weapon is hers.",
            ],
            "next_scene": None,
        }

    if action_id == "accept_challenge":
        set_flag(state, STATE_AGORA_CHALLENGE_STARTED, True)
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella accepts the badminton challenge.",
                "The Seven Dwarfs cheer and hurry into position.",
                "The atmosphere turns from ridiculous to intensely competitive.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_AGORA,
        "scene_facts": [
            "Cinderella pauses in Agora Hall.",
            "The dwarfs wait for her next move.",
        ],
        "next_scene": None,
    }


def _handle_started_state(state, action_id):
    if action_id == "study_formation":
        set_flag(state, STATE_AGORA_STUDIED_FORMATION, True)
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella studies the court again.",
                "All seven dwarfs drift toward the front line whenever the rally speeds up.",
                "The back court is left exposed.",
            ],
            "next_scene": None,
        }

    if action_id == "taunt_dwarfs":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella tries to throw the dwarfs off their concentration.",
                "The team reacts loudly and emotionally.",
                "They become even more chaotic, but not necessarily smarter.",
            ],
            "next_scene": None,
        }

    if action_id == "start_rally":
        set_flag(state, STATE_AGORA_RALLY_ACTIVE, True)
        set_flag(state, STATE_AGORA_CHALLENGE_RESOLVED, False)

        if get_flag(state, STATE_AGORA_STUDIED_FORMATION):
            facts = [
                "The rally begins at high speed.",
                "Every dwarf rushes toward the front court at once.",
                "Cinderella recognizes the opening she observed earlier.",
                "She must choose her shot carefully.",
            ]
        else:
            facts = [
                "The rally begins suddenly and at high speed.",
                "The dwarfs surge forward in chaotic formation.",
                "Everything happens fast, leaving little time to think.",
                "Cinderella must react under pressure.",
            ]

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": facts,
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_AGORA,
        "scene_facts": [
            "The dwarfs hold their positions on the court.",
            "The challenge is ready to begin.",
        ],
        "next_scene": None,
    }


def _resolve_rally(state, action_id):
    set_flag(state, STATE_AGORA_RALLY_ACTIVE, False)
    set_flag(state, STATE_AGORA_CHALLENGE_RESOLVED, True)

    if action_id == "send_behind":
        set_flag(state, STATE_AGORA_CHALLENGE_WON, True)
        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella sends the shuttle behind all seven dwarfs.",
                "They all spin around in panic at the same moment.",
                "The team collapses into a chaotic pileup.",
                "Cinderella wins the rally through timing and observation.",
            ],
            "next_scene": None,
        }

    set_flag(state, STATE_AGORA_CHALLENGE_WON, False)

    if action_id == "smash_front":
        damage_player(state, 5)
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella smashes directly into the crowded front line.",
                "The dwarfs block the shot almost by accident.",
                "The point is lost, and the failed exchange leaves her slightly drained.",
            ],
            "next_scene": None,
        }

    if action_id == "drop_shot":
        damage_player(state, 5)
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella tries a soft drop shot near the net.",
                "With all seven dwarfs already crowding the front court, the shot fails immediately.",
                "The point is lost, and the rally knocks some energy out of her.",
            ],
            "next_scene": None,
        }

    if action_id == "hesitate":
        damage_player(state, 5)
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella hesitates for just a second too long.",
                "The moment to exploit the opening disappears.",
                "The rally slips away from her, leaving her frustrated and winded.",
            ],
            "next_scene": None,
        }

    damage_player(state, 5)
    return {
        "prompt_type": "penalty_event",
        "scene_id": SCENE_AGORA,
        "scene_facts": [
            "The rally falls apart before Cinderella can take control of it.",
            "The dwarfs take the point in a burst of chaotic energy.",
            "She loses some momentum in the process.",
        ],
        "next_scene": None,
    }


def _handle_resolved_state(state, action_id):
    if get_flag(state, STATE_AGORA_CHALLENGE_WON):
        if action_id == "catch_breath":
            return {
                "prompt_type": "action_reaction",
                "scene_id": SCENE_AGORA,
                "scene_facts": [
                    "The dwarfs are still untangling themselves after the pileup.",
                    "Cinderella takes a moment to steady her breathing.",
                ],
                "next_scene": None,
            }

        if action_id == "claim_lightsaber":
            add_item(state, ITEM_LIGHTSABER)
            set_flag(state, STATE_HAS_LIGHTSABER, True)

            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_AGORA,
                "scene_facts": [
                    "After a long awkward silence, the dwarfs admit defeat.",
                    "The lightsaber is presented to Cinderella.",
                    "She takes the weapon she earned through observation and action.",
                ],
                "next_scene": None,
            }

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "The challenge has already been won.",
                "The lightsaber is now hers to claim.",
            ],
            "next_scene": None,
        }

    if action_id == "retry_rally":
        set_flag(state, STATE_AGORA_CHALLENGE_RESOLVED, False)
        set_flag(state, STATE_AGORA_RALLY_ACTIVE, True)

        facts = [
            "Cinderella prepares for another rally.",
            "The dwarfs rush into the same risky formation again.",
            "The court opens in familiar ways.",
        ]

        if get_flag(state, STATE_AGORA_STUDIED_FORMATION):
            facts.append("This time, she understands their weakness more clearly.")

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": facts,
            "next_scene": None,
        }

    if action_id == "study_formation_again":
        set_flag(state, STATE_AGORA_STUDIED_FORMATION, True)
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella watches the dwarfs reset their positions.",
                "Once again, they commit too heavily to the front court.",
                "Their weakness is still there, waiting to be used.",
            ],
            "next_scene": None,
        }

    if action_id == "taunt_dwarfs":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_AGORA,
            "scene_facts": [
                "Cinderella tries to get under the dwarfs' skin.",
                "They react with loud competitive outrage.",
                "The court grows even more chaotic, but their formation stays careless.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_AGORA,
        "scene_facts": [
            "The dwarfs wait for Cinderella's next move.",
        ],
        "next_scene": None,
    }