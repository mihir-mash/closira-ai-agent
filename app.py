"""
Flask web server exposing the ClosiraAgent via a simple JSON API.

The UI is a minimal single‑page app located in the frontend/ directory.
All interactions are routed through ``/api/chat`` which expects a JSON
payload ``{"message": "..."}`` and returns ``{"reply": "...", "ended": bool}``.

The server runs on ``http://localhost:5000`` (default Flask port) and is
intended for local development only.
"""

from flask import Flask, request, jsonify, send_from_directory
import os
from pathlib import Path

# Ensure project root is on sys.path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from agent import ClosiraAgent

app = Flask(__name__, static_folder="frontend", static_url_path="")

# ---------------------------------------------------------------------------
# Initialise a single shared ClosiraAgent instance for the life of the server
# ---------------------------------------------------------------------------
agent = ClosiraAgent()
agent.load_sop("data/sop.json")

# ---------------------------------------------------------------------------
# Helper – decide if the user wants to end the session
# ---------------------------------------------------------------------------
EXIT_COMMANDS = {"exit", "quit", "bye", "done"}

@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "[SYSTEM] Empty message received.", "ended": False})

    # Check for exit command – generate summary and indicate session end
    if user_msg.lower() in EXIT_COMMANDS:
        # Trigger a friendly closing message and final summary
        farewell = "Thank you for chatting with us today! We hope to see you at Bloom soon. 🌸"
        summary = agent.generate_summary()
        full_reply = f"{farewell}\n\n{summary}"
        return jsonify({"reply": full_reply, "ended": True})

    # Normal conversation turn
    reply = agent.chat(user_msg)
    return jsonify({"reply": reply, "ended": False})

# Serve the frontend HTML page at the root URL
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    # Run on the default Flask port (5000) – suitable for local use
    app.run(host="127.0.0.1", port=5000, debug=False)
