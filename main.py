from binance.client import Client
import os
import datetime

# connect to binance
api_key = os.environ.get('binance_api_key')
api_secret = os.environ.get('binance_api_secret')
client = Client(api_key, api_secret)

# constants
# MINIMUM = 0.011 ETH (0.001 ETH of leg space)
MINIMUM = float(client.get_symbol_ticker(symbol='ETHBTC')['price']) / 90

# initializing variables
# portfolio object's final structure
# portfolio = {
#     KEY: {
#         'percentage': int[DEFAULT],
#         'symbol': str[DEFAULT],
#         'btc_value': float,
#         'balance': float,
#         'uncorrected_btc_value': float,
#         'uncorrected_amount': float
#     }
# }
portfolio = {
    'ETH': {
        'percentage': 50,
        'symbol': 'BNBETH'
    },
    'BNB': {
        'percentage': 50,
        'symbol': 'BNBETH'
    }
}
portfolio_value = 0

# function definitions
def calculate_uncorrected_value(total_value, current_value, percentage):
    return -(((total_value / 100) * percentage) - current_value)

# retrieve portfolio's total BTC value & individual asset value
for key in portfolio:
    portfolio[key]['balance'] = float(client.get_asset_balance(asset=key)['free'])

prices = client.get_all_tickers()
for price in prices:
    for key in portfolio.keys():
        if price['symbol'] == key + 'BTC':
            portfolio[key]['btc_value'] = float(price['price']) * portfolio[key]['balance']
            portfolio_value += portfolio[key]['btc_value']

# calculate uncorrected btc value
for key in portfolio.keys():
    total_value = portfolio_value
    current_value = portfolio[key]['btc_value']
    percentage = portfolio[key]['percentage']

    ticker = key + 'BTC'
    uncorrected_btc_value = calculate_uncorrected_value(total_value, current_value, percentage)
    btc_rate = float(client.get_symbol_ticker(symbol=ticker)['price'])
    uncorrected_amount = uncorrected_btc_value / btc_rate

    portfolio[key]['uncorrected_btc_value'] = uncorrected_btc_value
    portfolio[key]['uncorrected_amount'] = round(uncorrected_amount, 2)

# rebalance if there is an asset uncorrected enough to buy and an asset uncorrected enough to sell
for key in portfolio:
    if (portfolio[key]['uncorrected_btc_value'] > MINIMUM):
        # found a sellable asset, now find a buyable
        sellable = key

        for key in portfolio:
            if (portfolio[key]['uncorrected_btc_value'] < -MINIMUM):
                buyable = key
                order = client.create_test_order(
                    symbol=portfolio[key]['symbol'],
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=portfolio[sellable]['uncorrected_amount'])

                # save output to debug.log
                f = open('./history.log','a')
                output = str(datetime.datetime.now()) + ": rebalanced"
                f.write(output + '\n')
