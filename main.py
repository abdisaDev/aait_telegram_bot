import os
import logging
import requests
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from typing import Dict, List, Tuple

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if OPENROUTER_API_KEY:
    OPENROUTER_API_KEY = OPENROUTER_API_KEY.strip()
    token_length = len(OPENROUTER_API_KEY)
    token_prefix = OPENROUTER_API_KEY[:4] if token_length > 3 else ""
    token_suffix = OPENROUTER_API_KEY[-4:] if token_length > 3 else ""
    logger.info(f"OpenRouter API Key loaded. Length: {token_length}. Prefix: '{token_prefix}', Suffix: '{token_suffix}'.")
else:
    logger.error("OpenRouter API Key is NOT SET or is empty in the .env file!")

OPENROUTER_MODEL = "openai/gpt-3.5-turbo"

conversation_history: Dict[int, List[Dict[str, str]]] = {}

SYSTEM_PROMPT = (
    "You are Daddy, a witty, informative, and slightly sarcastic AI assistant. "
    "You are highly intelligent and have a vast knowledge base. "
    "You answer questions directly and concisely, but with a touch of humor and a hint of rebellious spirit. "
    "You are not afraid to challenge assumptions or offer unconventional perspectives. "
    "Keep your responses relatively short and engaging."
)

CUSTOM_MENTIONS = ["@homie", "@daddy", "@bro", "@abdisaDev", "@abdisadev", "@abdisa"]

def test_openrouter_connection():
    if not OPENROUTER_API_KEY:
        logger.error("Cannot test OpenRouter API: No API key provided")
        return False
        
    test_url = "https://openrouter.ai/api/v1/models"
    test_headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/yourusername/daddy-telegram-bot",
        "X-Title": "Daddy Telegram Bot"
    }
    
    try:
        logger.info(f"Testing OpenRouter API connectivity to {test_url}")
        response = requests.get(test_url, headers=test_headers, timeout=10)
        logger.info(f"OpenRouter API test response status: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            logger.info(f"✅ OpenRouter API connection test successful! Found {len(models)} available models.")
            return True
        else:
            logger.error(f"❌ OpenRouter API connection test failed with status code: {response.status_code}")
            if response.status_code == 401:
                logger.error("This suggests an authentication problem with your API key.")
            return False
    except Exception as e:
        logger.error(f"❌ OpenRouter API connection test failed with exception: {e}")
        return False

async def generate_openrouter_response(prompt: str, chat_id: int, is_group_mention: bool = False) -> Tuple[str, bool]:
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY":
        logger.error("OpenRouter API key not found or is placeholder. Please set OPENROUTER_API_KEY in your .env file.")
        return "I'm having trouble connecting to my brain. Please check the API key configuration.", False
    
    if not prompt or prompt.strip() == "":
        return "You didn't ask me anything. What's on your mind?", True
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    
    history = conversation_history[chat_id]
    
    if is_group_mention:
        history.append({"role": "user", "content": prompt})
    else:
        history.append({"role": "user", "content": prompt})
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/daddy-telegram-bot",
        "X-Title": "Daddy Telegram Bot"
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": messages
    }
    
    try:
        logger.info(f"Sending request to OpenRouter API for chat {chat_id}")
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                response_text = response_data["choices"][0]["message"]["content"]
                
                history.append({"role": "assistant", "content": response_text})
                
                if len(history) > 20:
                    history = history[-20:]
                conversation_history[chat_id] = history
                
                return response_text, True
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to parse OpenRouter API response: {e}")
                logger.debug(f"Response data: {response.text[:500]}")
                return "I received a response from my brain, but it was in a format I couldn't understand.", False
        else:
            error_msg = f"OpenRouter API returned status code {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error']['message']}"
            except:
                error_msg += f": {response.text[:100]}"
            
            logger.error(error_msg)
            
            if response.status_code == 401:
                return "I'm having trouble authenticating with my brain. Please check the API key configuration.", False
            elif response.status_code == 429:
                return "I'm thinking too much right now (rate limit exceeded). Please try again in a moment.", False
            elif response.status_code >= 500:
                return "My brain is experiencing some technical difficulties. Please try again later.", False
            else:
                return f"I encountered an error while thinking: {error_msg}", False
    
    except requests.exceptions.Timeout:
        logger.error("OpenRouter API request timed out")
        return "I'm taking too long to think. The connection to my brain timed out. Please try again.", False
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API request failed: {e}")
        return "I'm having trouble connecting to my brain. Please check your internet connection and try again.", False
    except Exception as e:
        logger.error(f"Unexpected error generating response: {e}", exc_info=True)
        return "I encountered an unexpected error while processing your request. Please try again.", False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm Daddy, your AI assistant. Ask me anything, and I'll do my best to help you!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here's how to use me:\n\n"
        "• Simply send me a message, and I'll respond\n"
        "• Use /clear to reset our conversation history\n"
        "• In groups, mention me by my username or use @daddy to get my attention\n\n"
        "I'm powered by AI and can discuss a wide range of topics. Let's chat!"
    )
    await update.message.reply_text(help_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in conversation_history:
        conversation_history[chat_id] = []
    await update.message.reply_text("Our conversation history has been cleared. Let's start fresh!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        message_text = update.message.text
        user_name = update.message.from_user.first_name
        
        is_private_chat = update.effective_chat.type == "private"
        is_group_chat = update.effective_chat.type in ["group", "supergroup"]
        
        logger.info(f"Received message from {user_name} in chat {chat_id}: '{message_text[:50]}...' (Private: {is_private_chat}, Group: {is_group_chat})")
        
        bot_username = context.bot.username
        
        if is_group_chat:
            is_mentioned = False
            mention_text = f"@{bot_username}"
            
            if mention_text.lower() in message_text.lower():
                is_mentioned = True
                message_text = message_text.replace(mention_text, "", 1).strip()
            else:
                for custom_mention in CUSTOM_MENTIONS:
                    if custom_mention.lower() in message_text.lower():
                        is_mentioned = True
                        message_text = message_text.replace(custom_mention, "", 1).strip()
                        break
            
            if not is_mentioned:
                logger.info(f"Message in group chat {chat_id} did not mention the bot - ignoring")
                return
            
            logger.info(f"Bot was mentioned in group chat {chat_id}, responding to: '{message_text[:50]}...'")
            
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception as e:
                logger.warning(f"Could not send typing action: {e}")
            
            response_text, success = await generate_openrouter_response(message_text, chat_id, is_group_mention=True)
        else:
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception as e:
                logger.warning(f"Could not send typing action: {e}")
            
            response_text, success = await generate_openrouter_response(message_text, chat_id)
        
        if success and response_text:
            try:
                await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
                logger.info(f"Sent response to chat {chat_id}: '{response_text[:100]}...'")
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id}: {e}")
        elif response_text:
            try:
                await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
                logger.info(f"Sent error/fallback response to chat {chat_id}: '{response_text[:100]}...'")
            except Exception as e:
                logger.error(f"Failed to send fallback message to chat {chat_id}: {e}")
        else:
            logger.error(f"No response text (even fallback) from generate_openrouter_response for chat {chat_id}")
            try:
                await update.message.reply_text("I seem to be speechless at the moment. Try again?", reply_to_message_id=update.message.message_id)
            except Exception as e:
                logger.error(f"Failed to send default fallback message to chat {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        try:
            await update.message.reply_text("Sorry, I encountered a network error. Please try again in a moment.", reply_to_message_id=update.message.message_id)
        except Exception as reply_error:
            logger.error(f"Could not send error message: {reply_error}")

def main():
    logger.info("Starting Daddy Telegram Bot (OpenRouter Edition)...")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("Telegram Bot Token not found. Please set TELEGRAM_BOT_TOKEN in your .env file.")
        return
        
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY":
        logger.critical("OpenRouter API Key not found or is placeholder. Please set a valid OPENROUTER_API_KEY in your .env file.")
        return
    
    test_openrouter_connection()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    async def setup_commands(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Start a conversation with me"),
            BotCommand("help", "Show help information"),
            BotCommand("clear", "Clear conversation history")
        ])
        logger.info("Bot commands have been set.")
    
    application.post_init = setup_commands
    
    logger.info("Bot is polling for updates...")
    
    application.run_polling(drop_pending_updates=True)
    
    logger.info("Bot has stopped.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Keyboard Interrupt)")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}", exc_info=True)
