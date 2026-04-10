import logging
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    ContextTypes,
    filters,
)

# ================= ENV CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # <-- এখানে token থাকবে env এ
BOT_USERNAME = os.getenv("BOT_USERNAME", "Ghriftygbot")  # optional fallback

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# ================= LOGGING =================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

pending_requests = {}

# ---------------- /start COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    text = (
        f"🙋‍♂️ Hello {user.full_name}\n\n"
        "আমি একটি Join Request Verification Bot\n\n"
        "User কে verify করে তারপর approve করে।\n\n"
        "⚠️ অবশ্যই সব permission দিয়ে admin করবেন।"
    )

    keyboard = [
        [InlineKeyboardButton("➕ Add To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📢 Add To Channel", url=f"https://t.me/{BOT_USERNAME}?startchannel=true")]
    ]

    await update.message.reply_photo(
        photo="https://i.ibb.co/YKyw0BQ/1000007551.png",
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- JOIN REQUEST HANDLER ----------------
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):

    request = update.chat_join_request
    user = request.from_user

    # Fake account filter: username না থাকলে decline
    if user.username is None:
        await context.bot.decline_chat_join_request(request.chat.id, user.id)
        return

    pending_requests[user.id] = request

    message = (
        f"Hello {user.first_name}! 👋\n\n"
        "Do you want to join the group?\n\n"
        "✅ Write yes — if you want to join\n\n"
        "❌ Write no — if you don't want to join"
    )

    try:
        await context.bot.send_message(user.id, message)
    except:
        print("User did not start bot")

    asyncio.create_task(timeout_request(user.id))

async def timeout_request(user_id):
    await asyncio.sleep(60)
    if user_id in pending_requests:
        req = pending_requests[user_id]
        try:
            await req.decline()
        except:
            pass
        del pending_requests[user_id]

# ---------------- PRIVATE MESSAGE HANDLER ----------------
async def handle_private(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text.lower()

    if user_id not in pending_requests:
        return

    request = pending_requests[user_id]

    if text == "yes":
        await context.bot.approve_chat_join_request(request.chat.id, user_id)
        await update.message.reply_text("✅ You are approved!")
        del pending_requests[user_id]

    elif text == "no":
        await context.bot.decline_chat_join_request(request.chat.id, user_id)
        await update.message.reply_text("❌ Request cancelled.")
        del pending_requests[user_id]

    else:
        await update.message.reply_text("⚠️ Reply only: yes / no")

# ---------------- ADMIN COMMAND ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 Pending Requests: {len(pending_requests)}")

# ---------------- MAIN FUNCTION ----------------
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private)
    )

    app.run_polling()

if __name__ == "__main__":
    main()