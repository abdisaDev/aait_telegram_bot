import asyncio
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import telegram.error

from config import TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, IS_PRODUCTION, USE_WEBHOOK, WEBHOOK_URL, PORT, logger
from openrouter_client import test_openrouter_connection
from bot_handlers import start_command, help_command, clear_command, handle_message
from web_server import create_server, start_server

async def setup_commands(app):
    """Set up the bot commands menu"""
    await app.bot.set_my_commands([
        BotCommand("start", "Start a conversation with me"),
        BotCommand("help", "Show help information"),
        BotCommand("clear", "Clear conversation history")
    ])
    logger.info("Bot commands have been set.")

async def error_handler(update, context):
    """Handle errors in the telegram-python-bot library"""
    if isinstance(context.error, telegram.error.Conflict):
        logger.warning("Conflict error: Another instance of the bot is running. Shutting down this instance.")

        return
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)

def main():
    """Main function to start the bot"""
    logger.info("Starting Daddy Telegram Bot (OpenRouter Edition)...")

    if not TELEGRAM_BOT_TOKEN:
        logger.critical("Telegram Bot Token not found. Please set TELEGRAM_BOT_TOKEN in your .env file.")
        return
        
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY":
        logger.critical("OpenRouter API Key not found or is placeholder. Please set a valid OPENROUTER_API_KEY in your .env file.")
        return

    test_openrouter_connection()

    app = create_server()
    start_server(app)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    application.post_init = setup_commands

    if USE_WEBHOOK and IS_PRODUCTION:
        logger.info(f"Starting bot in webhook mode on port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
        )
    else:
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
