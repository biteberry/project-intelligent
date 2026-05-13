# Unit tests for Lambda SSM dispatcher
# Issue #72: Test for handler.py

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/lambda/ssm_dispatcher')))
import handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_env(instance_id="i-004ede57a842280fe", doc_name="project-intelligent-pipeline"):
    os.environ["EC2_INSTANCE_ID"] = instance_id
    os.environ["SSM_DOCUMENT_NAME"] = doc_name


def _clear_env():
    os.environ.pop("EC2_INSTANCE_ID", None)
    os.environ.pop("SSM_DOCUMENT_NAME", None)


@pytest.fixture(autouse=True)
def reset_ssm_client():
    """Reset the cached SSM client before each test."""
    handler._ssm = None
    yield
    handler._ssm = None


# ---------------------------------------------------------------------------
# Happy path — success scenarios
# ---------------------------------------------------------------------------

@patch('handler._get_ssm_client')
def test_daily_event_returns_200_with_command_id(mock_ssm):
    """Daily EventBridge trigger returns 200 and logs command ID."""
    _set_env()
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-daily-001"}}

    result = handler.lambda_handler({"detail-type": "Scheduled Event - Daily"}, MagicMock())

    assert result["statusCode"] == 200
    assert "cmd-daily-001" in result["body"]


@patch('handler._get_ssm_client')
def test_weekly_event_returns_200_with_command_id(mock_ssm):
    """Weekly EventBridge trigger returns 200 and logs command ID."""
    _set_env()
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-weekly-001"}}

    result = handler.lambda_handler({"detail-type": "Scheduled Event - Weekly"}, MagicMock())

    assert result["statusCode"] == 200
    assert "cmd-weekly-001" in result["body"]


@patch('handler._get_ssm_client')
def test_ssm_send_command_called_once(mock_ssm):
    """SSM send_command is called exactly once per invocation."""
    _set_env()
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-abc"}}

    handler.lambda_handler({"detail-type": "Scheduled Event - Daily"}, MagicMock())

    mock_ssm.return_value.send_command.assert_called_once()


@patch('handler._get_ssm_client')
def test_ssm_send_command_uses_correct_instance_id(mock_ssm):
    """SSM send_command receives correct EC2 instance ID from env var."""
    _set_env(instance_id="i-004ede57a842280fe")
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-abc"}}

    handler.lambda_handler({"detail-type": "Scheduled Event - Daily"}, MagicMock())

    call_kwargs = mock_ssm.return_value.send_command.call_args[1]
    assert call_kwargs["InstanceIds"] == ["i-004ede57a842280fe"]


@patch('handler._get_ssm_client')
def test_ssm_send_command_uses_correct_document_name(mock_ssm):
    """SSM send_command receives correct document name from env var."""
    _set_env(doc_name="project-intelligent-pipeline")
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-abc"}}

    handler.lambda_handler({"detail-type": "Scheduled Event - Daily"}, MagicMock())

    call_kwargs = mock_ssm.return_value.send_command.call_args[1]
    assert call_kwargs["DocumentName"] == "project-intelligent-pipeline"


# ---------------------------------------------------------------------------
# Event type parsing
# ---------------------------------------------------------------------------

@patch('handler._get_ssm_client')
def test_daily_event_type_detected_in_parameters(mock_ssm):
    """'daily' in detail-type maps to event_type parameter = 'daily'."""
    _set_env()
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-x"}}

    handler.lambda_handler({"detail-type": "Scheduled Event - Daily"}, MagicMock())

    call_kwargs = mock_ssm.return_value.send_command.call_args[1]
    assert call_kwargs["Parameters"]["eventType"] == ["daily"]


@patch('handler._get_ssm_client')
def test_weekly_event_type_detected_in_parameters(mock_ssm):
    """'weekly' in detail-type maps to event_type parameter = 'weekly'."""
    _set_env()
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-x"}}

    handler.lambda_handler({"detail-type": "Scheduled Event - Weekly"}, MagicMock())

    call_kwargs = mock_ssm.return_value.send_command.call_args[1]
    assert call_kwargs["Parameters"]["eventType"] == ["weekly"]


@patch('handler._get_ssm_client')
def test_unknown_event_type_fallback(mock_ssm):
    """Event with no recognisable detail-type falls back to 'unknown'."""
    _set_env()
    mock_ssm.return_value.send_command.return_value = {"Command": {"CommandId": "cmd-x"}}

    handler.lambda_handler({"source": "aws.events"}, MagicMock())  # no detail-type

    call_kwargs = mock_ssm.return_value.send_command.call_args[1]
    assert call_kwargs["Parameters"]["eventType"] == ["unknown"]


# ---------------------------------------------------------------------------
# Missing environment variables
# ---------------------------------------------------------------------------

@patch('handler._get_ssm_client')
def test_missing_ec2_instance_id_raises(mock_ssm):
    """Missing EC2_INSTANCE_ID raises and does not call SSM."""
    _clear_env()
    os.environ["SSM_DOCUMENT_NAME"] = "my-doc"

    with pytest.raises(Exception, match="Missing required environment variables"):
        handler.lambda_handler({"detail-type": "Daily"}, MagicMock())

    mock_ssm.return_value.send_command.assert_not_called()


@patch('handler._get_ssm_client')
def test_missing_ssm_document_name_raises(mock_ssm):
    """Missing SSM_DOCUMENT_NAME raises and does not call SSM."""
    _clear_env()
    os.environ["EC2_INSTANCE_ID"] = "i-004ede57a842280fe"

    with pytest.raises(Exception, match="Missing required environment variables"):
        handler.lambda_handler({"detail-type": "Daily"}, MagicMock())

    mock_ssm.return_value.send_command.assert_not_called()


@patch('handler._get_ssm_client')
def test_both_env_vars_missing_raises(mock_ssm):
    """Both env vars missing raises exception."""
    _clear_env()

    with pytest.raises(Exception, match="Missing required environment variables"):
        handler.lambda_handler({"detail-type": "Daily"}, MagicMock())

    mock_ssm.return_value.send_command.assert_not_called()


# ---------------------------------------------------------------------------
# SSM failure
# ---------------------------------------------------------------------------

@patch('handler._get_ssm_client')
def test_ssm_exception_propagates(mock_ssm):
    """SSM send_command failure is re-raised to Lambda runtime."""
    _set_env()
    mock_ssm.return_value.send_command.side_effect = Exception("SSM service unavailable")

    with pytest.raises(Exception, match="SSM service unavailable"):
        handler.lambda_handler({"detail-type": "Daily"}, MagicMock())
