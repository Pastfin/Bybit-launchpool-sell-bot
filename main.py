import requests
import time
import hmac
import hashlib
import json
import uuid
import pandas as pd
from decimal import Decimal, ROUND_DOWN

class BybiyTokenSell:
    def __init__(self, api_key, api_secret, proxies, token_to_sell, base_endpoint, recv_window, base_precision):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxies = proxies
        self.token_to_sell = token_to_sell
        self.base_endpoint = base_endpoint
        self.recv_window = recv_window
        self.base_precision = base_precision

    def get_actual_timestamp(self):
        response = requests.get(f'{self.base_endpoint}/market/time')
        return str(response.json()['time'])

    def generate_headers(self, params):
        time_stamp = self.get_actual_timestamp()
        signature = self.gen_signature(params, time_stamp)
        return {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': time_stamp,
            'X-BAPI-RECV-WINDOW': self.recv_window,
            'Content-Type': 'application/json'
        }

    def gen_signature(self, query, time_stamp):
        param_str = time_stamp + self.api_key + self.recv_window + query
        hash = hmac.new(bytes(self.api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
        signature = hash.hexdigest()
        return signature

    def get_balance(self, account_type):
        url = f'{self.base_endpoint}/asset/transfer/query-account-coins-balance?coin={self.token_to_sell}&accountType={account_type}'
        headers = self.generate_headers(f"coin={self.token_to_sell}&accountType={account_type}")
        response = requests.get(url, headers=headers, proxies=self.proxies).json()
        try:
            balance = float(response['result']['balance'][0]['transferBalance'])
            return balance
        except Exception as e:
            print(f"Error getting balance for public_key {self.api_key}: {e}")
            return 0
    
    def transform_token_balance_amount(self, spot_balance):
        precision_decimal = Decimal(self.base_precision)
        rounded_balance = Decimal(str(spot_balance)).quantize(precision_decimal, rounding=ROUND_DOWN)
        return float(rounded_balance)

    def transfer_to_unified(self):
        token_balance = self.get_balance("FUND")

        if token_balance == 0:
            return 0

        transfer_id = uuid.uuid4().hex
        params = json.dumps({
            "transferId": transfer_id,
            "coin": self.token_to_sell,
            "amount": str(token_balance),
            "fromAccountType": "FUND",
            "toAccountType": "UNIFIED"
        })

        url = f'{self.base_endpoint}/asset/transfer/inter-transfer'
        headers = self.generate_headers(params)
        response = requests.post(url, headers=headers, data=params, proxies=self.proxies).json()

        if response.get('retMsg') == 'success':
            print(f'{self.token_to_sell} transferred successfully for public_key {self.api_key}, amount: {token_balance}')
            return token_balance
        else:
            return 0

    def sell_token(self):
        token_amount = self.transfer_to_unified()
        
        if token_amount == 0:
            print(f'Token amount 0 or error occurred while transferring for public_key {self.api_key}.')
            return
        
        spot_balance = self.get_balance("UNIFIED")
        if spot_balance == 0:
            print(f'No balance available for selling for public_key {self.api_key}.')
            return

        url = f'{self.base_endpoint}/order/create'
        order_link_id = uuid.uuid4().hex
        amount_to_sell = self.transform_token_balance_amount(spot_balance)
        if amount_to_sell == 0:
            print(f'Too small a balance to sell the token for public_key {self.api_key}.')
            return

        params = f'{{"category":"spot","symbol": "{self.token_to_sell}USDT","side": "Sell","positionIdx": 0,"orderType": "Market","qty": "{amount_to_sell}","timeInForce": "GTC","orderLinkId": "{order_link_id}"}}'

        headers = self.generate_headers(params)
        response = requests.post(url, headers=headers, data=params, proxies=self.proxies).json()

        if response.get('retMsg') == 'OK':
            print(f'{self.token_to_sell} was sold for public_key {self.api_key}: {amount_to_sell}')
        else:
            print(f'Error selling {self.token_to_sell} for public_key {self.api_key}: {response.get("retMsg")}')
    
    def test_proxy(self):
        try:
            response = requests.get('http://www.google.com', proxies=self.proxies, timeout=10)
            if response.status_code == 200:
                return True
            else:
                return False
        except:
            return False


if __name__ == "__main__":
    token_to_sell = "".upper() ### Example: token_to_sell = "CATS".upper()

    recv_window = str(5000)
    base_endpoint = 'https://api.bybit.com/v5'

    precision_endpoint = f'{base_endpoint}/market/instruments-info?category=spot&symbol={token_to_sell}USDT'
    base_precision = requests.get(precision_endpoint).json()["result"]["list"][0]["lotSizeFilter"]["basePrecision"]
    
    df = pd.read_excel('bybit_keys.xlsx')
    proxy_list = []

    for index, row in df.iterrows():
        proxies = {
            "http": row['Proxy'],
            "https": row['Proxy']
        }

        bot = BybiyTokenSell(row['api_key'], row['api_secret'], proxies, token_to_sell, base_endpoint, recv_window, base_precision)
        
        if not bot.test_proxy():
            print(f"Proxy not working for public_key {row['api_key']}: {proxies}")
            continue

        bot.sell_token()

        time.sleep(1)