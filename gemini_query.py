# gemini_query.py
import os
import subprocess
import json
from datetime import datetime

LOG_PATH = "query_log.json"

def get_gemini_analysis(tokens: list, news_md: str, user_query: str, chat_id: str, memory: list) -> str:
    """
    Constructs a dynamic prompt for the Gemini CLI, now with a "Safety Net" instruction.
    """
    try:
        with open("./prompt/GEMINI.md", "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        return "❌ Critical Error: The 'prompt/GEMINI.md' file was not found."

    memory_str = "\n".join([f"User: {m['text']}" if m['role'] == 'user' else f"You: {m['text']}" for m in memory])

    task_specific_prompt = ""
    if len(tokens) == 1:
        token = tokens[0]
        task_specific_prompt = f"""
---
## Current Task
- **Analyze this token:** {token}
- **Recent News:**
{news_md}
- **User History:** {memory_str}
- **User's Query:** "{user_query}"

**Your Instructions:** FPerform a full analysis of **{token}**, synthesizing MCP data with the **Relevant News** provided. Follow your core rules in `GEMINI.md`.
"""
    elif len(tokens) == 2:
        token1, token2 = tokens
        task_specific_prompt = f"""
---
## Current Task: Compare Two Tokens
- **Tokens to Compare:** {token1} vs {token2}
- **Relevant News Context:**
{news_md}
- **User's Query:** "{user_query}"
- **User History:** {memory_str}

**YOUR IMMEDIATE INSTRUCTIONS:**
1.  **Use your MCP tools** to get the key metrics (Price, Market Cap, Volume, 7D Volatility, and Liquidity) for **both {token1} and {token2}**.
2.  **You MUST generate a Markdown comparison table** using this data, exactly as defined in your core rules.
3.  After the table, **you MUST provide a one-line summary** that compares their stability and risk, use the **Relevant News Context** to inform your final summary statement about risk and stability.

"""
    else:
        task_specific_prompt = f"""
---
## Current Task
- **This is a general conversational query.** Do not assume it's about a specific token unless mentioned.
- **General Market News Pulse:**
{news_md}
- **User History:**
{memory_str}
- **User's Query:** "{user_query}"

**Your Instructions:** Follow your core rules for General Conversation. Analyze the user history for context. **Do NOT call any MCP tools unless the user explicitly asks for new data.** Provide a helpful, conversational response.
"""

    safety_net_prompt = """
---
## ABSOLUTE SAFETY RULE
You have many tools. Sometimes you might choose one that requires an 'interval'.
**IF AND ONLY IF you call a tool that needs an `interval` parameter, you MUST use `"interval": "1d"`.**
This is your only fallback. Your primary goal is to use the tools as described in your main instructions (e.g., for snapshots or comparisons). This rule is to prevent an error if you deviate.
"""

    final_prompt = base_prompt + "\n" + task_specific_prompt.strip() + "\n" + safety_net_prompt.strip()

    # Define the models to try, in order of preference.
    models_to_try = ["gemini-2.5-pro", "gemini-2.5-flash","gemini-1.5-flash"]
    final_output = None

    fallback_occurred = False

    print(f"📡 Sending task to Gemini CLI for tokens: {', '.join(tokens) or 'General Query'}")

    for model in models_to_try:
        try:
            print(f"Attempting to use model: {model}...")
            result = subprocess.run(
                ["gemini", "--model", model, "--prompt", final_prompt],
                capture_output=True, text=True, timeout=300, check=True
            )
            
            raw_output = result.stdout.strip()
            lines = raw_output.splitlines()
            filtered_lines = [line for line in lines if not line.strip().startswith("[INFO]")]
            output = "\n".join(filtered_lines).strip()

            if output:
                print(f"✅ Successfully received response from model: {model}")
                final_output = output
                break 
            else:
                print(f"⚠️ Model '{model}' ran successfully but returned an empty response. Trying next model...")
                # Set the flag if a model fails
                fallback_occurred = True
                continue

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            print(f"⚠️ Model '{model}' failed. Error: {e}. Trying next model...")
            fallback_occurred = True
            continue
        except Exception as e:
            print(f"An unexpected error occurred with model '{model}'. Error: {e}. Trying next model...")
            fallback_occurred = True
            continue

    if final_output:
        # If a fallback happened, prepend a friendly notification message.
        if fallback_occurred:
            notification_message = "ℹ️ My primary AI model is currently busy. I've switched to a faster alternative to get you a response. The analysis continues below."
            final_response_to_user = f"{notification_message}\n\n---\n\n{final_output}"
        else:
            final_response_to_user = final_output
            
        if chat_id: _log_query(chat_id, {"timestamp": datetime.utcnow().isoformat(), "query": user_query, "response": final_response_to_user[:4000]})
        return final_response_to_user
    else:
        return "❌ A critical error occurred. All available AI models failed to respond. Please try again later."

def _log_query(chat_id, entry):
    try:
        logs = json.load(open(LOG_PATH)) if os.path.exists(LOG_PATH) else {}
        logs.setdefault(str(chat_id), []).append(entry)
        with open(LOG_PATH, "w") as f: json.dump(logs, f, indent=2)
    except Exception as e: print(f"⚠️ Logging failed:", e)