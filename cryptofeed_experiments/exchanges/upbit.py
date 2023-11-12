from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple

import pandas as pd
from cryptofeed.defines import BID, TRADES
from cryptofeed.exchanges import Upbit as BaseUpbit

from ..feed import Feed


class Upbit(Feed, BaseUpbit):
    def parse_datetime(self, value: int, unit: str = "ms") -> datetime:
        """Parse datetime with pandas."""
        return pd.Timestamp(value, unit=unit).replace(tzinfo=timezone.utc)

    async def _trade(self, msg: dict, timestamp: float) -> Tuple[str, dict, float]:
        """
        Doc : https://docs.upbit.com/v1.0.7/reference#시세-체결-조회
        {
            'ty': 'trade'             // Event type
            'cd': 'KRW-BTC',          // Symbol
            'tp': 6759000.0,          // Trade Price
            'tv': 0.03243003,         // Trade volume(amount)
            'tms': 1584257228806,     // Timestamp
            'ttms': 1584257228000,    // Trade Timestamp
            'ab': 'BID',              // 'BID' or 'ASK'
            'cp': 64000.0,            // Change of price
            'pcp': 6823000.0,         // Previous closing price
            'sid': 1584257228000000,  // Sequential ID
            'st': 'SNAPSHOT',         // 'SNAPSHOT' or 'REALTIME'
            'td': '2020-03-15',       // Trade date utc
            'ttm': '07:27:08',        // Trade time utc
            'c': 'FALL',              // Change - 'FALL' / 'RISE' / 'EVEN'
        }
        """

        price = Decimal(msg["tp"])
        notional = Decimal(msg["tv"])
        volume = price * notional
        t = {
            "exchange": self.id.lower(),
            "uid": msg["sid"],
            "symbol": msg["cd"],
            "timestamp": self.parse_datetime(msg["ttms"]),
            "price": price,
            "volume": volume,
            "notional": notional,
            "tickRule": 1 if msg["ab"].lower() == BID else -1,
        }
        await self.callback(TRADES, t, self.timestamp_normalize(msg["ttms"]))
