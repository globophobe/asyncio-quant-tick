from collections.abc import Callable
from typing import List, Optional, Tuple

from .window import WindowMixin


class TradeClusterCallback(WindowMixin):
    """Trade cluster callback."""

    def __init__(
        self,
        handler: Callable,
        window_seconds: Optional[int] = None,
    ) -> None:
        """Init."""
        self.handler = handler
        self.tick_rule = None
        self.trades = {}
        self.window_seconds = window_seconds
        self.window = {}

    async def __call__(self, trade: dict, timestamp: float) -> Tuple[dict, float]:
        """Call."""
        result = self.main(trade)
        if isinstance(result, dict):
            await self.handler(result, timestamp)

    def main(self, trade: dict) -> Optional[dict]:
        """Main."""
        symbol = trade["symbol"]
        timestamp = trade["timestamp"]
        window = self.get_window(symbol, timestamp)
        if window is not None:
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
                # Set window
                self.set_window(symbol, timestamp)
                # Finally, return tick
                return self.get_tick(symbol)
            else:
                return self.get_trade_cluster_or_tick(symbol, trade)
        else:
            return self.get_trade_cluster_or_tick(symbol, trade)

    def get_trade_cluster_or_tick(self, symbol: str, trade: dict) -> Optional[dict]:
        """Get trade cluster or tick."""
        trades = self.trades.setdefault(symbol, [])
        is_same_direction = True
        tick_rule = trade.get("tickRule")
        if self.tick_rule:
            is_same_direction = self.tick_rule == tick_rule
        if is_same_direction:
            self.trades[symbol].append(trade)
            self.tick_rule = tick_rule
        elif len(trades):
            tick = self.aggregate(trades)
            # Reset
            self.trades[symbol] = [trade]
            self.tick_rule = tick_rule
            return tick

    def aggregate(self, trades: List[dict], is_late: bool = False) -> None:
        """Aggregate."""
        first_trade = trades[0]
        last_trade = trades[-1]
        data = {
            "exchange": first_trade["exchange"],
            "symbol": first_trade["symbol"],
            "timestamp": first_trade["timestamp"],
            "price": last_trade["price"],
            "high": max(t.get("high", t["price"]) for t in trades),
            "low": min(t.get("low", t["price"]) for t in trades),
            "tickRule": self.tick_rule,
        }
        volume = ["volume", "totalBuyVolume", "totalVolume"]
        notional = ["notional", "totalBuyNotional", "totalNotional"]
        ticks = ["ticks", "totalBuyTicks", "totalTicks"]
        for sample_type in volume + notional + ticks:
            value = sum([t.get(sample_type, 0) for t in trades])
            if sample_type in ticks:
                value = int(value)
            data[sample_type] = value
        return data
