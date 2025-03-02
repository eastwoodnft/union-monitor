import aiohttp

async def get_latest_height():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://your_rpc_endpoint.com/latest_block") as response:
            data = await response.json()
            return data["height"]

async def get_missed_blocks(last_height, missed_blocks_timestamps):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://your_rpc_endpoint.com/missed_blocks?height={last_height}") as response:
            data = await response.json()
            missed = data["missed"]
            current_height = data["height"]
            total_missed = data["total_missed"]
            avg_block_time = data["avg_block_time"]
            return missed, current_height, total_missed, avg_block_time
