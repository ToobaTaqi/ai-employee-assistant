"""
Gmail Watcher for AI Employee

This watcher monitors Gmail for new unread/important emails and creates
corresponding action files in the Needs_Action folder for the AI Employee to process.

Features:
- OAuth2 authentication support
- Monitors unread and important emails
- Keyword-based priority detection
- Deduplication via Gmail message IDs
- Full email content extraction with attachments info

Setup:
1. Enable Gmail API in Google Cloud Console
2. Create OAuth2 credentials (OAuth client ID)
3. Download credentials.json to credentials/ folder
4. Run initial auth: python gmail_watcher.py --auth
5. Run watcher: python gmail_watcher.py

Usage:
    python gmail_watcher.py [--vault-path PATH] [--interval SECONDS]
    python gmail_watcher.py --auth  # Initial OAuth setup
"""

import os
import sys
import base64
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from email import message_from_bytes
from email.utils import parsedate_to_datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher

# Try to import Google libraries
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("WARNING: Google API libraries not installed.")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")


class GmailMessage:
    """Represents a Gmail message with parsed content."""

    def __init__(self, msg_data: Dict[str, Any], service=None):
        self.raw_data = msg_data
        self.id = msg_data.get('id', '')
        self.thread_id = msg_data.get('threadId', '')
        self.internal_date = msg_data.get('internalDate', '')
        self.labels = msg_data.get('labelIds', [])
        self.service = service

        # Parse headers and body
        self._parse_message()

    def _parse_message(self):
        """Parse email headers and content."""
        payload = self.raw_data.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}

        self.from_email = headers.get('From', 'Unknown')
        self.to_email = headers.get('To', '')
        self.subject = headers.get('Subject', 'No Subject')
        self.date = headers.get('Date', '')
        self.cc = headers.get('Cc', '')
        self.bcc = headers.get('Bcc', '')

        # Parse body
        self.body_plain = ''
        self.body_html = ''
        self._extract_body(payload)

        # Parse attachments
        self.attachments = self._extract_attachments(payload)

        # Parse date
        try:
            self.parsed_date = parsedate_to_datetime(self.date)
        except Exception:
            self.parsed_date = datetime.now()

    def _extract_body(self, payload: Dict):
        """Extract email body (plain text and HTML)."""
        # Try multipart
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                data = part.get('body', {}).get('data', '')
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    if mime_type == 'text/plain':
                        self.body_plain = decoded
                    elif mime_type == 'text/html':
                        self.body_html = decoded
        else:
            # Try single part
            body = payload.get('body', {})
            data = body.get('data', '')
            if data:
                decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                mime_type = payload.get('mimeType', '')
                if mime_type == 'text/html':
                    self.body_html = decoded
                else:
                    self.body_plain = decoded

        # Fallback to snippet if no body
        if not self.body_plain and not self.body_html:
            self.body_plain = self.raw_data.get('snippet', '')

    def _extract_attachments(self, payload: Dict) -> List[Dict]:
        """Extract attachment metadata."""
        attachments = []

        def traverse(part):
            if 'parts' in part:
                for child in part['parts']:
                    traverse(child)
            else:
                mime_type = part.get('mimeType', '')
                if mime_type.startswith('application/') or mime_type.startswith('image/'):
                    filename = part.get('filename', '')
                    attachment_id = part.get('body', {}).get('attachmentId', '')
                    size = part.get('body', {}).get('size', 0)
                    if filename and attachment_id:
                        attachments.append({
                            'filename': filename,
                            'mime_type': mime_type,
                            'attachment_id': attachment_id,
                            'size': size
                        })

        traverse(payload)
        return attachments

    def get_priority_keywords(self, keywords: List[str]) -> List[str]:
        """Check if email contains priority keywords."""
        text = f"{self.subject} {self.body_plain}".lower()
        return [kw for kw in keywords if kw.lower() in text]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for action file."""
        return {
            'id': self.id,
            'thread_id': self.thread_id,
            'from': self.from_email,
            'to': self.to_email,
            'subject': self.subject,
            'date': self.date,
            'cc': self.cc,
            'body_plain': self.body_plain,
            'body_html': self.body_html,
            'attachments': self.attachments,
            'labels': self.labels
        }


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new unread/important emails and creates action files.

    Features:
    - OAuth2 authentication
    - Monitors unread and important emails
    - Keyword-based priority detection
    - Attachment tracking
    - Deduplication via message IDs
    """

    # Keywords that indicate high priority
    PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'invoice', 'payment', 'help', 'emergency',
        'deadline', 'important', 'action required', 'review', 'approve'
    ]

    # Labels to monitor (can be customized)
    MONITOR_LABELS = ['INBOX', 'UNREAD', 'IMPORTANT']

    def __init__(self, vault_path: str, credentials_path: str = None,
                 check_interval: int = 120, user_email: str = 'me'):
        """
        Initialize the Gmail watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to OAuth2 credentials JSON file
            check_interval: Seconds between checks (default: 120)
            user_email: Gmail address to monitor ('me' for authenticated user)
        """
        if not GMAIL_AVAILABLE:
            raise ImportError(
                "Google API libraries required. Install with:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )

        super().__init__(vault_path, check_interval)

        self.user_email = user_email
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self.token_path = self.vault_path / 'credentials' / 'gmail_token.json'

        # Ensure credentials directory exists
        (self.vault_path / 'credentials').mkdir(parents=True, exist_ok=True)

        # Load or create credentials
        self.creds = self._load_credentials()
        self.service = None

        if self.creds:
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.logger.info(f'Gmail service initialized for: {user_email}')
        else:
            self.logger.warning('Gmail credentials not available. Run --auth first.')

        # Track processed message IDs
        self.processed_ids: set = set()

        # Load priority keywords from handbook if available
        self._load_priority_keywords()

    def _load_credentials(self) -> Optional[Credentials]:
        """Load or create Gmail credentials."""
        creds = None

        # Try to load token file first
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_path)
                self.logger.info('Loaded existing Gmail credentials')
            except Exception as e:
                self.logger.error(f'Error loading token file: {e}')

        # If no valid credentials, try to authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self._save_credentials(creds)
                    self.logger.info('Refreshed Gmail credentials')
                except Exception as e:
                    self.logger.error(f'Error refreshing credentials: {e}')
                    return None
            elif self.credentials_path and self.credentials_path.exists():
                # Interactive auth needed
                self.logger.info('Credentials expired or missing. Re-authentication needed.')
                return None

        return creds

    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file."""
        self.token_path.write_text(creds.to_json())
        self.token_path.chmod(0o600)  # Restrict permissions

    def _load_priority_keywords(self):
        """Load priority keywords from Company Handbook if available."""
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if handbook_path.exists():
            content = handbook_path.read_text(encoding='utf-8')
            # Could parse handbook for custom keywords
            # For now, use defaults
            pass

    def run_auth_flow(self):
        """Run OAuth2 authentication flow."""
        if not self.credentials_path or not self.credentials_path.exists():
            print(f"ERROR: Credentials file not found: {self.credentials_path}")
            print("\nSetup Instructions:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a new project or select existing")
            print("3. Enable Gmail API")
            print("4. Create OAuth2 credentials (Desktop app)")
            print("5. Download credentials.json")
            print(f"6. Save to: {self.credentials_path}")
            sys.exit(1)

        print("Starting Gmail OAuth2 authentication...")
        print(f"Using credentials from: {self.credentials_path}")

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            creds = flow.run_local_server(port=0, open_browser=True)

            # Save credentials
            self._save_credentials(creds)
            print(f"\n✓ Authentication successful!")
            print(f"Token saved to: {self.token_path}")
            print("\nYou can now run the watcher without --auth flag.")

        except Exception as e:
            print(f"\n✗ Authentication failed: {e}")
            sys.exit(1)

    def check_for_updates(self) -> List[GmailMessage]:
        """
        Check for new unread/important emails.

        Returns:
            List of GmailMessage objects for new emails
        """
        if not self.service:
            self.logger.warning('Gmail service not available, skipping check')
            return []

        new_messages = []

        try:
            # Build query for unread and important emails
            query_parts = []
            if 'UNREAD' in self.MONITOR_LABELS:
                query_parts.append('is:unread')
            if 'IMPORTANT' in self.MONITOR_LABELS:
                query_parts.append('is:important')

            query = ' '.join(query_parts) if query_parts else ''

            # Fetch messages
            results = self.service.users().messages().list(
                userId=self.user_email,
                q=query,
                maxResults=50  # Limit to prevent API quota issues
            ).execute()

            messages = results.get('messages', [])

            for msg in messages:
                # Skip if already processed
                if self.is_processed(msg['id']):
                    continue

                # Fetch full message
                try:
                    full_msg = self.service.users().messages().get(
                        userId=self.user_email,
                        id=msg['id'],
                        format='full'
                    ).execute()

                    gmail_msg = GmailMessage(full_msg, self.service)
                    new_messages.append(gmail_msg)
                    self.logger.info(f'Found new email: {gmail_msg.subject[:50]}...')

                except HttpError as e:
                    self.logger.error(f'Error fetching message {msg["id"]}: {e}')
                    continue

        except HttpError as e:
            self.logger.error(f'Gmail API error: {e}')
            if e.resp.status == 401:
                self.logger.error('Authentication error. Re-run with --auth')
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')

        return new_messages

    def create_action_file(self, message: GmailMessage) -> Optional[Path]:
        """
        Create a markdown action file for the email.

        Args:
            message: GmailMessage to create action file for

        Returns:
            Path to created action file, or None if failed
        """
        try:
            # Check for priority keywords
            priority_keywords = message.get_priority_keywords(self.PRIORITY_KEYWORDS)
            priority = 'high' if priority_keywords else 'medium'

            # Determine if approval needed
            needs_approval = any(kw in priority_keywords for kw in ['invoice', 'payment', 'approve'])

            # Create frontmatter
            frontmatter = self.create_frontmatter(
                type='email',
                from_email=message.from_email,
                subject=message.subject,
                date=message.date,
                message_id=message.id,
                thread_id=message.thread_id,
                priority=priority,
                needs_approval=str(needs_approval).lower(),
                has_attachments=str(len(message.attachments) > 0).lower(),
                attachment_count=len(message.attachments)
            )

            # Build suggested actions
            suggested_actions = self._get_suggested_actions(message, priority_keywords)
            actions_text = '\n'.join(f'- [ ] {action}' for action in suggested_actions)

            # Format attachments
            attachments_text = ''
            if message.attachments:
                attachments_text = '\n## Attachments\n\n'
                for att in message.attachments:
                    attachments_text += f'- 📎 `{att["filename"]}` ({self._format_size(att["size"])})\n'
                attachments_text += '\n*Note: Download attachments via Gmail or request AI to fetch*\n'

            # Create content
            content = f'''{frontmatter}

# Email Received

## Header Information

| Field | Value |
|-------|-------|
| **From** | {message.from_email} |
| **To** | {message.to_email} |
| **Subject** | {message.subject} |
| **Date** | {message.date} |
| **Message ID** | `{message.id}` |
| **Thread ID** | `{message.thread_id}` |

## Priority Assessment

- **Priority Level**: {priority.upper()}
- **Keywords Detected**: {', '.join(priority_keywords) if priority_keywords else 'None'}
- **Needs Approval**: {'Yes' if needs_approval else 'No'}

## Email Content

{message.body_plain if message.body_plain else '*HTML content only - view in Gmail*'}

{attachments_text}
## Suggested Actions

{actions_text}

## Notes

*Add any additional context or response draft here*

---

*Action file created by Gmail Watcher*
'''

            # Generate filename
            safe_subject = ''.join(c for c in message.subject if c.isalnum() or c in (' ', '-', '_'))[:50]
            safe_from = ''.join(c for c in message.from_email.split('@')[0] if c.isalnum())[:20]
            filename = self.generate_filename('EMAIL', f'{safe_from}_{safe_subject}_{message.id[:8]}')
            filepath = self.needs_action / filename

            # Write action file
            filepath.write_text(content, encoding='utf-8')

            # Mark as processed
            self.mark_processed(message.id)

            return filepath

        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')
            return None

    def _get_suggested_actions(self, message: GmailMessage, keywords: List[str]) -> List[str]:
        """Get suggested actions based on email content."""
        actions = []

        # Always add read/reply
        actions.append('Read and understand email content')
        actions.append('Determine if response is needed')

        # Add keyword-specific actions
        if 'invoice' in keywords or 'payment' in keywords:
            actions.extend([
                'Extract invoice/payment details (amount, due date, vendor)',
                'Categorize expense in accounting',
                'Schedule payment if approved'
            ])
        elif 'urgent' in keywords or 'asap' in keywords or 'emergency' in keywords:
            actions.extend([
                'Respond immediately',
                'Escalate to human if needed'
            ])
        elif 'help' in keywords:
            actions.extend([
                'Assess what help is needed',
                'Provide information or escalate'
            ])
        elif 'deadline' in keywords:
            actions.extend([
                'Note deadline in calendar',
                'Prioritize related tasks'
            ])
        elif 'approve' in keywords or 'review' in keywords:
            actions.extend([
                'Review requested item',
                'Create approval request if needed'
            ])

        # Add attachment handling
        if message.attachments:
            actions.append('Download and process attachments')

        # Add filing
        actions.append('Archive email after processing')

        return actions

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'

    def download_attachment(self, message_id: str, attachment_id: str,
                           dest_path: Path) -> Optional[Path]:
        """
        Download an attachment from Gmail.

        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID
            dest_path: Destination path

        Returns:
            Path to downloaded file, or None if failed
        """
        if not self.service:
            return None

        try:
            attachment = self.service.users().messages().attachments().get(
                userId=self.user_email,
                messageId=message_id,
                id=attachment_id
            ).execute()

            file_data = base64.urlsafe_b64decode(attachment.get('data', ''))

            dest_path.write_bytes(file_data)
            self.logger.info(f'Downloaded attachment to: {dest_path}')
            return dest_path

        except Exception as e:
            self.logger.error(f'Error downloading attachment: {e}')
            return None


def main():
    """Main entry point for the Gmail watcher."""
    parser = argparse.ArgumentParser(
        description='Gmail Watcher for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python gmail_watcher.py --auth              # Initial OAuth setup
  python gmail_watcher.py                     # Run watcher
  python gmail_watcher.py --interval 60       # Check every 60 seconds
  python gmail_watcher.py --user you@gmail.com

Setup Instructions:
  1. Go to https://console.cloud.google.com/
  2. Create project and enable Gmail API
  3. Create OAuth2 credentials (Desktop app)
  4. Download credentials.json to credentials/ folder
  5. Run: python gmail_watcher.py --auth
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault (default: parent directory of scripts)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=120,
        help='Check interval in seconds (default: 120)'
    )

    parser.add_argument(
        '--credentials',
        type=str,
        default=None,
        help='Path to OAuth2 credentials JSON file'
    )

    parser.add_argument(
        '--user',
        type=str,
        default='me',
        help='Gmail address to monitor (default: authenticated user)'
    )

    parser.add_argument(
        '--auth',
        action='store_true',
        help='Run OAuth2 authentication flow'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Determine credentials path
    if args.credentials:
        credentials_path = args.credentials
    else:
        credentials_path = str(Path(vault_path) / 'credentials' / 'credentials.json')

    # Create watcher
    watcher = GmailWatcher(
        vault_path=vault_path,
        credentials_path=credentials_path,
        check_interval=args.interval,
        user_email=args.user
    )

    # Run auth flow if requested
    if args.auth:
        watcher.run_auth_flow()
        return

    # Check if authenticated
    if not watcher.service:
        print("\n✗ Gmail authentication required.")
        print("Run: python gmail_watcher.py --auth")
        print("\nOr ensure credentials.json exists at:", credentials_path)
        sys.exit(1)

    # Run watcher
    print(f'''
╔══════════════════════════════════════════════════════════╗
║              Gmail Watcher Started                        ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: {vault_path[:55]}{"..." if len(vault_path) > 55 else ""}
║  User: {args.user}
║  Check Interval: {args.interval}s
║  Monitoring: UNREAD, IMPORTANT emails
║                                                            ║
║  Action files created in: {watcher.needs_action}
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
''')

    watcher.run()


if __name__ == '__main__':
    main()
