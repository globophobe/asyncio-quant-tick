from decimal import Decimal

from cryptofeed.backends.aggregate import AggregateCallback


class TradeCallback(AggregateCallback):
    """
    Aggregate sequences of trades that have equal symbol, timestamp, nanoseconds, and
    tick rule.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trades = {}

    async def __call__(self, *args, **kwargs):
        tick = self.main(*args, **kwargs)
        if tick is not None:
            symbol = tick["symbol"]
            self.trades[symbol] = []  # Reset
            await self.handler(tick)

    def main(self, *args, **kwargs):
        """Subclasses override this method"""
        trade = self.get_trade(**kwargs)
        return self.aggregate(trade)

    def aggregate(self, trade: dict):
        symbol = trade["symbol"]
        trades = self.trades.setdefault(symbol, [])
        if not len(trades):
            self.trades[symbol].append(trade)
        else:
            last_trade = trades[-1]
            if last_trade["timestamp"] == trade["timestamp"]:
                if last_trade["tickRule"] == trade["tickRule"]:
                    self.trades[symbol].append(trade)
                    return
            return self.get_tick(symbol)

    def get_trade(
        self,
        feed: str,
        uid: str,
        symbol: str,
        timestamp: float,
        price: Decimal,
        volume: Decimal,
        notional: Decimal,
        tickRule: int,
        ticks: int = 1,
        isSequential: bool = False,
    ):
        return {
            "feed": feed,
            "uid": uid,
            "symbol": symbol,
            "timestamp": timestamp,
            "price": price,
            "volume": volume,
            "notional": notional,
            "tickRule": tickRule,
            "ticks": ticks,  # B/C Binance
            "isSequential": isSequential,
        }

    def get_tick(self, symbol: str):
        trades = self.trades[symbol]
        last_trade = trades[-1]
        # Is there more than 1 trade?
        if len(trades) > 1:
            # Assert
            keys = ["timestamp", "tickRule"]
            if last_trade.get("symbol", None):
                keys.append("symbol")
            for key in keys:
                assert len(set([trade[key] for trade in trades])) == 1
            # Aggregate
            last_trade["volume"] = sum([trade["volume"] for trade in trades])
            last_trade["notional"] = sum([trade["notional"] for trade in trades])
            last_trade["ticks"] = sum([trade["ticks"] for trade in trades])
        return last_trade


class SequentialIntegerTradeCallback(TradeCallback):
    """Coinbase has sequential IDs"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uids = {}

    def main(self, *args, **kwargs):
        trade = self.get_trade(**kwargs)
        symbol = trade["symbol"]
        uid = self.uids.get(symbol, None)
        if uid:
            trade["isSequential"] = trade["uid"] == uid + 1
        else:
            trade["isSequential"] = True
        self.uids["symbol"] = trade["uid"]
        return self.aggregate(trade)


class NonSequentialIntegerTradeCallback(TradeCallback):
    """Bitfinex and FTX have non-sequential IDs"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uids = {}

    def main(self, *args, **kwargs):
        trade = self.get_trade(**kwargs)
        symbol = trade["symbol"]
        uid = self.uids.get(symbol, None)
        if uid:
            trade["isSequential"] = trade["uid"] > uid
        else:
            trade["isSequential"] = True
        self.uids["symbol"] = trade["uid"]
        return self.aggregate(trade)
