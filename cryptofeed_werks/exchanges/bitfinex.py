from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple

import pandas as pd
from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bitfinex as BaseBitfinex
from cryptofeed.exchanges.bitfinex import LOG

from ..feed import Feed


class Bitfinex(Feed, BaseBitfinex):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_initialized = False

    def parse_datetime(self, value: int, unit: str = "ms") -> datetime:
        """Parse datetime with pandas."""
        return pd.Timestamp(value, unit=unit).replace(tzinfo=timezone.utc)

    async def _trades(
        self, pair: str, msg: list, timestamp: float
    ) -> Tuple[str, dict, float]:
        async def _trade_update(trade: list, timestamp: float):
            uid, ts, notional, price = trade
            price = Decimal(price)
            volume = price * abs(notional)
            t = {
                "exchange": self.id.lower(),
                "uid": uid,
                "symbol": pair,
                "timestamp": self.parse_datetime(ts),
                "price": price,
                "volume": volume,
                "notional": abs(notional),
                "tickRule": -1 if notional < 0 else 1,
            }
            await self.callback(TRADES, t, timestamp)

        # Drop first message.
        if self.is_initialized:
            if isinstance(msg[1], list):
                # Snapshot.
                for trade in msg[1]:
                    await _trade_update(trade, timestamp)
            elif msg[1] in ("te", "fte"):
                # Update.
                await _trade_update(msg[2], timestamp)
            elif msg[1] not in ("tu", "ftu", "hb"):
                # Ignore trade updates and heartbeats.
                LOG.warning("%s %s: Unexpected trade message %s", self.id, pair, msg)
        else:
            self.is_initialized = True
