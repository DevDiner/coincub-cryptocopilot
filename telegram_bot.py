# telegram_bot.py
import os
import json
import asyncio
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode, ChatAction #ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.helpers import escape_markdown
from dotenv import load_dotenv
# from flask import Flask
# from threading import Thread

from fetch_rss import fetch_token_headlines
from extract_token import extract_token_name_symbol
from gemini_query import get_gemini_analysis

load_dotenv()
COINCUB_BOT_TOKEN = os.getenv("COINCUB_BOT_TOKEN")

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

async def send_safe_reply(update: Update, text: str):
    cleaned_text = clean_response(str(text)) # Ensure text is a string
    try:
        for i in range(0, len(cleaned_text), 4096):
            await update.message.reply_text(escape_markdown(cleaned_text[i:i+4096], version=2), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        print(f"❌ Failed to send reply with markdown: {e}")
        await update.message.reply_text(cleaned_text)

async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in chat_queues: chat_queues[chat_id] = asyncio.Queue()
    await chat_queues[chat_id].put(update)
    if chat_queues[chat_id].qsize() > 1: return

    while not chat_queues[chat_id].empty():
        current_update = await chat_queues[chat_id].get()
        current_chat_id = current_update.effective_chat.id; current_user_query = current_update.message.text.strip()
        
        if not current_user_query: continue
        save_memory(current_chat_id, "user", current_user_query)
        
        async def keep_typing_action():
            try:
                while True:
                    await current_update.message.chat.send_action(action=ChatAction.TYPING)
                    await asyncio.sleep(4)
            except asyncio.CancelledError: pass

        typing_task = asyncio.create_task(keep_typing_action())
        
        await asyncio.sleep(0)

        response = ""
        try:
            tokens = extract_token_name_symbol(current_user_query)
            memory = load_memory(current_chat_id)
            
            news_md = ""
            if len(tokens) == 1:
                headlines = fetch_token_headlines(tokens[0], max_articles=6)
                news_md = "\n".join([f"- “{n['title']}” — {n['source']}" for n in headlines]) or "No relevant news found."
                response = await asyncio.to_thread(get_gemini_analysis, tokens, news_md, current_user_query, current_chat_id, memory)
            
            elif len(tokens) == 2:
                all_headlines = []
                # Fetch 1-3 articles for each token to create a combined news context
                all_headlines.extend(fetch_token_headlines(tokens[0], max_articles=3))
                all_headlines.extend(fetch_token_headlines(tokens[1], max_articles=3))
                news_md = "\n".join([f"- “{n['title']}” — {n['source']}" for n in all_headlines]) or "No relevant news found for these tokens."
                response = await asyncio.to_thread(get_gemini_analysis, tokens, news_md, current_user_query, current_chat_id, memory)
            
            else:
                # Fetch general market news to give the AI context for conversational chat
                general_headlines = fetch_token_headlines(token_name_or_symbol=None, max_articles=6)
                news_md = "\n".join([f"- “{n['title']}” — {n['source']}" for n in general_headlines]) or "No general news found."
                response = await asyncio.to_thread(get_gemini_analysis, [], news_md, current_user_query, current_chat_id, memory)
        
        except Exception as e:
            print(f"❌ An error occurred in ask_handler: {e}"); response = "😵 Sorry, a general error occurred."
        finally:
            typing_task.cancel()

        save_memory(current_chat_id, "assistant", response)
        await send_safe_reply(current_update, response)
        print(f"✅ Response successfully sent to chat_id: {current_chat_id}")

# #This part is for the web server to keep our block awake
# app = Flask('')

# @app.route('/')
# def home():
#     return "CoinCub is alive!"

# def run_web_server():
#   # Runs the Flask app on the host and port Render expects
#   app.run(host='0.0.0.0', port=8080)

# def keep_alive():
#     # Starts the web server in a separate thread
#     t = Thread(name='keep_alive_thread', target=run_web_server)
#     t.daemon = True # Allows the main bot to exit even if this thread is running
#     t.start()

def run_bot():
    
    # keep_alive() 

    print("✅ Bot is now listening..."); app = ApplicationBuilder().token(COINCUB_BOT_TOKEN).build(); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_handler)); app.run_polling()
if __name__ == "__main__": asyncio.run(run_bot())