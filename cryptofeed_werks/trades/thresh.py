from decimal import Decimal

from cryptofeed.backends.aggregate import AggregateCallback

from .base import WindowMixin
from .constants import NOTIONAL, TICKS, VOLUME


class ThreshCallback(WindowMixin, AggregateCallback):
    def __init__(
        self,
        *args,
        thresh_attr=VOLUME,
        thresh_value=1000,
        window_seconds=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.thresh_attr = thresh_attr
        self.thresh_value = Decimal(thresh_value)
        self.trades = {}
        self.window_seconds = window_seconds
        self.window = {}

    async def __call__(self, *args, **kwargs):
        result = self.main(*args, **kwargs)
        if isinstance(result, list):
            for tick in result:
                await self.handler(tick)
        elif isinstance(result, dict):
            await self.handler(result)

    def main(self, trade: dict):
        symbol = trade["symbol"]
        timestamp = trade["timestamp"]
        self.trades.setdefault(symbol, [])
        window = self.get_window(symbol, timestamp)
        # Was message received late?
        if window["start"] is not None and timestamp < window["start"]:
            # FUBAR
            return self.aggregate([trade], is_late=True)
        # Is window exceeded?
        elif window["stop"] is not None and timestamp >= window["stop"]:
            ticks = []
            # Get tick
            tick = self.get_tick(symbol)
            if tick is not None:
                ticks.append(tick)
            # Append trade
            self.trades[symbol].append(trade)
            # Maybe another tick
            if trade[self.thresh_attr] >= self.thresh_value:
                tick = self.get_tick(symbol)
                ticks.append(tick)
            # Set window
            self.set_window(symbol, timestamp)
            # Finally, return ticks
            return ticks
        elif trade[self.thresh_attr] < self.thresh_value:
            self.trades[symbol].append(trade)
        else:
            self.trades[symbol].append(trade)
            return self.get_tick(symbol)

    def aggregate(self, trades, is_late=False):
        buy_trades = [t for t in trades if t["tickRule"] == 1]
        stats = {
            "high": max(t["price"] for t in trades),
            "low": min(t["price"] for t in trades),
            "totalBuyVolume": sum([t[VOLUME] for t in buy_trades]),
            "totalVolume": sum([t[VOLUME] for t in trades]),
            "totalBuyNotional": sum([t[NOTIONAL] for t in buy_trades]),
            "totalNotional": sum([t[NOTIONAL] for t in trades]),
            "totalBuyTicks": sum([t[TICKS] for t in buy_trades]),
            "totalTicks": sum([t[TICKS] for t in trades]),
        }
        greater_than_thresh = [
            t for t in trades if t[self.thresh_attr] >= self.thresh_value
        ]
        # Is there 1 or 0 trades, which exceed the thresh_value?
        assert len(greater_than_thresh) <= 1
        if greater_than_thresh:
            data = greater_than_thresh[0]
            data.update(stats)
        else:
            last_trade = trades[-1]
            data = {
                "feed": last_trade["feed"],
                "symbol": last_trade["symbol"],
                "timestamp": last_trade["timestamp"],
                "price": last_trade["price"],
                "isSequential": all([t["isSequential"] for t in trades]),
            }
            data.update(stats)
        if is_late:
            data["isLate"] = is_late
        return data
