from datetime import datetime
from typing import List, Optional

from cryptofeed.defines import TRADES
from dateutil.relativedelta import relativedelta


class WindowMixin:
    """Window mixin."""

    default_key = TRADES

    def get_start(self, timestamp: datetime) -> datetime:
        """Get start."""
        return timestamp.replace(second=0, microsecond=0, nanosecond=0)

    def get_stop(self, timestamp: datetime) -> datetime:
        """Get stop."""
        return timestamp + relativedelta(seconds=self.window_seconds)

    def get_window(self, symbol: str, timestamp: datetime) -> datetime:
        """Get window."""
        if symbol not in self.window:
            return self.window.setdefault(symbol, self.set_window(symbol, timestamp))
        return self.window[symbol]

    def set_window(self, symbol: str, timestamp: datetime) -> datetime:
        """Set window."""
        if self.window_seconds is not None:
            window = self.window.setdefault(symbol, {})
            start = self.get_start(timestamp)
            window["start"] = start
            window["stop"] = self.get_stop(start)

    def main(self, trade: dict) -> None:
        """Main."""
        raise NotImplementedError

    def get_tick(self, symbol: str) -> Optional[dict]:
        """Get tick."""
        trades = self.trades[symbol]
        if len(trades):
            tick = self.aggregate(trades)
            # Reset
            self.trades[symbol] = []
            return tick

    def aggregate(self, trades: List[dict], is_late: bool = False) -> None:
        """Aggregate."""
        raise NotImplementedError
