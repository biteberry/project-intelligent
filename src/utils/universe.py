def get_universe(market_context: str = None):
    """
    Mock function to return active universe of symbols.
    In a real scenario, this would read from DynamoDB or a static config.
    """
    universe = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT"]
    if market_context:
        return [sym for sym in universe if get_market_context(sym) == market_context]
    return universe

def get_market_context(symbol: str) -> str:
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return "india"
    return "us"
