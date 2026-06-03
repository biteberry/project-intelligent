def get_universe():
    """
    Mock function to return active universe of symbols.
    In a real scenario, this would read from DynamoDB or a static config.
    """
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT"]
