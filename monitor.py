import asyncio
from collections import deque
from validator_api.block_data import get_latest_height, get_missed_blocks
from validator_api.validator_status import get_validator_status
from telegram_bot.alerts import send_telegram_alert, application, status_command, missed_command, network_command, validator_command
from telegram.ext import CommandHandler
from config.settings import SLASHING_WINDOW, SLASHING_THRESHOLD
from graphing.plot import plot_missed_blocks
from graphing.storage import load_history, append_history

class MonitorState:
    def __init__(self):
        self.last_height = 0
        self.missed_since_last_alert = 0
        self.total_missed = 0
        self.total_blocks = 0
        self.avg_block_time = 0
        self.active = False
        self.voting_power = None
        self.total_voting_power = None
        self.rank = None
        self.jailed = False
        self.delegator_count = None
        self.uptime = None
        self.slashing_window = SLASHING_WINDOW

state = MonitorState()

# Load history from disk
history = load_history()

async def graph_command(update, context, state, history):
    """Telegram command to send a graph of missed blocks."""
    plot_path = plot_missed_blocks(history)
    if plot_path:
        with open(plot_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption="Missed Blocks Over Time")
    else:
        await update.message.reply_text("No data available to generate graph.")

async def monitor():
    last_height = await get_latest_height()
    if last_height == 0:
        await send_telegram_alert("⚠️ Failed to fetch initial block height. Starting from 0.")
    state.last_height = last_height
    missed_blocks_timestamps = deque(maxlen=SLASHING_WINDOW)
    failures = 0
    max_failures = 5

    commands = [
        {"command": "status", "description": "Get validator status"},
        {"command": "missed", "description": "Check missed blocks"},
        {"command": "network", "description": "View network stats"},
        {"command": "validator", "description": "Validator details"},
        {"command": "graph", "description": "Graph missed blocks over time"}
    ]
    await application.bot.set_my_commands([(cmd["command"], cmd["description"]) for cmd in commands])

    application.add_handler(CommandHandler("status", lambda u, c: status_command(u, c, state)))
    application.add_handler(CommandHandler("missed", lambda u, c: missed_command(u, c, state)))
    application.add_handler(CommandHandler("network", lambda u, c: network_command(u, c, state)))
    application.add_handler(CommandHandler("validator", lambda u, c: validator_command(u, c, state)))
    application.add_handler(CommandHandler("graph", lambda u, c: graph_command(u, c, state, history)))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        active, voting_power, total_voting_power, rank, jailed, delegator_count, _ = await get_validator_status()
        missed, current_height, total_missed, avg_block_time = await get_missed_blocks(state.last_height, missed_blocks_timestamps)

        state.active = active
        state.voting_power = voting_power
        state.total_voting_power = total_voting_power
        state.rank = rank
        state.jailed = jailed
        state.delegator_count = delegator_count
        state.total_missed = total_missed
        state.avg_block_time = avg_block_time
        state.uptime = 100 * (1 - (total_missed / SLASHING_WINDOW)) if total_missed > 0 else 100

        # Update history on disk
        from time import time
        append_history(history, time(), state.total_missed)

        print(
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
            print(f"Missed {missed} blocks this check. Total since last alert: {state.missed_since_last_alert}")
            if state.missed_since_last_alert > 5:
                miss_rate = (state.total_missed / SLASHING_WINDOW * 100)
                await send_telegram_alert(
                    f"🚨 *Validator missed {state.missed_since_last_alert} blocks since last alert!* "
                    f"Slashing Window: {state.total_missed}/{SLASHING_WINDOW} ({miss_rate:.1f}%)"
                )
                state.missed_since_last_alert = 0

        state.last_height = current_height
        await asyncio.sleep(60)
