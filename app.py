from flask import Flask, request, render_template
from util.Logging import log_request

app = Flask(__name__, template_folder="templates")


@app.before_request
def log_incoming_request():
    ip = request.remote_addr
    method = request.method
    path = request.path
    log_request(ip, method, path)

@app.route("/gameboard")
def gameboard():
    return render_template("gameboard.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)