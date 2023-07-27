from datetime import datetime
from binance.client import Client
import time
from decimal import Decimal

# Create a Binance client
client = Client('iJw7FfZIXfo44dV9QXED8pRfBdRvFMdXsx4acSj7T4bUB7Q4nuORt4micZfq5NsW',
                'wuQICi5wYpPF2D1WS4dEzAvBpvZX2HiGgIloRwYOZsvhJSMfRZnKVqzyNdE38Y1t')

# Define the trading pair
symbol = 'SHIBBUSD'

# Define price step 0.00000005
step_course = float("0.01e-06")
last_buy_price_UP = None
last_buy_price_DOWN = None
# Fetch current prices
ticker = client.get_symbol_ticker(symbol=symbol)
current_price = float(ticker["price"])
# Keep track of price movements in the last 15 minutes
price_history = []

# Define the maximum number of bids to fetch from the order book
MAX_BIDS_TO_FETCH = 99


def fetch_active_sell_prices(symbol):
    # Fetch active sell orders using the /api/v3/openOrders endpoint
    active_orders = client.get_open_orders(symbol=symbol)
    active_sell_prices = [float(order['price']) for order in active_orders if order['side'] == 'SELL']
    active_sell_prices.sort()
    return active_sell_prices


def fetch_buy_prices():
    # Subtract step_course from each price in the list
    active_sell_prices = fetch_active_sell_prices(symbol)
    adjusted_prices = [price - step_course for price in active_sell_prices]
    active_buy_prices = adjusted_prices
    return active_buy_prices


def min_buy_price_in_orderBook():
    active_sell_prices = fetch_active_sell_prices(symbol)
    adjusted_prices = [price - step_course for price in active_sell_prices]
    first_price_in_orderBook = adjusted_prices[0]
    return first_price_in_orderBook


def max_buy_price_in_orderBook():
    active_sell_prices = fetch_active_sell_prices(symbol)
    adjusted_prices = [price - step_course for price in active_sell_prices]
    last_price_in_orderBook = adjusted_prices[-1]
    return last_price_in_orderBook


def get_price_history():
    # Fetch historical klines for the trading pair (5 minutes interval)
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "5 min ago UTC")
    # Extract closing prices from klines
    closing_prices = [float(kline[4]) for kline in klines]
    price_history = closing_prices[-5:]
    return price_history


def define_change_price():
    # Call the function and get the price history
    price_history = get_price_history()
    if len(price_history) >= 5:  # Ensure we have at least 4 data points for the calculation
        first_closing_price = float("{:.8f}".format(float(price_history[0])))
        last_closing_price = float("{:.8f}".format(float(price_history[-1])))
        percentage_price_change = round(((last_closing_price - first_closing_price) / first_closing_price) * 100, 2)
    else:
        print("Not enough historical kline data available.")
        percentage_price_change = None
    return percentage_price_change


def should_buy():
    executed_buy_prices = fetch_buy_prices()
    # Check if current_price is not equal to any of the executed buy prices
    if current_price not in executed_buy_prices:
        print(f'current_price--{current_price}--not in OB')
        # Calculate the price drop percentage
        price_drop_percentage = define_change_price()
        if price_drop_percentage <= -1:
            print('price falls >1% in last 5 minutes', price_drop_percentage)
        return price_drop_percentage
    else:
        return False


def step_algo(buy_amt, sell_order_counter=0):
    global price_history, last_buy_price_UP, last_buy_price_DOWN
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print('----------------------------')
    print('-', 'Started at', formatted_time, '-', flush=True)
    while True:
        # Fetch current prices
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float("{:.8f}".format(float(ticker["price"])))
        qty = round(buy_amt / current_price)
        try:
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
            last_buy_price_UP = last_buy_price_UP
            last_buy_price_DOWN = last_buy_price_DOWN
            print(f'last_price_UP----->{last_buy_price_UP}')
            print(f'last_price_DOWN--->{last_buy_price_DOWN}')
            print(f'-{formatted_time}-', flush=True)
            # Your algorithmic conditions and actions go here
            if current_price > max_buy_price_in_orderBook():
                print(f'current_price<--  {current_price}>{max_buy_price_in_orderBook()}  -->max_price_in_OB')
                if should_buy() and current_price != last_buy_price_UP:
                    # Place buy order only if the current price is different from the last buy price
                    buy_order = client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                    buy_price = float(buy_order['fills'][0]['price'])
                    last_buy_price_UP = buy_price  # Update the last_buy_price
                    print(float(buy_price), "= Buy price", flush=True)
                    print(qty, "= Buy quantity", flush=True)
                    print('Bought_Course_UP!', flush=True)
                    sell_price = round(buy_price + step_course, 8)
                    sell_price = Decimal("{:.8f}".format(sell_price))
                    sell_order = client.create_order(symbol=symbol, side='SELL', type='LIMIT', timeInForce='GTC',
                                                     price=sell_price, quantity=qty)
                    sell_order_counter += 1
                    sell_price = float(sell_order['price'])
                    Profit_Cents = ((((float(buy_amt / buy_price)) - (float(buy_amt / sell_price)))
                                     * float(sell_price)) - float((buy_amt * 0.075) / 100)) * sell_order_counter
                    Profit_Cents = round(Profit_Cents, 2)
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                    print('-', formatted_time, '-', flush=True)
                    print(float(sell_price), "= Sell price", flush=True)
                    print(qty, "= Sell quantity", flush=True)
                    print('Sell orders have placed -> ' + str(sell_order_counter) + 'pcs',
                          '(' + str(Profit_Cents) + '$' + ')', flush=True)
                    print("----------------------------", flush=True)
            elif current_price < min_buy_price_in_orderBook():
                print(f'current_price<-- {current_price}<{min_buy_price_in_orderBook()} -->min_price_in_OB')
                if should_buy() and current_price != last_buy_price_DOWN:
                    # Place buy order only if the current price is different from the last buy price
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_price = float("{:.8f}".format(float(ticker["price"])))
                    qty = round(buy_amt / current_price)
                    buy_order = client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                    buy_price = float(buy_order['fills'][0]['price'])
                    last_buy_price_DOWN = buy_price  # Update the last_buy_price
                    print(float(buy_price), "= Buy price", flush=True)
                    print(qty, "= Buy quantity", flush=True)
                    print('Bought_Course_DOWN!', flush=True)
                    sell_price = round(buy_price + step_course, 8)
                    sell_price = Decimal("{:.8f}".format(sell_price))
                    sell_order = client.create_order(symbol=symbol, side='SELL', type='LIMIT', timeInForce='GTC',
                                                     price=sell_price, quantity=qty)
                    sell_order_counter += 1
                    sell_price = float(sell_order['price'])
                    Profit_Cents = ((((float(buy_amt / buy_price)) - (float(buy_amt / sell_price)))
                                     * float(sell_price)) - float((buy_amt * 0.075) / 100)) * sell_order_counter
                    Profit_Cents = round(Profit_Cents, 2)
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                    print('-', formatted_time, '-', flush=True)
                    print(float(sell_price), "= Sell price", flush=True)
                    print(qty, "= Sell quantity", flush=True)
                    print('Sell orders have placed -> ' + str(sell_order_counter) + 'pcs',
                          '(' + str(Profit_Cents) + '$' + ')', flush=True)
                    print("----------------------------", flush=True)
        except Exception as e:
            print("An error occurred", e)


# Run the algorithm
step_algo(13)
