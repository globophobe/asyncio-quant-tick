from decimal import Decimal
from typing import Tuple

from cryptofeed.defines import BUY, TRADES
from cryptofeed.exchanges import Bybit as BaseBybit

from ..feed import Feed


class Bybit(Feed, BaseBybit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable instrument filter
        self.websocket_endpoints[0].instrument_filter = None

    async def _trade(self, msg: dict, timestamp: float) -> Tuple[str, dict, float]:
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
            price = Decimal(trade["price"])
            volume = Decimal(trade["size"])
            notional = volume / price
            t = {
                "exchange": self.id.lower(),
                "uid": trade["trade_id"],
                "symbol": trade["symbol"],
                "timestamp": self.parse_datetime(trade["timestamp"]),
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if trade["side"].lower() == BUY else -1,
            }
            await self.callback(TRADES, t, timestamp)
