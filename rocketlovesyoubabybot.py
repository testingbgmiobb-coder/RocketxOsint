#!/usr/bin/env python3
"""
Number Info Telegram Bot – Public Access with Admin Panel
Supports justrunmy.app environment variables.
Admin: @rocket_xd777, @rocketxd555
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Set
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
import requests

# ===================== CONFIGURATION =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8725394387:AAHSKd3CHo--H_sglPnM32uaeKiRv2kfNp0")

# Admin usernames (case‑insensitive)
ADMIN_USERNAMES = ["rocket_xd777", "rocketxd555"]

# API endpoint
API_URL = "https://ftosint.world/api/numleak"
API_KEY = "rocket-itsdonebro"

# Store user IDs for broadcast/stats
known_users: Set[int] = set()

# ===================== LOGGING =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== ADMIN CHECK =====================
def is_admin(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    if user.username and user.username.lower() in [a.lower() for a in ADMIN_USERNAMES]:
        return True
    return False

# ===================== API FUNCTIONS =====================
def query_api(phone: str) -> Optional[Dict]:
    try:
        resp = requests.get(
            API_URL,
            params={"key": API_KEY, "num": phone},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"API error for {phone}: {e}")
        return None

def parse_addr(adres: str) -> str:
    if not adres or adres.startswith("!!"):
        return None
    parts = [p.strip() for p in adres.split("!") if p.strip()]
    skip_keywords = ["s/o", "c/o"]
    filtered = [p for p in parts if not any(p.lower().startswith(k) for k in skip_keywords)]
    if filtered and len(filtered[0].split()) <= 3 and not any(c.isdigit() for c in filtered[0]) and len(filtered) > 2:
        filtered = filtered[1:]
    return ", ".join(filtered) if filtered else None

def fmt_aadhaar(doc: str) -> str:
    doc = doc.strip()
    if doc.isdigit() and len(doc) == 12:
        return f"{doc[:4]}-{doc[4:8]}-{doc[8:]}"
    return doc

def build_result(data: Dict, username: str) -> str:
    number = data.get("number", "N/A")
    records = data.get("chain", {}).get("records", [])
    ct = data.get("calltracer", {})

    seen = set()
    alt_phones = []
    for rec in records:
        if rec.get("Phone"):
            seen.add(rec["Phone"])
        for k in [f"Phone{i}" for i in range(2, 37)]:
            p = rec.get(k, "")
            if p and p not in seen:
                alt_phones.append(p)
                seen.add(p)

    rec = next((r for r in records if r.get("Phone") == number), records[0] if records else None)

    lines = ["═══ RESULT ═══", "📊 OUTPUT DETAILS:"]

    if rec:
        name = rec.get("FullName", "").strip()
        father = rec.get("FatherName", "").strip()
        doc = rec.get("DocumentNumber", "").strip()
        region = rec.get("Region", "").strip()
        addr = None
        for af in ["Adres", "Adres2", "Adres3"]:
            a = rec.get(af, "")
            if a:
                addr = parse_addr(a)
                if addr:
                    break

        if name:
            lines.append(f"👤 Name: {name}")
        if father:
            lines.append(f"👨‍👦 Father: {father}")
        lines.append(f"📱 Mobile: {number}")
        if alt_phones:
            lines.append(f"📞 Alt: {', '.join(alt_phones[:10])}")
        if addr:
            lines.append(f"🏠 Address: {addr}")
        if doc:
            lines.append(f"🪪 Aadhaar: {fmt_aadhaar(doc)}")
        if region:
            lines.append(f"📡 Circle: {region}")

    extras = []
    if ct.get("SIM card"):
        extras.append(f"📡 SIM: {ct['SIM card']}")
    if ct.get("Mobile State"):
        extras.append(f"📍 State: {ct['Mobile State']}")
    elif ct.get("Mobile City"):
        extras.append(f"📍 City: {ct['Mobile City']}")
    if ct.get("Connection"):
        extras.append(f"🔌 Connection: {ct['Connection']}")
    if ct.get("Language"):
        extras.append(f"🗣️ Language: {ct['Language']}")
    if ct.get("Helpline"):
        extras.append(f"📞 Helpline: {ct['Helpline']}")
    if extras:
        lines.append("")
        lines.append("📋 ADDITIONAL INFO:")
        lines.extend(extras)

    lines.extend([
        "",
        "✅ Search Complete",
        f"📱 Number: {number}",
        f"📊 Results Found: {len(records)}",
        f"👤 Checked by: @{username}",
        "👨‍💻 Developer: @rocket_xd777"
    ])
    return "\n".join(lines)

# ===================== BOT HANDLERS =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    known_users.add(user.id)
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        "📱 Send me any Indian mobile number (10 digits) to get details.\n"
        "🔍 I will fetch information from public sources."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    known_users.add(user.id)

    raw = update.message.text.strip()
    phone = "".join(c for c in raw if c.isdigit())
    for prefix in ["91", "091", "0"]:
        if phone.startswith(prefix):
            phone = phone[len(prefix):]
            break

    if len(phone) != 10 or not phone.isdigit():
        await update.message.reply_text("❌ Invalid number. Please send a 10‑digit Indian mobile number.")
        return

    msg = await update.message.reply_text(f"🔍 Searching for {phone}... ⏳")
    t0 = time.time()
    data = query_api(phone)
    elapsed = time.time() - t0

    if not data or not data.get("success"):
        await msg.edit_text(f"❌ API returned an error for {phone}.\nPlease try again later.")
        return

    result = build_result(data, user.username or f"user_{user.id}")
    result += f"\n⚡ Response: {elapsed*1000:.0f}ms"

    if len(result) <= 4096:
        await msg.edit_text(result)
    else:
        await msg.delete()
        for part in [result[i:i+4000] for i in range(0, len(result), 4000)]:
            await update.message.reply_text(part)

# ===================== ADMIN COMMANDS =====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ You are not an admin.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 List Users", callback_data="admin_users")],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")],
    ])
    await update.message.reply_text(
        "🔐 **Admin Panel**\nChoose an action:",
        reply_markup=keyboard
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update):
        await query.edit_message_text("⛔ Unauthorized.")
        return

    action = query.data
    if action == "admin_stats":
        total = len(known_users)
        await query.edit_message_text(
            f"📊 **Bot Statistics**\n"
            f"• Total unique users: {total}\n"
            f"• Admins: {', '.join('@'+a for a in ADMIN_USERNAMES)}"
        )
    elif action == "admin_users":
        users_list = list(known_users)[:20]
        if users_list:
            text = "👥 **Recent Users (IDs)**\n" + "\n".join(str(uid) for uid in users_list)
            if len(known_users) > 20:
                text += f"\n... and {len(known_users)-20} more"
        else:
            text = "No users recorded yet."
        await query.edit_message_text(text)
    elif action == "admin_broadcast":
        await query.edit_message_text(
            "📢 **Broadcast**\n"
            "Send a message to this chat, and I will forward it to all users.\n"
            "Reply to this message with the broadcast text."
        )
        context.user_data["broadcast_mode"] = True
    elif action == "admin_restart":
        await query.edit_message_text("🔄 Restarting bot... (not implemented; you can manually restart the script)")

async def broadcast_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if context.user_data.get("broadcast_mode"):
        text = update.message.text
        count = 0
        for uid in known_users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 **Announcement**\n{text}")
                count += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
        context.user_data["broadcast_mode"] = False
    else:
        await update.message.reply_text("Not in broadcast mode. Use /admin to start.")

# ===================== MAIN =====================
def main():
    if BOT_TOKEN == "8868460494:AAGIhqCeSxRiKX6UmsrLxgQ79GienXntlak" and not os.environ.get("BOT_TOKEN"):
        print("⚠️  WARNING: Using hardcoded token. For security, set BOT_TOKEN in environment.")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # Error handler
    app.add_error_handler(lambda u, c: logger.error(f"Error: {c.error}"))

    print("🤖 Bot started. Public access, admin panel enabled.")
    print(f"   Admins: {', '.join('@'+a for a in ADMIN_USERNAMES)}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()