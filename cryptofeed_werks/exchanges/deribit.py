from decimal import Decimal

from cryptofeed.defines import BUY, FILLED, LIQUIDATIONS, SELL, TRADES
from cryptofeed.exchanges import Deribit
from cryptofeed.types import Liquidation

from ..exchange import Exchange


class DeribitExchange(Exchange, Deribit):
    async def _trade(self, msg: dict, timestamp: float):
        """
        {
            "params":
            {
                "data":
                [
                    {
                        "trade_seq": 933,
                        "trade_id": "9178",
                        "timestamp": 1550736299753,
                        "tick_direction": 3,
                        "price": 3948.69,
                        "instrument_name": "BTC-PERPETUAL",
                        "index_price": 3930.73,
                        "direction": "sell",
                        "amount": 10
                    }
                ],
                "channel": "trades.BTC-PERPETUAL.raw"
            },
            "method": "subscription",
            "jsonrpc": "2.0"
        }
        """
        for trade in msg["params"]["data"]:
            price = Decimal(trade["price"])
            volume = Decimal(trade["amount"])
            notional = volume / price
            ts = self.timestamp_normalize(trade["timestamp"])
            trade = {
                "exchange": self.id,
                "uid": trade["trade_id"],
                "symbol": trade["instrument_name"],  # Do not normalize
                "timestamp": ts,
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if trade["direction"] == "buy" else -1,
            }
            await self.callback(TRADES, trade, ts)
            if "liquidation" in trade:
                liq = Liquidation(
                    self.id,
                    trade["instrument_name"],
                    BUY if trade["direction"] == "buy" else SELL,
                    Decimal(trade["amount"]),
                    Decimal(trade["price"]),
                    trade["trade_id"],
                    FILLED,
                    ts,
                    raw=trade,
                )
                await self.callback(LIQUIDATIONS, liq, ts)
