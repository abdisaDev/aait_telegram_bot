import asyncio
import time
import sys
import os
import signal
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import telegram.error
import nest_asyncio

from config import TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, IS_PRODUCTION, USE_WEBHOOK, WEBHOOK_URL, PORT, logger
from openrouter_client import test_openrouter_connection
from bot_handlers import start_command, help_command, clear_command, handle_message
import bot_handlers
from web_server import create_server, start_server

nest_asyncio.apply()

bot_running = False
last_activity_time = time.time()
KEEPALIVE_INTERVAL = 30 
MAX_IDLE_TIME = 15 * 60  
PING_FAILURE_COUNT = 0 
MAX_PING_FAILURES = 3 

bot_handlers.last_activity_time = last_activity_time

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
    global bot_running, last_activity_time
    
    last_activity_time = time.time()
    
    if isinstance(context.error, telegram.error.Conflict):
        logger.warning("Conflict error: Another instance of the bot is running. Shutting down this instance.")
        bot_running = False
        return
    
    if isinstance(context.error, telegram.error.NetworkError):
        logger.error(f"Network error: {context.error}. Will continue running.")
        try:
            if hasattr(context.application, 'updater') and context.application.updater:
                logger.info("Attempting to restart polling after network error...")
                await context.application.updater.stop_polling()
                await asyncio.sleep(1)
                await context.application.updater.start_polling()
                logger.info("Successfully restarted polling")
        except Exception as e:
            logger.error(f"Failed to restart polling: {e}")
        return
        
    if isinstance(context.error, telegram.error.TimedOut):
        logger.error(f"Request timed out: {context.error}. Will continue running.")
        return
    
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)

async def keepalive_ping(application):
    """Send periodic pings to keep the connection alive"""
    global last_activity_time, bot_running, PING_FAILURE_COUNT
    
    while bot_running:
        try:
            current_time = time.time()
            time_since_activity = current_time - last_activity_time
            
            # If too much time has passed without activity, restart the bot
            if time_since_activity > MAX_IDLE_TIME:
                logger.warning(f"No activity for {time_since_activity:.1f} seconds. Restarting bot...")
                restart_bot()
                return
                
            # Otherwise, just log that we're still alive
            if time_since_activity > KEEPALIVE_INTERVAL:
                logger.info(f"Keepalive: Bot running for {time_since_activity:.1f} seconds since last activity")
                
                # Try to send a getMe request to keep the connection alive
                try:
                    await application.bot.get_me()
                    logger.info("Keepalive ping successful")
                    PING_FAILURE_COUNT = 0  # Reset failure count on success
                    
                    # Only reset the timer if we haven't had user activity in a while
                    if time_since_activity > KEEPALIVE_INTERVAL * 2:
                        last_activity_time = current_time  # Reset the timer after successful ping
                except Exception as e:
                    logger.error(f"Keepalive ping failed: {e}")
                    PING_FAILURE_COUNT += 1
                    
                    # If we've had multiple consecutive ping failures, restart the bot
                    if PING_FAILURE_COUNT >= MAX_PING_FAILURES:
                        logger.warning(f"Experienced {PING_FAILURE_COUNT} consecutive ping failures. Restarting bot...")
                        restart_bot()
                        return
            
            # Sleep for a bit before the next check
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in keepalive loop: {e}")
            await asyncio.sleep(KEEPALIVE_INTERVAL)

def restart_bot():
    """Restart the entire bot process"""
    logger.info("Restarting bot...")
    
    try:
        # Close any resources if needed
        
        # Restart the process
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        # If restart fails, exit and let the process manager restart it
        sys.exit(1)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        global bot_running
        logger.info(f"Received signal {sig}, shutting down...")
        bot_running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main_async():
    """Async main function to start the bot"""
    global bot_running, last_activity_time
    
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
    
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    application.add_error_handler(error_handler)
    application.post_init = setup_commands
    
    bot_running = True
    last_activity_time = time.time()
    
    asyncio.create_task(keepalive_ping(application))
    
    try:
        if USE_WEBHOOK and IS_PRODUCTION:
            logger.info(f"Starting bot in webhook mode on port {PORT}")
            await application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=TELEGRAM_BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}",
                drop_pending_updates=True
            )
        else:
            logger.info("Bot is polling for updates...")
            await application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        bot_running = False
        raise
    finally:
        bot_running = False
        logger.info("Bot has stopped.")

def main():
    """Main function to start the bot"""
    setup_signal_handlers()
    
    # Run the async main function
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Keyboard Interrupt)")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}", exc_info=True)
        # Wait a bit before restarting to avoid rapid restart loops
        time.sleep(5)
        restart_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Keyboard Interrupt)")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}", exc_info=True)
        # Wait a bit before exiting to allow logs to be written
        time.sleep(1)
        sys.exit(1)
