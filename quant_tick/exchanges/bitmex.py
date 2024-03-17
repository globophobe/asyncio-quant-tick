from collections import defaultdict
from decimal import Decimal
from typing import Dict, Tuple

from cryptofeed.defines import BUY, FUTURES, PERPETUAL, SPOT, TRADES
from cryptofeed.exchanges import Bitmex as BaseBitmex
from cryptofeed.exchanges.bitmex import LOG
from cryptofeed.symbols import Symbol

from ..feed import Feed


class Bitmex(Feed, BaseBitmex):
    """Bitmex."""

    @classmethod
    def _parse_symbol_data(cls, data: dict) -> Tuple[Dict, Dict]:
        """Parse symbol data."""
        ret = {}
        info = defaultdict(dict)

        for entry in data:
            base = entry["rootSymbol"].replace("XBT", "BTC")
            quote = entry["quoteCurrency"].replace("XBT", "BTC")

            if entry["typ"] == "FFWCSX":
                stype = PERPETUAL
            elif entry["typ"] == "FFCCSX":
                stype = FUTURES
            elif entry["typ"] == "IFXXXP":
                stype = SPOT
            else:
                LOG.info(
                    "Unsupported type %s for instrument %s",
                    entry["typ"],
                    entry["symbol"],
                )

            # region custom
            s = Symbol(base, quote, type=stype, expiry_date=entry.get("expiry"))
            # endregion
            if s.normalized not in ret:
                ret[s.normalized] = entry["symbol"]
                info["tick_size"][s.normalized] = entry["tickSize"]
                info["instrument_type"][s.normalized] = stype
                info["is_quanto"][s.normalized] = entry["isQuanto"]
            else:
                LOG.info(
                    "Ignoring duplicate symbol mapping %s<=>%s",
                    s.normalized,
                    entry["symbol"],
                )

        return ret, info

    async def _trade(self, msg: dict, timestamp: float) -> Tuple[str, dict, float]:
        """
        trade msg example
        {
            'timestamp': '2018-05-19T12:25:26.632Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 40,
            'price': 8335,
            'tickDirection': 'PlusTick',
            'trdMatchID': '5f4ecd49-f87f-41c0-06e3-4a9405b9cdde',
            'grossValue': 479920,
            'homeNotional': Decimal('0.0047992'),
            'foreignNotional': 40
        }
        """
        for data in msg["data"]:
            price = Decimal(data["price"])
            volume = Decimal(data["foreignNotional"])
            notional = volume / price
            t = {
                "exchange": self.id.lower(),
                "uid": data["trdMatchID"],
                "symbol": data["symbol"],
                "timestamp": self.parse_datetime(data["timestamp"]),
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if data["side"].lower() == BUY else -1,
            }
            await self.callback(TRADES, t, timestamp)
