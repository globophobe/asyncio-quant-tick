from typing import Tuple

from cryptofeed.defines import BUY, TRADES
from cryptofeed.exchanges import Bitflyer as BaseBitflyer

from ..feed import Feed


class Bitflyer(Feed, BaseBitflyer):
    def std_symbol_to_exchange_symbol(self, symbol: str) -> str:
        """Standard symbol to exchange symbol."""
        return symbol.replace("/", "_")

    def exchange_symbol_to_std_symbol(self, symbol: str) -> str:
        """Exchange symbol to standard symbol."""
        return symbol.replace("_", "/")

    async def _trade(self, msg: dict, timestamp: float) -> Tuple[str, dict, float]:
        """
        {
            "jsonrpc":"2.0",
            "method":"channelMessage",
            "params":{
                "channel":"lightning_executions_BTC_JPY",
                "message":[
                    {
                        "id":2084881071,
                        "side":"BUY",
                        "price":2509125.0,
                        "size":0.005,
                        "exec_date":"2020-12-25T21:36:22.8840579Z",
                        "buy_child_order_acceptance_id":"JRF20201225-213620-004123",
                        "sell_child_order_acceptance_id":"JRF20201225-213620-133314"
                    }
                ]
            }
        }
        """
        pair = msg["params"]["channel"][21:]
        for update in msg["params"]["message"]:
            price = update["price"]
            notional = update["size"]
            volume = price * notional
            t = {
                "exchange": self.id.lower(),
                "uid": update["id"],
                "symbol": self.exchange_symbol_to_std_symbol(pair),
                "timestamp": self.parse_datetime(update["exec_date"]),
                "price": price,
                "volume": volume,
                "notional": notional,
                "tickRule": 1 if update["side"] == BUY else -1,
            }
            await self.callback(TRADES, t, timestamp)
