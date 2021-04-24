from decimal import Decimal

from cryptofeed.defines import BUY, LIQUIDATIONS, SELL, TRADES
from cryptofeed.exchanges import Deribit
from cryptofeed.standards import timestamp_normalize


class DeribitBlotter(Deribit):
    async def _trade(self, msg: dict, timestamp: float):
        """
        {
            "params":
            {
                "data":
                [
                    {
                        "trade_seq": 933,
                        "trade_id": "9178",
                        "timestamp": 1550736299753,
                        "tick_direction": 3,
                        "price": 3948.69,
                        "instrument_name": "BTC-PERPETUAL",
                        "index_price": 3930.73,
                        "direction": "sell",
                        "amount": 10
                    }
                ],
                "channel": "trades.BTC-PERPETUAL.raw"
            },
            "method": "subscription",
            "jsonrpc": "2.0"
        }
        """
        for trade in msg["params"]["data"]:
            price = Decimal(trade["price"])
            volume = Decimal(trade["amount"])
            notional = volume / price
            await self.callback(
                TRADES,
                feed=self.id,
                uid=trade["trade_id"],
                symbol=trade["instrument_name"],  # Do not normalize
                timestamp=timestamp_normalize(self.id, trade["timestamp"]),
                price=price,
                volume=volume,
                notional=notional,
                tickRule=1 if trade["direction"] == "buy" else -1,
            )
            if "liquidation" in trade:
                await self.callback(
                    LIQUIDATIONS,
                    feed=self.id,
                    symbol=trade["instrument_name"],
                    side=BUY if trade["direction"] == "buy" else SELL,
                    leaves_qty=Decimal(trade["amount"]),
                    price=Decimal(trade["price"]),
                    order_id=trade["trade_id"],
                    timestamp=timestamp_normalize(self.id, trade["timestamp"]),
                    receipt_timestamp=timestamp,
                )
