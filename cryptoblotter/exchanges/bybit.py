from decimal import Decimal

from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bybit
from cryptofeed.standards import timestamp_normalize


class BybitBlotter(Bybit):
    async def _trade(self, msg: dict, timestamp: float):
        """
        {"topic":"trade.BTCUSD",
        "data":[
            {
                "timestamp":"2019-01-22T15:04:33.461Z",
                "symbol":"BTCUSD",
                "side":"Buy",
                "size":980,
                "price":3563.5,
                "tick_direction":"PlusTick",
                "trade_id":"9d229f26-09a8-42f8-aff3-0ba047b0449d",
                "cross_seq":163261271}]}
        """
        data = msg["data"]
        for trade in data:
            if isinstance(trade["trade_time_ms"], str):
                ts = int(trade["trade_time_ms"])
            else:
                ts = trade["trade_time_ms"]
            price = Decimal(trade["price"])
            volume = Decimal(trade["size"])
            notional = volume / price
            await self.callback(
                TRADES,
                feed=self.id,
                uid=trade["trade_id"],
                symbol=trade["symbol"],  # Do not normalize
                timestamp=timestamp_normalize(self.id, ts),
                price=price,
                volume=volume,
                notional=notional,
                tickRule=1 if trade["side"] == "Buy" else -1,
            )
