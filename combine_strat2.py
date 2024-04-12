from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Optional
import string
import jsonpickle

class Trader:
    # Bots make bid and ask offers
    # You have the chance to make offers on the bot offers from step 1 with 100% chance they get executed
    # You can make offers that doesn’t match the current bots offers
    # Bots get the chance to match your offers if they are interesting enough according to them
    position_limits = {'AMETHYSTS': 20, 'STARFRUIT': 20}

    def match_best(self, position: dict, best_ask: int, best_bid: int, best_ask_amount: int, best_bid_amount: int, result: dict, theo: int, product: str, limited: bool = False, mult: int = 2) -> tuple[int]:
        orders: List[Order] = []

        buying = selling = False

        buy_count = sell_count = 0

        if best_ask < theo:
            if limited:
                bid_size = min(-best_ask_amount*mult, self.position_limits[product] - position.get(product, 0))
            else:
                bid_size = -best_ask_amount*mult
            print("BUY", bid_size, "x", best_ask)
            orders.append(Order(product, best_ask, bid_size))
            buying = True
            buy_count = bid_size
        else:
            if limited:
                ask_size = max(best_ask_amount*mult, -self.position_limits[product] - position.get(product, 0))
            else:
                ask_size = best_ask_amount*mult
            print("SELL", ask_size, "x", best_ask)
            orders.append(Order(product, best_ask, ask_size))
            selling = True
            sell_count = ask_size

        if best_bid > theo:
            if selling:
                orders.pop()
            if limited:
                ask_size = max(-best_bid_amount*mult, -self.position_limits[product] - position.get(product, 0))
            else:
                ask_size = -best_bid_amount*mult
            print("SELL", ask_size, "x", best_bid)
            orders.append(Order(product, best_bid, ask_size))
            sell_count = ask_size
        elif not buying:
            if limited:
                bid_size = min(best_bid_amount*mult, self.position_limits[product] - position.get(product, 0))
            else:
                bid_size = best_bid_amount*mult
            print("BUY", bid_size, "x", best_bid)
            orders.append(Order(product, best_bid, bid_size))
            buy_count = bid_size

        result[product] = orders
        return (buy_count, sell_count)

    def maintain_spread(self, spread: int, position: dict, result: dict, acceptable_price: int, product: str, buy_count: int = 0, sell_count: int = 0) -> Optional[int]:
        orders: List[Order] = []
        # print(product, "Acceptable Price:", acceptable_price)
        # print("Applied Spread:", spread)
        if product in position:
            print("Position:", position[product])
            print("BUY", str(self.position_limits[product] - position[product] - buy_count) + "x", acceptable_price-spread)
            print("SELL", str(-self.position_limits[product] - position[product] - sell_count) + "x", acceptable_price+spread)
            # balance our book
            # if product == 'AMETHYSTS':
            #     acceptable_price -= position[product] // 7
            # elif product == 'STARFRUIT':
            #     acceptable_price -= position[product] // 11
            # acceptable_price -= position[product] // 7
            print("Balanced Acceptable Price:", acceptable_price)
            orders.append(Order(product, acceptable_price-spread, self.position_limits[product] - position[product] - buy_count))
            orders.append(Order(product, acceptable_price+spread, -self.position_limits[product] - position[product] - sell_count))
        else:
            print("BUY", str(self.position_limits[product] - buy_count) + "x", acceptable_price-spread)
            print("SELL", str(-self.position_limits[product] - sell_count) + "x", acceptable_price+spread)
            orders.append(Order(product, acceptable_price-spread, self.position_limits[product] - buy_count))
            orders.append(Order(product, acceptable_price+spread, -self.position_limits[product] - sell_count))

        result[product] = orders
        return acceptable_price

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

            # print("Acceptable price : " + str(acceptable_price))
            # print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            acceptable_price = None

            if len(order_depth.sell_orders) != 0 and len(order_depth.buy_orders) != 0:
                # sell orders
                sell_orders = list(order_depth.sell_orders.items())
                sell_orders.sort()
                best_ask, best_ask_amount = sell_orders[0]
                # buy orders
                buy_orders = list(order_depth.buy_orders.items())
                buy_orders.sort(reverse=True)
                best_bid, best_bid_amount = buy_orders[0]
                # floor half of previous spread
                # spread = round(best_ask - best_bid)
                # mid price
                acceptable_price = round((best_ask + best_bid) / 2.0)
                # market making strat
                if product == 'AMETHYSTS':
                    if product in theos:
                        theo = theos[product]
                        buy_count, sell_count = self.match_best(state.position, best_ask, best_bid, best_ask_amount, best_bid_amount, result, theo, product, True, mult=1)
                        acceptable_price = self.maintain_spread(3, state.position, result, acceptable_price, product, buy_count, sell_count)
                    else:
                        acceptable_price = self.maintain_spread(3, state.position, result, acceptable_price, product)
                # fill order strat
                elif product == 'STARFRUIT' and product in theos:
                    theo = theos[product]
                    self.match_best(state.position, best_ask, best_bid, best_ask_amount, best_bid_amount, result, theo, product)

                # save current mid point price
                theos[product] = acceptable_price

        traderData = jsonpickle.encode(theos)
        # traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = 0
        return result, conversions, traderData