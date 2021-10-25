#!/usr/bin/env python3
import os

import sentry_sdk
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

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
    FirestoreTradeCallback,
    NonSequentialIntegerTradeCallback,
    SequentialIntegerTradeCallback,
    ThreshCallback,
    TradeCallback,
)
from cryptofeed_werks.trades.constants import VOLUME
from cryptofeed_werks.utils import is_local, set_environment

sequential_integer_exchanges = {
    BinanceExchange: ["BTC-USDT", "ETH-USDT"],
    CoinbaseExchange: ["BTC-USD", "ETH-USD"],
}

non_sequential_integer_exchanges = {
    FTXExchange: ["BTC-PERP", "ETH-PERP"],
    BitfinexExchange: ["BTC-USDT", "ETH-USDT"],
}

other_exchanges = {
    BitmexExchange: ["BTC-USD", "ETH-USD"],
    BybitExchange: ["BTC-USD", "ETH-USD"],
    # DeribitExchange: ["BTC-PERPETUAL", "ETH-PERPETUAL"],
    UpbitExchange: ["BTC-KRW", "ETH-KRW"],
}


def get_callback(
    exchange, thresh_attr=VOLUME, thresh_value=1000, window_seconds=60, top_n=25
):
    if exchange == BitflyerExchange:
        thresh_value *= 100
    elif exchange == UpbitExchange:
        thresh_value *= 1000
    firestore_callback = FirestoreTradeCallback(None, key="candles")  # TODO: Fix this
    candle_callback = CandleCallback(
        firestore_callback, window_seconds=window_seconds, top_n=top_n
    )
    return ThreshCallback(
        candle_callback,
        thresh_attr=VOLUME,
        thresh_value=thresh_value,
        window_seconds=window_seconds,
    )


if __name__ == "__main__":
    if is_local():
        set_environment()

    sentry_sdk.init(
        os.environ.get(SENTRY_DSN),
        traces_sample_rate=1.0,
    )

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
