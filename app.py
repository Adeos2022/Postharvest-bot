"""
Postharvest Extension WhatsApp Bot - Trial Version (Text Only)
Connects Twilio WhatsApp Sandbox <-> Claude API

SETUP:
1. pip install flask anthropic twilio --break-system-packages
2. Set environment variables:
   - ANTHROPIC_API_KEY
   - (Twilio credentials are NOT needed for receiving/replying via TwiML,
     only if you want to send proactive messages later)
3. Run: python app.py
4. Expose it publicly (for trial: use ngrok -> ngrok http 5000)
5. In Twilio Console > WhatsApp Sandbox Settings, set the
   "WHEN A MESSAGE COMES IN" webhook to: https://<your-ngrok-url>/whatsapp
6. Join the sandbox from your WhatsApp by sending the join code Twilio gives you
   to the Twilio sandbox number.
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import anthropic

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Mukulima AI, a friendly agricultural extension assistant \
specializing in postharvest handling for small-scale farmers in Uganda.

Your job is to help farmers reduce postharvest losses through practical, low-cost, \
locally-relevant advice. Follow these rules:

1. Keep answers SHORT and SIMPLE - farmers are reading on basic phones, often in a \
field, often not native English speakers. Use short sentences. Avoid jargon. \
Explain any technical term in plain words if you must use it.

2. Always prioritize LOW-COST or NO-COST solutions first (e.g. proper drying on \
raised mats, sorting, hermetic/triple-layer storage bags, local materials) before \
suggesting anything that requires significant money or equipment.

3. Be crop-specific when possible. Common Ugandan crops to know well: maize, beans, \
cassava, groundnuts, coffee, bananas/matooke, sweet potatoes, sorghum, millet, \
tomatoes, and other vegetables. Postharvest handling differs a lot by crop.

4. Cover the full postharvest chain when relevant: harvest timing, field handling, \
drying, threshing/shelling, sorting/grading, storage, pest and mold prevention, \
transport, and market timing.

5. If a farmer describes a problem (e.g. "my maize has weevils" or "my beans are \
rotting in storage"), ask 1-2 clarifying questions ONLY if truly necessary, \
otherwise give your best practical answer right away. Don't over-interrogate -- \
farmers want answers, not a long Q&A.

6. If you're not fully sure or the situation sounds serious (e.g. suspected \
aflatoxin contamination in grain/groundnuts, which is a serious health risk), say \
so clearly and recommend they contact their local agricultural extension officer \
or NAADS office, in addition to whatever practical guidance you give.

7. Be warm and respectful, like a knowledgeable neighbor, not a corporate chatbot. \
Use a tone that builds trust.

8. Keep replies under roughly 100 words unless the farmer asks for more detail.

9. Reply in English for this trial, but keep wording simple enough that it could \
be easily translated or understood by someone with basic English.
"""

# Simple in-memory conversation history (per WhatsApp number)
# NOTE: this resets if the server restarts. Fine for a solo trial.
conversations = {}

MAX_HISTORY_TURNS = 10  # keep last N user/assistant exchanges per user


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "unknown")

    if sender not in conversations:
        conversations[sender] = []

    history = conversations[sender]
    history.append({"role": "user", "content": incoming_msg})

    # Trim history to avoid unbounded growth
    trimmed_history = history[-(MAX_HISTORY_TURNS * 2):]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=trimmed_history,
        )
        reply_text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
    except Exception as e:
        reply_text = (
            "Sorry, I had a problem answering that. Please try again in a moment."
        )
        print(f"Error calling Claude API: {e}")

    history.append({"role": "assistant", "content": reply_text})
    conversations[sender] = history

    twiml = MessagingResponse()
    twiml.message(reply_text)
    return str(twiml)


@app.route("/", methods=["GET"])
def health_check():
    return "Postharvest bot is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
