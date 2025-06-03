import requests
import logging
from typing import Tuple, List, Dict
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, SYSTEM_PROMPT, logger

conversation_history: Dict[int, List[Dict[str, str]]] = {}

def test_openrouter_connection() -> bool:
    """Test the connection to OpenRouter API"""
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
    """Generate a response using the OpenRouter API"""
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
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        logger.info(f"Sending request to OpenRouter API for chat {chat_id}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        logger.info(f"OpenRouter API response status: {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                assistant_message = response_json["choices"][0]["message"]["content"]

                history.append({"role": "assistant", "content": assistant_message})

                if len(history) > 10:
                    history = history[-10:]
                conversation_history[chat_id] = history
                
                return assistant_message, True
            else:
                logger.error(f"Unexpected response format from OpenRouter API: {response_json}")
                return "I received an unexpected response format. Please try again later.", False
        else:
            error_message = f"OpenRouter API error: {response.status_code}"
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_message += f" - {error_json['error']['message']}"
            except:
                pass
            
            logger.error(error_message)
            return "I encountered an error while processing your request. Please try again later.", False
    except Exception as e:
        logger.error(f"Exception while calling OpenRouter API: {e}")
        return "I encountered a network error. Please check your connection and try again.", False

def clear_chat_history(chat_id: int) -> bool:
    """Clear the conversation history for a specific chat"""
    if chat_id in conversation_history:
        conversation_history[chat_id] = []
        return True
    return False
