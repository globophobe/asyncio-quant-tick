from .candles import CandleCallback
from .thresh import ThreshCallback
from .trades import (
    NonSequentialIntegerTradeCallback,
    SequentialIntegerTradeCallback,
    TradeCallback,
)

# Optional
try:
    from .gcppubsub import GCPPubSubTradeCallback
except ImportError:
    pass
try:
    from .firestore import FirestoreTradeCallback
except ImportError:
    pass

__all__ = [
    "FirestoreTradeCallback",
    "GCPPubSubTradeCallback",
    "CandleCallback",
    "TradeCallback",
    "ThreshCallback",
    "SequentialIntegerTradeCallback",
    "NonSequentialIntegerTradeCallback",
]
