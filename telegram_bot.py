import os
import json
import asyncio
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from telegram.helpers import escape_markdown
from dotenv import load_dotenv

# These imports are for the keep-alive web server
# from flask import Flask
# from threading import Thread

# Import custom modules
from fetch_rss import fetch_token_headlines
from extract_token import extract_token_name_symbol
from gemini_query import get_gemini_analysis

load_dotenv()
COINCUB_BOT_TOKEN = os.getenv("COINCUB_BOT_TOKEN")

# Helper Functions
os.makedirs("memory", exist_ok=True); os.makedirs("logs", exist_ok=True)
def get_memory_path(chat_id): return f"memory/{chat_id}.json"
def load_memory(chat_id):
    if not os.path.exists(get_memory_path(chat_id)): return []
    with open(get_memory_path(chat_id), "r", encoding="utf-8") as f:
        try:
            return [json.loads(line) for line in f if (datetime.utcnow() - datetime.fromisoformat(json.loads(line).get("timestamp", "1970-01-01T00:00:00.000000"))).total_seconds() < 86400]
        except (json.JSONDecodeError, TypeError): return []
def save_memory(chat_id, role, text):
    with open(get_memory_path(chat_id), "a", encoding="utf-8") as f: f.write(json.dumps({"role": role, "text": text.strip(), "timestamp": datetime.utcnow().isoformat()}) + "\n")
def clean_response(text: str) -> str:
    return "\n".join([line for line in text.splitlines() if not any(k in line.lower() for k in [".env", "readme", ".py", "working directory"])])
chat_queues = {}

# Keep-Alive Web Server for Deployment
# app = Flask('')

# @app.route('/')
# def home():
#     return "CoinCub is alive!"

# def run_web_server():
#   app.run(host='0.0.0.0', port=8080)

# def keep_alive():
#     t = Thread(name='keep_alive_thread', target=run_web_server)
#     t.daemon = True
#     t.start()

# Telegram Bot Functions 
async def send_safe_reply(update: Update, text: str):
    cleaned_text = clean_response(str(text))
    try:
        for i in range(0, len(cleaned_text), 4096):
            await update.message.reply_text(escape_markdown(cleaned_text[i:i+4096], version=2), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        print(f"❌ Failed to send reply with markdown: {e}")
        await update.message.reply_text(cleaned_text)

# Core logic refactored into a reusable function
async def handle_analysis_query(user_query: str, current_update: Update):
    """Handles the main logic of fetching data and getting an analysis."""
    if not user_query:
        await send_safe_reply(current_update, "Please provide a token or question after the command. Example: `/ask btc`")
        return

    chat_id = current_update.effective_chat.id
    save_memory(chat_id, "user", user_query)

    async def keep_typing_action():
        try:
            while True:
                await current_update.message.chat.send_action(action=ChatAction.TYPING)
                await asyncio.sleep(4)
        except asyncio.CancelledError: pass

    typing_task = asyncio.create_task(keep_typing_action())
    await asyncio.sleep(0)

    fallback_notification_sent = False
    async def send_fallback_notification(failed_model_name):
        nonlocal fallback_notification_sent
        if not fallback_notification_sent:
            fallback_notification_sent = True
            message = f"ℹ️ My primary AI model (`{failed_model_name}`) appears to be busy. I'm trying a faster alternative..."
            await send_safe_reply(current_update, message)
    
    response = ""
    try:
        tokens = extract_token_name_symbol(user_query)
        memory = load_memory(chat_id)
        
        loop = asyncio.get_running_loop()
        def thread_safe_callback(model_name):
            asyncio.run_coroutine_threadsafe(send_fallback_notification(model_name), loop)

        news_md = ""
        if len(tokens) == 1:
            headlines = fetch_token_headlines(tokens[0], max_articles=6)
            news_md = "\n".join([f"- “{n['title']}” — {n['source']}, {n['published']}" for n in headlines]) or "No relevant news found."
            response = await asyncio.to_thread(get_gemini_analysis, tokens, news_md, user_query, chat_id, memory, fallback_callback=thread_safe_callback)
        elif len(tokens) == 2:
            all_headlines = [h for t in tokens for h in fetch_token_headlines(t, max_articles=3)]
            news_md = "\n".join([f"- “{n['title']}” — {n['source']}, {n['published']}" for n in all_headlines]) or "No relevant news found."
            response = await asyncio.to_thread(get_gemini_analysis, tokens, news_md, user_query, chat_id, memory, fallback_callback=thread_safe_callback)
        else:
            general_headlines = fetch_token_headlines(token_name_or_symbol=None, max_articles=6)
            news_md = "\n".join([f"- “{n['title']}” — {n['source']}, {n['published']}" for n in general_headlines]) or "No general news found."
            response = await asyncio.to_thread(get_gemini_analysis, [], news_md, user_query, chat_id, memory, fallback_callback=thread_safe_callback)
    
    except Exception as e:
        print(f"❌ An error occurred in handle_analysis_query: {e}"); response = "😵 Sorry, a general error occurred."
    finally:
        typing_task.cancel()

    save_memory(chat_id, "assistant", response)

    if "❌" not in response:
        await send_safe_reply(current_update, response)
    elif "❌" in response and not fallback_notification_sent:
         await send_safe_reply(current_update, response)

    print(f"✅ Response successfully sent to chat_id: {chat_id}")

# Command Handlers 
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Hey there! Welcome to CoinCub, your AI Crypto Intelligence Assistant!\n\n"
        "I can provide real-time analysis on any cryptocurrency. To get started, just ask me a question!\n\n"
        "Please use the /ask command to ask anything and append your queries after.\n\n"
        "Example Commands:\n"
        "🔹 `/ask btc` - Get a full analysis of Bitcoin.\n"
        "🔹 `/ask eth vs sol` - Compare Ethereum and Solana.\n"
        "🔹 `/ask what is trending?` - Get the latest market trends.\n\n"
        "Type `/help` to see all available commands."
    )
    await send_safe_reply(update, welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "Here's how you can use CoinCub:\n\n"
        "/ask [your query]\n"
        "This is the main command to get crypto analysis. It works in private chats and groups.\n\n"
        "Examples:\n"
        "1️⃣ Single Token Analysis:\n"
        "`/ask What is the latest on Dogecoin?`\n"
        "`/ask price of $ETH`\n\n"
        "2️⃣ Token Comparison:\n"
        "`/ask compare avax vs sui`\n\n"
        "3️⃣ General Questions:\n"
        "`/ask what are the top gainers today?`\n\n"
        "--- \n"
        "*** In a PRIVATE CHAT with me, you can also just type your query WITHOUT the `/ask` command. Just ask me what you want to know! ***\n\n"
    )
    await send_safe_reply(update, help_message)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /ask command by extracting the query and calling the main analysis logic."""
    if not context.args:
        await send_safe_reply(update, "Please provide a question after the `/ask` command. Example: `/ask btc`")
        return
    
    user_query = " ".join(context.args)
    await handle_analysis_query(user_query, update)

async def private_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles regular text messages in private chats."""
    user_query = update.message.text
    await handle_analysis_query(user_query, update)

def run_bot():
    # Starts the keep-alive web server before the bot starts polling
    # keep_alive() 

    print("✅ Bot is now listening..."); 
    app = ApplicationBuilder().token(COINCUB_BOT_TOKEN).build()
    
    # Register all command handlers 
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", ask_command))

    # Register the text handler ONLY for private chats 
    # This prevents the bot from replying to every message in a group.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, private_text_handler))
    
    app.run_polling()

if __name__ == "__main__": 
    asyncio.run(run_bot())