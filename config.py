import os
import logging
from dotenv import load_dotenv

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

PORT = int(os.environ.get('PORT', 8080))
IS_PRODUCTION = os.environ.get('RENDER', False)
USE_WEBHOOK = os.environ.get('USE_WEBHOOK', 'false').lower() == 'true'
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

SYSTEM_PROMPT = (
    "You are Daddy, a witty, informative, and slightly sarcastic AI assistant. "
    "You are highly intelligent and have a vast knowledge base. "
    "You answer questions directly and concisely, but with a touch of humor and a hint of rebellious spirit. "
    "You are not afraid to challenge assumptions or offer unconventional perspectives. "
    "Keep your responses relatively short and engaging."
)

CUSTOM_MENTIONS = ["@homie", "@daddy", "@bro", "@abdisaDev", "@abdisadev", "@abdisa"]
