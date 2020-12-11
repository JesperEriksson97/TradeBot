# From here we run the robot.
import os
import time as true_time
import pprint
import pathlib
import operator
import pandas as pd

from datetime import datetime
from datetime import timedelta
from configparser import ConfigParser

from robot import Robot
from essentials.indicators import Indicators

api_key = os.environ.get("BINANCE_PUBLIC_KEY")
api_secret = os.environ.get("BINANCE_PRIVATE_KEY")

robot = Robot()
