from decimal import Decimal

from cryptofeed.defines import BUY, FILLED, LIQUIDATIONS, SELL, TRADES
from cryptofeed.exchanges import FTX
from cryptofeed.types import Liquidation

from ..exchange import Exchange


class FTXExchange(Exchange, FTX):
    async def _trade(self, msg: dict, timestamp: float):
        """
        {
            "channel": "trades",
            "market": "BTC-PERP",
            "type": "update",
            "data": [{
                "id": null,
                "price": 10738.75,
                "size": 0.3616,
                "side": "buy",
                "liquidation": false,
                "time": "2019-08-03T12:20:19.170586+00:00"
            }]
        }
        """
        for trade in msg["data"]:
            ts = float(self.timestamp_normalize(trade["time"]))
            price = Decimal(trade["price"])
            notional = Decimal(trade["size"])
            volume = price * notional
            t = {
                "exchange": self.id,
                "uid": trade["id"],
                "symbol": msg["market"],  # Do not normalize
                "timestamp": ts,
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if trade["side"] == "buy" else -1,
            }
            await self.callback(TRADES, t, ts)
            if bool(trade["liquidation"]):
                liq = Liquidation(
                    self.id,
                    msg["market"],
                    BUY if trade["side"] == "buy" else SELL,
                    Decimal(trade["size"]),
                    Decimal(trade["price"]),
                    str(trade["id"]),
                    FILLED,
                    ts,
                    raw=trade,
                )
                await self.callback(LIQUIDATIONS, liq, ts)
