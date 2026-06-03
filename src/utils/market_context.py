def get_market_context(symbol: str) -> str:
    """
    Determine the market context based on the ticker suffix.
    .NS = India (NSE)
    .BO = India (BSE)
    no suffix = US
    """
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return "india"
    return "us"
