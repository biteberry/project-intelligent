# Unit tests for Lambda SSM dispatcher
# Issue #72: Test for handler.py

import os
import sys
import types
import pytest
from unittest.mock import patch, MagicMock

# Import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/lambda/ssm_dispatcher')))
import handler

@patch('handler.ssm')
def test_lambda_handler_success(mock_ssm):
    # Arrange: mock environment and SSM
    os.environ['EC2_INSTANCE_ID'] = 'i-1234567890abcdef0'
    os.environ['SSM_DOCUMENT_NAME'] = 'MySSMDocument'
    mock_ssm.send_command.return_value = {'Command': {'CommandId': 'cmd-1234'}}

    # EventBridge event for daily trigger
    event = {'detail-type': 'Scheduled Event - Daily'}
    context = MagicMock()

    # Act
    result = handler.lambda_handler(event, context)

    # Assert
    assert result['statusCode'] == 200
    assert 'cmd-1234' in result['body']
    mock_ssm.send_command.assert_called_once()

@patch('handler.ssm')
def test_lambda_handler_missing_env(mock_ssm):
    # Arrange: remove env vars
    if 'EC2_INSTANCE_ID' in os.environ:
        del os.environ['EC2_INSTANCE_ID']
    if 'SSM_DOCUMENT_NAME' in os.environ:
        del os.environ['SSM_DOCUMENT_NAME']
    event = {'detail-type': 'Scheduled Event - Daily'}
    context = MagicMock()

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        handler.lambda_handler(event, context)
    assert 'Missing required environment variables' in str(excinfo.value)
