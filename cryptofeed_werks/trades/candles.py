from decimal import Decimal
from typing import List, Optional

from cryptofeed.backends.aggregate import AggregateCallback

from .base import WindowMixin


class CandleCallback(WindowMixin, AggregateCallback):
    def __init__(self, *args, window_seconds: int = 60, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.window_seconds = window_seconds
        self.window = {}
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
        return {
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

    def get_prices(self, trades: List[dict]) -> List[Decimal]:
        prices = []
        for trade in trades:
            for key in ("price", "high", "low"):
                value = trade.get(key, None)
                if value:
                    prices.append(value)
        return prices
