achievements_list = {
    "win_game": {
        "title": "Victor!",
        "description": "Win a game.",
        "check": lambda stats: stats.get("games_won", 0) >= 1
    },
    "self_elim": {
        "title": "Oops!",
        "description": "Eliminate yourself.",
        "check": lambda stats: stats.get("self_deaths", 0) >= 1
    },
    "ten_games": {
        "title": "Veteran",
        "description": "Play 10 games.",
        "check": lambda stats: stats.get("games_played", 0) >= 10
    },
    "three_kills": {
        "title": "Hunter",
        "description": "Eliminate 3 players.",
        "check": lambda stats: stats.get("kills", 0) >= 3
    },
    "five_food": {
        "title": "Hungry",
        "description": "Eat 5 food.",
        "check": lambda stats: stats.get("food_eaten", 0) >= 5
    },
    "length_10": {
        "title": "Long Boi",
        "description": "Reach a snake length of 10.",
        "check": lambda stats: stats.get("longest_length", 0) >= 10
    },
}
