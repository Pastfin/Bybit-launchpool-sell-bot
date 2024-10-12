# Bybit Launchpool Sell Bot

The script helps sell all the tokens that come in during Launchpool to the Funding account. Thus, you don't need to log in to a large number of accounts manually, but just run the script.
## Code Logic:

1. Transfers all specified tokens from Funding to Unified Trading.
2. Retrieves information about the specified token and its balance on Unified Trading. If tokens were previously present on Unified Trading, it will also be sold.
3. Sells the maximum amount of specified tokens at the market price on spot trading.

## Quick Start:

1. Clone the repository:

   ```bash
   git clone https://github.com/Pastfin/Bybit-launchpool-sell-bot
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create API keys in your Bybit accounts with full rights.

4. Put API keys in a file named `bybit_keys.xlsx`. Columns:

   - **api_key** (required)
   - **api_secret** (required)
   - **Proxy** (required) - Format: `http://{user_name}:{password}@{ip}:{port}`
   - **Acc** (optional for your usage)

5. Open the file `main.py` and edit the `token_to_sell` variable which is located at the very bottom of the code (line 124). Write your token that you want to sell after Launchpool credited it to the Funding account. Example: `Example: token_to_sell = "CATS".upper()`.

6. Run the script:

   ```bash
   python3 main.py
   ```
