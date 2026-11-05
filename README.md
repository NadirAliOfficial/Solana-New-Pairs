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
<!-- updated: 2025-12-16-r01 -->

## Requirements

- Python 3
- `requests` library (used for HTTP calls to Dexscreener)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NadirAliOfficial/Solana-New-Pairs.git
   cd Solana-New-Pairs
   ```
2. Install the required Python package:
   ```bash
   pip install requests
   ```
   (If you prefer a virtual environment, create one before installing.)

## Usage

Run the desired script directly with Python. Example entry points:

- Fetch and display Solana token profiles:
  ```bash
  python solana_pair.py
  ```
- Run the full filtering pipeline:
  ```bash
  python data.py
  ```
- Execute the deep analysis module:
  ```bash
  python deep_analysis.py
  ```
- Test the API connectivity:
  ```bash
  python api_test.py
  ```
- Run the final aggregation script:
  ```bash
  python finaly.py
  ```

## Project Structure

- `api_test.py` – Simple script to call Dexscreener token‑profiles endpoint and print the raw response.
- `data.py` – Implements fetching of token profiles, pair data, and basic filtering based on volume, liquidity, and age.
- `deep_analysis.py` – Contains placeholder functions for holder distribution, liquidity lock checks, and scoring logic.
- `finaly.py` – (Large script) orchestrates the overall analysis workflow.
- `solana_pair.py` – Minimal script that fetches and prints Solana token profiles.
- `apis.txt` – List of API endpoints used by the project.
- `README.md` – Project documentation.
- `LICENSE` – MIT license for the project.
- `.env` – Environment file (currently not used by the code).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
