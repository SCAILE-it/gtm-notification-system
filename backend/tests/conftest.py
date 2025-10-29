"""
Pytest configuration and fixtures for notification system tests
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    client = Mock()

    # Mock auth
    client.auth.admin.get_user_by_id = AsyncMock()
    client.auth.admin.get_user_by_id.return_value = Mock(
        user=Mock(
            id="test-user-id",
            email="test@example.com",
            email_confirmed_at=datetime.now()
        )
    )

    # Mock table queries
    def create_table_mock():
        table = Mock()
        table.select = Mock(return_value=table)
        table.insert = Mock(return_value=table)
        table.update = Mock(return_value=table)
        table.upsert = Mock(return_value=table)
        table.eq = Mock(return_value=table)
        table.maybe_single = Mock(return_value=table)
        table.single = Mock(return_value=table)
        table.execute = AsyncMock(return_value=Mock(data=None, error=None))
        return table

    client.table = Mock(side_effect=create_table_mock)

    # Mock storage
    storage_bucket = Mock()
    storage_bucket.upload = AsyncMock(return_value=Mock(error=None))
    storage_bucket.create_signed_url = Mock(return_value={
        'signedURL': 'https://storage.example.com/signed-url'
    })

    client.storage.from_ = Mock(return_value=storage_bucket)

    return client


@pytest.fixture
def mock_resend():
    """Mock Resend API client"""
    with pytest.mock.patch('resend.Emails.send') as mock_send:
        mock_send.return_value = {'id': 'email_test123'}
        yield mock_send


@pytest.fixture
def test_user_preferences():
    """Sample user preferences"""
    return {
        'user_id': 'test-user-id',
        'email_job_complete': True,
        'email_job_failed': True,
        'email_quota_warning': True,
        'email_quota_exceeded': True,
        'email_weekly_summary': False,
        'inapp_job_complete': True,
        'inapp_job_failed': True,
        'digest_frequency': 'realtime'
    }


@pytest.fixture
def test_job_results():
    """Sample job completion results"""
    return {
        'total_rows': 100,
        'successful': 95,
        'failed': 5,
        'processing_time_seconds': 12.5
    }


@pytest.fixture
def test_csv_data():
    """Sample CSV data"""
    return b"name,email\nJohn Doe,john@example.com\nJane Smith,jane@example.com"


@pytest.fixture
def test_csv_data_large():
    """Large CSV data (>2MB)"""
    # Generate 3MB of CSV data
    header = b"name,email,company,phone,address\n"
    row = b"John Doe,john@example.com,Acme Inc,555-1234,123 Main St\n"
    num_rows = (3 * 1024 * 1024) // len(row)  # ~3MB worth of rows
    return header + (row * num_rows)


@pytest.fixture
def env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv('RESEND_API_KEY', 'test_resend_key')
    monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'test_service_key')
    monkeypatch.setenv('FROM_EMAIL', 'test@example.com')
    monkeypatch.setenv('APP_URL', 'https://test-app.com')
