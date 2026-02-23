
game_state = {
    "players": ["Charlie", "Alex"],
    "scores": [12, 8],
    "dealer": 0
}




import json

json_string = json.dumps(game_state)

print(json_string)


loaded = json.loads(json_string)

print(type(loaded))   # dict
print(loaded["scores"])

