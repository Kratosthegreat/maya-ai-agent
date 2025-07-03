from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"service": "maya-bot", "status": "ok"})

@app.route("/webhook", methods=["POST"])
def webhook():
    # process Telegram's update here
    update = request.get_json()
    # ... your logic ...
    return "OK", 200
