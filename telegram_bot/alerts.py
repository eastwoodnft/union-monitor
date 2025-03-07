import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SLASHING_WINDOW

bot = Bot(token=TELEGRAM_BOT_TOKEN)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def send_telegram_alert(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

async def status_command(update, context, state):
    missed_percentage = (state.total_missed / state.slashing_window * 100) if state.total_missed > 0 else 0
    msg = (
        f"*Validator Status*\n"
        f"Active: {'Yes' if state.active else 'No'}\n"
        f"Voting Power: {state.voting_power // 10**6 if state.voting_power is not None else 'N/A'} UNION "
        f"(Rank: {state.rank if state.rank is not None else 'N/A'})\n"
        f"Jailed: {'Yes' if state.jailed else 'No'}\n"
        f"Delegators: {state.delegator_count if state.delegator_count is not None else 'N/A'} UNION\n"
        f"Missed Blocks: {state.total_missed}/{SLASHING_WINDOW} ({missed_percentage:.1f}%)\n"
        f"Uptime: {state.uptime:.1f}%\n"
        f"Sync Status: {'Synced' if not state.syncing else 'Catching Up'}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def missed_command(update, context, state):
    missed_percentage = (state.total_missed / state.slashing_window * 100) if state.total_missed > 0 else 0
    msg = (
        f"*Missed Blocks*\n"
        f"Slashing Window ({SLASHING_WINDOW} blocks): {state.total_missed} ({missed_percentage:.1f}%)"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def network_command(update, context, state):
    msg = f"*Network Stats*\nAvg Block Time: {state.avg_block_time:.2f}s"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def validator_command(update, context, state):
    msg = (
        f"*Validator Details*\n"
        f"Voting Power: {state.voting_power // 10**6 if state.voting_power is not None else 'N/A'} UNION "
        f"(Rank: {state.rank if state.rank is not None else 'N/A'})\n"
        f"Jailed: {'Yes' if state.jailed else 'No'}\n"
        f"Delegators: {state.delegator_count if state.delegator_count is not None else 'N/A'} UNION"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def pause_command(update, context, state):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /pause <hours> (e.g., /pause 2)")
        return
    hours = int(context.args[0])
    if hours <= 0 or hours > 24:
        await update.message.reply_text("Please specify a number between 1 and 24 hours.")
        return
    from time import time
    state.paused_until = time() + (hours * 3600)
    await update.message.reply_text(f"Alerts paused for {hours} hour(s).")
