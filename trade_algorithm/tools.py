#import csv
#import requests
#import settings
#from typing import List

import csv
import os
import requests
import sys
#sys.path.append(os.path.abspath("../"))
sys.path.append("../")

import settings
from typing import List


def write_csv(file_name: str, content: List):
    with open(file_name, 'a', newline='') as f: 
        # Pass the CSV  file object to the writer() function
        writer_object = csv.writer(f)
        # Result - a writer object
        # Pass the data in the list as an argument into the writerow() function
        writer_object.writerow(content)

#複数の通貨の残高を要素として持つリストから，特定の資産(JPYとかBTCとか)を抽出する関数
def get_each_balance(balance:List, currency:str):
    target_balance = next(x for x in balance if x["currency_code"] == currency)
    target_balance = target_balance["amount"]
    return target_balance

#LINEにメッセージを通知する関数
def line_notify(text):
	url = "https://notify-api.line.me/api/notify"
	data = {"message": text}
	headers = {"Authorization": "Bearer " + settings.line_token} 
	requests.post(url, data=data, headers=headers)
