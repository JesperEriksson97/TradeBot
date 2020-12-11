import pandas as pdb

from binance.client import Client

from datetime import datetime
from datetime import time
from datetime import timezone

import os
from os.path import join, dirname
from dotenv import load_dotenv

from typing import List
from typing import Dict
from typing import Union

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path, verbose=True)


class Robot:
    def __init__(self,
                 client_id: str,
                 redirect_uri: str,
                 credentials_path: str = None,
                 trading_account: str = None)\
                 -> None:

        print("Initiating...")

        self.trading_account: str = trading_account
        self.client_id: str = client_id
        self.credentials_path: str = credentials_path
        self.redirect_uri: str = redirect_uri
        self.trades: dict = {}
        self.historical_prices: dict = {}
        self.stock_frame = None

        client = self._create_client(self)

        depth = client.get_order_book(symbol='BNBBTC')
        print(depth)

    def _create_client(self) -> Client:
        api_key = os.environ.get("BINANCE_PUBLIC_KEY")
        api_secret = os.environ.get("BINANCE_PRIVATE_KEY")
        client = Client(api_key, api_secret)
        return client

    @property
    def pre_market_open(self) -> bool:
        pre_market_start_time = datetime.now().replace(hour=12, minute=00, second=00, tzinfo=timezone.utc).timestamp()
        market_start_time = datetime.now().replace(hour=13, minute=30, second=00, tzinfo=timezone.utc).timestamp()
        right_now = datetime.now().replace(tzinfo=timezone.utc).timestamp()

        if market_start_time >= right_now >= pre_market_start_time:
            return True
        else:
            return False

    @property
    def post_market_open(self) -> bool:
        post_market_end_time = datetime.now().replace(hour=22, minute=30, second=00, tzinfo=timezone.utc).timestamp()
        market_end_time = datetime.now().replace(hour=20, minute=00, second=00, tzinfo=timezone.utc).timestamp()
        right_now = datetime.now().replace(tzinfo=timezone.utc).timestamp()

        if post_market_end_time >= right_now >= market_end_time:
            return True
        else:
            return False

    @property
    def regular_market_open(self) -> bool:
        market_start_time = datetime.now().replace(hour=13, minute=30, second=00, tzinfo=timezone.utc).timestamp()
        market_end_time = datetime.now().replace(hour=20, minute=00, second=00, tzinfo=timezone.utc).timestamp()
        right_now = datetime.now().replace(tzinfo=timezone.utc).timestamp()

        if market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False

    def create_portfolio(self):
        pass

    def create_trade(self):
        pass

    def create_stock_frame(self):
        pass

    def grab_current_quotes(self) -> dict :
        pass

    def grab_historical_prices(self) -> List[Dict] :
        pass



