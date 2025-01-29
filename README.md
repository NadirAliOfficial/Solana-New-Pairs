# Solana-New-Pairs

## Description

**Solana-New-Pairs** is a Python-based tool designed to monitor and analyze new token pairs on the Solana blockchain using the Dexscreener API. It performs advanced filtering based on liquidity, transaction count, holder distribution, and historical performance data to identify promising and legitimate tokens for potential investment or trading strategies.

## Features

- **Fetch Latest Solana Token Profiles**
  - Retrieves the most recent token profiles specific to the Solana blockchain from Dexscreener.

- **Advanced Filtering**
  - **Minimum Liquidity Requirements:** Ensures tokens have sufficient liquidity to support trading activities.
  - **Transaction Count:** Filters tokens based on the number of transactions to gauge activity levels.
  - **Holder Distribution:** Identifies tokens where top holders possess less than 30% of the total supply, reducing the risk of large holder manipulation.
  - **Liquidity Lock Verification:** Confirms that a token's liquidity is locked to prevent rug pulls and ensure project credibility.

- **Historical Data Integration**
  - Incorporates historical performance data to refine coin selection strategies.
  - Establishes weighted scoring metrics based on transaction count, volume, and liquidity for effective token ranking.

- **Scoring and Ranking**
  - Computes a comprehensive score for each token to prioritize investments based on multiple criteria.
