import pandas as pd
import numpy as np

# Theo Pricing Models
# NOTE: Please set "theo_price" as the column in which the calculated theoretical price is stored
def weighted_mid_price(dataframe: pd.DataFrame) -> None:
    """
    Calculate the weighted mid price for the given DataFrame.

    This function calculates the weighted mid price using bid and ask prices
    along with their respective volumes in the provided DataFrame.

    Parameters:
    - dataframe (pd.DataFrame): The DataFrame containing bid and ask prices
                                along with their respective volumes.

    Returns:
    - None
    """
    bid_prices = dataframe.filter(like='bid_price')
    bid_vol = dataframe.filter(like='bid_volume')
    ask_prices = dataframe.filter(like='ask_price')
    ask_vol = dataframe.filter(like='ask_volume')
    # volume weighted mean of top 3 bid/ask
    bid_weighted_mean = np.nan_to_num((bid_prices.values * bid_vol.values)).sum(axis=1) / np.nan_to_num(bid_vol.sum(axis=1))
    ask_weighted_mean = np.nan_to_num((ask_prices.values * ask_vol.values)).sum(axis=1) / np.nan_to_num(ask_vol.sum(axis=1))
    # merge timestamp across days
    dataframe['timestamp'] += dataframe['day'] * 1000000
    dataframe.drop(columns='day', inplace=True)
    # weighted prices
    dataframe['weighted_bid_price'] = bid_weighted_mean
    dataframe['weighted_ask_price'] = ask_weighted_mean
    dataframe['theo_price'] = round((dataframe['weighted_ask_price'] + dataframe['weighted_bid_price']) / 2.0)
    dataframe['theo_price'] = dataframe['theo_price'].shift(1)


def plain_mid_price(dataframe: pd.DataFrame) -> None:
    """
    Calculate the weighted mid price for the given DataFrame.

    This function calculates the weighted mid price using bid and ask prices
    along with their respective volumes in the provided DataFrame.

    Parameters:
    - dataframe (pd.DataFrame): The DataFrame containing bid and ask prices
                                along with their respective volumes.

    Returns:
    - None
    """
    dataframe['theo_price'] = dataframe['mid_price'].shift(1)

def position_weighted_mid_price(dataframe: pd.DataFrame) -> None:
    """
    Calculate the weighted mid price for the given DataFrame.

    This function calculates the weighted mid price using bid and ask prices
    along with their respective volumes in the provided DataFrame.

    Parameters:
    - dataframe (pd.DataFrame): The DataFrame containing bid and ask prices
                                along with their respective volumes.

    Returns:
    - None
    """
    dataframe['theo_price'] = dataframe['mid_price'].shift(1)

def backtest_theo_model(dir: str, filename: str, theo_price_model: callable) -> dict[str, pd.DataFrame]:
    """
    Calculates the theoretical maximum profit given a theoretical price model

    This function tests the profit from a simple strategy matching buy (sell) orders for
    outstanding asks (bids) are below (above) the theoretical price from a provided theoretical price model

    Parameters:
    - dir (str): Directory in which data file is stored
    - filename (str): Filename of csv data file
    - theo_price_model (callable): The theoretical pricing model which is a function that takes a DataFrame as input

    Returns:
    - Dictionary of product name and DataFrame of order and profit information
    """
    df = pd.read_csv(f'{dir}/{filename}', delimiter=';')
    grouped_df = df.groupby('product')
    product_df = {}
    for product, dataframe in grouped_df:
        theo_price_model(dataframe)
        # theoretical positions
        # sell orders
        trades = dataframe[['bid_volume_1', 'bid_volume_2', 'bid_volume_3']].values * (dataframe[['bid_price_1', 'bid_price_2', 'bid_price_3']] > dataframe['theo_price'].values[:, None]).values
        trades = np.nan_to_num(trades, nan=0)
        asks = trades * dataframe[['bid_price_1', 'bid_price_2', 'bid_price_3']].values
        asks = np.nan_to_num(asks, nan=0)
        dataframe['sell'] = np.sum(asks, axis=1)
        dataframe['sell_trades'] = np.sum(trades, axis=1)
        # buy orders
        trades = dataframe[['ask_volume_1', 'ask_volume_2', 'ask_volume_3']].values * (dataframe[['ask_price_1', 'ask_price_2', 'ask_price_3']] < dataframe['theo_price'].values[:, None]).values
        trades = np.nan_to_num(trades, nan=0)
        bids = trades * dataframe[['ask_price_1', 'ask_price_2', 'ask_price_3']].values
        bids = np.nan_to_num(bids, nan=0)
        dataframe['buy'] = np.sum(bids, axis=1)
        dataframe['buy_trades'] = np.sum(trades, axis=1)
        print(dataframe)
        # mark to market final position
        buy_vol = dataframe['buy_trades'].sum()
        sell_vol = dataframe['sell_trades'].sum()
        position = buy_vol - sell_vol
        # realized profits plus final position marked to market at last mid_price
        sell_gain = dataframe['sell'].sum()
        buy_cost = dataframe['buy'].sum()
        average_buy = buy_cost / buy_vol
        average_sell = sell_gain / sell_vol
        # realized_profit = sell_gain - buy_cost
        realized_profit = (average_sell - average_buy) * min(buy_vol, sell_vol)
        closing_mid_price = dataframe.iloc[-1]['mid_price']
        outstanding_amount = position * closing_mid_price
        # offload long position
        if position > 0:    
            unrealized_profit = outstanding_amount - position * average_buy
        else: # offload short position
            unrealized_profit = outstanding_amount - position * average_sell
        final_profit = realized_profit + unrealized_profit
        # remove market orders and product column
        dataframe.drop(columns=df.columns[df.columns.str.startswith('bid') | df.columns.str.startswith('ask')], inplace=True)
        dataframe.drop(columns='product', inplace=True)
        # save df
        product_df[product] = dataframe
        print(f'\n{product}\nTotal Buy Volume: {buy_vol}\nTotal Buy Cost: {buy_cost}\nTotal Sell Volume: {sell_vol}\nTotal Sell Cost: {sell_gain}\n')
        print(f'\nFinal Position: {position}\nAverage Buy Price: {average_buy}\nAverage Sell Price: {average_sell}\nClosing Mid Price: {closing_mid_price}\n')
        print(f'\nRealized Profit: {realized_profit}\nUnrealized Profit: {unrealized_profit}\nFinal Profit: {final_profit}\n')

    return product_df

output = backtest_theo_model('r1_data', 'prices_round_1_day_0.csv', weighted_mid_price)
for key in output:
    print(output[key])
# backtest_theo_model('order_data', 'r1_best_max.csv')

output = backtest_theo_model('r1_data', 'prices_round_1_day_0.csv', plain_mid_price)