import operator
import numpy as np
import pandas as pd

from typing import List, Tuple
from typing import Dict
from typing import Union
from typing import Optional

from essentials.stock_frame import StockFrame


class Indicator:
    def __init__(self, price_data_frame: StockFrame) -> None:

        self._stock_frame: StockFrame = price_data_frame
        self._price_groups = price_data_frame.symbol_groups
