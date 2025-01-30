import time
import requests
import uuid
import threading
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional

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

# Jupiter API
JUPITER_API_BASE_URL = "https://api.jupiter.xyz"  # Replace with actual Jupiter API base URL
JUPITER_API_KEY = os.getenv("JUPITER_API_KEY")  # Securely store your API key

# Phantom Wallet
PHANTOM_PRIVATE_KEY = os.getenv("PHANTOM_PRIVATE_KEY")  # Securely store your private key
PHANTOM_WALLET_ADDRESS = os.getenv("PHANTOM_WALLET_ADDRESS")

# Investment Percentages
INVESTMENT_PERCENTAGES = [5, 10, 15, 20]

# --------------------------------------------------
# 2) DATA CLASSES
# --------------------------------------------------

@dataclass
class Milestone:
    percentage_gain: float  # e.g., 30.0 for 30%
    is_sold: bool = False
    sold_amount: float = 0.0  # USD amount sold at this milestone

@dataclass
class Trade:
    token_address: str
    entry_price: float  # USD price at which the token was bought
    investment_amount: float  # USD amount invested
    purchase_levels: List[float]  # e.g., [5, 10, 15, 20] percentages
    stop_loss: float  # Percentage drop from entry_price to trigger stop-loss
    milestones: List[Milestone] = field(default_factory=lambda: [
        Milestone(percentage_gain=30.0),
        Milestone(percentage_gain=65.0),
        Milestone(percentage_gain=100.0)
    ])
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_status: str = "OPEN"  # Could be OPEN, STOPPED, COMPLETED

    def update_status(self, new_status: str):
        self.current_status = new_status

# --------------------------------------------------
# 3) PLACEHOLDER FUNCTIONS FOR ADDITIONAL DATA
# --------------------------------------------------

def fetch_holder_distribution(token_address):
    # Placeholder implementation
    data = {
        "topHolders": [
            {"address": "WhaleA", "percentage": 15.0},
            {"address": "WhaleB", "percentage": 12.5}
        ],
        "totalHolders": 650
    }
    return data

def check_liquidity_lock(token_address):
    # Placeholder always returns True for demonstration
    return True

def fetch_transaction_count(token_address):
    # Placeholder returns a static number for demonstration
    return 500

def fetch_historical_data(token_address):
    # Placeholder historical data
    historical = [
        {"timestamp": 1690000000, "volume": 30000, "liquidity": 9000},
        {"timestamp": 1690086400, "volume": 35000, "liquidity": 10000},
        {"timestamp": 1690172800, "volume": 40000, "liquidity": 11000},
    ]
    return historical

# --------------------------------------------------
# 4) HELPER FUNCTIONS FOR DEXSCREENER
# --------------------------------------------------

def fetch_solana_token_profiles():
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
    url = TOKEN_PAIRS_URL_TEMPLATE.format(tokenAddress=token_address)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()  # Usually a list of pairs
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch pairs for {token_address}: {e}")
        return []

# --------------------------------------------------
# 5) SCORING / ANALYSIS
# --------------------------------------------------

def compute_token_score(volume_24h, liquidity_usd, tx_count, top_holder_pct, historical_data=None):
    base_score = (
        (WEIGHT_LIQUIDITY * liquidity_usd) +
        (WEIGHT_VOLUME    * volume_24h) +
        (WEIGHT_TX_COUNT  * tx_count) -
        (WEIGHT_HOLDER_DISTRIB * top_holder_pct)
    )

    # Optionally incorporate historical growth
    if historical_data:
        bonus = compute_historical_bonus(historical_data)
        base_score += bonus

    return base_score

def compute_historical_bonus(historical_data):
    if len(historical_data) < 2:
        return 0
    volumes = [day["volume"] for day in historical_data]
    if volumes[-1] > volumes[0]:
        return 100
    return 0

# --------------------------------------------------
# 6) FILTERING LOGIC
# --------------------------------------------------

def advanced_filter_solana_tokens():
    solana_profiles = fetch_solana_token_profiles()
    print(f"Found {len(solana_profiles)} Solana token profiles.")

    valid_tokens = []
    
    for profile in solana_profiles:
        token_address = profile.get("tokenAddress", "")
        if not token_address:
            continue
        
        pairs = fetch_pairs_for_token(token_address)
        if not pairs:
            continue
        
        best_pair = max(pairs, key=lambda p: p.get("volume", {}).get("h24", 0))
        
        volume_24h = best_pair.get("volume", {}).get("h24", 0)
        liquidity_usd = best_pair.get("liquidity", {}).get("usd", 0)
        
        if liquidity_usd < MIN_LIQUIDITY_USD:
            continue  # fails liquidity
        
        tx_count_24h = fetch_transaction_count(token_address)
        if tx_count_24h < MIN_TX_COUNT_24H:
            continue  # fails tx count
        
        holder_info = fetch_holder_distribution(token_address)
        top_holders = holder_info.get("topHolders", [])
        if top_holders:
            max_holder_pct = max([h["percentage"] for h in top_holders])
            if max_holder_pct > TOP_HOLDER_MAX_PERCENT:
                continue  # fails top-holder distribution
        else:
            max_holder_pct = 0
        
        if REQUIRED_LIQUIDITY_LOCK and not check_liquidity_lock(token_address):
            continue  # fails liquidity lock
        
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

# --------------------------------------------------
# 7) TRADING MANAGEMENT SYSTEM
# --------------------------------------------------

class TradeManager:
    def __init__(self):
        self.active_trades = {}
        self.lock = threading.Lock()

    def add_trade(self, trade: Trade):
        with self.lock:
            self.active_trades[trade.trade_id] = trade
            print(f"[INFO] Trade {trade.trade_id} added.")

    def remove_trade(self, trade_id: str):
        with self.lock:
            if trade_id in self.active_trades:
                del self.active_trades[trade_id]
                print(f"[INFO] Trade {trade_id} removed.")

    def monitor_trades(self):
        while True:
            with self.lock:
                for trade_id, trade in list(self.active_trades.items()):
                    current_price = fetch_current_price(trade.token_address)  # Implement this function
                    self.evaluate_trade(trade, current_price)
            time.sleep(60)  # Wait for 1 minute before next check

    def evaluate_trade(self, trade: Trade, current_price: float):
        if trade.current_status != "OPEN":
            return

        pct_change = ((current_price - trade.entry_price) / trade.entry_price) * 100

        if pct_change <= -trade.stop_loss:
            print(f"[ALERT] Trade {trade.trade_id} hit stop-loss. Liquidating position.")
            self.liquidate_trade(trade, reason="STOP_LOSS")
            return

        for milestone in trade.milestones:
            if not milestone.is_sold and pct_change >= milestone.percentage_gain:
                sell_amount = trade.investment_amount * (milestone.percentage_gain / 100)
                self.execute_sell(trade, sell_amount, milestone)
                break

    def execute_sell(self, trade: Trade, amount: float, milestone: Milestone):
        success = execute_sell_order(trade.token_address, amount)
        if success:
            milestone.is_sold = True
            milestone.sold_amount = amount
            print(f"[INFO] Sold ${amount} of {trade.token_address} at milestone {milestone.percentage_gain}%.")

            if all(m.is_sold for m in trade.milestones):
                trade.update_status("COMPLETED")
                self.remove_trade(trade.trade_id)
                print(f"[INFO] Trade {trade.trade_id} completed.")

    def liquidate_trade(self, trade: Trade, reason: str):
        amount = trade.investment_amount
        success = execute_sell_order(trade.token_address, amount)
        if success:
            trade.update_status("STOPPED")
            self.remove_trade(trade.trade_id)
            print(f"[INFO] Trade {trade.trade_id} liquidated due to {reason}.")

# --------------------------------------------------
# 8) JUPITER API INTEGRATION
# --------------------------------------------------

def execute_buy_order(token_address: str, amount_usd: float) -> Optional[float]:
    payload = {
        "tokenAddress": token_address,
        "amountUSD": amount_usd,
        "wallet": PHANTOM_WALLET_ADDRESS
    }
    headers = {
        "Authorization": f"Bearer {JUPITER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{JUPITER_API_BASE_URL}/trade/buy", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        entry_price = data.get("executedPriceUSD")
        print(f"[SUCCESS] Bought {token_address} at ${entry_price} per token.")
        return entry_price
    except requests.RequestException as e:
        print(f"[ERROR] Buy order failed: {e}")
        return None

def execute_sell_order(token_address: str, amount_usd: float) -> bool:
    payload = {
        "tokenAddress": token_address,
        "amountUSD": amount_usd,
        "wallet": PHANTOM_WALLET_ADDRESS
    }
    headers = {
        "Authorization": f"Bearer {JUPITER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{JUPITER_API_BASE_URL}/trade/sell", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"[SUCCESS] Sold ${amount_usd} of {token_address}.")
        return True
    except requests.RequestException as e:
        print(f"[ERROR] Sell order failed: {e}")
        return False

# --------------------------------------------------
# 9) PHANTOM WALLET INTEGRATION
# --------------------------------------------------

from web3 import Web3

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Replace with actual Solana RPC URL
w3 = Web3(Web3.HTTPProvider(SOLANA_RPC_URL))

def get_wallet_balance():
    try:
        balance = w3.eth.get_balance(PHANTOM_WALLET_ADDRESS)
        return w3.fromWei(balance, 'ether')
    except Exception as e:
        print(f"[ERROR] Could not fetch wallet balance: {e}")
        return 0

# --------------------------------------------------
# 10) HELPER FUNCTIONS
# --------------------------------------------------

def fetch_current_price(token_address: str) -> float:
    """
    Fetch the current price of the token in USD.
    Implement this function based on your data source.
    """
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/solana/{token_address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data['price']['currentPrice'])  # Adjust based on actual response structure
        return price
    except Exception as e:
        print(f"[ERROR] Could not fetch current price for {token_address}: {e}")
        return 0.0

def calculate_investment_amount(total_budget: float, percentage: float) -> float:
    return (percentage / 100) * total_budget

def setup_trade(token_address: str, investment_percentage: float, total_budget: float, stop_loss: float) -> Optional[Trade]:
    investment_amount = calculate_investment_amount(total_budget, investment_percentage)
    entry_price = execute_buy_order(token_address, investment_amount)
    if entry_price:
        trade = Trade(
            token_address=token_address,
            entry_price=entry_price,
            investment_amount=investment_amount,
            purchase_levels=INVESTMENT_PERCENTAGES,
            stop_loss=stop_loss
        )
        return trade
    return None

# --------------------------------------------------
# 11) MAIN EXECUTION
# --------------------------------------------------

def main():
    trade_manager = TradeManager()
    monitoring_thread = threading.Thread(target=trade_manager.monitor_trades, daemon=True)
    monitoring_thread.start()

    final_list = advanced_filter_solana_tokens()

    total_budget = 305  # USD
    investment_percentages = [5, 10, 15, 20]

    for token in final_list:
        for pct in investment_percentages:
            investment_amount = calculate_investment_amount(total_budget, pct)
            if investment_amount > 0:
                trade = setup_trade(
                    token_address=token['tokenAddress'],
                    investment_percentage=pct,
                    total_budget=total_budget,
                    stop_loss=10  # Example: 10% stop-loss
                )
                if trade:
                    trade_manager.add_trade(trade)

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
