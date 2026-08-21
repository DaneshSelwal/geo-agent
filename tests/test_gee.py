import pytest
from unittest.mock import patch, MagicMock

from app.gee import initialize_gee

@patch('app.gee.ee.Initialize')
@patch('app.gee.ee.Authenticate')
def test_initialize_gee_success(mock_authenticate, mock_initialize):
    """
    Test successful initialization without exception.
    """
    project_id = "test-project-id"

    initialize_gee(project_id)

    mock_initialize.assert_called_once_with(project=project_id)
    mock_authenticate.assert_not_called()

@patch('app.gee.ee.Initialize')
@patch('app.gee.ee.Authenticate')
def test_initialize_gee_fallback_authenticate(mock_authenticate, mock_initialize):
    """
    Test fallback to authenticate when initialize throws an exception.
    """
    project_id = "test-project-id"

    # Configure mock_initialize to raise an exception on the first call
    # and succeed on the second call.
    mock_initialize.side_effect = [Exception("Init failed"), None]

    initialize_gee(project_id)

    # Initialize should be called twice
    assert mock_initialize.call_count == 2
    mock_initialize.assert_any_call(project=project_id)

    # Authenticate should be called once
    mock_authenticate.assert_called_once()
