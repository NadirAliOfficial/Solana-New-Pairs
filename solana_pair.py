import requests

# Dexscreener endpoint for the latest token profiles
TOKEN_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"




def fetch_solana_token_profiles():
    try:
        response = requests.get(TOKEN_PROFILES_URL, timeout=10)
        response.raise_for_status()
        
        # The API returns a list of token profile objects (for multiple chains).
        all_profiles = response.json()
        
        # Filter out only the Solana profiles:
        solana_profiles = [profile for profile in all_profiles if profile.get("chainId") == "solana"]
        
        print(f"Total token profiles returned (all chains): {len(all_profiles)}")
        print(f"Total Solana-specific profiles: {len(solana_profiles)}\n")

        # Display details for each Solana token
        for idx, profile in enumerate(solana_profiles, start=1):
            token_address = profile.get("tokenAddress", "N/A")
            description = profile.get("description", "No description")
            links = profile.get("links", [])
            
            print(f"--- Solana Profile {idx} ---")
            print(f"Token Address: {token_address}")
            print(f"Description: {description}")
            
            # Print links (website, Twitter, Telegram, etc.)
            for link in links:
                label = link.get("label", link.get("type", "link"))
                url = link.get("url", "")
                print(f"  {label}: {url}")
            
            print()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not fetch Solana token profiles: {e}")
        



if __name__ == "__main__":
    fetch_solana_token_profiles()
