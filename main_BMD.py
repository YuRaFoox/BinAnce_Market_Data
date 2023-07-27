from datetime import datetime
from binance.client import Client
import time
from decimal import Decimal
from collections import deque

# Create a Binance client
client = Client('iJw7FfZIXfo44dV9QXED8pRfBdRvFMdXsx4acSj7T4bUB7Q4nuORt4micZfq5NsW',
                'wuQICi5wYpPF2D1WS4dEzAvBpvZX2HiGgIloRwYOZsvhJSMfRZnKVqzyNdE38Y1t')

# Define the trading pair
symbol = 'SHIBBUSD'

# Define price step 0.00000005
step_course = float("{:.8f}".format(float("0.01e-06")))

# Fetch current prices
ticker = client.get_symbol_ticker(symbol=symbol)
current_price = float("{:.8f}".format(float(ticker["price"])))
algo_curr_pri = 0.00000785
# Keep track of price movements in the last 15 minutes
price_history = []
# Keep track of executed buy orders (deque with a maximum length of 3)
executed_buy_prices = deque(maxlen=3)


def bnb_current_price():
    ticker = client.get_symbol_ticker(symbol='BNBBUSD')
    current_price = round(float(ticker["price"]), 2)
    return current_price


def get_price_history():
    global price_history
    # Fetch historical klines for the trading pair (5 minutes interval)
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE, "5 min ago UTC")
    # Extract closing prices from klines
    closing_prices = [float(kline[4]) for kline in klines]
    price_history = closing_prices[-5:]


def should_buy(current_price, algo_curr_pri):
    # Check if current_price is not equal to any of the executed buy prices
    if current_price in executed_buy_prices:
        return False
    # Calculate the price drop percentage
    if algo_curr_pri == 0:
        return False
    price_drop_percentage = ((algo_curr_pri - current_price) / algo_curr_pri) * 100
    if price_drop_percentage > 1:
        print('price falls >1% in last 5 minutes')
    else:
        # Add current_price to the executed buy prices deque
        executed_buy_prices.append(current_price)
    return price_drop_percentage < 1


def step_algo(buy_amt, algo_curr_pri, sell_order_counter=0):
    global price_history
    global executed_buy_prices
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print('----------------------------')
    print('-', 'Started at', formatted_time, '-', flush=True)
    while True:
        # Fetch current prices
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float("{:.8f}".format(float(ticker["price"])))
        qty = round(buy_amt / current_price)
        algo_curr_pri = algo_curr_pri
        get_price_history()
        try:
            # Your algorithmic conditions and actions go here
            if current_price > algo_curr_pri:
                if should_buy(current_price, algo_curr_pri):
                    buy_order = client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                    buy_price = float(buy_order['fills'][0]['price'])
                    # Add executed buy price to the set
                    executed_buy_prices.append(buy_price)
                    print(float(buy_price), "= Buy price", flush=True)
                    print(qty, "= Buy quantity", flush=True)
                    print('Bought_Course_UP!', flush=True)
                    sell_price = round(buy_price + step_course, 8)
                    sell_price = Decimal("{:.8f}".format(sell_price))
                    sell_order = client.create_order(symbol=symbol, side='SELL', type='LIMIT', timeInForce='GTC',
                                                     price=sell_price, quantity=qty)
                    sell_order_counter += 1
                    algo_curr_pri = float(sell_order['price'])
                    Profit_Cents = ((((float(buy_amt / buy_price)) - (float(buy_amt / sell_price)))
                                    * float(sell_price)) - float((buy_amt*0.075)/100)) * sell_order_counter
                    Profit_Cents = round(Profit_Cents, 2)
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                    print('-', formatted_time, '-', flush=True)
                    print(float(algo_curr_pri), "= Sell price", flush=True)
                    print(qty, "= Sell quantity", flush=True)
                    print('Sell orders have placed -> ' + str(sell_order_counter) + 'pcs',
                          '(' + str(Profit_Cents) + '$' + ')', flush=True)
                    print("----------------------------", flush=True)
            elif current_price < algo_curr_pri - (step_course * 2):
                if should_buy(current_price, algo_curr_pri):
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_price = float("{:.8f}".format(float(ticker["price"])))
                    qty = round(buy_amt / current_price)
                    buy_order = client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                    buy_price = float(buy_order['fills'][0]['price'])
                    # Add executed buy price to the set
                    executed_buy_prices.append(buy_price)
                    print(float(buy_price), "= Buy price", flush=True)
                    print(qty, "= Buy quantity", flush=True)
                    print('Bought_Course_DOWN!', flush=True)
                    sell_price = round(buy_price + step_course, 8)
                    sell_price = Decimal("{:.8f}".format(sell_price))
                    sell_order = client.create_order(symbol=symbol, side='SELL', type='LIMIT', timeInForce='GTC',
                                                     price=sell_price, quantity=qty)
                    sell_order_counter += 1
                    algo_curr_pri = float(sell_order['price'])
                    Profit_Cents = (((float(buy_amt / buy_price)) - (float(buy_amt / sell_price)))
                                    * float(sell_price)) * sell_order_counter
                    Profit_Cents = round(Profit_Cents, 2)
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                    print('-', formatted_time, '-', flush=True)
                    print(float(algo_curr_pri), "= Sell price", flush=True)
                    print(qty, "= Sell quantity", flush=True)
                    print('Sell orders have placed -> ' + str(sell_order_counter) + 'pcs',
                          '(' + str(Profit_Cents) + '$' + ')', flush=True)
                    print("----------------------------", flush=True)
            time.sleep(1)
        except Exception as e:
            print("An error occurred", e)


# Run the algorithm
step_algo(55, algo_curr_pri)
