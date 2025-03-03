import aiohttp
from config.settings import *



async def get_validator_status():
    url = f"{UNION_REST_API}/cosmos/staking/v1beta1/validators/{VALIDATOR_OPERATOR_ADDRESS}"
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                validator = data["validator"]
                
                # Map fields to your tuple
                active = validator["status"] == "BOND_STATUS_BONDED"
                voting_power = int(validator["tokens"])
                total_voting_power = None  # Requires separate query or node data
                rank = None  # May need custom logic or another endpoint
                jailed = validator["jailed"]
                delegator_count = None  # May need /delegators endpoint
                uptime = None  # Requires missed block data or custom logic
                
                return (
                    active,
                    voting_power,
                    total_voting_power or 0,
                    rank or 0,
                    jailed,
                    delegator_count or 0,
                    uptime or 0.0
                )
        except (aiohttp.ClientError, KeyError, ValueError) as e:
            print(f"⚠️ Error fetching validator status: {e}")
            return False, 0, 0, 0, False, 0, 0.0
