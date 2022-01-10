from decimal import Decimal
from functools import partial
from typing import Any

from cryptofeed.connection import AsyncConnection, WSAsyncConn
from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bybit

from ..exchange import Exchange


class BybitExchange(Exchange, Bybit):
    def connect(self) -> Any:
        """
        Linear PERPETUAL (USDT) public goes to USDT endpoint
        Linear PERPETUAL (USDT) private goes to USDTP endpoint
        Inverse PERPETUAL and FUTURES (USD) both private and public goes to USD endpoint
        """
        ret = []
        if any(pair.endswith("USDT") for pair in self.normalized_symbols):
            if any(
                self.is_authenticated_channel(self.exchange_channel_to_std(chan))
                for chan in self.subscription
            ):
                ret.append(
                    (
                        WSAsyncConn(self.address["USDTP"], self.id, **self.ws_defaults),
                        partial(self.subscribe, quote="USDTP"),
                        self.message_handler,
                        self.authenticate,
                    )
                )
            if any(
                not self.is_authenticated_channel(self.exchange_channel_to_std(chan))
                for chan in self.subscription
            ):
                ret.append(
                    (
                        WSAsyncConn(self.address["USDT"], self.id, **self.ws_defaults),
                        partial(self.subscribe, quote="USDT"),
                        self.message_handler,
                        self.__no_auth,
                    )
                )
        if any(pair.endswith("USD") for pair in self.normalized_symbols):
            ret.append(
                (
                    WSAsyncConn(self.address["USD"], self.id, **self.ws_defaults),
                    partial(self.subscribe, quote="USD"),
                    self.message_handler,
                    self.authenticate,
                )
            )
        return ret

    async def __no_auth(self, conn: AsyncConnection) -> None:
        pass

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
            ts = self.timestamp_normalize(ts)
            trade = {
                "exchange": self.id,
                "uid": trade["trade_id"],
                "symbol": trade["symbol"],  # Do not normalize
                "timestamp": ts,
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if trade["side"] == "Buy" else -1,
            }
            await self.callback(TRADES, trade, ts)
