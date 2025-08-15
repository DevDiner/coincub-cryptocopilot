# CoinCub - Your Intelligent Crypto Copilot

CoinCub is a sophisticated Telegram bot that acts as a crypto research assistant. Powered by Google's Gemini and live data from the CoinGecko MCP, it provides real-time token analysis, comparisons, and conversational insights directly in your chat.

*This project was developed for the CoinGecko MCP Hackathon 2025.*

![CoinCub Demo](https://raw.githubusercontent.com/DevDiner/coincub-cryptocopilot/main/media/demoVideo.gif)

## Features

- **Single Token Analysis:** Get a full overview of any cryptocurrency, including price, market cap, volume, volatility, and liquidity.
- **Dual Token Comparison:** Compare two tokens side-by-side with a clean, formatted Markdown table.
- **News Integration:** Fetches the latest headlines from top crypto news sources (CoinDesk, CoinTelegraph, Decrypt) to provide context for market movements.
- **Conversational AI:** Ask general questions or follow-ups. The bot uses chat history to understand context.
- **Risk Assessment:** Automatically flags risk indicators like low liquidity, low volume, and high volatility.
- **Intent-Driven:** Understands various user intents, from simple price checks ("how's btc?") to complex risk analysis.

## Tech Stack

- **Backend:** Python 3.10+
- **Telegram Framework:** `python-telegram-bot` (v20+)
- **AI & Language Model:** Google Gemini via the official CLI
- **Core Data Source:** CoinGecko's Model Context Protocol (MCP)
- **News Feeds:** RSS from CoinDesk, CoinTelegraph, Decrypt
- **Concurrency:** `asyncio`

## Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

- Python 3.10 or higher
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- An environment with the Gemini CLI configured and authenticated.
- RSS Feed URLs (optional but recommended)

### Installation & Running

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/DevDiner/coincub-cryptocopilot.git
    cd cryptocopilot
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    -   Copy the example `.env.example` file to a new `.env` file:
        ```sh
        cp .env.example .env
        ```
    -   Open the `.env` file and fill in your actual API keys and tokens.

5.  **Run the bot:**
    ```sh
    python telegram_bot.py
    ```
    The bot will start listening for messages.

## Environment Variables

To run this project, you will need to add the following environment variables to your `.env` file:

- `COINCUB_BOT_TOKEN=` (Telegram bot token)
- `RSS_COINDESK=` (Full URL for CoinDesk RSS feed)
- `RSS_COINTELEGRAPH=` (Full URL for CoinTelegraph RSS feed)
- `RSS_DECRYPT=` (Full URL for Decrypt RSS feed)

## Prompt Engineering

A key component of CoinCub is the detailed system prompt located in `prompt/GEMINI.md`. This file acts as the bot's "constitution," defining its personality, tools, and response formats for various user intents. This allows for rapid iteration on the bot's behavior without changing the core Python code.

## Hackathon Submission

This project is a submission for the **CoinGecko MCP Hackathon**. It demonstrates the power of combining a large language model with real-time, high-quality financial data from the CoinGecko MCP to create a useful tool for crypto enthusiasts.

---
