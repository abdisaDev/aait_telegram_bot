import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import CUSTOM_MENTIONS, logger
from openrouter_client import generate_openrouter_response, clear_chat_history
import time

# This global variable is initialized by main.py and updated here.
last_activity_time = time.time() # Initialize to current time as a fallback

async def _update_activity_time():
    """Helper function to update the last activity time and log it."""
    global last_activity_time
    last_activity_time = time.time()
    logger.debug(f"User activity in bot_handlers: last_activity_time updated to {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_activity_time))}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command"""
    await _update_activity_time()
    await update.message.reply_text("Hello! I'm Daddy, your witty AI assistant. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command"""
    await _update_activity_time()
    help_text = (
        "I'm Daddy, your AI assistant. Here's how you can interact with me:\n\n"
        "• Just send me a message and I'll respond\n"
        "• Use /clear to reset our conversation\n"
        "• In group chats, mention me with @daddy or other custom mentions\n\n"
        "I'm powered by OpenRouter AI and I'm here to help with information, ideas, or just chat!"
    )
    await update.message.reply_text(help_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /clear command to reset conversation history"""
    await _update_activity_time()
    chat_id = update.effective_chat.id
    if clear_chat_history(chat_id):
        await update.message.reply_text("Our conversation history has been cleared. What would you like to talk about now?")
    else:
        await update.message.reply_text("There was no conversation history to clear. Let's start fresh!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for regular messages"""
    await _update_activity_time()
    try:
        
        if not update.message or (not update.message.text and not update.message.photo and not update.message.document):
            logger.debug("Received an update without text, photo, or document content. Ignoring.")
            return

        chat_id = update.effective_chat.id
        message_text = update.message.text.strip() if update.message.text else "" # Handle None text
        user_name = update.effective_user.first_name

        is_group = update.effective_chat.type in ["group", "supergroup"]
        
        if is_group:

            is_mentioned = False

            if context.bot.username and f"@{context.bot.username.lower()}" in message_text.lower():
                is_mentioned = True

                message_text = message_text.replace(f"@{context.bot.username}", "").strip()
            
            for mention in CUSTOM_MENTIONS:
                if mention.lower() in message_text.lower():
                    is_mentioned = True
                    message_text = message_text.replace(mention, "").strip()
            

            if not is_mentioned:
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
