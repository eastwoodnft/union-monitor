import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import UNION_RPC, UNION_REST_API, VALIDATOR_CONSENSUS_ADDRESS, VALIDATOR_OPERATOR_ADDRESS

async def get_validator_status():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    try:
        # Get sync status and basic info from RPC
        response = session.get(f"{UNION_RPC}/status?", timeout=10)
        response.raise_for_status()
        status = response.json()["result"]
        latest_height = int(status["sync_info"]["latest_block_height"])
        syncing = status["sync_info"]["catching_up"]

        # Get validator set
        response = session.get(f"{UNION_RPC}/validators?height={latest_height}&page=1&per_page=100", timeout=10)
        response.raise_for_status()
        validators_data = response.json()["result"]
        validators = validators_data["validators"]
        total_voting_power = sum(int(v["voting_power"]) for v in validators)
        my_validator = next((v for v in validators if v["address"] == VALIDATOR_CONSENSUS_ADDRESS), None)

        if not my_validator:
            # Get peer count from REST API as fallback
            response = session.get(f"{UNION_REST_API}/cosmos/base/tendermint/v1beta1/node_info", timeout=10)
            peer_count = len(response.json()["default_node_info"]["peers"]) if response.status_code == 200 else 0
            return True, None, total_voting_power, None, False, None, None, syncing, peer_count

        voting_power = int(my_validator["voting_power"])
        rank = sorted(validators, key=lambda x: int(x["voting_power"]), reverse=True).index(my_validator) + 1
        jailed = my_validator.get("jailed", False)

        # Get delegator count
        response = session.get(f"{UNION_REST_API}/cosmos/staking/v1beta1/validators/{VALIDATOR_OPERATOR_ADDRESS}", timeout=10)
        delegator_count = None
        if response.status_code == 200:
            val_data = response.json()["validator"]
            delegator_count = int(val_data.get("delegator_shares", "0").split('.')[0]) // 10**18

        # Get peer count from REST API
        response = session.get(f"{UNION_REST_API}/cosmos/base/tendermint/v1beta1/node_info", timeout=10)
        peer_count = len(response.json()["default_node_info"]["peers"]) if response.status_code == 200 else 0

        return True, voting_power, total_voting_power, rank, jailed, delegator_count, None, syncing, peer_count
    except Exception as e:
        print(f"Error fetching validator status: {e}")
        return False, None, None, None, None, None, None, False, 0
