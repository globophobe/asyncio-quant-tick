#!/usr/bin/env python3

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from cryptoblotter.exchanges import (
    BinanceBlotter,
    BitfinexBlotter,
    BitflyerBlotter,
    BitmexBlotter,
    BybitBlotter,
    CoinbaseBlotter,
    DeribitBlotter,
    FTXBlotter,
    UpbitBlotter,
)
from cryptoblotter.trades import (
    CandleCallback,
    FirestoreTradeCallback,
    GCPPubSubTradeCallback,
    NonSequentialIntegerTradeCallback,
    SequentialIntegerTradeCallback,
    ThreshCallback,
    TradeCallback,
)
from cryptoblotter.trades.constants import VOLUME

sequential_integer_blotters = {
    BinanceBlotter: ["BTC-USDT", "ETH-USDT"],
    CoinbaseBlotter: ["BTC-USD", "ETH-USD"],
}

non_sequential_integer_blotters = {
    FTXBlotter: ["BTC-PERP", "ETH-PERP"],
    BitfinexBlotter: ["BTC-USDT", "ETH-USDT"],
}

blotters = {
    BitmexBlotter: ["BTC-USD", "ETH-USD"],
    BybitBlotter: ["BTC-USD", "ETH-USD"],
    # DeribitBlotter: ["BTC-PERPETUAL", "ETH-PERPETUAL"],
    UpbitBlotter: ["BTC-KRW", "ETH-KRW"],
}


def get_callback(
    blotter, thresh_attr=VOLUME, thresh_value=1000, window_seconds=60, top_n=10
):
    if blotter == BitflyerBlotter:
        thresh_value *= 100
    elif blotter == UpbitBlotter:
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
    fh = FeedHandler()

    for blotter, symbols in sequential_integer_blotters.items():
        callback = SequentialIntegerTradeCallback(get_callback(blotter))
        fh.add_feed(
            blotter(
                symbols=symbols,
                channels=[TRADES],
                callbacks={TRADES: callback},
            )
        )
    for blotter, symbols in non_sequential_integer_blotters.items():
        callback = NonSequentialIntegerTradeCallback(get_callback(blotter))
        fh.add_feed(
            blotter(
                symbols=symbols,
                channels=[TRADES],
                callbacks={TRADES: callback},
            )
        )
    for blotter, symbols in blotters.items():
        callback = TradeCallback(get_callback(blotter))
        fh.add_feed(
            blotter(
                symbols=symbols,
                channels=[TRADES],
                callbacks={TRADES: callback},
            )
        )

    fh.run()
