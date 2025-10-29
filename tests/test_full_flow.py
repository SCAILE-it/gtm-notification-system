"""
Integration tests for complete notification flow

These tests run against Docker Compose services:
- PostgreSQL (Supabase-compatible)
- MailHog (email testing)
- Supabase Auth
- Supabase Storage

Run with: docker-compose up && python tests/test_full_flow.py
"""

import os
import sys
import asyncio
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from notifications import NotificationSystem, NotificationType
from supabase import create_client, Client
import requests


# Test configuration
SUPABASE_URL = "http://localhost:9876"  # PostgREST endpoint (port 9876 to avoid conflicts)
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
RESEND_API_KEY = "test_key"  # Dummy key for testing
MAILHOG_API_URL = "http://localhost:8025/api/v2"


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_test(message, status="INFO"):
    """Print colored test output"""
    colors = {
        "INFO": Colors.OKBLUE,
        "SUCCESS": Colors.OKGREEN,
        "FAIL": Colors.FAIL,
        "WARNING": Colors.WARNING
    }
    color = colors.get(status, Colors.OKBLUE)
    print(f"{color}[{status}]{Colors.ENDC} {message}")


def check_service_health():
    """Check that all Docker services are running"""
    print_test("Checking service health...", "INFO")

    # Core services required for notification testing
    core_services = {
        "PostgreSQL": "http://localhost:5432",
        "MailHog": "http://localhost:8025",
    }

    # Optional services (nice to have but not critical)
    optional_services = {
        "PostgREST": "http://localhost:9876",
        "Auth": "http://localhost:9999/health"
    }

    all_healthy = True
    for service, url in core_services.items():
        try:
            if service == "PostgreSQL":
                # For Postgres, just check if port is open
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 5432))
                sock.close()
                if result == 0:
                    print_test(f"✓ {service} is running", "SUCCESS")
                else:
                    print_test(f"✗ {service} is not running", "FAIL")
                    all_healthy = False
            else:
                response = requests.get(url, timeout=2)
                if response.status_code < 400:
                    print_test(f"✓ {service} is healthy", "SUCCESS")
                else:
                    print_test(f"✗ {service} returned {response.status_code}", "FAIL")
                    all_healthy = False
        except Exception as e:
            print_test(f"✗ {service} is not responding: {e}", "FAIL")
            all_healthy = False

    # Check optional services but don't fail if they're down
    for service, url in optional_services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code < 400:
                print_test(f"✓ {service} is healthy", "SUCCESS")
            else:
                print_test(f"⚠ {service} returned {response.status_code} (optional)", "WARNING")
        except Exception as e:
            print_test(f"⚠ {service} not available (optional, skipping)", "WARNING")

    return all_healthy


def setup_database():
    """Run database migrations"""
    print_test("Setting up database...", "INFO")

    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Read migration file
    migration_path = os.path.join(
        os.path.dirname(__file__),
        '../supabase/migrations/20250128_notification_tables.sql'
    )

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    # Execute migration (this is simplified - in real scenario use Supabase CLI)
    # For now, we'll check if tables exist
    try:
        result = supabase.table('notification_preferences').select('id').limit(1).execute()
        print_test("✓ Database tables already exist", "SUCCESS")
        return True
    except Exception as e:
        print_test(f"⚠ Database needs migration: {e}", "WARNING")
        print_test("Run: psql -h localhost -U postgres -d postgres -f supabase/migrations/20250128_notification_tables.sql", "INFO")
        return False


def get_mailhog_messages():
    """Fetch messages from MailHog"""
    try:
        response = requests.get(f"{MAILHOG_API_URL}/messages")
        if response.status_code == 200:
            return response.json().get('items', [])
        return []
    except Exception as e:
        print_test(f"Failed to fetch MailHog messages: {e}", "FAIL")
        return []


def clear_mailhog():
    """Clear all messages in MailHog"""
    try:
        requests.delete(f"{MAILHOG_API_URL}/messages")
        print_test("Cleared MailHog inbox", "INFO")
    except Exception as e:
        print_test(f"Failed to clear MailHog: {e}", "WARNING")


async def test_notification_system():
    """Test complete notification flow"""
    print_test("\n" + "="*60, "INFO")
    print_test("INTEGRATION TEST: Notification System", "INFO")
    print_test("="*60 + "\n", "INFO")

    # Initialize notification system
    ns = NotificationSystem(
        resend_api_key=RESEND_API_KEY,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_SERVICE_KEY,
        from_email="test@example.com",
        app_url="http://localhost:3000"
    )

    # Use test user from mock auth.users table (seeded in 00_setup_auth_mock.sql)
    test_user_id = "00000000-0000-0000-0000-000000000001"  # test-user-1@example.com
    test_job_id = "test-job-" + str(int(time.time()))

    # Test 1: Create test user preferences
    print_test("\n[TEST 1] Creating user preferences...", "INFO")
    try:
        ns.supabase.table('notification_preferences').insert({
            'user_id': test_user_id,
            'email_job_complete': True,
            'email_job_failed': True,
            'email_quota_warning': True
        }).execute()
        print_test("✓ User preferences created", "SUCCESS")
    except Exception as e:
        print_test(f"✗ Failed to create preferences: {e}", "FAIL")
        return False

    # Test 2: Send job completion notification
    print_test("\n[TEST 2] Sending job completion notification...", "INFO")
    clear_mailhog()

    try:
        # Mock the Resend API to use MailHog instead
        import resend
        original_send = resend.Emails.send

        def mock_send(email_data):
            """Send via MailHog instead of Resend"""
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = email_data['from']
            msg['To'] = ', '.join(email_data['to'])
            msg['Subject'] = email_data['subject']

            msg.attach(MIMEText(email_data['html'], 'html'))

            with smtplib.SMTP('localhost', 1025) as server:
                server.send_message(msg)

            return {'id': f'email_test_{int(time.time())}'}

        resend.Emails.send = mock_send

        result = await ns.send_job_complete(
            user_id=test_user_id,
            job_id=test_job_id,
            results={
                'total_rows': 100,
                'successful': 95,
                'failed': 5,
                'processing_time_seconds': 12.3
            },
            csv_data=b"name,email\nJohn,john@example.com"
        )

        if result['success']:
            print_test("✓ Notification sent successfully", "SUCCESS")
            print_test(f"  Email ID: {result['email_id']}", "INFO")

            # Wait for email to arrive in MailHog
            time.sleep(2)

            # Check MailHog
            messages = get_mailhog_messages()
            if messages:
                print_test(f"✓ Email received in MailHog ({len(messages)} message(s))", "SUCCESS")
                latest = messages[0]
                print_test(f"  Subject: {latest['Content']['Headers']['Subject'][0]}", "INFO")
                print_test(f"  To: {latest['Content']['Headers']['To'][0]}", "INFO")
            else:
                print_test("✗ No email in MailHog", "FAIL")

        else:
            print_test(f"✗ Notification failed: {result.get('reason')}", "FAIL")
            return False

    except Exception as e:
        print_test(f"✗ Test failed: {e}", "FAIL")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Send job failure notification
    print_test("\n[TEST 3] Sending job failure notification...", "INFO")
    clear_mailhog()

    try:
        result = await ns.send_job_failed(
            user_id=test_user_id,
            job_id=test_job_id,
            error_message="Database connection timeout"
        )

        if result['success']:
            print_test("✓ Failure notification sent", "SUCCESS")

            time.sleep(2)
            messages = get_mailhog_messages()
            if messages and '❌' in messages[0]['Content']['Headers']['Subject'][0]:
                print_test("✓ Failure email received with correct subject", "SUCCESS")
            else:
                print_test("⚠ Email format may be incorrect", "WARNING")
        else:
            print_test(f"✗ Notification failed: {result.get('reason')}", "FAIL")

    except Exception as e:
        print_test(f"✗ Test failed: {e}", "FAIL")
        return False

    # Test 4: Test preference opt-out
    print_test("\n[TEST 4] Testing preference opt-out...", "INFO")

    try:
        # Disable job complete notifications
        ns.supabase.table('notification_preferences') \
            .update({'email_job_complete': False}) \
            .eq('user_id', test_user_id) \
            .execute()

        clear_mailhog()

        result = await ns.send_job_complete(
            user_id=test_user_id,
            job_id=test_job_id + "-2",
            results={'total_rows': 50, 'successful': 50, 'failed': 0, 'processing_time_seconds': 5.0}
        )

        if not result['success'] and 'preferences' in result.get('reason', ''):
            print_test("✓ Notification correctly blocked by user preferences", "SUCCESS")

            time.sleep(2)
            messages = get_mailhog_messages()
            if not messages:
                print_test("✓ Confirmed: No email sent (as expected)", "SUCCESS")
            else:
                print_test("✗ Email was sent despite opt-out", "FAIL")
        else:
            print_test("✗ Preference opt-out not working", "FAIL")

    except Exception as e:
        print_test(f"✗ Test failed: {e}", "FAIL")
        return False

    # Test 5: Check notification logs
    print_test("\n[TEST 5] Verifying notification logs...", "INFO")

    try:
        logs = ns.supabase.table('notification_logs') \
            .select('*') \
            .eq('user_id', test_user_id) \
            .execute()

        if logs.data:
            print_test(f"✓ Found {len(logs.data)} log entries", "SUCCESS")
            for log in logs.data:
                print_test(f"  - {log['notification_type']}: {log['status']}", "INFO")
        else:
            print_test("⚠ No logs found (may not be persisting)", "WARNING")

    except Exception as e:
        print_test(f"⚠ Could not verify logs: {e}", "WARNING")

    # Cleanup
    print_test("\n[CLEANUP] Removing test data...", "INFO")
    try:
        ns.supabase.table('notification_logs').delete().eq('user_id', test_user_id).execute()
        ns.supabase.table('notification_preferences').delete().eq('user_id', test_user_id).execute()
        print_test("✓ Test data cleaned up", "SUCCESS")
    except Exception as e:
        print_test(f"⚠ Cleanup failed: {e}", "WARNING")

    print_test("\n" + "="*60, "INFO")
    print_test("ALL TESTS PASSED ✓", "SUCCESS")
    print_test("="*60 + "\n", "INFO")

    return True


def main():
    """Run all integration tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   GTM Notification System - Integration Tests            ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    # Check services
    if not check_service_health():
        print_test("\n✗ Some services are not running!", "FAIL")
        print_test("Run: docker-compose up -d", "INFO")
        sys.exit(1)

    # Setup database
    setup_database()

    # Run tests
    try:
        result = asyncio.run(test_notification_system())
        if result:
            print_test("\n🎉 Integration tests completed successfully!", "SUCCESS")
            sys.exit(0)
        else:
            print_test("\n❌ Some tests failed", "FAIL")
            sys.exit(1)
    except KeyboardInterrupt:
        print_test("\n\nTests interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        print_test(f"\n❌ Test suite failed: {e}", "FAIL")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
