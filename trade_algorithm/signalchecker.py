import datetime
import logging
import pandas as pd
import talib as ta

import bitflyer
import settings
import tools


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('trade.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s  %(asctime)s  [%(name)s] %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

class Ema():
    def __init__(self, price_df, period_short, period_long):
        self.API = bitflyer.APIClient(settings.api_key, settings.api_secret, settings.base_url)
        self.trade_duration = settings.trade_duration
        self.price_df = price_df
        self.period_short = min(period_short, period_long)
        self.period_long = max(period_short, period_long)    #period_shortを短期足，period_longを長期足に設定.
        self.latest_short_ema_value = self.get_ema(self.period_short).iloc[-1]   #最新のemaの値。
        self.latest_long_ema_value = self.get_ema(self.period_long).iloc[-1]


    #指定した期間でのEMAのデータをデータフレーム形式で返す関数。    
    def get_ema(self, period):
        price_df = self.API.get_price(self.trade_duration)
        return ta.EMA(price_df.Close, timeperiod=period)
    
    def update_ema(self):
        self.former_short_ema_value = self.latest_short_ema_value
        self.former_long_ema_value = self.latest_long_ema_value
        self.latest_short_ema_value = self.get_ema(self.period_short).iloc[-1]
        self.latest_long_ema_value = self.get_ema(self.period_long).iloc[-1]


    @property
    def ema_signal(self):

        #former_short_ema_value = self.latest_short_ema_value
        #former_long_ema_value = self.latest_long_ema_value
        #self.latest_short_ema_value = self.get_ema(self.period_short).iloc[-1]
        #self.latest_long_ema_value = self.get_ema(self.period_long).iloc[-1]
        self.update_ema()
        #print(self.former_short_ema_value, self.former_long_ema_value, self.latest_short_ema_value, self.latest_long_ema_value)


        if self.former_short_ema_value < self.former_long_ema_value and self.latest_short_ema_value > self.latest_long_ema_value:  #ゴールデンクロスのチェック
            #ema_signal = 1
            tools.write_csv(settings.signal_history, [datetime.datetime.today(),"buy signal"])
            logging.info(f"date:{datetime.datetime.today()}:buy signal")
            return 1

        elif self.former_short_ema_value > self.former_long_ema_value and self.latest_short_ema_value < self.latest_long_ema_value:  #デッドクロスのチェック
            #ema_signal = -1
            tools.write_csv(settings.signal_history, [datetime.datetime.today(),"sell signal"])
            logging.info(f"date:{datetime.datetime.today()}:sell signal")
            return -1

        else:
            #ema_signal = 0
            return 0


class Signals():
    def __init__(self, price_df):
        self.ema = Ema(price_df, settings.ema_short, settings.ema_long)
        self.buy_signal = False
        self.sell_signal = False

    def check_signals(self):
        if self.ema.ema_signal == 1:
            self.buy_signal = True
        if  self.ema.ema_signal == -1:
            self.sell_signal = True

