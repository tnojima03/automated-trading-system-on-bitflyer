import json


with open("states.json") as f:
    states = json.load(f)
    is_position = states["is_position"] #ポジションを持っているかどうか
    is_order = states["is_order"]

def update_is_order(new_is_order):
    global is_order
    is_order = new_is_order
    with open("states.json", "w") as f:
	    json.dump({"is_position":is_position, "is_order":new_is_order},f)

def update_is_position(new_is_position):
    global is_position
    is_position = new_is_position
    with open("states.json", "w") as f:
	    json.dump({"is_position":new_is_position, "is_order":is_order},f)
