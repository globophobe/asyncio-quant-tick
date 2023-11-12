#!/usr/bin/env python3
from typing import Callable

import sentry_sdk
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from decouple import config

from cryptofeed_experiments.exchanges import (
    Binance,
    Bitfinex,
    Bitflyer,
    Bitmex,
    Bybit,
    Coinbase,
    Upbit,
)
from cryptofeed_experiments.trades import (
    NonSequentialIntegerTradeCallback,
    SequentialIntegerTradeCallback,
    SignificantTradeCallback,
    TradeCallback,
    TradeClusterCallback,
)

sequential_integer_exchanges = {Binance: ["BTCUSDT"], Coinbase: ["BTC-USD"]}

non_sequential_integer_exchanges = {Bitfinex: ["BTCUSD"]}

other_exchanges = {
    Bitmex: ["XBTUSD"],
    Bybit: ["BTCUSD"],
    Bitflyer: ["BTC/JPY"],
    Upbit: ["BTC-KRW"],
}


async def trades(trade: dict, timestamp: float) -> None:
    """Trades."""
    print(trade)


def get_callback(exchange: any, significant_trade_filter: int = 1_000) -> Callable:
    """Get callback."""
    if exchange == Bitflyer:
        significant_trade_filter *= 100
    elif exchange == Upbit:
        significant_trade_filter *= 1000
    return SignificantTradeCallback(
        TradeClusterCallback(trades), significant_trade_filter=significant_trade_filter
    )


if __name__ == "__main__":
    sentry_sdk.init(config("SENTRY_DSN"), traces_sample_rate=1.0)

    fh = FeedHandler()

    for exchange, symbols in sequential_integer_exchanges.items():
        callback = SequentialIntegerTradeCallback(get_callback(exchange))
        fh.add_feed(
            exchange(
                symbols=symbols,
                channels=[TRADES],
                callbacks={TRADES: callback},
            )
        )
    for exchange, symbols in non_sequential_integer_exchanges.items():
        callback = NonSequentialIntegerTradeCallback(get_callback(exchange))
        fh.add_feed(
            exchange(
                symbols=symbols,
                channels=[TRADES],
                callbacks={TRADES: callback},
            )
        )
    for exchange, symbols in other_exchanges.items():
        callback = TradeCallback(get_callback(exchange))
        fh.add_feed(
            exchange(
                symbols=symbols,
                channels=[TRADES],
                callbacks={TRADES: callback},
            )
        )

    fh.run()
