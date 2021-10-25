from decimal import Decimal

from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bitfinex


class BitfinexExchange(Bitfinex):
    async def _trades(self, pair: str, msg: dict, timestamp: float):
        async def _trade_update(trade: list, timestamp: float):
            uid, ts, notional, price = trade
            price = Decimal(price)
            notional = abs(Decimal(notional))
            volume = price * notional
            await self.callback(
                TRADES,
                feed=self.id,
                uid=uid,
                symbol=pair,  # Do not normalize
                timestamp=self.timestamp_normalize(ts),
                price=price,
                volume=volume,
                notional=notional,
                tickRule=-1 if notional < 0 else 1,
            )
