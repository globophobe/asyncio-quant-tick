from decimal import Decimal

from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bitmex

from ..exchange import Exchange


class BitmexExchange(Exchange, Bitmex):
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
            price = Decimal(data["price"])
            volume = Decimal(data["foreignNotional"])
            notional = volume / price
            ts = self.timestamp_normalize(data["timestamp"])
            trade = {
                "exchange": self.id,
                "uid": data["trdMatchID"],
                "symbol": data["symbol"],  # Do not normalize
                "timestamp": ts,
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if data["side"] == "Buy" else -1,
            }
            await self.callback(TRADES, trade, ts)
