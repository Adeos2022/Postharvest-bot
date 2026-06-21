"""
Postharvest Extension WhatsApp Bot - Trial Version (Text Only)
Connects Twilio WhatsApp Sandbox <-> Google Gemini API (free tier)

SETUP:
1. requirements.txt should contain: flask, google-generativeai, twilio
2. Set environment variable on Render:
   - GEMINI_API_KEY  (get this free from https://aistudio.google.com/app/apikey)
3. Start Command on Render: python app.py
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

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

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
)

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

    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(incoming_msg)
        reply_text = response.text.strip()
        # Save updated history (Gemini's chat object tracks it in its own format)
        conversations[sender] = chat.history[-(MAX_HISTORY_TURNS * 2):]
    except Exception as e:
        reply_text = (
            "Sorry, I had a problem answering that. Please try again in a moment."
        )
        print(f"Error calling Gemini API: {e}")

    twiml = MessagingResponse()
    twiml.message(reply_text)
    return str(twiml)


@app.route("/", methods=["GET"])
def health_check():
    return "Postharvest bot is running."


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
