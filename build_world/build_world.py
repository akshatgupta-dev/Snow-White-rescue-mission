def build_world():
    return {
        "samk_night": {
            "name": "SAMK at Night",
            "desc": (
                "SAMK is quiet, dark, and a little too dramatic for a normal school night. "
                "The library doors are locked, the halls are empty, and Cinderella is pretty sure "
                "this rescue mission was not mentioned during student orientation."
            ),
            "exits": {
                "north": "samk_library"
            },
            "items": [],
            "locked_exits": {
                "north": "library_access"
            },
            "events": {
                "visited": False,
                "library_access": False
            }
        },

        "samk_library": {
            "name": "SAMK Library",
            "desc": (
                "The library is silent except for the soft hum of computers. On a table lies a map of Pori. "
                "Next to it is a note: 'The weapon of the rescuer is earned, not borrowed. Seek Agora Hall.'"
            ),
            "exits": {
                "south": "samk_night",
                "east": "agora_hall"
            },
            "items": ["map"],
            "locked_exits": {},
            "events": {
                "visited": False,
                "map_taken": False
            }
        },

        "agora_hall": {
            "name": "Agora Hall",
            "desc": (
                "The huge hall is lit like a championship final. In the middle of the court stand "
                "the Seven Dwarfs in matching badminton outfits, guarding the lightsaber like this "
                "is the most normal thing in the world."
            ),
            "exits": {
                "west": "samk_library",
                "east": "cafeteria"
            },
            "items": [],
            "locked_exits": {},
            "events": {
                "visited": False,
                "badminton_won": False,
                "lightsaber_taken": False
            }
        },

        "cafeteria": {
            "name": "SAMK Cafeteria",
            "desc": (
                "The cafeteria is empty except for trays, chairs, and one bright orange pumpkin "
                "sitting on a table. It looks surprisingly fresh. It also looks surprisingly important."
            ),
            "exits": {
                "west": "agora_hall",
                "north": "bridge"
            },
            "items": ["pumpkin"],
            "locked_exits": {},
            "events": {
                "visited": False,
                "pumpkin_taken": False,
                "carriage_used": False
            }
        },

        "bridge": {
            "name": "Bridge to Kirjurinluoto",
            "desc": (
                "The road ends at the bridge to Kirjurinluoto. The magical carriage ride is over. "
                "A bear is nearby, and something about the place feels important."
            ),
            "exits": {
                "south": "cafeteria",
                "north": "kirjurinluoto"
            },
            "items": [],
            "locked_exits": {
                "north": "bear_passed"
            },
            "events": {
                "visited": False,
                "bear_passed": False
            }
        },

        "kirjurinluoto": {
            "name": "Kirjurinluoto Park",
            "desc": (
                "Fog curls between the trees, strange lights shimmer in the distance, and every path looks right "
                "until it suddenly does not. The Evil Queen has filled the park with confusing magic."
            ),
            "exits": {
                "south": "bridge",
                "east": "queen_stage"
            },
            "items": [],
            "locked_exits": {
                "east": "park_puzzle_solved"
            },
            "events": {
                "visited": False,
                "park_puzzle_solved": False
            }
        },

        "queen_stage": {
            "name": "Evil Queen's Stage",
            "desc": (
                "At the center of Kirjurinluoto stands a dark stage glowing with cold purple light. "
                "The Evil Queen waits there with a smile that suggests she has practiced this entrance."
            ),
            "exits": {
                "west": "kirjurinluoto",
                "north": "snow_white_room"
            },
            "items": [],
            "locked_exits": {
                "north": "queen_defeated"
            },
            "events": {
                "visited": False,
                "queen_defeated": False
            }
        },

        "snow_white_room": {
            "name": "Snow White's Chamber",
            "desc": (
                "Snow White is trapped inside a glowing magical chamber. The spell flickers weakly now. "
                "One final brave action will free her and end this strange adventure."
            ),
            "exits": {
                "south": "queen_stage"
            },
            "items": ["apple"],
            "locked_exits": {},
            "events": {
                "visited": False,
                "snow_white_rescued": False,
                "apple_eaten": False
            }
        }
    }


def pretty_item(item_id):
    names = {
        "map": "City Map",
        "pumpkin": "Magic Pumpkin",
        "lightsaber": "Lightsaber",
        "apple": "Shiny Apple"
    }
    return names.get(item_id, item_id.replace("_", " ").title())