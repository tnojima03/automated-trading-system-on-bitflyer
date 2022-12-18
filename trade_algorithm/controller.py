import csv
import datetime
import logging
import os
import sys
import time
#sys.path.append(os.path.abspath(".."))
sys.path.append("../")

import bitflyer
import settings
import states
import tools
import signalchecker

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('trade.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s  %(asctime)s  [%(name)s] %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


class TradeController():
	def __init__(self, trade_duration, check_loss_limit_duration, loss_limit_percentage, 
				trade_history, balance_history):
		self.API = bitflyer.APIClient(settings.api_key, settings.api_secret, settings.base_url)
		self.balance = bitflyer.Balance()
		self.trade_duration = trade_duration
		self.check_loss_limit_duration = check_loss_limit_duration
		self.loss_limit_percentage = loss_limit_percentage
		self.trade_history = trade_history
		self.balance_history = balance_history
		self.ema = signalchecker.Ema(self.API.get_price(self.trade_duration), settings.ema_short, settings.ema_long)
		

	#ポジションを持っている間，BTC価格をチェック．BTCが購入時の90%を切ったら，強制的に売却する
	def check_ninety(self):
		while True:
			if states.is_position:
				#購入時のBTCの価格をチェック
				response = self.API.get_order()
				order_price = response['price']
				current_price = self.API.get_latest_price()
				if current_price < order_price * self.loss_limit_percentage:
					order_info = self.API.send_order("SELL")
					self.accept_order(order_info)
				logger.info(f"Checking {self.loss_limit_percentage*100}%")
				time.sleep(self.check_loss_limit_duration)

	#トレードの履歴を記録
	def record_trade(self, date, side, price, amount, profit):
		new_trade = [date, side, price, amount, profit]
		tools.write_csv(self.trade_history, new_trade)

    #注文が約定したかを5秒おきに確認し，約定した場合取引履歴に記録する関数
	def process_order(self, order_info:dict):
		ORDER_CHECK_INTERVAL = 5	#約定したかどうかを確認する間隔(秒)
		TIME_TO_CANCEL = 1200	#この秒数を経過しても約定していない場合，注文をキャンセル．
		elapsed_time = 0			#注文時点からの経過時間

		side = order_info["side"]
		price = order_info["price"]
		amount = order_info["amount"]
		while states.is_order:
			response = self.API.get_order()
			if response["child_order_state"] == "COMPLETED": 
				if side == "BUY":
					states.update_is_order(False)
					states.update_is_position(True)
				if side == "SELL":
					states.update_is_order(False)
					states.update_is_position(False)

				#約定した場合，取引履歴(trade_history.csv)に新たな取引を記録
				
				date = datetime.datetime.today()
				#売り注文の場合は利益を計算
				if side == "SELL":
					with open(settings.trade_history) as f: #前回の買い注文価格を取得
						reader = csv.reader(f)
						l = [row for row in reader]
						latest_ordered_price = float(l[-1][2])  #前回の注文価格
						latest_ordered_amount = float(l[-1][3]) #前回の注文量
						profit = price * amount - latest_ordered_price * latest_ordered_amount
				else:
					profit = ""
				#約定した注文を約定履歴に記録
				self.record_trade(date=date, side=side,
											price=price, amount=amount, profit=profit)
				logger.info(f"約定(Date:{date}, Side:{side}, Price:{price}, Amount:{amount}, Profit:{profit})")
				logger.info("Finished to process order")
				logger.info(f"is_order:{states.is_order}, is_position:{states.is_position}")
				tools.line_notify(f"約定(Date:{date}, Side:{side}, Price:{price}, Amount:{amount}, Profit:{profit})")

			time.sleep(ORDER_CHECK_INTERVAL)
			#注文が一定時間約定しなければ，注文をキャンセルする．
			elapsed_time += ORDER_CHECK_INTERVAL
			if elapsed_time >= TIME_TO_CANCEL:
				self.API.cancel_order()

	#1時間に１度チャートチェック
	def trade_controller(self):
		while True:
			#まず市場分析
			price_df = self.API.get_price(self.trade_duration)  #価格データを取得
			ema_signal = self.ema.ema_signal #update ema signals
			
			#売りシグナル/買いシグナルを確認(EMA)
			if ema_signal == 1:
				buy_signal = True
			elif ema_signal == -1:
				sell_signal = True
			else:
				buy_signal = False
				sell_signal = False
			#トレード
			if not states.is_position and buy_signal:  #ポジションがなく，買いシグナルが出ている場合買う．
				order_info = self.API.send_order("BUY")
				self.process_order(order_info)
			elif states.is_position and not sell_signal:  #ポジションがあり，売りシグナルが出ている場合売る
				order_info = self.API.send_order("SELL")
				self.process_order(order_info)

			#現在の残高をcsvファイルに出力
			self.balance.record_balance()
			print("To stop the system, press c and Enter.")
			print(f"{datetime.datetime.today()}:Read the chart.")
			
			time.sleep(self.trade_duration)