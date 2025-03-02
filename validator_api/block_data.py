import aiohttp
from config.settings import *

async def get_latest_height():
    url = f"{UNION_RPC}/abci_info?"
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return int(data["result"]["response"]["last_block_height"])
        except (aiohttp.ClientError, KeyError, ValueError) as e:
            print(f"⚠️ RPC Connection error: {e}")
            return 0

async def get_missed_blocks(last_height, missed_blocks_timestamps=None):
    url = f"{UNION_RPC}/missed_blocks?height={last_height}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                missed = data["missed"]
                current_height = data["height"]
                total_missed = data["total_missed"]
                avg_block_time = data["avg_block_time"]
                return missed, current_height, total_missed, avg_block_time
        except (aiohttp.ClientError, KeyError) as e:
            print(f"⚠️ Error fetching missed blocks: {e}")
            return 0, last_height, 0, 0
