import logging
import os
import sys
import threading
import time
#sys.path.append(os.path.abspath("../"))
sys.path.append("../")

import bitflyer
import settings
import tools
from controller import TradeController


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('trade.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s  %(asctime)s  [%(name)s] %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

settings_dict = {
    "trade_duration": settings.trade_duration,
    "check_loss_limit_duration": settings.check_loss_limit_duration,
    "loss_limit_percentage": settings.loss_limit_percentage,
    "trade_history": settings.trade_history,
    "balance_history": settings.balance_history
}

#threadingはCTRL+Cで止められないようなので，"c+Enter"で止める関数を用意する．
#参考：https://qiita.com/KjumanEnobikto/items/ae9458d0be283db1887b
def listen_keyboard():
    while True:
        n = input()
        if n == "c":
            print("Finished by KeyboardInterrupt")
            logger.info("Finished by KeyboardInterrupt")
            sys.exit()

if __name__ == "__main__":
    trade_controller = TradeController(**settings_dict)
    t1 = threading.Thread(target=trade_controller.trade_controller)
    t2 = threading.Thread(target=trade_controller.check_ninety)

    # # デーモン化(参考：https://qiita.com/KjumanEnobikto/items/ae9458d0be283db1887b)
    t1.setDaemon(True)
    t2.setDaemon(True)

    t1.start()
    t2.start()
    
    logger.info("Started to trade")
    
    listen_keyboard()