from decimal import Decimal
from typing import List, Optional

from cryptofeed.backends.aggregate import AggregateCallback

from .base import WindowMixin
from .constants import NOTIONAL


class CandleCallback(WindowMixin, AggregateCallback):
    def __init__(
        self, *args, window_seconds: int = 60, top_n: Optional[int] = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.window_seconds = window_seconds
        self.window = {}
        self.top_n = top_n
        self.trades = {}

    async def __call__(self, trade: dict) -> None:
        candle = self.main(trade)
        if candle is not None:
            await self.handler(candle)

    def main(self, trade: dict) -> Optional[dict]:
        symbol = trade["symbol"]
        timestamp = trade["timestamp"]
        self.trades.setdefault(symbol, [])
        window = self.get_window(symbol, timestamp)
        # Was message received late?
        if timestamp < window["start"]:
            # FUBAR
            return self.aggregate([trade], is_late=True)
        elif timestamp >= window["stop"]:
            # Get tick
            tick = self.get_tick(symbol)
            # Append trade
            self.trades[symbol].append(trade)
            # Set window
            self.set_window(symbol, timestamp)
            # Finally, return tick
            return tick
        else:
            self.trades[symbol].append(trade)

    def aggregate(self, trades: List[dict], is_late: bool = False) -> Optional[dict]:
        first_trade = trades[0]
        prices = self.get_prices(trades)
        candle = {
            "exchange": first_trade["exchange"],
            "symbol": first_trade["symbol"],
            "timestamp": self.get_start(first_trade["timestamp"]),
            "open": first_trade["price"],
            "high": max(prices),
            "low": min(prices),
            "close": trades[-1]["price"],
            "totalBuyVolume": sum([t["totalBuyVolume"] for t in trades]),
            "totalVolume": sum([t["totalVolume"] for t in trades]),
            "totalBuyNotional": sum([t["totalBuyNotional"] for t in trades]),
            "totalNotional": sum([t["totalNotional"] for t in trades]),
            "totalBuyTicks": sum([t["totalBuyTicks"] for t in trades]),
            "totalTicks": sum([t["totalTicks"] for t in trades]),
        }
        if self.top_n:
            candle["topN"] = self.get_top_n(trades)
        return candle

    def get_prices(self, trades: List[dict]) -> List[Decimal]:
        prices = []
        for trade in trades:
            for key in ("price", "high", "low"):
                value = trade.get(key, None)
                if value:
                    prices.append(value)
        return prices

    def get_top_n(self, trades: List[dict]) -> List[dict]:
        filtered = [t for t in trades if "uid" in t]
        filtered.sort(key=lambda t: t[NOTIONAL], reverse=True)
        top_n = filtered[: self.top_n]
        for trade in top_n:
            for key in list(trade):
                if key not in (
                    "timestamp",
                    "price",
                    "volume",
                    "notional",
                    "tickRule",
                    "ticks",
                ):
                    del trade[key]
        top_n.sort(key=lambda t: t["timestamp"])
        return top_n
