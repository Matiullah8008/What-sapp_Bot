"""Flask webhook for WhatsApp Cloud API: verification + incoming messages."""
import os

import requests
from flask import Flask, jsonify, request

from bot import BotEngine

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "demo_verify_token")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
GRAPH_URL = "https://graph.facebook.com/v21.0"

engine = BotEngine(business_id=os.environ.get("BUSINESS_ID", "demo_shop"))


def send_whatsapp(to, text):
    """Send a WhatsApp text message. Dry-run (print) when no credentials set."""
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("[DRY-RUN] To {}: {}".format(to, text))
        return {"dry_run": True}
    url = "{}/{}/messages".format(GRAPH_URL, PHONE_NUMBER_ID)
    headers = {
        "Authorization": "Bearer {}".format(WHATSAPP_TOKEN),
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    return r.json()


@app.route("/", methods=["GET"])
def health():
    return "bot running", 200


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def incoming():
    data = request.get_json(force=True, silent=True) or {}
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        for msg in entry.get("messages", []):
            if msg.get("type") != "text":
                continue
            sender = msg["from"]
            text = msg["text"]["body"]
            reply = engine.reply(text)
            send_whatsapp(sender, reply)
    except Exception as e:  # noqa: BLE001 - never break the webhook
        print("webhook error:", e)
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
