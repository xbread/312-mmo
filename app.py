from flask import Flask, request, render_template, redirect
from flask_socketio import SocketIO, emit
from util.Logging import log_request
from util.Authentication import registration, login, logout, get_username_from_request
from util.websocket_functions import *
import threading
import time
import random

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app)

# Dict of users w/ sid
user_sessions = {}
# list of just users
user_list = []
player_snakes = {}
player_ready = {}  # sid -> bool
current_food = []


@app.before_request
def log_incoming_request():
    ip = request.remote_addr
    method = request.method
    path = request.path
    log_request(ip, method, path)
    
@app.route('/')
def start():
    return redirect("/register")
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        response = registration(request)
        if response.status_code == 200:
            return redirect('/login')
        else:
            error_type = response.get_data(as_text=True)
            if error_type == "USERNAME_TAKEN":
                message = "Username is already taken."
            elif error_type == "WEAK_PASSWORD":
                message = "Password is too weak."
            return render_template('register.html', error=message)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        response = login(request)
        if response.status_code == 200:
            response.status_code = 302
            response.headers["Location"] = "/home"
            return response
        else:
            error_message = "Invalid credentials."
            return render_template('login.html', error=error_message)
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def log_out():
    return logout(request)

@app.route('/home')
def home():
    auth_token = request.cookies.get('auth_token')
    username = get_username_from_request(request)
    if not username:
        return redirect('/login')
    # print("token: ", auth_token)
    return render_template('home.html', username=username, auth_token=auth_token)


@app.route('/profile')
def profile():
    username = get_username_from_request(request)
    if not username:
        return redirect('/login')
    # Look up the user's imageURL
    user = user_collection.find_one({"username": username})
    image_url = user.get("imageURL", "public/avatar/default_avatar.png")

    return render_template("profile.html", username=username, image_url=image_url)


@app.route("/gameboard")
def gameboard():
    return render_template("gameboard.html")

@socketio.on('connect')
def handle_connect(auth_token):
    username = get_username(auth_token)
    if username is not None:
        user_sessions[request.sid] = username
        user_list.append(username)
        player_ready[request.sid] = False

        broadcast_users_update()
        # if current_food is not None:
        #     emit('food_update', current_food)
    else:
        raise ConnectionRefusedError('unauthorized!')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    username = user_sessions.get(sid)

    if username:
        try:
            user_list.remove(username)
        except ValueError:
            pass
        del user_sessions[sid]
        player_ready.pop(sid, None)
        player_snakes.pop(sid, None)
        socketio.emit('update_players', player_snakes)
        
        broadcast_users_update()


# WebSocket event to send player positions to the client
@socketio.on('get_players')
def handle_get_users():
    emit('update_players', user_list)

# WebSocket event to update player position
@socketio.on('move_user')
def handle_move_user(data):
    player_id = data['id']
    new_x = data['x']
    new_y = data['y']

    # Update the player's position in the list
    for user in user_list:
        if user['id'] == player_id:
            user['x'] = new_x
            user['y'] = new_y

    # Emit updated player positions
    emit('update_players', user_list, broadcast=True)

@socketio.on('player_update')
def handle_player_update(data):
    sid = request.sid
    player_snakes[sid] = data['snake']  # store the snake list

    # Broadcast updated positions to everyone
    emit('update_players', player_snakes, broadcast=True)

@socketio.on('ready_up')
def handle_ready_up():
    sid = request.sid
    player_ready[sid] = True

    broadcast_users_update()

    # Check if all players are ready
    if all(player_ready.get(s, False) for s in user_sessions.keys()):
        # Move this into spawn_new_food:
        spawn_new_food(start_countdown=True)


@socketio.on('food_eaten')
def handle_food_eaten(data):
    global current_food
    eaten_x = data['x']
    eaten_y = data['y']

    # Remove the eaten food
    current_food = [f for f in current_food if not (f['x'] == eaten_x and f['y'] == eaten_y)]

    # Spawn a new food
    grid_width = 20
    grid_height = 20
    while True:
        x = random.randint(0, grid_width - 1)
        y = random.randint(0, grid_height - 1)
        if {'x': x, 'y': y} not in current_food:
            current_food.append({'x': x, 'y': y})
            break

    # Broadcast updated food list
    emit('food_update', current_food, broadcast=True)

    
@socketio.on('player_died')
def handle_player_died():
    sid = request.sid
    if sid in player_snakes:
        del player_snakes[sid]

    if sid in player_ready:
        player_ready[sid] = False  # Not ready anymore

    socketio.emit('update_players', player_snakes)
    
    check_for_game_end()    
        
def check_for_game_end():
    alive_players = [sid for sid in player_snakes if player_snakes[sid]]

    if len(alive_players) <= 1:
        print("Game over!")
        # Reset all players' ready status
        for sid in player_ready.keys():
            player_ready[sid] = False

        broadcast_users_update()
        winner_username = None
        if alive_players:
            winner_sid = alive_players[0]
            winner_username = user_sessions.get(winner_sid)
        socketio.emit('game_over', {'winner': winner_username})    
        
def spawn_new_food(start_countdown=False):
    global current_food
    grid_width = 20
    grid_height = 20

    if start_countdown:
        # Reset current food
        current_food = []
        # Spawn starting positions
        starting_positions = {}
        used_positions = set()
        player_colors = {}


        for sid in user_sessions.keys():
            while True:
                x = random.randint(0, grid_width - 1)
                y = random.randint(0, grid_height - 1)
                if (x, y) not in used_positions:
                    used_positions.add((x, y))
                    starting_positions[sid] = {"x": x, "y": y}
                    player_colors[sid] = random_color()
                    break

        # Spawn 1 food per player
        for _ in range(len(user_sessions)):
            while True:
                x = random.randint(0, grid_width - 1)
                y = random.randint(0, grid_height - 1)
                if (x, y) not in used_positions:
                    used_positions.add((x, y))
                    current_food.append({'x': x, 'y': y})
                    break

        emit('start_countdown', 
             {'food': current_food, 
              'starting_positions': starting_positions,
              'player_colors': player_colors},
             broadcast=True)
    else:
        # During normal gameplay, spawn 1 food
        grid_width = 20
        grid_height = 20
        while True:
            x = random.randint(0, grid_width - 1)
            y = random.randint(0, grid_height - 1)
            if {'x': x, 'y': y} not in current_food:
                current_food.append({'x': x, 'y': y})
                break
        emit('food_update', current_food, broadcast=True)
        
def random_color():
    # Avoid "red" and "green"
    bad_colors = ['red', 'green', '#ff0000', '#00ff00', '#a8d080', '#98c070']
    while True:
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        if color.lower() not in bad_colors:
            return color

        
        
def broadcast_users_update():
    users_data = []
    for sid, username in user_sessions.items():
        users_data.append({
            'username': username,
            'ready': player_ready.get(sid, False)
        })
    emit('update_users', {'users': users_data}, broadcast=True)
    

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)