import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

#Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VALIDATOR_CONSENSUS_ADDRESS = os.getenv("VALIDATOR_CONSENSUS_ADDRESS")
VALIDATOR_OPERATOR_ADDRESS = os.getenv("VALIDATOR_OPERATOR_ADDRESS")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
UNION_RPC = "http://161.35.98.109:26657"
UNION_REST_API = "http://161.35.98.109:1317"
SLASHING_WINDOW = 100
SLASHING_THRESHOLD = 0.20  # 20% threshold for slashing alert
