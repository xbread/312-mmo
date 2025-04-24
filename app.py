from flask import Flask, request, render_template, redirect
from flask_socketio import SocketIO, emit
from util.Logging import log_request
from util.Authentication import registration, login, logout, get_username_from_request
from util.websocket_functions import *

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app)

# Dict of users w/ sid
user_sessions = {}
# list of just users
user_list = []
# saving username
session = {}

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
            session["username"] = request.form.get("0")
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
    username = session["username"]
    print(username)
    if not username:
        return redirect('/login')
    return render_template('home.html', username=username)

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
def handle_connet(auth_token):
    username = get_username(auth_token)
    if username is not None:
        user_sessions[request.sid] = username
        user_list.append(username)
        emit('update_users', user_list, broadcast=True)
    else:
        raise ConnectionRefusedError('unauthorized!')

@socketio.on('disconnect')
def handle_disconnect():
    username = user_sessions.pop(request.sid)
    user_list.remove(username)
    emit('update_players', user_list, broadcast=True)

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


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=8080)