from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle

class Trader:
    # Bots make bid and ask offers
    # You have the chance to make offers on the bot offers from step 1 with 100% chance they get executed
    # You can make offers that doesn’t match the current bots offers
    # Bots get the chance to match your offers if they are interesting enough according to them

    def run(self, state: TradingState):
        result = {}
        traderData = jsonpickle.encode({})
        conversions = 0
        return result, conversions, traderData