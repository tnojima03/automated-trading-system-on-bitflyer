import datetime
import decimal
import hashlib
import hmac
import json
import logging
import os
import pandas as pd
import sys
import requests
import time
#sys.path.append(os.path.abspath("../"))
sys.path.append("../")
#sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

import settings
import states
import tools


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('trade.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s  %(asctime)s  [%(name)s] %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


class Balance():
	def __init__(self):
		self.API = APIClient(settings.api_key, settings.api_secret, settings.base_url)

	@property
	def balance_list(self):
		return self.API.get_balance()

	@property
	def jpy(self):
		return tools.get_each_balance(self.balance_list,"JPY")

	@property
	def btc(self):
		return tools.get_each_balance(self.balance_list,"BTC")
	
	@property
	def total_balance(self):
		current_btc_price = self.API.get_latest_price() #現在のBTC価格
		return self.jpy + self.btc * current_btc_price  #日本円+BTC

	def record_balance(self):
		date = datetime.datetime.today()
		new_balance = [date, self.total_balance, self.jpy, self.btc]
		tools.write_csv(settings.balance_history, new_balance)


class APIClient():
	def __init__(self, api_key, api_secret, base_url):
		self.api_key = api_key
		self.api_secret = api_secret
		self.base_url = base_url

	#HTTPヘッダを構成
	def header(self, method: str, path: str, body: str) -> dict:
		timestamp = str(datetime.datetime.today())
		if body == '':
			message = timestamp + method + path
		else:
			message = timestamp + method + path + body
		signature = hmac.new(bytearray(self.api_secret.encode('utf-8')), message.encode('utf-8') , digestmod = hashlib.sha256 ).hexdigest()

		headers = {
		'ACCESS-KEY' : self.api_key,
			'ACCESS-TIMESTAMP' : timestamp,
			'ACCESS-SIGN' : signature,
			'Content-Type' : 'application/json'
		}
		return headers

	#指定した足での価格情報を得てdataframe形式で返す
	def get_price(self, minute):
		while True:
			try:
				response = requests.get(f"https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc?periods={str(minute)}")
				response = response.json()
				break
			except requests.exceptions.RequestException as e:
				logger.info("Cryptowatchの価格取得でエラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)

		# ローソク足の情報を取り出す
		price_data = response["result"][str(minute)]

		#日時をUNIX時間から変換(世界標準時UTC)
		for item in price_data:
			uni_time = item[0]
			item[0] = datetime.datetime.fromtimestamp(uni_time)  

		price_df = pd.DataFrame(price_data,columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume ', 'Quote Volume'])
		del price_df["Quote Volume"]  #不要な列削除
	    #mplでロウソク表示するためにはindexはDataTimeIndexでなければならない
		price_df.set_index('Date', inplace=True)

		return price_df

	#現在の注文状況を取得する関数
	def get_order(self):
		path = "/v1/me/getchildorders"
		method = "GET"
		headers = self.header(method=method, path=path,body="")
	    
		while True:
			try:
				response = requests.get(self.base_url+path , headers=headers)
				break
			except requests.exceptions.RequestException as e:
				logger.info("現在の注文状況取得でエラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)

		return response.json()[0]

	#現在の資産を取得する関数
	def get_balance(self):
		path = "/v1/me/getbalance"
		method = "GET"
		headers = self.header(method=method, path=path, body="")

		while True:
			try:
				response = requests.get(self.base_url + path , headers = headers)
				response = response.json()
				break
			except requests.exceptions.RequestException as e:
				logger.info("現在の資産取得でエラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)
		return response
	            
	#手数料を確認
	def get_commission(self):
		path = f"/v1/me/gettradingcommission?product_code={settings.product_code}"
		method = "GET"
		headers = self.header(method=method,path=path,body="")
	    
		while True:
			try:
				response = requests.get(self.base_url + path , headers = headers)
				response = response.json()
				break
			except requests.exceptions.RequestException as e:
				logger.info("手数料取得でエラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)
	        
		commission_rate = response["commission_rate"]
	    
		return commission_rate

	#最新のBTCの約定価格(最新のBTC価格)を取得
	def get_latest_price(self):
		while True:
			try:
				response = requests.get(f"https://api.bitflyer.jp/v1/getticker?product_code={settings.product_code}")
				response = response.json()
				break
			except requests.exceptions.RequestException as e:
				logger.info("手数料取得でエラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)
		current_price = response["ltp"]
	    
		return current_price

	def send_order(self, side:str):
		#取引量の計算
		price = self.get_latest_price()  #最新の約定価格で注文を出す.
		balance = self.get_balance() #現在の資産状況を取得
		commission_rate = self.get_commission()
		if side == "BUY":
			jpy = tools.get_each_balance(balance, "JPY") #日本円の9割分のBTCを買うために，保有する日本円を取得．
			size = jpy / price   #保有する日本円は何BTC分か
		else:
			size = tools.get_each_balance(balance, "BTC")

		#手数料分だけ売り/買い量を減じる
		#0.00000001 BTC単位でしか取引できないので，0.00000001の倍数になるようにする．
		#jsonはdecimalに対応していないので，最後にfloat型に変換．
		size = float(decimal.Decimal(str((size * (1 - commission_rate)// settings.satoshi))) * decimal.Decimal(str(settings.satoshi)))
	    

		method = 'POST'
		path = '/v1/me/sendchildorder'
		body = json.dumps({
			'product_code': settings.product_code,
			'child_order_type': 'LIMIT',
			'side': side,
			'price': price,
			'size': size, 
			})
			#'minute_to_expire': 10,})

		headers = self.header(method=method, path=path, body=body)

		while True:
			try:
				response = requests.post(self.base_url + path , data = body , headers = headers)
				logger.info(response.json())

				if response.status_code == 200:
					is_order = True
					states.update_is_order(is_order)
					logger.info(f"Sent {side} order. Response code: {response.status_code}")
					break
			except requests.exceptions.RequestException as e:
				logger.info(f"{side}注文で通信エラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)

		order_info = {"status_code":response.status_code, "side":side, "price":price, "amount":size}

		#注文の反映待ち(?).これがないとすぐにprocess_orderが終了してしまう．
		time.sleep(10)

		return order_info

	#未約定の注文をキャンセルする関数
	def cancel_order(self):
		#キャンセルする注文のidを取得
		response = self.get_order()
		order_id = response['child_order_acceptance_id']

		method = 'POST'
		path = '/v1/me/cancelchildorder'
		body = json.dumps({
			'product_code': settings.product_code,
			'child_order_acceptance_id': order_id,
			})

		headers = self.header(method=method, path=path, body=body)
	    
		while True:
			try:
				response = requests.post(self.base_url + path, data = body, headers = headers)
				is_order = False
				states.update_is_order(is_order)
				logger.info("Canceled order.")
				break
			except requests.exceptions.RequestException as e:
				logger.info("注文キャンセルでエラー発生 : ",e)
				logger.info("10秒後にやり直します")
				time.sleep(10)