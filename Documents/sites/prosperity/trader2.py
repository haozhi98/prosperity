from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle

class Trader:
    # Bots make bid and ask offers
    # You have the chance to make offers on the bot offers from step 1 with 100% chance they get executed
    # You can make offers that doesn’t match the current bots offers
    # Bots get the chance to match your offers if they are interesting enough according to them
    position_limits = {'AMETHYSTS': 20, 'STARFRUIT': 20}

    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        # print("traderData: " + state.traderData)
        # print("Observations: " + str(state.observations))

        result = {}
        if state.traderData:
            theos = jsonpickle.decode(state.traderData)
        else:
            theos = {}

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # acceptable_price = 10;  # Participant should calculate this value
            try:
                acceptable_price = theos[product]
            except:
                acceptable_price = None

            # print("Acceptable price : " + str(acceptable_price))
            # print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))

            best_bid = best_ask = None
            current_order_position = 0

            # NOTE: Volume weighted theoretical price

            if len(order_depth.sell_orders) != 0:
                sell_orders = list(order_depth.sell_orders.items())
                sell_orders.sort(reverse=True)
                best_ask = sell_orders[-1][0]
                if acceptable_price:
                    # buy for all outstanding sell orders below acceptable_price
                    while len(sell_orders) > 0 and sell_orders[-1][0] < acceptable_price:
                    # TODO: Position limit -> Estimation?
                        orders.append(Order(product, sell_orders[-1][0], -sell_orders[-1][1]))
                        # counting buy orders
                        current_order_position -= sell_orders[-1][1]
                        sell_orders.pop()
    
            if len(order_depth.buy_orders) != 0:
                buy_orders = list(order_depth.buy_orders.items())
                buy_orders.sort()
                best_bid = buy_orders[-1][0]
                if acceptable_price:
                    # sell for all outstanding buy orders above acceptable_price
                    while len(buy_orders) > 0 and buy_orders[-1][0] > acceptable_price:
                    # TODO: Position limit -> Estimation?
                        orders.append(Order(product, buy_orders[-1][0], -buy_orders[-1][1]))
                        # counting sell orders
                        current_order_position -= buy_orders[-1][1]
                        buy_orders.pop()

            # buying at best bid if less than acceptable)
            # if best_bid and best_bid < acceptable_price:
            #     orders.append(Order(product, best_bid + 1, 20 - state.position[product] - current_order_position))

            # # selling at best ask (more than acceptable)
            # if best_ask and best_ask - 1 > acceptable_price:
            #     orders.append(Order(product, best_ask - 1, -20 - state.position[product] - current_order_position))

            result[product] = orders

            if best_bid and best_ask:
                theos[product] = (best_ask + best_bid) / 2.0
                # theos[product] = (best_ask * best_bid_amount - best_bid * best_ask_amount) / 2.0 / (best_bid_amount - best_ask_amount)
    
        traderData = jsonpickle.encode(theos)
        # traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 0
        return result, conversions, traderData