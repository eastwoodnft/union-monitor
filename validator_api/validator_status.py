import aiohttp
from config.settings import *

async def get_validator_status(validator_address=VALIDATOR_CONSENSUS_ADDRESS):
    url = f"{UNION_RPC}/validator_status?address={validator_address}"
    timeout = aiohttp.ClientTimeout(total=10)  # Add timeout like get_latest_height
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return (
                    bool(data["active"]),
                    int(data["voting_power"]),
                    int(data["total_voting_power"]),
                    int(data["rank"]),
                    bool(data["jailed"]),
                    int(data["delegator_count"]),
                    float(data["uptime"]),
                )
        except (aiohttp.ClientError, KeyError, ValueError) as e:
            print(f"⚠️ Error fetching validator status: {e}")
            return False, 0, 0, 0, False, 0, 0.0  # Consistent fallback
