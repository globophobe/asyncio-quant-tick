#!/usr/bin/env python3
import sentry_sdk
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from decouple import config

from cryptofeed_werks.constants import SENTRY_DSN
from cryptofeed_werks.exchanges import (
    BinanceExchange,
    BitfinexExchange,
    BitflyerExchange,
    BitmexExchange,
    BybitExchange,
    CoinbaseExchange,
    FTXExchange,
    UpbitExchange,
)
from cryptofeed_werks.trades import (
    CandleCallback,
    MinVolumeCallback,
    NonSequentialIntegerTradeCallback,
    SequentialIntegerTradeCallback,
    TradeCallback,
)

sequential_integer_exchanges = {
    BinanceExchange: ["BTC-USDT"],
    CoinbaseExchange: ["BTC-USD"],
}

non_sequential_integer_exchanges = {
    FTXExchange: ["BTC-PERP"],
    BitfinexExchange: ["BTCUSD"],
}

other_exchanges = {
    BitmexExchange: ["XBTUSD"],
    BybitExchange: ["BTCUSDT"],
    # DeribitExchange: ["BTC-PERPETUAL"],
    UpbitExchange: ["BTC-KRW"],
}


async def trades(trade):
    print(trade)


def get_callback(exchange, min_volume=1000, window_seconds=60):
    if exchange == BitflyerExchange:
        min_volume *= 100
    elif exchange == UpbitExchange:
        min_volume *= 1000
    candle_callback = CandleCallback(trades, window_seconds=window_seconds)
    return MinVolumeCallback(
        candle_callback, min_volume=min_volume, window_seconds=window_seconds
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
