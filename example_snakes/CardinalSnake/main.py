# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import random
import typing


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#888888",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")




# Things needed to imporve: 
# fix collision with opponents ?
# fix collision with myself -- maybe think 2 steps ahead 
# more advanced strategies 

# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # Step 1 - Prevent your Battlesnake from moving out of bounds
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    # print("my head", my_head)
    # print("board_width",board_width, "board_height", board_height)

    if my_head["x"] >= (board_width - 1):
        is_move_safe["right"] = False
    elif my_head["x"] <= 0:
        is_move_safe["left"] = False

    if my_head["y"] >= (board_height - 1):
        is_move_safe["up"] = False
    elif my_head["y"] <= 0:
        is_move_safe["down"] = False

    # Step 2 - Prevent your Battlesnake from colliding with itself
    # Step 3 - Prevent your Battlesnake from colliding with other Battlesnakes
    my_body = game_state['you']['body']
    opponents = game_state['board']['snakes']

    new_head = {
    "x": my_head["x"],
    "y": my_head["y"] + 1
    }

    if (new_head in my_body) or (new_head in opponents[0]["body"]):
        is_move_safe["up"] = False

    new_head = {
    "x": my_head["x"],
    "y": my_head["y"] - 1
    }

    if (new_head in my_body) or (new_head in opponents[0]["body"]):
        is_move_safe["down"] = False
    
    new_head = {
    "x": my_head["x"] + 1,
    "y": my_head["y"]
    }

    if (new_head in my_body) or (new_head in opponents[0]["body"]):
        is_move_safe["right"] = False


    new_head = {
    "x": my_head["x"] - 1,
    "y": my_head["y"]
    }

    if (new_head in my_body) or (new_head in opponents[0]["body"]):
        is_move_safe["left"] = False

    # TODO: problem: need to control 2 moves or more ahead to prevent self-collision 

    

    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    # Step 4 - Move towards food instead of random, to regain health and survive longer
    food = game_state['board']['food']

    closest = food[0]
    min_dis = 0
    for piece in food:
        distance = abs(piece["x"] - my_head["x"]) + abs(piece["y"] - my_head["y"])
        if distance < min_dis:
            min_dis = distance
            closest = piece

    if (closest["x"] > my_head["x"]) and is_move_safe["right"]:
        next_move = "right"
    elif (closest["x"] < my_head["x"]) and is_move_safe["left"]:
        next_move = "left"
    elif (closest["y"] > my_head["y"]) and is_move_safe["up"]:
        next_move = "up"
    elif (closest["y"] < my_head["y"]) and is_move_safe["down"]:
        next_move = "down"
    else:
        next_move = random.choice(safe_moves) 


    # next_move = random.choice(safe_moves) 


    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})