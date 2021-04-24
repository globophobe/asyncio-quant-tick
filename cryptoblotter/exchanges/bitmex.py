from decimal import Decimal

from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bitmex
from cryptofeed.standards import timestamp_normalize


class BitmexBlotter(Bitmex):
    async def _trade(self, msg: dict, timestamp: float):
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
            ts = timestamp_normalize(self.id, data["timestamp"])
            price = Decimal(data["price"])
            volume = Decimal(data["foreignNotional"])
            notional = volume / price
            await self.callback(
                TRADES,
                feed=self.id,
                uid=data["trdMatchID"],
                symbol=data["symbol"],  # Do not normalize
                timestamp=ts,
                price=price,
                volume=volume,
                notional=notional,
                tickRule=1 if data["side"] == "Buy" else -1,
            )
