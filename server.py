import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 1️⃣ Facebook Webhook Verification
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Forbidden", 403

# 2️⃣ Handle Messages and Send to OpenAI
@app.route('/webhook', methods=['POST'])
def handle_messages():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]
                    ai_response = get_ai_response(user_message)
                    send_message(sender_id, ai_response)
    return "EVENT_RECEIVED", 200

# 3️⃣ OpenAI API Call
def get_ai_response(user_message):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": user_message}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

# 4️⃣ Send Response to Messenger
def send_message(recipient_id, message):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message}
    }
    requests.post(url, json=data)

# 5️⃣ Run the Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True))
