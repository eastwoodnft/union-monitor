import requests
import logging
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def send_telegram_alert(message):
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(TELEGRAM_API_URL, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to send Telegram alert: {e}")
