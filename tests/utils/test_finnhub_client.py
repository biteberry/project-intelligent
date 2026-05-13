import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.finnhub_client import FinnhubClient
from utils.secrets import clear_cache


@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield
    clear_cache()


class TestFinnhubClient:

    def test_init_loads_key_from_secrets_manager(self):
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {"SecretString": "fake-token-for-testing"}

        with patch("boto3.client", return_value=mock_secrets_client):
            client = FinnhubClient()

        mock_secrets_client.get_secret_value.assert_called_once_with(
            SecretId="/project-intelligent/finnhub/api-key"
        )
        assert client._api_key == "fake-token-for-testing"

    def test_get_quote_returns_data(self):
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {"SecretString": "test-api-key"}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "c": 299.33, "h": 300.37, "l": 293.5, "o": 294.075, "pc": 294.8
        }
        mock_response.raise_for_status.return_value = None

        with patch("boto3.client", return_value=mock_secrets_client):
            with patch("requests.get", return_value=mock_response) as mock_get:
                client = FinnhubClient()
                result = client.get_quote("AAPL")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "AAPL" in str(call_kwargs)
        assert result["c"] == 299.33

    def test_get_quote_uses_api_key_from_secrets(self):
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {"SecretString": "fake-token-xyz"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"c": 100.0}
        mock_response.raise_for_status.return_value = None

        with patch("boto3.client", return_value=mock_secrets_client):
            with patch("requests.get", return_value=mock_response) as mock_get:
                client = FinnhubClient()
                client.get_quote("TSLA")

        params = mock_get.call_args.kwargs.get("params", {})
        assert params.get("token") == "fake-token-xyz"
