from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "maya-bot"})

@app.route('/webhook', methods=['POST'])
def webhook():
    # עיבוד update לטלגרם (ראה main.py)
    return "OK", 200
