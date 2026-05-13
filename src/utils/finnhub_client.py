import requests
from utils.secrets import get_secret

FINNHUB_SECRET_NAME = "/project-intelligent/finnhub/api-key"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubClient:
    """Finnhub API client. API key loaded from AWS Secrets Manager at init."""

    def __init__(self, region_name: str = "ap-south-1"):
        self._api_key = get_secret(FINNHUB_SECRET_NAME, region_name=region_name)

    def get_quote(self, symbol: str) -> dict:
        """Get real-time quote for a stock symbol.

        Args:
            symbol: Stock ticker, e.g. 'AAPL'

        Returns:
            Quote dict with keys: c (current), h (high), l (low), o (open), pc (prev close)
        """
        response = requests.get(
            f"{FINNHUB_BASE_URL}/quote",
            params={"symbol": symbol, "token": self._api_key},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
