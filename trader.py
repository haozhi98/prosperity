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

            try:
                acceptable_price = theos[product]
            except:
                acceptable_price = None

            # print("Acceptable price : " + str(acceptable_price))
            # print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))

            # NOTE: Match outstanding orders that are profitable based on theorethical price

            best_ask = None
            best_bid = None

            buying = False
            selling = False

            if len(order_depth.sell_orders) != 0:
                sell_orders = list(order_depth.sell_orders.items())
                sell_orders.sort()
                best_ask, best_ask_amount = sell_orders[0]
                # best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                # TODO: Position limit -> Estimation?
                if acceptable_price:
                    if int(best_ask) < acceptable_price:
                        # print("BUY", str(-best_ask_amount) + "x", best_ask)
                        # buy orders to fill sell orders below acceptable price
                        # if product in state.position:
                        #     bid_size = min(-best_ask_amount, self.position_limits[product] - state.position[product])
                        # else:
                        #     bid_size = min(-best_ask_amount, self.position_limits[product])
                        bid_size = -best_ask_amount*2
                        orders.append(Order(product, best_ask, bid_size))
                        # if product in state.position:
                        #     orders.append(Order(product, best_ask, self.position_limits[product] - state.position[product]))
                        # else:
                        #     orders.append(Order(product, best_ask, self.position_limits[product]))
                        buying = True
                    # best ask is above acceptable
                    elif int(best_ask) > acceptable_price:
                        # selling at best ask (more than acceptable)
                        # if product in state.position:
                        #     ask_size = max(best_ask_amount, -self.position_limits[product] - state.position[product])
                        # else:
                        #     ask_size = max(best_ask_amount, -self.position_limits[product])
                        ask_size = best_ask_amount*2
                        orders.append(Order(product, best_ask, ask_size))
                        # if product in state.position:
                        #     orders.append(Order(product, best_ask, -self.position_limits[product] - state.position[product]))
                        # else:
                        #     orders.append(Order(product, best_ask, -self.position_limits[product]))
                        selling = True
    
            if len(order_depth.buy_orders) != 0:
                buy_orders = list(order_depth.buy_orders.items())
                buy_orders.sort(reverse=True)
                best_bid, best_bid_amount = buy_orders[0]
                # best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                # TODO: Position limit -> Estimation?
                if acceptable_price:
                    if int(best_bid) > acceptable_price:
                        if selling:
                            orders.pop()
                        # sell orders to fill buy orders above acceptable price
                        # if product in state.position:
                        #     ask_size = max(-best_bid_amount, -self.position_limits[product] - state.position[product])
                        # else:
                        #     ask_size = max(-best_bid_amount, -self.position_limits[product])
                        ask_size = -best_bid_amount*2
                        orders.append(Order(product, best_bid, ask_size))
                        # if product in state.position:
                        #     orders.append(Order(product, best_bid, -self.position_limits[product] - state.position[product]))
                        # else:
                        #     orders.append(Order(product, best_bid, -self.position_limits[product]))
                        selling = True

                    # check if already buying or not and best bid is below acceptable
                    elif not buying and int(best_bid) < acceptable_price:
                        # buying at best bid (less than acceptable)
                        # if product in state.position:
                        #     bid_size = min(best_bid_amount, self.position_limits[product] - state.position[product])
                        # else:
                        #     bid_size = min(best_bid_amount, self.position_limits[product])
                        bid_size = best_bid_amount*2
                        orders.append(Order(product, best_bid, bid_size))
                        # if product in state.position:
                        #     orders.append(Order(product, best_bid, self.position_limits[product] - state.position[product]))
                        # else:
                        #     orders.append(Order(product, best_bid, self.position_limits[product]))
                        buying = True

            result[product] = orders

            if best_bid and best_ask:
                # position weighted theo
                # if product in state.position and state.position[product] != 0:
                #     # if we are long (position positive), theo should go up -> easier to sell, harder to buy
                #     # if we are short (position negative), theo should go down -> easier to buy, harder to sell
                #     theos[product] = round(best_ask * (self.position_limits[product] + state.position[product]) + best_bid * (self.position_limits[product] - state.position[product])) / (self.position_limits[product] * 2.0)
                # else:
                #     theos[product] = (best_ask + best_bid) / 2.0
                theos[product] = (best_ask + best_bid) / 2.0
                # volume weighted theo
                # total_ask = sum(order[0] for order in buy_orders)
                # vol_ask = sum(order[1] for order in buy_orders)
                # total_bid = sum(order[0] for order in sell_orders)
                # vol_bid = -sum(order[1] for order in sell_orders)
                # theos[product] = round((total_ask * vol_bid + total_bid * vol_ask) // (vol_bid + vol_ask))
    
        traderData = jsonpickle.encode(theos)
        # traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 0
        return result, conversions, traderData