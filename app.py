from flask import Flask, request, render_template, redirect
from flask_socketio import SocketIO, emit
from util.Logging import log_request
from util.Authentication import registration, login
from util.websocket_functions import *

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app)

# Dict of users w/ sid
user_sessions = {}
# list of just users
user_list = []

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
            return redirect('/home')  # or whatever page you want to land on
        else:
            error_message = "Invalid credentials."
            return render_template('login.html', error=error_message)
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route("/gameboard")
def gameboard():
    return render_template("gameboard.html")

@socketio.on('join')
def handle_join(auth_token):
    username = get_username(auth_token)
    if username is not None:
        user_sessions[request.sid] = username
        user_list.append(username)
        emit('connection', {'users' : user_list}, broadcast=True)
    else:
        raise ConnectionRefusedError('unauthorized!')

@socketio.on('disconnect')
def handle_disconnect():
    username = user_sessions.pop(request.sid)
    user_list.pop(username)
    emit('connection', {'users' : user_list}, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=8080)