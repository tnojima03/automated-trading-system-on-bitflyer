import configparser
import os


conf = configparser.ConfigParser()
path = os.path.join(os.path.dirname(__file__), 'settings.ini')
conf.read(path, "UTF-8")

api_key = conf["API"]["api_key"]
api_secret = conf["API"]["api_secret"]
line_token = conf["API"]["line_token"]
base_url = conf["API"]["base_url"]

satoshi = float(conf["BTC"]["satoshi"])

trade_duration = int(conf["trade"]["trade_duration"])
check_loss_limit_duration = int(conf["trade"]["check_loss_limit_duration"])
product_code = conf["trade"]["product_code"]
loss_limit_percentage = float(conf["trade"]["loss_limit_percentage"])
use_percentage = float(conf["trade"]["use_percentage"])

ema_short = int(conf["chart"]["EMA_short"])
ema_long = int(conf["chart"]["EMA_long"])

trade_history = conf["history_file"]["trade_history"]
balance_history = conf["history_file"]["balance_history"]
signal_history = conf["history_file"]["signal_history"]


