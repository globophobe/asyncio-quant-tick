from decimal import Decimal

from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Binance
from cryptofeed.standards import timestamp_normalize


class BinanceBlotter(Binance):
    def __init__(self, *args, **kwargs):
        """
        Cryptofeed uses aggregate trade streams. Raw trades are preferable,
        to calculate VWAP. Unfortunately, the raw trade stream is
        absolute trash and is frequently missing trades.
        """
        super().__init__(*args, **kwargs)
        self.last_id = None

    async def _trade(self, msg: dict, timestamp: float):
        """
        {
          "e": "aggTrade",  // Event type
          "E": 123456789,   // Event time
          "s": "BNBBTC",    // Symbol
          "a": 12345,       // Aggregate trade ID
          "p": "0.001",     // Price
          "q": "100",       // Quantity
          "f": 100,         // First trade ID
          "l": 105,         // Last trade ID
          "T": 123456785,   // Trade time
          "m": true,        // Is the buyer the market maker?
          "M": true         // Ignore
        }
        """
        if not self.last_id:
            self.last_id = int(msg["l"])
            is_sequential = True
        else:
            is_sequential = int(msg["f"]) == self.last_id + 1
            self.last_id = int(msg["l"])
        price = Decimal(msg["p"])
        notional = Decimal(msg["q"])
        volume = price * notional
        ticks = msg["l"] - msg["f"] + 1
        assert ticks >= 1, "Ticks not greater than or equal to 1"
        await self.callback(
            TRADES,
            feed=self.id,
            uid=int(msg["l"]),  # Last trade ID
            symbol=msg["s"],  # Do not normalize
            timestamp=timestamp_normalize(self.id, msg["E"]),
            price=price,
            volume=volume,
            notional=notional,
            tickRule=-1 if msg["m"] else 1,
            ticks=ticks,
            isSequential=is_sequential,
        )
