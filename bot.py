#!/usr/bin/env python3
"""
Minimal Telegram Spam Filter Bot - MVP
Quick test version for detecting financial spam with Gemini AI
"""

import os
import json
from dotenv import load_dotenv
import telebot
from telebot.types import Update
import google.generativeai as genai
from fastapi import FastAPI, Request, Response

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Set this in Railway

# Initialize
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

print("🤖 Bot starting...")


def is_spam(text):
    """Check if message is financial spam using Gemini"""
    prompt = f"""Analyze this message in ANY language (Russian, English, etc.) and determine if it contains financial spam.

Financial spam includes:
- USDT/cryptocurrency buying/selling for cash (юсдт за наличку, продать usdt)
- Crypto P2P exchange requests with meetups (встреча, обмен, наличные)
- Cryptocurrency trading signals or promotions (крипто сигналы)
- Forex trading schemes (форекс)
- Investment scams, pump-and-dump (инвестиции, памп)
- Guaranteed returns claims (гарантированный доход)
- Referral/affiliate links to trading platforms
- Asking to buy/sell crypto for cash in person

Message to analyze: {text}

Reply with JSON only. Use this exact format:
{{"is_spam": true/false, "confidence": <integer from 0 to 100>}}

Example: {{"is_spam": true, "confidence": 95}}"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Clean markdown if present
        if '```' in result_text:
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        result_text = result_text.strip()
        print(f"AI response: {result_text}", flush=True)

        result = json.loads(result_text)
        confidence = result.get('confidence', 0)

        # Handle both 0-1 scale (0.98) and 0-100 scale (98)
        if confidence <= 1:
            confidence = confidence * 100

        print(f"AI parsed: is_spam={result.get('is_spam')}, confidence={confidence}%", flush=True)

        return result.get('is_spam', False) and confidence > 80

    except Exception as e:
        print(f"AI Error: {e}")
        return False


@bot.channel_post_handler(func=lambda m: True)
def check_channel_post(message):
    """Check channel posts for spam"""
    text = message.text or message.caption
    if not text:
        return

    chat_title = message.chat.title or "Unknown"

    print(f"\n📢 Channel post in: {chat_title}")
    print(f"Message: {text[:100]}...")

    if is_spam(text):
        print(f"🚫 SPAM detected!")

        try:
            bot.delete_message(message.chat.id, message.message_id)
            print(f"✅ Deleted spam post\n")
        except Exception as e:
            print(f"⚠️  Can't delete: {e}\n")
    else:
        print(f"✅ Not spam\n")


@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def check_message(message):
    """Check group messages for spam and ban users"""
    # Skip if this is a channel post (already handled by channel_post_handler)
    if message.chat.type == 'channel':
        return

    text = message.text or message.caption
    if not text:
        print(f"📨 Non-text message from chat {message.chat.id}")
        return

    user = message.from_user.username or message.from_user.first_name
    chat_type = message.chat.type
    chat_title = message.chat.title or "DM"

    print(f"\n{'='*60}")
    print(f"📨 NEW MESSAGE")
    print(f"Chat: {chat_title} ({chat_type})")
    print(f"User: {user} (ID: {message.from_user.id})")
    print(f"Message: {text[:100]}...")
    print(f"{'='*60}")

    if is_spam(text):
        print(f"🚫 SPAM detected!")

        try:
            # Delete the message
            bot.delete_message(message.chat.id, message.message_id)
            print(f"✅ Deleted spam message")

            # Ban the user
            bot.ban_chat_member(message.chat.id, message.from_user.id)
            print(f"🔨 Banned user: {user} (ID: {message.from_user.id})\n")
        except Exception as e:
            print(f"⚠️  Error: {e}\n")
    else:
        print(f"✅ Not spam\n")


@app.on_event("startup")
async def on_startup():
    """Set webhook on startup"""
    me = bot.get_me()
    print(f"✅ Bot @{me.username} is starting!")
    print(f"Bot ID: {me.id}")

    if not WEBHOOK_URL:
        print("❌ ERROR: WEBHOOK_URL environment variable not set!")
        return

    webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    print(f"Setting webhook to: {webhook_url}")
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print("✅ Webhook set successfully!\n")


@app.post(f"/{BOT_TOKEN}")
async def webhook(request: Request):
    """Handle incoming Telegram updates"""
    if request.headers.get('content-type') == 'application/json':
        json_string = await request.body()
        update = Update.de_json(json_string.decode('utf-8'))
        bot.process_new_updates([update])
        return Response(status_code=200)
    return Response(status_code=403)


@app.get("/")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "bot": "running"}
