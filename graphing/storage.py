import json
import os
from collections import deque
from config.settings import SLASHING_WINDOW

HISTORY_FILE = "history.json"
MAX_ENTRIES = 30 * 24 * 7  # ~1 week at 1-minute intervals

def load_history():
    """Load history from disk, returning a dict with lists."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            # Convert to lists (could use deque if needed)
            return {
                "timestamps": data.get("timestamps", []),
                "missed_blocks": data.get("missed_blocks", [])
            }
    return {"timestamps": [], "missed_blocks": []}

def save_history(history):
    """Save history to disk, trimming to MAX_ENTRIES."""
    # Trim to max length
    if len(history["timestamps"]) > MAX_ENTRIES:
        history["timestamps"] = history["timestamps"][-MAX_ENTRIES:]
        history["missed_blocks"] = history["missed_blocks"][-MAX_ENTRIES:]
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def append_history(history, timestamp, missed_blocks):
    """Append new data to history and save."""
    history["timestamps"].append(timestamp)
    history["missed_blocks"].append(missed_blocks)
    save_history(history)
