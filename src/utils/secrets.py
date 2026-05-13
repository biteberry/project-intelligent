import boto3
from botocore.exceptions import ClientError

_cache: dict = {}


def get_secret(secret_name: str, region_name: str = "ap-south-1") -> str:
    """Retrieve a secret value from AWS Secrets Manager.

    Caches the result in memory for the process lifetime to avoid
    repeated API calls on every invocation.

    Args:
        secret_name: Full secret name, e.g. /project-intelligent/finnhub/api-key
        region_name: AWS region where the secret is stored.

    Returns:
        The secret string value.

    Raises:
        ClientError: If the secret does not exist or access is denied.
    """
    if secret_name in _cache:
        return _cache[secret_name]

    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret_value = response["SecretString"]
    _cache[secret_name] = secret_value
    return secret_value


def clear_cache() -> None:
    """Clear the in-memory secrets cache. Useful for testing."""
    _cache.clear()
