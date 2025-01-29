import requests
import time

# ================
# CONFIG / CONSTANTS
# ================
TOKEN_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
TOKEN_PAIRS_URL_TEMPLATE = "https://api.dexscreener.com/token-pairs/v1/solana/{tokenAddress}"

# Example thresholds
MIN_VOLUME_USD = 30000        # Must have at least $30k 24h volume
MIN_LIQUIDITY_USD = 1000    # Must have at least $1k in liquidity
MIN_AGE_SECONDS = 86400       # Must be at least 1 day old

# ================
# HELPERS
# ================

def fetch_solana_token_profiles():
    """
    Fetches the latest token profiles from Dexscreener and filters
    only those that belong to 'solana'.
    """
    try:
        response = requests.get(TOKEN_PROFILES_URL, timeout=10)
        response.raise_for_status()
        
        # Dexscreener returns a list of token profile objects (for multiple chains).
        all_profiles = response.json()
        
        # Filter out only the Solana profiles:
        solana_profiles = [profile for profile in all_profiles if profile.get("chainId") == "solana"]
        
        print(f"Total token profiles returned (all chains): {len(all_profiles)}")
        print(f"Total Solana-specific profiles: {len(solana_profiles)}\n")
        
        return solana_profiles

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not fetch Solana token profiles: {e}")
        return []


def fetch_token_pairs_for_solana_token(token_address):
    """
    Retrieves pool/pair data for a given Solana token address.
    This data typically includes volume, liquidity, etc.
    
    Endpoint:
      GET https://api.dexscreener.com/token-pairs/v1/solana/{tokenAddress}
    """
    try:
        url = TOKEN_PAIRS_URL_TEMPLATE.format(tokenAddress=token_address)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()  # Usually a list of pairs
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch pairs for {token_address}: {e}")
        return []


def passes_filter_criteria(pair_data,
                           min_volume=MIN_VOLUME_USD,
                           min_liquidity=MIN_LIQUIDITY_USD,
                           min_age=MIN_AGE_SECONDS):
    """
    Checks if the given pair_data meets:
      - 24h volume >= min_volume
      - liquidity >= min_liquidity
      - age >= min_age (in seconds)
    """
    volume_24h = pair_data.get("volume", {}).get("h24", 0)
    liquidity_usd = pair_data.get("liquidity", {}).get("usd", 0)
    pair_created_at = pair_data.get("pairCreatedAt", 0)  # Often in milliseconds

    # Convert timestamp from ms to seconds
    pair_created_at_s = pair_created_at / 1000.0
    current_ts = time.time()
    age_in_seconds = current_ts - pair_created_at_s

    if (volume_24h >= min_volume
        and liquidity_usd >= min_liquidity
        and age_in_seconds >= min_age):
        return True
    else:
        return False


def filter_solana_coins():
    """
    1) Fetch all Solana token profiles
    2) For each token, retrieve pair data
    3) Check if any pair meets the filter criteria (volume, liquidity, age)
    4) Print out those that pass
    """
    solana_profiles = fetch_solana_token_profiles()

    valid_tokens = []
    
    for idx, profile in enumerate(solana_profiles, start=1):
        token_address = profile.get("tokenAddress", "N/A")
        token_name_url = profile.get("url", "Unknown URL")
        
        # Retrieve all pairs for this token.
        pairs_data = fetch_token_pairs_for_solana_token(token_address)
        
        # Check if *any* of the token's pairs meets the criteria:
        if any(passes_filter_criteria(pair) for pair in pairs_data):
            valid_tokens.append(profile)
    
    # Print or return the valid tokens
    print(f"\n=== FILTER RESULTS ===")
    if not valid_tokens:
        print("No Solana tokens passed the filter criteria.")
        return
    
    print(f"{len(valid_tokens)} Solana tokens passed the filter criteria:")
    for idx, vtoken in enumerate(valid_tokens, start=1):
        print(f"{idx}. Token Address: {vtoken.get('tokenAddress')}")
        print(f"   URL: {vtoken.get('url')}")
        print(f"   Description: {vtoken.get('description', '')[:80]}...\n")


if __name__ == "__main__":
    filter_solana_coins()
