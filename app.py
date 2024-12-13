from flask import Flask, render_template, jsonify
import MetaTrader5 as mt5
import numpy as np

# Initialize Flask app
app = Flask(__name__)

# Initialize MetaTrader 5
mt5.initialize()

# Define the Forex symbol (example: EURUSD)
symbol = "EURUSD"

# Define parameters
short_ma_period = 9  # Short-term MA period
long_ma_period = 21  # Long-term MA period
adr_period = 14  # ADR period
adr_multiplier = 1.25  # How many times ADR should be used for stop loss/take profit


# Function to get the current price of the Forex pair
def get_current_price():
    symbol_info = mt5.symbol_info_tick(symbol)
    if symbol_info is not None:
        return symbol_info.bid  # For simplicity, using the bid price
    else:
        return None


# Function to calculate Simple Moving Average (SMA)
def calculate_sma(period, symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, period)
    close_prices = [rate['close'] for rate in rates]  # Access 'close' price
    sma = np.mean(close_prices)  # Calculate SMA
    return sma


# Function to calculate Average Daily Range (ADR)
def calculate_adr(symbol, period):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, period)
    adr_values = [rate['high'] - rate['low'] for rate in rates]  # Access 'high' and 'low'
    adr = np.mean(adr_values)  # Calculate the average ADR over the given period
    return adr


# Function to decide whether to buy, sell, or hold based on Moving Averages
def check_moving_average_strategy():
    short_ma = calculate_sma(short_ma_period, symbol)
    long_ma = calculate_sma(long_ma_period, symbol)
    
    if short_ma > long_ma:
        return "buy"
    elif short_ma < long_ma:
        return "sell"
    else:
        return "hold"


@app.route("/")
def index():
    """Render the main web page."""
    return render_template("index.html")


@app.route("/trade", methods=["GET"])
def trade():
    """Perform trading decision and return the results as JSON."""
    current_price = get_current_price()
    if current_price is None:
        return jsonify({"error": "Error fetching price data"}), 500

    adr = calculate_adr(symbol, adr_period)
    action = check_moving_average_strategy()

    result = {
        "current_price": current_price,
        "adr": adr,
        "action": action,
    }

    if action == "buy":
        take_profit, stop_loss = calculate_take_profit_and_stop_loss(current_price, adr, is_buy=True)
        result["take_profit"] = take_profit
        result["stop_loss"] = stop_loss
    elif action == "sell":
        take_profit, stop_loss = calculate_take_profit_and_stop_loss(current_price, adr, is_buy=False)
        result["take_profit"] = take_profit
        result["stop_loss"] = stop_loss

    return jsonify(result)


def calculate_take_profit_and_stop_loss(entry_price, adr, is_buy):
    """Calculate Take Profit and Stop Loss using ADR."""
    if is_buy:
        take_profit = entry_price + adr * adr_multiplier
        stop_loss = entry_price - adr * adr_multiplier
    else:
        take_profit = entry_price - adr * adr_multiplier
        stop_loss = entry_price + adr * adr_multiplier
    return take_profit, stop_loss


if __name__ == "__main__":
    app.run()
