from flask import Flask, request, render_template, redirect
from flask_socketio import SocketIO, emit
from util.Logging import log_request
from util.Authentication import registration, login, logout, get_username_from_request
from util.websocket_functions import *
import threading
import time

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app)

# Dict of users w/ sid
user_sessions = {}
# list of just users
user_list = []
player_snakes = {}
player_ready = {}  # sid -> bool


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
        emit('start_countdown', broadcast=True)
        
def broadcast_users_update():
    users_data = []
    for sid, username in user_sessions.items():
        users_data.append({
            'username': username,
            'ready': player_ready.get(sid, False)
        })
    emit('update_users', {'users': users_data}, broadcast=True)
    

def broadcast_snakes_periodically():
    while True:
        if player_snakes:
            socketio.emit('update_players', player_snakes)
        time.sleep(0.05)  # broadcast 20 times per second

# Start the periodic broadcast thread
threading.Thread(target=broadcast_snakes_periodically, daemon=True).start()
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)