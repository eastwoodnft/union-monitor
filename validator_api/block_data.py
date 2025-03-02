import aiohttp

async def get_latest_height():
    url = f"{UNION_RPC}/latest_block"
    timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise error for bad HTTP responses
                data = await response.json()
                return data.get("block_height", 0)
        except aiohttp.ClientError as e:
            print(f"⚠️ RPC Connection error: {e}")
            return 0

async def get_missed_blocks(last_height, missed_blocks_timestamps):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{UNION_RPC}/missed_blocks?height={last_height}") as response:
            data = await response.json()
            missed = data["missed"]
            current_height = data["height"]
            total_missed = data["total_missed"]
            avg_block_time = data["avg_block_time"]
            return missed, current_height, total_missed, avg_block_time
