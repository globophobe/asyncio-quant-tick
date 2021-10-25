#!/usr/bin/env python3

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from cryptofeed_werks.exchanges import CoinbaseExchange
from cryptofeed_werks.trades import SequentialIntegerTradeCallback, ThreshCallback
from cryptofeed_werks.trades.constants import VOLUME


async def trades(trade):
    print(trade)


if __name__ == "__main__":
    fh = FeedHandler()
    fh.add_feed(
        CoinbaseExchange(
            symbols=["BTC-USD"],
            channels=[TRADES],
            callbacks={
                TRADES: SequentialIntegerTradeCallback(
                    ThreshCallback(
                        trades,
                        thresh_attr=VOLUME,
                        thresh_value=1000,
                        window_seconds=60,
                    )
                )
            },
        )
    )
    fh.run()
