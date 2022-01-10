from typing import Optional

from cryptofeed.backends.aggregate import AggregateCallback


class TradeCallback(AggregateCallback):
    """
    Aggregate sequences of trades that have equal symbol, timestamp, nanoseconds, and
    tick rule.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.trades = {}

    async def __call__(self, *args, **kwargs) -> None:
        tick = self.main(*args, **kwargs)
        if tick is not None:
            symbol = tick["symbol"]
            self.trades[symbol] = []  # Reset
            await self.handler(tick)

    def main(self, trade: dict, timestamp: float) -> dict:
        """Subclasses override this method"""
        trade = self.get_trade(trade, timestamp)
        return self.aggregate(trade)

    def aggregate(self, trade: dict) -> Optional[dict]:
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

    def get_trade(self, trade: dict, timestamp: float) -> dict:
        if "ticks" not in trade:
            trade["ticks"] = 1  # b/c Binance
        if "isSequential" not in trade:
            trade["isSequential"] = False
        return trade

    def get_tick(self, symbol: str) -> dict:
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.uids = {}

    def main(self, trade: dict, timestamp: float) -> dict:
        trade = self.get_trade(trade, timestamp)
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.uids = {}

    def main(self, trade: dict, timestamp: float) -> dict:
        trade = self.get_trade(trade, timestamp)
        symbol = trade["symbol"]
        uid = self.uids.get(symbol, None)
        if uid:
            trade["isSequential"] = trade["uid"] > uid
        else:
            trade["isSequential"] = True
        self.uids["symbol"] = trade["uid"]
        return self.aggregate(trade)
