import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import UNION_RPC, VALIDATOR_CONSENSUS_ADDRESS, SLASHING_WINDOW

async def get_latest_height():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    try:
        response = session.get(f"{UNION_RPC}/block", timeout=10)
        response.raise_for_status()
        height = int(response.json()["result"]["block"]["header"]["height"])
        return height
    except Exception as e:
        print(f"Error fetching latest height: {e}")
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

        if latest_height - last_height > SLASHING_WINDOW:
            missed_blocks_timestamps.clear()
        else:
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
                    print(f"Skipping height {height} due to 500 Internal Server Error")
                    current_height = height
                    continue
                raise
        avg_block_time = (block_times[-1] - block_times[0]) / (len(block_times) - 1) if len(block_times) > 1 else 0
        total_missed = len(missed_blocks_timestamps)
        return missed, current_height, total_missed, avg_block_time
    except Exception as e:
        print(f"Error checking missed blocks: {e}")
        return -1, current_height, len(missed_blocks_timestamps), 0
