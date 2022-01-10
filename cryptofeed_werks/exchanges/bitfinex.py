from decimal import Decimal

from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bitfinex

from ..exchange import Exchange


class BitfinexExchange(Exchange, Bitfinex):
    def std_symbol_to_exchange_symbol(self, symbol: str) -> str:
        return "t" + symbol

    async def _trades(self, pair: str, msg: dict, timestamp: float):
        async def _trade_update(trade: list, timestamp: float):
            uid, ts, notional, price = trade
            price = Decimal(price)
            notional = abs(Decimal(notional))
            volume = price * notional
            ts = self.timestamp_normalize(ts)
            trade = {
                "exchange": self.id,
                "uid": uid,
                "symbol": pair,  # Do not normalize
                "timestamp": ts,
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": -1 if notional < 0 else 1,
            }
            await self.callback(TRADES, trade, ts)
