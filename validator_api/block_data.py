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
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{UNION_REST_API}/cosmos/slashing/v1beta1/signing_infos/{VALIDATOR_CONSENSUS_ADDRESS}", timeout=10) as response:
                response.raise_for_status()
                signing_info = (await response.json())["val_signing_info"]
                total_missed = int(signing_info["missed_blocks_counter"])
                current_height = await get_latest_height()
                missed = total_missed - sum(1 for ts in missed_blocks_timestamps) if missed_blocks_timestamps else total_missed
                avg_block_time = 0  # Could estimate from block timestamps if needed
                return missed, current_height, total_missed, avg_block_time
        except Exception as e:
            print(f"Error checking missed blocks: {e}")
            return -1, last_height, len(missed_blocks_timestamps), 0
