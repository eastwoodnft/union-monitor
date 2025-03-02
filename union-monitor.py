import requests
import time
import logging
import os
import asyncio
from collections import deque
from telegram import Bot
from telegram.ext import Application, CommandHandler
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VALIDATOR_CONSENSUS_ADDRESS = os.getenv("VALIDATOR_CONSENSUS_ADDRESS")
VALIDATOR_OPERATOR_ADDRESS = os.getenv("VALIDATOR_OPERATOR_ADDRESS")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
UNION_RPC = "http://161.35.98.109:26657"
UNION_REST_API = "http://161.35.98.109:1317"
SLASHING_WINDOW = 100
SLASHING_THRESHOLD = 0.20  # 20% threshold for slashing alert

# Initialize bot and application
bot = Bot(token=TELEGRAM_BOT_TOKEN)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Historical data for graphing
history = {
    "voting_power": deque(maxlen=30*24*7),  # ~1 week at 1-minute intervals
    "missed_blocks": deque(maxlen=30*24*7),
    "timestamps": deque(maxlen=30*24*7)
}

class MonitorState:
    def __init__(self):
        self.last_height = 0
        self.missed_since_last_alert = 0
        self.total_missed = 0
        self.total_blocks = 0
        self.avg_block_time = 0
        self.active = False
        self.catching_up = False
        self.voting_power = None
        self.total_voting_power = None
        self.rank = None
        self.jailed = False
        self.delegator_count = None
        self.uptime = None

state = MonitorState()

async def get_validator_status():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    try:
        response = session.get(f"{UNION_RPC}/status?", timeout=10)
        response.raise_for_status()
        status = response.json()["result"]
        logging.info(f"RPC /status response: {status}")

        catching_up = status["sync_info"]["catching_up"]
        latest_height = int(status["sync_info"]["latest_block_height"])
        logging.info(f"Parsed RPC status: height={latest_height}, catching_up={catching_up}")

        response = session.get(f"{UNION_RPC}/validators?height={latest_height}&page=1&per_page=100", timeout=10)
        response.raise_for_status()
        validators_data = response.json()["result"]
        logging.info(f"RPC /validators response: {validators_data}")
        validators = validators_data["validators"]
        total_voting_power = sum(int(v["voting_power"]) for v in validators)
        my_validator = next((v for v in validators if v["address"] == VALIDATOR_CONSENSUS_ADDRESS), None)

        if not my_validator:
            logging.warning(f"Validator {VALIDATOR_CONSENSUS_ADDRESS} not found in active set at height {latest_height}")
            return True, catching_up, None, total_voting_power, None, False, None, None

        voting_power = int(my_validator["voting_power"])
        rank = sorted(validators, key=lambda x: int(x["voting_power"]), reverse=True).index(my_validator) + 1
        jailed = my_validator.get("jailed", False)
        logging.info(f"Validator found: voting_power={voting_power}, rank={rank}, jailed={jailed}")

        response = session.get(f"{UNION_REST_API}/cosmos/staking/v1beta1/validators/{VALIDATOR_OPERATOR_ADDRESS}", timeout=10)
        if response.status_code == 200:
            val_data = response.json()["validator"]
            delegator_count = int(val_data.get("delegator_shares", "0").split('.')[0]) // 10**18
            logging.info(f"REST API: delegator_count={delegator_count}")
        else:
            logging.warning(f"REST API returned {response.status_code}: {response.text}")
            delegator_count = None

        return True, catching_up, voting_power, total_voting_power, rank, jailed, delegator_count, None
    except Exception as e:
        logging.error(f"Error fetching validator status: {e}")
        return False, None, None, None, None, None, None, None

async def get_latest_height():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    try:
        response = session.get(f"{UNION_RPC}/block", timeout=10)
        response.raise_for_status()
        height = int(response.json()["result"]["block"]["header"]["height"])
        logging.info(f"Latest height: {height}")
        return height
    except Exception as e:
        logging.error(f"Error fetching latest height: {e}")
        return 0

async def get_missed_blocks(last_height, missed_blocks_timestamps):
    missed = 0
    current_height = last_height
    block_times = []
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    try:
        response = session.get(f"{UNION_RPC}/block", timeout=10)
        response.raise_for_status()
        block_data = response.json()["result"]["block"]
        latest_height = int(block_data["header"]["height"])
        latest_block_time = block_data["header"]["time"]
        latest_time = time.mktime(time.strptime(latest_block_time[:19], "%Y-%m-%dT%H:%M:%S"))

        logging.info(f"Checking blocks from {last_height + 1} to {latest_height}")

        # Reset missed blocks if the window has moved beyond SLASHING_WINDOW
        if latest_height - last_height > SLASHING_WINDOW:
            missed_blocks_timestamps.clear()
            logging.info(f"Reset missed blocks: window moved beyond {SLASHING_WINDOW} blocks")
        else:
            # Trim old blocks outside the slashing window
            while missed_blocks_timestamps and (latest_height - missed_blocks_timestamps[0]["height"]) >= SLASHING_WINDOW:
                missed_blocks_timestamps.popleft()

        total_blocks = min(latest_height - last_height, SLASHING_WINDOW)
        for height in range(last_height + 1, latest_height + 1):
            try:
                response = session.get(f"{UNION_RPC}/block?height={height}", timeout=10)
                response.raise_for_status()
                block_data = response.json()["result"]["block"]
                block_time = time.mktime(time.strptime(block_data["header"]["time"][:19], "%Y-%m-%dT%H:%M:%S"))
                block_times.append(block_time)

                signatures = block_data["last_commit"]["signatures"]
                signed = any(sig["validator_address"] == VALIDATOR_CONSENSUS_ADDRESS for sig in signatures)
                if not signed:
                    missed += 1
                    missed_blocks_timestamps.append({"height": height, "timestamp": block_time})
                current_height = height
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 500:
                    logging.warning(f"Skipping height {height} due to 500 Internal Server Error")
                    current_height = height
                    continue
                raise
        avg_block_time = (block_times[-1] - block_times[0]) / (len(block_times) - 1) if len(block_times) > 1 else 0
        total_missed = len(missed_blocks_timestamps)  # Total missed within the current window
        logging.info(f"Missed blocks check: missed={missed}, total_missed={total_missed}, avg_block_time={avg_block_time}")
        return missed, current_height, total_missed, avg_block_time
    except Exception as e:
        logging.error(f"Error checking missed blocks: {e}")
        return -1, current_height, len(missed_blocks_timestamps), 0

async def send_telegram_alert(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

# Command handlers
async def status_command(update, context):
    missed_percentage = (state.total_missed / SLASHING_WINDOW * 100) if state.total_missed > 0 else 0
    msg = (
        f"*Validator Status*\n"
        f"Active: {'Yes' if state.active else 'No'}\n"
        f"Syncing: {'Yes' if not state.catching_up else 'No'}\n"
        f"Voting Power: {state.voting_power // 10**6 if state.voting_power is not None else 'N/A'} UNION "
        f"(Rank: {state.rank if state.rank is not None else 'N/A'})\n"
        f"Jailed: {'Yes' if state.jailed else 'No'}\n"
        f"Delegators: {state.delegator_count if state.delegator_count is not None else 'N/A'} UNION\n"
        f"Missed Blocks (Slashing Window): {state.total_missed}/{SLASHING_WINDOW} ({missed_percentage:.1f}%)"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def missed_command(update, context):
    missed_percentage = (state.total_missed / SLASHING_WINDOW * 100) if state.total_missed > 0 else 0
    msg = (
        f"*Missed Blocks*\n"
        f"Since Last Alert: {state.missed_since_last_alert}\n"
        f"Slashing Window ({SLASHING_WINDOW} blocks): {state.total_missed} ({missed_percentage:.1f}%)"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def network_command(update, context):
    msg = (
        f"*Network Stats*\n"
        f"Avg Block Time: {state.avg_block_time:.2f}s"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def validator_command(update, context):
    msg = (
        f"*Validator Details*\n"
        f"Voting Power: {state.voting_power // 10**6 if state.voting_power is not None else 'N/A'} UNION "
        f"(Rank: {state.rank if state.rank is not None else 'N/A'})\n"
        f"Jailed: {'Yes' if state.jailed else 'No'}\n"
        f"Delegators: {state.delegator_count if state.delegator_count is not None else 'N/A'} UNION"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def monitor():
    last_height = await get_latest_height()
    if last_height == 0:
        await send_telegram_alert("⚠️ Failed to fetch initial block height. Starting from 0.")
    state.last_height = last_height
    missed_blocks_timestamps = deque(maxlen=SLASHING_WINDOW)
    failures = 0
    max_failures = 5

    # Set Telegram command menu
    commands = [
        {"command": "status", "description": "Get validator status"},
        {"command": "missed", "description": "Check missed blocks"},
        {"command": "network", "description": "View network stats"},
        {"command": "validator", "description": "Validator details"}
    ]
    await application.bot.set_my_commands([(cmd["command"], cmd["description"]) for cmd in commands])

    # Add command handlers to the application
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("missed", missed_command))
    application.add_handler(CommandHandler("network", network_command))
    application.add_handler(CommandHandler("validator", validator_command))

    # Start polling in the background
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        active, catching_up, voting_power, total_voting_power, rank, jailed, delegator_count, _ = await get_validator_status()
        missed, current_height, total_missed, avg_block_time = await get_missed_blocks(state.last_height, missed_blocks_timestamps)

        state.active = active
        state.catching_up = catching_up
        state.voting_power = voting_power
        state.total_voting_power = total_voting_power
        state.rank = rank
        state.jailed = jailed
        state.delegator_count = delegator_count
        state.total_missed = total_missed
        state.avg_block_time = avg_block_time
        state.uptime = 100 * (1 - (total_missed / SLASHING_WINDOW)) if total_missed > 0 else 100

        logging.info(
            f"State updated: active={state.active}, voting_power={state.voting_power}, "
            f"total_missed={state.total_missed}, avg_block_time={state.avg_block_time}, uptime={state.uptime}"
        )

        if active is False and missed == -1:
            failures += 1
            if failures >= max_failures:
                await send_telegram_alert("🚨 *Critical Error*: RPC endpoint unreachable. Shutting down.")
                break
        else:
            failures = 0

        if not active and state.voting_power is None:
            await send_telegram_alert("*Validator is not in the active set!*")
        if catching_up:
            await send_telegram_alert("*Node is not synced!*")
        if jailed:
            await send_telegram_alert("*Validator is jailed!* Immediate action required!")
        if voting_power is not None and voting_power < 1000:
            await send_telegram_alert(f"*Low voting power*: {voting_power // 10**6} UNION (Rank: {rank})")
        if avg_block_time > 10:
            await send_telegram_alert(f"*Slow block time*: {avg_block_time:.2f}s")
        if delegator_count is not None and delegator_count < 10:
            await send_telegram_alert(f"*Low delegator count*: {delegator_count} UNION")
        if state.uptime is not None and state.uptime < (100 - SLASHING_THRESHOLD * 100):
            await send_telegram_alert(f"*High miss rate*: {state.total_missed}/{SLASHING_WINDOW} blocks missed!")

        if missed > 0:
            state.missed_since_last_alert += missed
            logging.info(f"Missed {missed} blocks this check. Total since last alert: {state.missed_since_last_alert}")
            if state.missed_since_last_alert > 5:
                miss_rate = (state.total_missed / SLASHING_WINDOW * 100)
                await send_telegram_alert(
                    f"🚨 *Validator missed {state.missed_since_last_alert} blocks since last alert!* "
                    f"Slashing Window: {state.total_missed}/{SLASHING_WINDOW} ({miss_rate:.1f}%)"
                )
                state.missed_since_last_alert = 0

        state.last_height = current_height
        await asyncio.sleep(60)

if __name__ == "__main__":
    logging.info("Starting bot...")
    asyncio.run(monitor())
