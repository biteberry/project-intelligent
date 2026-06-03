import pandas_market_calendars as mcal
from datetime import datetime
import pandas as pd

def is_trading_day(date_str: str, market: str = 'BSE') -> bool:
    """
    Check if a given date is a valid trading day for the specified market.
    Defaults to BSE (Bombay Stock Exchange) which mirrors NSE holiday schedules.
    """
    # Initialize the calendar
    calendar = mcal.get_calendar(market)
    
    # Parse the input date
    dt = pd.Timestamp(date_str)
    
    # Get valid trading days for the week around the date to handle timezone/boundary edge cases safely
    schedule = calendar.schedule(start_date=dt - pd.Timedelta(days=1), end_date=dt + pd.Timedelta(days=1))
    
    # If the date is in the schedule index, it's a trading day
    return dt.strftime('%Y-%m-%d') in schedule.index.strftime('%Y-%m-%d')

if __name__ == "__main__":
    # Test script locally
    test_dates = [
        "2026-01-26", # Republic Day (Holiday)
        "2026-06-03", # Normal Wednesday
        "2026-06-06"  # Saturday (Weekend)
    ]
    for d in test_dates:
        print(f"{d} is trading day? {is_trading_day(d)}")
