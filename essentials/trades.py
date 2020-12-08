import numpy as np
import pandas as pd

from datetime import time
from datetime import datetime
from datetime import timezone

from typing import List
from typing import Dict
from typing import Union

from pandas.core.groupby import DataFrameGroupBy
from pandas.core.window import RollingGroupby


class Trade:

    def __init__(self):

        self.order = {}
        self._order_response = {}

        self._trigger_added = False
        self._multi_leg = False

        # For identification
        self._trade_id = ""

        # Long or short
        self.side = ""

        # Opposite of the side chosen in self.side
        self.side_opposite = ""

        # Enter or exit a position
        self.enter_or_exit = ""

        # Opposite of the enter exit value
        self.enter_or_exit_opposite = ""

    def new_trade(self, trade_id: str, order_type: str, side: str, enter_or_exit: str, price: float = 0.0, stop_limit_price: float = 0.0) -> dict:

        self.trade_id = trade_id
        self.order_types = {
            'mkt': 'MARKET',
            'lmt': 'LIMIT',
            'stop': 'STOP',
            'stop_lmt': 'STOP_LIMIT',
            'trailing_stop': 'TRAILING_STOP'
        }

        self.order_instructions = {
            'enter': {
                'long': 'BUY',
                'short': 'SELL_SHORT'
            },
            'exit': {
                'long': 'SELL',
                'short': 'BUY_TO_COVER'
            }
        }

        self.order = {
            'orderStrategyType': "SINGLE",
            'orderType': self.order_types[order_type],
            'session': 'NORMAL',
            'duration': 'DAY',
            'orderLegCollection': [
                {
                    'instruction': self.order_instructions[enter_or_exit][side],
                    'quantity': 0,
                    'instrument': {
                        'symbol': None,
                        'assetType': None
                    }

                }
            ]

        }

        if self.order['orderType'] == 'STOP':
            self.order['stopPrice'] = price

        elif self.order['orderType'] == 'LIMIT':
            self.order['price'] = price

        elif self.order['orderType'] == 'STOP_LIMIT':
            self.order['stopPrice'] = price
            self.order['price'] = stop_limit_price

        elif self.order['orderType'] == 'TRAILING_STOP':
            self.order['stopPriceLinkBasis'] = ''
            self.order['stopPriceLinkType'] = ''
            self.order['stopPriceOffset'] = 0.00
            self.order['stopType'] = 'STANDARD'

        self.enter_or_exit = enter_or_exit
        self.side = side
        self.order_type = order_type
        self.price = price

        # Store important info for use later.
        if order_type == 'stop':
            self.stop_price = price
        elif order_type == 'stop-lmt':
            self.stop_price = price
            self.stop_limit_price = stop_limit_price
        else:
            self.stop_price = 0.0

        if self.enter_or_exit == 'enter':
            self.enter_or_exit_opposite = 'exit'
        elif self.enter_or_exit == 'exit':
            self.enter_or_exit_opposite = 'enter'

        if self.side == 'long':
            self.side_opposite = 'short'
        elif self.side == 'short':
            self.side_opposite = 'long'





