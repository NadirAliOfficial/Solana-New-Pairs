import requests

# Example: Get the latest token profiles (rate-limit 60 requests per minute)
DEXSCREENER_TOKEN_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"

def check_latest_token_profiles():
    try:
        # Send a GET request
        response = requests.get(DEXSCREENER_TOKEN_PROFILES_URL, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes

        # Parse the JSON data from the response
        data = response.json()

        # Here, we just print the entire response for debugging.
        # In practice, you might want to filter, transform, or store this data.
        print("Dexscreener latest token profiles response:")
        print(data)

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to call Dexscreener API: {e}")

if __name__ == "__main__":
    check_latest_token_profiles()
