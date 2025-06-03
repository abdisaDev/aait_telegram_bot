# Grok-like Telegram Chatbot

A sophisticated AI chatbot for Telegram that can engage in natural conversations, respond to direct messages, and react when mentioned in group chats.

## Setup Instructions

1. Create a new bot using BotFather on Telegram and get your bot token.
2. Sign up for OpenAI API access and get your API key.
3. Create a `.env` file in the project root with the following content:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

## Features

- Natural language processing using OpenAI's GPT-4
- Direct message handling with conversation context
- Group chat mention detection and response
- Error handling and logging
- Configurable through environment variables

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: (Optional) Specify which OpenAI model to use (default: gpt-4o)
- `LOG_FILE`: (Optional) Specify a log file path (default: bot.log)
