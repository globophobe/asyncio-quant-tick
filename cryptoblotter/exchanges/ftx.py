from decimal import Decimal

from cryptofeed.defines import BUY, LIQUIDATIONS, SELL, TRADES
from cryptofeed.exchanges import FTX
from cryptofeed.standards import timestamp_normalize


class FTXBlotter(FTX):
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
            price = Decimal(trade["price"])
            notional = Decimal(trade["size"])
            volume = price * notional
            await self.callback(
                TRADES,
                feed=self.id,
                uid=trade["id"],
                symbol=msg["market"],  # Do not normalize
                timestamp=float(timestamp_normalize(self.id, trade["time"])),
                price=price,
                volume=volume,
                notional=notional,
                tickRule=1 if trade["side"] == "buy" else -1,
            )
            if bool(trade["liquidation"]):
                await self.callback(
                    LIQUIDATIONS,
                    feed=self.id,
                    symbol=msg["market"],
                    side=BUY if trade["side"] == "buy" else SELL,
                    leaves_qty=Decimal(trade["size"]),
                    price=Decimal(trade["price"]),
                    order_id=trade["id"],
                    timestamp=float(timestamp_normalize(self.id, trade["time"])),
                    receipt_timestamp=timestamp,
                )
