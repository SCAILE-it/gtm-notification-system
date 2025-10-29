#!/usr/bin/env python3
"""
ABOUTME: Sends real test emails via Resend API for visual verification
ABOUTME: Use this to check SCAILE branding and email rendering in actual email clients

Usage:
    python scripts/send_test_emails.py

Environment variables required:
    RESEND_API_KEY - Your Resend API key (from resend.com)
    TEST_RECIPIENT_EMAIL - Email address to send test emails to
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from notifications import NotificationSystem
from dotenv import load_dotenv

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")


def print_success(text):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")


def print_error(text):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")


def print_info(text):
    print(f"{Colors.OKBLUE}ℹ{Colors.ENDC} {text}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {text}")


async def main():
    # Load environment variables
    load_dotenv()

    print(f"\n{Colors.BOLD}{Colors.HEADER}╔═══════════════════════════════════════════════════════════╗{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}║   SCAILE Email Visual Verification Tool                  ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}╚═══════════════════════════════════════════════════════════╝{Colors.ENDC}\n")

    # Get configuration
    resend_api_key = os.getenv('RESEND_API_KEY')
    supabase_url = os.getenv('SUPABASE_URL', 'https://placeholder.supabase.co')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'placeholder_key')

    if not resend_api_key or resend_api_key == 're_xxxxx':
        print_error("RESEND_API_KEY not found or not set in .env")
        print_info("Get your API key from: https://resend.com/api-keys")
        print_info("Then add to .env: RESEND_API_KEY=re_your_actual_key")
        sys.exit(1)

    # Get recipient email
    recipient = os.getenv('TEST_RECIPIENT_EMAIL')

    if not recipient or recipient == 'your-email@example.com':
        print_info("TEST_RECIPIENT_EMAIL not set in .env")
        recipient = input(f"{Colors.OKCYAN}Enter your email address to receive test emails: {Colors.ENDC}").strip()

        if not recipient or '@' not in recipient:
            print_error("Invalid email address")
            sys.exit(1)

    print_success(f"Sending test emails to: {Colors.BOLD}{recipient}{Colors.ENDC}")
    print_info(f"Using Resend API key: {resend_api_key[:10]}...")

    # Ask for confirmation
    print(f"\n{Colors.WARNING}This will send 4 real emails via Resend API.{Colors.ENDC}")
    confirm = input(f"{Colors.OKCYAN}Continue? (y/N): {Colors.ENDC}").strip().lower()

    if confirm != 'y':
        print_info("Cancelled")
        sys.exit(0)

    # Initialize notification system
    print_header("Initializing Notification System...")

    try:
        ns = NotificationSystem(
            resend_api_key=resend_api_key,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            from_email=None,  # Use default: SCAILE <hello@g-gpt.com>
            app_url="https://g-gpt.com"
        )
        print_success("NotificationSystem initialized")
        print_info(f"From: {ns.from_email}")
        print_info(f"App URL: {ns.app_url}")
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        sys.exit(1)

    test_user_id = "00000000-0000-0000-0000-999999999999"  # Dummy UUID for testing
    test_job_id = "visual-test-job-001"

    # Email 1: Job Complete
    print_header("[1/4] Sending Job Complete Email...")

    try:
        # Bypass preferences check for visual testing
        ns.check_user_preferences = lambda user_id, notification_type: {'enabled': True}

        result = await ns.send_job_complete(
            user_id=test_user_id,
            recipient_email=recipient,  # Override recipient
            job_id=test_job_id,
            results={
                'total_rows': 1250,
                'successful': 1200,
                'failed': 50,
                'processing_time_seconds': 18.7
            },
            csv_data=b"company,email,industry\nAcme Corp,contact@acme.com,Software\nTech Inc,hello@tech.com,SaaS"
        )

        if result['success']:
            print_success(f"Sent! Email ID: {result['email_id']}")
            print_info(f"View in Resend: https://resend.com/emails/{result['email_id']}")
        else:
            print_error(f"Failed: {result.get('reason')}")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # Email 2: Job Failed
    print_header("[2/4] Sending Job Failed Email...")

    try:
        result = await ns.send_job_failed(
            user_id=test_user_id,
            recipient_email=recipient,
            job_id=test_job_id,
            error_message="Database connection timeout after 30 seconds. The external API (api.example.com) failed to respond."
        )

        if result['success']:
            print_success(f"Sent! Email ID: {result['email_id']}")
            print_info(f"View in Resend: https://resend.com/emails/{result['email_id']}")
        else:
            print_error(f"Failed: {result.get('reason')}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Email 3: Quota Warning
    print_header("[3/4] Sending Quota Warning Email...")

    try:
        result = await ns.send_quota_warning(
            user_id=test_user_id,
            recipient_email=recipient,
            current_usage=8500,
            quota_limit=10000,
            quota_period="monthly"
        )

        if result['success']:
            print_success(f"Sent! Email ID: {result['email_id']}")
            print_info(f"View in Resend: https://resend.com/emails/{result['email_id']}")
        else:
            print_error(f"Failed: {result.get('reason')}")
    except Exception as e:
        print_error(f"Error: {e}")

    # Email 4: Welcome Email (via Edge Function - simulate)
    print_header("[4/4] Welcome Email (not sent - Edge Function only)...")
    print_info("Welcome emails are sent via Supabase Edge Function on signup")
    print_info("To test welcome emails, deploy the Edge Function and trigger a signup")
    print_info("See: supabase/functions/send-welcome-email/index.ts")

    # Summary
    print_header("Visual Verification Checklist")
    print(f"""
{Colors.BOLD}Check your inbox ({recipient}) and verify:{Colors.ENDC}

✓ SCAILE Branding:
  • Header uses SCAILE name (not "GTM Power App")
  • Primary color is #282936 (dark blue-purple)
  • Geist font family loads correctly

✓ Layout & Design:
  • Emails render correctly in your email client
  • Colors match SCAILE design system
  • Buttons have proper border-radius (6px)
  • Stats grids display correctly

✓ Content:
  • All links point to g-gpt.com
  • Footer shows "SCAILE - GTM Intelligence Copilot"
  • Email addresses use hello@g-gpt.com

✓ Responsive:
  • Check on mobile device
  • Check in dark mode (if supported)

{Colors.WARNING}Test in multiple email clients:{Colors.ENDC}
  • Gmail (web + mobile)
  • Outlook (web + desktop)
  • Apple Mail
  • ProtonMail / other privacy clients

{Colors.OKBLUE}For detailed checklist, see:{Colors.ENDC} docs/EMAIL_VISUAL_CHECKLIST.md
    """)

    print(f"\n{Colors.OKGREEN}✓ Test emails sent successfully!{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Cancelled by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ Unexpected error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
