import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import UNION_RPC, UNION_REST_API, VALIDATOR_CONSENSUS_ADDRESS, VALIDATOR_OPERATOR_ADDRESS

async def get_validator_status():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    try:
        response = session.get(f"{UNION_RPC}/status?", timeout=10)
        response.raise_for_status()
        status = response.json()["result"]
        latest_height = int(status["sync_info"]["latest_block_height"])

        response = session.get(f"{UNION_RPC}/validators?height={latest_height}&page=1&per_page=100", timeout=10)
        response.raise_for_status()
        validators_data = response.json()["result"]
        validators = validators_data["validators"]
        total_voting_power = sum(int(v["voting_power"]) for v in validators)
        my_validator = next((v for v in validators if v["address"] == VALIDATOR_CONSENSUS_ADDRESS), None)

        if not my_validator:
            return True, None, total_voting_power, None, False, None, None

        voting_power = int(my_validator["voting_power"])
        rank = sorted(validators, key=lambda x: int(x["voting_power"]), reverse=True).index(my_validator) + 1
        jailed = my_validator.get("jailed", False)

        response = session.get(f"{UNION_REST_API}/cosmos/staking/v1beta1/validators/{VALIDATOR_OPERATOR_ADDRESS}", timeout=10)
        delegator_count = None
        if response.status_code == 200:
            val_data = response.json()["validator"]
            delegator_count = int(val_data.get("delegator_shares", "0").split('.')[0]) // 10**18

        return True, voting_power, total_voting_power, rank, jailed, delegator_count, None
    except Exception as e:
        print(f"Error fetching validator status: {e}")
        return False, None, None, None, None, None, None
