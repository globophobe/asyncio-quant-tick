#!/usr/bin/env python3
import sentry_sdk
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from decouple import config

from cryptofeed_werks.constants import SENTRY_DSN
from cryptofeed_werks.exchanges import (
    Binance,
    Bitfinex,
    Bitflyer,
    Bitmex,
    Bybit,
    Coinbase,
    Upbit,
)
from cryptofeed_werks.trades import (
    CandleCallback,
    NonSequentialIntegerTradeCallback,
    SequentialIntegerTradeCallback,
    SignificantTradeCallback,
    TradeCallback,
)

sequential_integer_exchanges = {Binance: ["BTCUSDT"], Coinbase: ["BTC-USD"]}

non_sequential_integer_exchanges = {Bitfinex: ["BTCUSD"]}

other_exchanges = {
    Bitmex: ["XBTUSD"],
    Bybit: ["BTCUSD"],
    Bitflyer: ["BTC/JPY"],
    Upbit: ["BTC-KRW"],
}


async def candles(candle: dict, timestamp: float) -> None:
    """Candles."""
    print(candle)


def get_callback(exchange, min_volume=1_000, window_seconds=60):
    if exchange == Bitflyer:
        min_volume *= 100
    elif exchange == Upbit:
        min_volume *= 1000
    candle_callback = CandleCallback(candles, window_seconds=window_seconds)
    return SignificantTradeCallback(
        candle_callback,
        significant_trade_filter=min_volume,
        window_seconds=window_seconds,
    )


if __name__ == "__main__":
    sentry_sdk.init(config(SENTRY_DSN), traces_sample_rate=1.0)

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
