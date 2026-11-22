import os
import json
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests

# --- Config (same as yours) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = "https://ftosint.world/api/numleak"
API_KEY = "rocket-itsdonebro"
ADMIN_USERNAMES = ["rocket_xd777", "rocketxd555"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App ---
flask_app = Flask(__name__)

# --- PTB Application (build once) ---
ptb_app = Application.builder().token(BOT_TOKEN).build()

# ... (Aapke saare helper functions: is_admin, query_api, parse_addr, fmt_aadhaar, build_result yahan paste karein) ...

# ... (Aapke saare handlers: start, handle_message, admin_panel, admin_callback, broadcast_reply yahan paste karein) ...

# Handlers register karein
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("admin", admin_panel))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
ptb_app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

# --- Flask Routes ---
@flask_app.route("/api", methods=["POST"])
def webhook():
    """Telegram se aane wale updates yahan receive honge."""
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(force=True), ptb_app.bot)
            # Async handler ko sync context mein run karein
            import asyncio
            asyncio.run(ptb_app.process_update(update))
            return "OK", 200
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return "Error", 500

@flask_app.route("/api", methods=["GET"])
def health():
    """Health check ke liye."""
    return "Bot is alive!", 200

# Vercel ke liye entrypoint
app = flask_app
