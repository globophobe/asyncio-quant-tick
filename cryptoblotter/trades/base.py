class WindowMixin:
    default_key = "trades"

    def get_start(self, timestamp: float):
        return int(timestamp / self.window_seconds) * self.window_seconds

    def get_stop(self, timestamp: float):
        return timestamp + self.window_seconds

    def get_window(self, symbol: str, timestamp: float):
        if symbol not in self.window:
            return self.window.setdefault(symbol, self.set_window(symbol, timestamp))
        return self.window[symbol]

    def set_window(self, symbol: str, timestamp: float):
        if self.window_seconds is not None:
            window = self.window.setdefault(symbol, {})
            start = self.get_start(timestamp)
            window["start"] = start
            window["stop"] = self.get_stop(start)

    def main(self, trade: dict):
        raise NotImplementedError

    def get_tick(self, symbol: str):
        trades = self.trades[symbol]
        if len(trades):
            tick = self.aggregate(trades)
            # Reset
            self.trades[symbol] = []
            return tick

    def aggregate(self, trades, is_late=False):
        raise NotImplementedError
