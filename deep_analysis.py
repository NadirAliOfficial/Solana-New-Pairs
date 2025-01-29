import time
import requests

# --------------------------------------------------
# 1) CONFIG / CONSTANTS
# --------------------------------------------------

# Dexscreener endpoint for the latest token profiles
TOKEN_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
# Dexscreener endpoint for token pairs
TOKEN_PAIRS_URL_TEMPLATE = "https://api.dexscreener.com/token-pairs/v1/solana/{tokenAddress}"

# Example thresholds (tweak as needed)
MIN_LIQUIDITY_USD = 10000     # must have at least $10k liquidity
MIN_TX_COUNT_24H = 300        # must have at least 300 transactions in 24h
TOP_HOLDER_MAX_PERCENT = 30   # top holder must have < 30% supply
REQUIRED_LIQUIDITY_LOCK = True

# Weighted scoring parameters
WEIGHT_LIQUIDITY = 0.4
WEIGHT_VOLUME = 0.3
WEIGHT_TX_COUNT = 0.2
WEIGHT_HOLDER_DISTRIB = 0.1  # or negative weighting if top holder % is large

# Minimum final score to pass (example)
MIN_SCORE_THRESHOLD = 2000


# --------------------------------------------------
# 2) PLACEHOLDER FUNCTIONS FOR ADDITIONAL DATA
# --------------------------------------------------

def fetch_holder_distribution(token_address):
    """
    Returns data about token holder distribution:
      {
        "topHolders": [
          {"address": "SomeWhale1", "percentage": 15.0},
          {"address": "SomeWhale2", "percentage": 12.5},
          ...
        ],
        "totalHolders": 987
      }
    In reality, you'd query:
      - A Solana explorer
      - On-chain data
      - Another aggregator service
    """
    # Placeholder data for demonstration:
    data = {
        "topHolders": [
            {"address": "WhaleA", "percentage": 15.0},
            {"address": "WhaleB", "percentage": 12.5}
        ],
        "totalHolders": 650
    }
    return data

def check_liquidity_lock(token_address):
    """
    Returns True/False indicating whether the token's liquidity is locked.
    In reality, you'd check a known lock/vesting service or do an on-chain check.
    """
    # Placeholder always returns True for demonstration
    return True

def fetch_transaction_count(token_address):
    """
    Returns the 24h transaction count for the token.
    You can glean this from Dexscreener pairs 'txns.h24' or an on-chain analytics API.
    """
    # Placeholder returns a random or static number for demonstration
    # E.g., combined buys + sells if you have that data from Dexscreener
    return 500

def fetch_historical_data(token_address):
    """
    Could return a list of daily volume/liquidity for the past 7 days, for example:
      [
        {"timestamp": 1690000000, "volume": 35000, "liquidity": 12000},
        {"timestamp": 1690086400, "volume": 42000, "liquidity": 15000},
        ...
      ]
    Or retrieve from your DB if you're storing historical snapshots.
    """
    # Placeholder: random or static example
    historical = [
        {"timestamp": 1690000000, "volume": 30000, "liquidity": 9000},
        {"timestamp": 1690086400, "volume": 35000, "liquidity": 10000},
        {"timestamp": 1690172800, "volume": 40000, "liquidity": 11000},
    ]
    return historical


# --------------------------------------------------
# 3) HELPER FUNCTIONS FOR DEXSCREENER
# --------------------------------------------------

def fetch_solana_token_profiles():
    """
    Fetch the latest token profiles from Dexscreener and filter for Solana.
    """
    try:
        response = requests.get(TOKEN_PROFILES_URL, timeout=10)
        response.raise_for_status()
        all_profiles = response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Could not fetch token profiles: {e}")
        return []

    # Filter to only Solana
    solana_profiles = [p for p in all_profiles if p.get("chainId") == "solana"]
    return solana_profiles

def fetch_pairs_for_token(token_address):
    """
    Retrieves pool/pair data for a given Solana token address from Dexscreener,
    which includes liquidity, volume, etc.
    """
    url = TOKEN_PAIRS_URL_TEMPLATE.format(tokenAddress=token_address)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()  # Usually a list of pairs
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch pairs for {token_address}: {e}")
        return []


# --------------------------------------------------
# 4) SCORING / ANALYSIS
# --------------------------------------------------

def compute_token_score(volume_24h, liquidity_usd, tx_count, top_holder_pct, historical_data=None):
    """
    Example weighted scoring function:
      score = (WEIGHT_LIQUIDITY * liquidity_usd)
            + (WEIGHT_VOLUME   * volume_24h)
            + (WEIGHT_TX_COUNT * tx_count)
            - (WEIGHT_HOLDER_DISTRIB * top_holder_pct if we consider big whales negative)
    
    Then you can adjust the result based on historical trends (volume or liquidity growth, etc.).
    """
    base_score = (
        (WEIGHT_LIQUIDITY * liquidity_usd) +
        (WEIGHT_VOLUME    * volume_24h) +
        (WEIGHT_TX_COUNT  * tx_count) -
        (WEIGHT_HOLDER_DISTRIB * top_holder_pct)
    )

    # Optionally incorporate historical growth
    if historical_data:
        # Example: if liquidity or volume is trending up, add a small bonus
        bonus = compute_historical_bonus(historical_data)
        base_score += bonus
    
    return base_score

def compute_historical_bonus(historical_data):
    """
    Quick example: If volume has increased from oldest to newest record, add +100, else 0.
    This is simplistic; you can do more advanced analysis (like a regression).
    """
    if len(historical_data) < 2:
        return 0
    volumes = [day["volume"] for day in historical_data]
    if volumes[-1] > volumes[0]:
        return 100
    return 0


# --------------------------------------------------
# 5) MAIN FILTERING LOGIC
# --------------------------------------------------

def advanced_filter_solana_tokens():
    """
    1. Fetch the latest Solana tokens from Dexscreener.
    2. For each token:
       - Get pair data (liquidity, volume).
       - Get holder distribution, check top holder < 30%.
       - Check liquidity lock if required.
       - Check transaction count.
       - Compute a weighted score using historical data.
       - Decide if the token passes minimum thresholds & scoring.
    3. Return or print the tokens that pass.
    """
    solana_profiles = fetch_solana_token_profiles()
    print(f"Found {len(solana_profiles)} Solana token profiles.")

    valid_tokens = []
    
    for profile in solana_profiles:
        token_address = profile.get("tokenAddress", "")
        if not token_address:
            continue
        
        pairs = fetch_pairs_for_token(token_address)
        if not pairs:
            # No pair data => skip
            continue
        
        # We'll assume we only need to evaluate the "primary" or first pair
        # or you can combine the logic (e.g., pick the pair with highest volume).
        best_pair = max(pairs, key=lambda p: p.get("volume", {}).get("h24", 0))
        
        volume_24h = best_pair.get("volume", {}).get("h24", 0)
        liquidity_usd = best_pair.get("liquidity", {}).get("usd", 0)
        
        # BASIC THRESHOLD CHECKS
        if liquidity_usd < MIN_LIQUIDITY_USD:
            continue  # fails liquidity
        # transaction count
        tx_count_24h = fetch_transaction_count(token_address)
        if tx_count_24h < MIN_TX_COUNT_24H:
            continue  # fails tx count
        
        # DISTRIBUTION & LIQUIDITY LOCK
        holder_info = fetch_holder_distribution(token_address)
        top_holders = holder_info.get("topHolders", [])
        if top_holders:
            max_holder_pct = max([h["percentage"] for h in top_holders])
            if max_holder_pct > TOP_HOLDER_MAX_PERCENT:
                continue  # fails top-holder distribution
        else:
            max_holder_pct = 0
        
        # liquidity lock
        if REQUIRED_LIQUIDITY_LOCK and not check_liquidity_lock(token_address):
            continue  # fails liquidity lock
        
        # H ISTORICAL DATA & SCORING
        historical_data = fetch_historical_data(token_address)
        score = compute_token_score(volume_24h, liquidity_usd, tx_count_24h, max_holder_pct, historical_data)

        if score >= MIN_SCORE_THRESHOLD:
            valid_tokens.append({
                "tokenAddress": token_address,
                "score": score,
                "volume_24h": volume_24h,
                "liquidity_usd": liquidity_usd,
                "tx_count_24h": tx_count_24h,
                "top_holder_pct": max_holder_pct
            })
    
    # Sort final tokens by descending score
    valid_tokens.sort(key=lambda x: x["score"], reverse=True)

    # Print or return the results
    print("\n=== ADVANCED FILTERING RESULTS ===")
    if not valid_tokens:
        print("No tokens passed the advanced filters.")
    else:
        for idx, t in enumerate(valid_tokens, start=1):
            print(f"{idx}. {t['tokenAddress']} - Score: {t['score']:.2f}, "
                  f"Vol: {t['volume_24h']}, Liq: {t['liquidity_usd']}, "
                  f"TxCount: {t['tx_count_24h']}, TopHolder: {t['top_holder_pct']}%")

    return valid_tokens


if __name__ == "__main__":
    # Run the advanced filter logic
    final_list = advanced_filter_solana_tokens()
