"""
Unit tests for notification system
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the module we're testing
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notifications import (
    NotificationSystem,
    NotificationType,
    EmailStatus,
    notify_job_complete,
    notify_job_failed,
    notify_quota_warning
)


class TestNotificationSystem:
    """Test NotificationSystem class"""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test NotificationSystem initialization"""
        ns = NotificationSystem(
            resend_api_key="test_key",
            supabase_url="https://test.supabase.co",
            supabase_key="test_service_key",
            from_email="test@example.com"
        )

        assert ns.from_email == "test@example.com"
        assert ns.app_url == "https://app.gtmpowerapp.com"  # default
        assert ns.max_retries == 3  # default
        assert ns.attachment_threshold_bytes == 2_000_000  # 2MB default

    @pytest.mark.asyncio
    async def test_check_user_preferences_enabled(self, mock_supabase_client):
        """Test checking user preferences when notifications are enabled"""
        # Mock preferences response
        mock_table = mock_supabase_client.table('notification_preferences')
        mock_table.execute.return_value = Mock(
            data={'email_job_complete': True},
            error=None
        )

        with patch('notifications.create_client', return_value=mock_supabase_client):
            ns = NotificationSystem(
                resend_api_key="test_key",
                supabase_url="https://test.supabase.co",
                supabase_key="test_service_key"
            )
            ns.supabase = mock_supabase_client

            should_send, email = await ns._check_user_preferences(
                user_id="test-user-id",
                notification_type=NotificationType.JOB_COMPLETE
            )

            assert should_send is True
            assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_check_user_preferences_disabled(self, mock_supabase_client):
        """Test checking user preferences when notifications are disabled"""
        # Mock preferences response with email_job_complete = False
        mock_table = mock_supabase_client.table('notification_preferences')
        mock_table.execute.return_value = Mock(
            data={'email_job_complete': False},
            error=None
        )

        with patch('notifications.create_client', return_value=mock_supabase_client):
            ns = NotificationSystem(
                resend_api_key="test_key",
                supabase_url="https://test.supabase.co",
                supabase_key="test_service_key"
            )
            ns.supabase = mock_supabase_client

            should_send, email = await ns._check_user_preferences(
                user_id="test-user-id",
                notification_type=NotificationType.JOB_COMPLETE
            )

            assert should_send is False
            assert email is None

    @pytest.mark.asyncio
    async def test_check_user_preferences_unverified_email(self, mock_supabase_client):
        """Test that unverified emails don't receive non-onboarding notifications"""
        # Mock user with unverified email
        mock_supabase_client.auth.admin.get_user_by_id.return_value = Mock(
            user=Mock(
                id="test-user-id",
                email="test@example.com",
                email_confirmed_at=None  # NOT verified
            )
        )

        with patch('notifications.create_client', return_value=mock_supabase_client):
            ns = NotificationSystem(
                resend_api_key="test_key",
                supabase_url="https://test.supabase.co",
                supabase_key="test_service_key"
            )
            ns.supabase = mock_supabase_client

            # Should not send job notifications to unverified emails
            should_send, email = await ns._check_user_preferences(
                user_id="test-user-id",
                notification_type=NotificationType.JOB_COMPLETE
            )

            assert should_send is False
            assert email is None

            # But SHOULD send welcome emails even to unverified
            should_send, email = await ns._check_user_preferences(
                user_id="test-user-id",
                notification_type=NotificationType.WELCOME
            )

            assert should_send is True
            assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_upload_to_storage(self, mock_supabase_client, test_csv_data_large):
        """Test uploading large CSV to Supabase Storage"""
        with patch('notifications.create_client', return_value=mock_supabase_client):
            ns = NotificationSystem(
                resend_api_key="test_key",
                supabase_url="https://test.supabase.co",
                supabase_key="test_service_key"
            )
            ns.supabase = mock_supabase_client

            signed_url = await ns._upload_to_storage(
                user_id="test-user-id",
                job_id="test-job-id",
                csv_data=test_csv_data_large
            )

            assert signed_url == 'https://storage.example.com/signed-url'
            # Verify upload was called
            mock_supabase_client.storage.from_.return_value.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_retry_success(self, mock_supabase_client):
        """Test successful email send on first attempt"""
        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'email_abc123'}

            with patch('notifications.create_client', return_value=mock_supabase_client):
                ns = NotificationSystem(
                    resend_api_key="test_key",
                    supabase_url="https://test.supabase.co",
                    supabase_key="test_service_key"
                )
                ns.supabase = mock_supabase_client

                result = await ns._send_email_with_retry(
                    user_email="test@example.com",
                    subject="Test Subject",
                    html="<p>Test</p>",
                    notification_type=NotificationType.JOB_COMPLETE,
                    user_id="test-user-id",
                    job_id="test-job-id"
                )

                assert result['success'] is True
                assert result['email_id'] == 'email_abc123'
                assert mock_send.call_count == 1

    @pytest.mark.asyncio
    async def test_send_email_with_retry_failure(self, mock_supabase_client):
        """Test email send with retry after failures"""
        with patch('resend.Emails.send') as mock_send:
            # Simulate 2 failures, then success
            mock_send.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                {'id': 'email_abc123'}
            ]

            with patch('notifications.create_client', return_value=mock_supabase_client):
                ns = NotificationSystem(
                    resend_api_key="test_key",
                    supabase_url="https://test.supabase.co",
                    supabase_key="test_service_key"
                )
                ns.supabase = mock_supabase_client

                result = await ns._send_email_with_retry(
                    user_email="test@example.com",
                    subject="Test Subject",
                    html="<p>Test</p>",
                    notification_type=NotificationType.JOB_COMPLETE,
                    user_id="test-user-id",
                    job_id="test-job-id"
                )

                assert result['success'] is True
                assert result['email_id'] == 'email_abc123'
                assert mock_send.call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_send_job_complete_small_file(
        self,
        mock_supabase_client,
        test_job_results,
        test_csv_data
    ):
        """Test job complete notification with small CSV attachment"""
        # Mock preferences: enabled
        mock_table = mock_supabase_client.table('notification_preferences')
        mock_table.execute.return_value = Mock(
            data={'email_job_complete': True},
            error=None
        )

        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'email_abc123'}

            with patch('notifications.create_client', return_value=mock_supabase_client):
                ns = NotificationSystem(
                    resend_api_key="test_key",
                    supabase_url="https://test.supabase.co",
                    supabase_key="test_service_key"
                )
                ns.supabase = mock_supabase_client

                result = await ns.send_job_complete(
                    user_id="test-user-id",
                    job_id="test-job-id",
                    results=test_job_results,
                    csv_data=test_csv_data
                )

                assert result['success'] is True
                assert result['email_id'] == 'email_abc123'

                # Verify email was sent with attachment
                call_args = mock_send.call_args[0][0]
                assert 'attachments' in call_args
                assert call_args['subject'].startswith('✅ Job Complete')

    @pytest.mark.asyncio
    async def test_send_job_complete_large_file(
        self,
        mock_supabase_client,
        test_job_results,
        test_csv_data_large
    ):
        """Test job complete notification with large CSV (storage link)"""
        # Mock preferences: enabled
        mock_table = mock_supabase_client.table('notification_preferences')
        mock_table.execute.return_value = Mock(
            data={'email_job_complete': True},
            error=None
        )

        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'email_abc123'}

            with patch('notifications.create_client', return_value=mock_supabase_client):
                ns = NotificationSystem(
                    resend_api_key="test_key",
                    supabase_url="https://test.supabase.co",
                    supabase_key="test_service_key"
                )
                ns.supabase = mock_supabase_client

                result = await ns.send_job_complete(
                    user_id="test-user-id",
                    job_id="test-job-id",
                    results=test_job_results,
                    csv_data=test_csv_data_large
                )

                assert result['success'] is True

                # Verify email was sent WITHOUT attachment (uses storage link)
                call_args = mock_send.call_args[0][0]
                assert 'attachments' not in call_args or call_args['attachments'] is None
                # HTML should contain download link
                assert 'storage.example.com' in call_args['html']

    @pytest.mark.asyncio
    async def test_send_job_failed(self, mock_supabase_client):
        """Test job failure notification"""
        # Mock preferences: enabled
        mock_table = mock_supabase_client.table('notification_preferences')
        mock_table.execute.return_value = Mock(
            data={'email_job_failed': True},
            error=None
        )

        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'email_abc123'}

            with patch('notifications.create_client', return_value=mock_supabase_client):
                ns = NotificationSystem(
                    resend_api_key="test_key",
                    supabase_url="https://test.supabase.co",
                    supabase_key="test_service_key"
                )
                ns.supabase = mock_supabase_client

                result = await ns.send_job_failed(
                    user_id="test-user-id",
                    job_id="test-job-id",
                    error_message="Database connection timeout"
                )

                assert result['success'] is True
                assert result['email_id'] == 'email_abc123'

                # Verify error message in email
                call_args = mock_send.call_args[0][0]
                assert 'Database connection timeout' in call_args['html']
                assert call_args['subject'].startswith('❌ Job Failed')

    @pytest.mark.asyncio
    async def test_send_quota_warning(self, mock_supabase_client):
        """Test quota warning notification"""
        # Mock preferences: enabled
        mock_table = mock_supabase_client.table('notification_preferences')
        mock_table.execute.return_value = Mock(
            data={'email_quota_warning': True},
            error=None
        )

        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'email_abc123'}

            with patch('notifications.create_client', return_value=mock_supabase_client):
                ns = NotificationSystem(
                    resend_api_key="test_key",
                    supabase_url="https://test.supabase.co",
                    supabase_key="test_service_key"
                )
                ns.supabase = mock_supabase_client

                result = await ns.send_quota_warning(
                    user_id="test-user-id",
                    current_usage=8000,
                    limit=10000
                )

                assert result['success'] is True
                assert result['email_id'] == 'email_abc123'

                # Verify quota info in email
                call_args = mock_send.call_args[0][0]
                assert '8,000' in call_args['html']
                assert '10,000' in call_args['html']
                assert '80%' in call_args['subject']


class TestConvenienceFunctions:
    """Test standalone convenience functions"""

    @pytest.mark.asyncio
    async def test_notify_job_complete(self, env_vars, mock_supabase_client, test_job_results):
        """Test notify_job_complete convenience function"""
        with patch('notifications.create_client', return_value=mock_supabase_client):
            with patch('resend.Emails.send') as mock_send:
                mock_send.return_value = {'id': 'email_abc123'}

                # Mock preferences
                mock_table = mock_supabase_client.table('notification_preferences')
                mock_table.execute.return_value = Mock(
                    data={'email_job_complete': True},
                    error=None
                )

                result = await notify_job_complete(
                    user_id="test-user-id",
                    job_id="test-job-id",
                    results=test_job_results
                )

                assert result['success'] is True

    @pytest.mark.asyncio
    async def test_notify_job_failed(self, env_vars, mock_supabase_client):
        """Test notify_job_failed convenience function"""
        with patch('notifications.create_client', return_value=mock_supabase_client):
            with patch('resend.Emails.send') as mock_send:
                mock_send.return_value = {'id': 'email_abc123'}

                # Mock preferences
                mock_table = mock_supabase_client.table('notification_preferences')
                mock_table.execute.return_value = Mock(
                    data={'email_job_failed': True},
                    error=None
                )

                result = await notify_job_failed(
                    user_id="test-user-id",
                    job_id="test-job-id",
                    error_message="Test error"
                )

                assert result['success'] is True

    @pytest.mark.asyncio
    async def test_notify_quota_warning(self, env_vars, mock_supabase_client):
        """Test notify_quota_warning convenience function"""
        with patch('notifications.create_client', return_value=mock_supabase_client):
            with patch('resend.Emails.send') as mock_send:
                mock_send.return_value = {'id': 'email_abc123'}

                # Mock preferences
                mock_table = mock_supabase_client.table('notification_preferences')
                mock_table.execute.return_value = Mock(
                    data={'email_quota_warning': True},
                    error=None
                )

                result = await notify_quota_warning(
                    user_id="test-user-id",
                    current_usage=8000,
                    limit=10000
                )

                assert result['success'] is True
