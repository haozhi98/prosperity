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

            # print("Acceptable price : " + str(acceptable_price))
            # print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))

            # NOTE: Order agnostic, just place orders based on theoretical price

            if len(order_depth.sell_orders) != 0 and len(order_depth.buy_orders) != 0:
                # sell orders
                sell_orders = list(order_depth.sell_orders.items())
                sell_orders.sort()
                best_ask = sell_orders[0][0]
                # buy orders
                buy_orders = list(order_depth.buy_orders.items())
                buy_orders.sort(reverse=True)
                best_bid = buy_orders[0][0]
                # mid price
                acceptable_price = round((best_ask + best_bid) / 2.0)
                print(product, "Acceptable Price:", acceptable_price)
                if product in state.position:
                    print("Position:", state.position[product])
                    print("BUY", str(self.position_limits[product] - state.position[product]) + "x", acceptable_price-3)
                    print("SELL", str(-self.position_limits[product] - state.position[product]) + "x", acceptable_price+3)
                    orders.append(Order(product, acceptable_price-3, self.position_limits[product] - state.position[product]))
                    orders.append(Order(product, acceptable_price+3, -self.position_limits[product] - state.position[product]))
                else:
                    print("BUY", str(self.position_limits[product]) + "x", acceptable_price-3)
                    print("SELL", str(-self.position_limits[product]) + "x", acceptable_price+3)
                    orders.append(Order(product, acceptable_price-3, self.position_limits[product]))
                    orders.append(Order(product, acceptable_price+3, -self.position_limits[product]))

                result[product] = orders
                theos[product] = acceptable_price
    
                traderData = jsonpickle.encode(theos)
            else:
                traderData = None
        # traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = 0
        return result, conversions, traderData