import aiohttp

async def get_validator_status():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://your_rpc_endpoint.com/validator_status") as response:
            data = await response.json()
            return (
                data["active"],
                data["voting_power"],
                data["total_voting_power"],
                data["rank"],
                data["jailed"],
                data["delegator_count"],
                data["uptime"],
            )
