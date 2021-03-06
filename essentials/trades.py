import numpy as np
import pandas as pd

from datetime import time
from datetime import datetime
from datetime import timezone

from typing import List, Optional
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

        return self.order

    def instrument(self, symbol: str, quantity: int, asset_type: str, sub_asset_type: str = None, order_leg_id: int = 0) -> dict:

        leg = self.order['orderLegCollection'][order_leg_id]

        leg['instrument']['symbol'] = symbol
        leg['instrument']['asset_type'] = asset_type
        leg['quantity'] = quantity

        self.order_size = quantity
        self.symbol = symbol
        self.asset_type = asset_type

        return leg

    def good_till_cancel(self, cancel_time: datetime) -> None:

        self.order['duration'] = 'GOOD_TILL_CANCEL'
        self.order['cancelTime'] = cancel_time.isoformat()

    def modify_side(self, side: Optional[str], order_leg_id: int = 0) -> None:

        if side and side not in ['buy', 'sell', 'sell_short', 'but_to_cover']:
            raise ValueError("You passed through an invalid side.")

        if side:
            self.side['orderLegCollection'][order_leg_id]['instructions'] = side.upper()
        else:
            self.order['orderLegCollection'][order_leg_id]['instructions'] = self.order_instructions[self.enter_or_exit][self.side_opposite]

    def add_box_range(self, profit_size: float = 0.00, percentage: bool = False, stop_limit: bool = False):
        if not self._trigger_added:
            self._convert_to_trigger()

        self.add_take_profit(profit_size=profit_size, percentage=percentage)

        if not stop_limit:
            self.add_stop_loss(stop_size=profit_size, percentage=percentage)

    def add_stop_loss(self, stop_size: float, percentage: bool = False) -> bool:

        if not self._trigger_added:
            self._convert_to_trigger()

        if self.order_type == 'mkt':
            pass
        elif self.order_type == 'lmt':
            price = self.price

        if percentage:
            adjustment = 1.0 - stop_size
            new_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=True)
        else:
            adjustment = stop_size
            new_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=False)

        stop_loss_order = {
            "order_type": "STOP",
            "session": "NORMAL",
            "duration": "DAY",
            "stopPrice": new_price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {
                        "symbol": self.symbol,
                        "assetType": self.asset_type
                    }
                }
            ]
        }

        self.add_stop_loss = stop_loss_order
        self.order['childOrderStrategies'].append(self.stop_loss_order)

        return True

    def add_stop_limit(self, stop_size: float, limit_size: float, stop_percentage: bool = False, limit_percentage: bool = False) -> bool :

        if not self._trigger_added:
            self._convert_to_trigger()

        if self.order_type == 'mkt':
            pass
        elif self.order_type == 'lmt':
            price = self.price

        if stop_percentage:
            adjustment = 1.0 - stop_size
            stop_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=True)
        else:
            adjustment = stop_size
            stop_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=False)

        if limit_percentage:
            adjustment = 1.0 - limit_size
            limit_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=True)
        else:
            adjustment = limit_size
            limit_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=False)

        stop_limit_order = {
            "order_type": "STOP_LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": limit_price,
            "stopPrice": stop_price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {
                        "symbol": self.symbol,
                        "assetType": self.asset_type
                    }
                }
            ]
        }

        self.stop_limit_order = stop_limit_order
        self.order['childOrderStrategies'].append(self.stop_limit_order)

        return True

    def _calculate_new_price(self, price: float, adjustment: float, percentage: bool) -> float:
        """
        :param price: This is the price which should be re calculated
        :param adjustment: The adjustment to made
        :param percentage: This determiens wheter the adjustment are of
        a percentage stake or just simply an addition / subtraction of the price.
        :return: float new_price
        """
        if percentage:
            new_price = price * adjustment
        else:
            new_price = price + adjustment

        if new_price < 1:
            new_price = round(new_price, 4)
        else:
            new_price = round(new_price, 2)

        return new_price

    def add_take_profit(self, profit_size: float, percentage: bool = False) -> bool:

        if not self._triggered_added:
            self._convert_to_trigger()

        if self.order_type == 'mkt':
            pass
        elif self.order_type == 'lmt':
            price = self.price

        if percentage:
            # The adjustment will be based on a percentage.
            adjustment = 1.0 - profit_size
            profit_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=True)
        else:
            # The adjustment will be plain
            adjustment = profit_size
            profit_price = self._calculate_new_price(price=price, adjustment=adjustment, percentage=False)

        take_profit_order = {
            "order_type": "LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": profit_price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {
                        "symbol": self.symbol,
                        "assetType": self.asset_type
                    }
                }
            ]
        }

        # Add the order.
        self.take_profit_order = take_profit_order
        self.order['childOrderStrategies'].append(self.take_profit_order)

        return True

    def _convert_to_trigger(self):

        if self.order and self._trigger_added == False:
            self.order['orderStrategyType'] = 'TRIGGER'
            self.order['childOrderStrategies'] = []
            self._trigger_added = True

    def modify_session(self, session: str) -> None:
        #TODO: This might not be needed when trading with bitcoin.
        if session in ['am', 'pm', 'normal', 'seamless']:
            self.order['session'] = session.upper()
        else:
            raise ValueError("Invalid session")

    @property
    def order_response(self) -> dict:

        return self._order_response

    @order_response
    def order_response(self, order_response_dict: dict) -> None:

        self._order_response = order_response_dict

    def _generate_order_id(self) -> str:

        if self.order:

            order_id = "{symbol}_{side}_{enter _or_exit}_{timestamp}"
            order_id = order_id.format(
                symbol=self.symbol,
                side=self.side,
                enter_or_exit=self.enter_or_exit,
                timestamp=datetime.now().timestamp()
            )

            return order_id

        else:

            return ""

    def add_leg(self, order_leg_id: int, symbol: str, quantity: int, asset_type: str, sub_asset_type: str=None) -> List[Dict]:

        # Define the leg
        leg = {}
        leg['instrument']['symbol'] = symbol
        leg['instrument']['assetType'] = asset_type
        leg['quantity'] = quantity

        if sub_asset_type:
            leg['instrument']['subAssetType'] = sub_asset_type

        if order_leg_id == 0:
            self.instrument(
                symbol=symbol,
                asset_type=asset_type,
                quantity=quantity,
                sub_asset_type=sub_asset_type,
                order_leg_id=0
            )
        else:
            order_leg_collection: list = self.order['orderLegCollection']
            order_leg_collection.insert(order_leg_id, leg)

        return self.order['orderLegCollection']




