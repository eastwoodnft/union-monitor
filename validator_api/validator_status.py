import aiohttp
from config.settings import UNION_RPC, UNION_REST_API, VALIDATOR_CONSENSUS_ADDRESS, VALIDATOR_OPERATOR_ADDRESS

async def get_validator_status():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{UNION_RPC}/status?", timeout=10) as response:
                response.raise_for_status()
                status = await response.json()
                latest_height = int(status["result"]["sync_info"]["latest_block_height"])
                syncing = status["result"]["sync_info"]["catching_up"]

            # Fetch all validators with pagination
            page = 1
            per_page = 100
            validators = []
            while True:
                async with session.get(f"{UNION_RPC}/validators?height={latest_height}&page={page}&per_page={per_page}", timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    validators.extend(data["result"]["validators"])
                    total_validators = int(data["result"]["total"])
                    if len(validators) >= total_validators or not data["result"]["validators"]:
                        break
                    page += 1

            total_voting_power = sum(int(v["voting_power"]) for v in validators)
            my_validator = next((v for v in validators if v["address"] == VALIDATOR_CONSENSUS_ADDRESS), None)

            if not my_validator:
                return True, None, total_voting_power, None, False, None, None, syncing

            voting_power = int(my_validator["voting_power"])
            rank = sorted(validators, key=lambda x: int(x["voting_power"]), reverse=True).index(my_validator) + 1
            jailed = my_validator.get("jailed", False)

            async with session.get(f"{UNION_REST_API}/cosmos/staking/v1beta1/validators/{VALIDATOR_OPERATOR_ADDRESS}", timeout=10) as response:
                delegator_count = None
                if response.status == 200:
                    val_data = await response.json()
                    delegator_count = int(val_data["validator"].get("delegator_shares", "0").split('.')[0]) // 10**18

            return True, voting_power, total_voting_power, rank, jailed, delegator_count, None, syncing
        except Exception as e:
            print(f"Error fetching validator status: {e}")
            return False, None, None, None, None, None, None, False
