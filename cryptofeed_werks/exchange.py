from cryptofeed.exchange import Exchange as CryptofeedExchange


class Exchange(CryptofeedExchange):
    def std_symbol_to_exchange_symbol(self, symbol: str) -> str:
        return symbol

    def exchange_symbol_to_std_symbol(self, symbol: str) -> str:
        return symbol
