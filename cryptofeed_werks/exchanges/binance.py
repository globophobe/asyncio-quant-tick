from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple

import pandas as pd
from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Binance as BaseBinance

from ..feed import Feed


class Binance(Feed, BaseBinance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_id = None

    def parse_datetime(self, value: int, unit: str = "ms") -> datetime:
        """Parse datetime with pandas."""
        return pd.Timestamp(value, unit="ms").replace(tzinfo=timezone.utc)

    async def _trade(self, msg: dict, timestamp: float) -> Tuple[str, dict, float]:
        """
        Cryptofeed uses aggregate trade streams.
        The raw trade stream frequently misses trades, and is absolute trash.

        {
          "e": "aggTrade",  // Event type
          "E": 123456789,   // Event time
          "s": "BNBBTC",    // Symbol
          "a": 12345,       // Aggregate trade ID
          "p": "0.001",     // Price
          "q": "100",       // Quantity
          "f": 100,         // First trade ID
          "l": 105,         // Last trade ID
          "T": 123456785,   // Trade time
          "m": true,        // Is the buyer the market maker?
          "M": true         // Ignore
        }
        """
        if not self.last_id:
            self.last_id = int(msg["l"])
            is_sequential = True
        else:
            is_sequential = int(msg["f"]) == self.last_id + 1
            self.last_id = int(msg["l"])
        price = Decimal(msg["p"])
        notional = Decimal(msg["q"])
        volume = price * notional
        ticks = msg["l"] - msg["f"] + 1
        assert ticks >= 1, "Ticks not greater than or equal to 1"
        t = {
            "exchange": self.id.lower(),
            "uid": self.last_id,
            "symbol": msg["s"],
            "timestamp": self.parse_datetime(msg["T"]),
            "price": price,
            "volume": volume,
            "notional": notional,
            "tickRule": -1 if msg["m"] else 1,
            "ticks": ticks,
            "isSequential": is_sequential,
        }
        await self.callback(TRADES, t, timestamp)
