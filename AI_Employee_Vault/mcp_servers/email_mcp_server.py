#!/usr/bin/env python3
"""
Email MCP Server for AI Employee

Model Context Protocol (MCP) server for sending emails via Gmail API.
Supports OAuth2 authentication, draft mode, and audit logging.

Features:
- Send emails via Gmail API
- Create drafts (for approval workflow)
- Search/read emails
- Full audit logging
- Dry-run mode for testing

Usage:
    # Run as stdio MCP server
    python email_mcp_server.py

    # Or with uvicorn for HTTP transport
    uvicorn email_mcp_server:app --host 0.0.0.0 --port 8809

Setup:
    1. Enable Gmail API in Google Cloud Console
    2. Create OAuth2 credentials
    3. Download credentials.json to credentials/ folder
    4. Run: python email_mcp_server.py --auth
"""

import os
import sys
import json
import base64
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

# Try to import Google libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# Try to import MCP libraries
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("WARNING: MCP library not installed. Run: pip install mcp")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_mcp_server')


class EmailService:
    """Gmail API service wrapper."""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.credentials_path = self.vault_path / 'credentials' / 'credentials.json'
        self.token_path = self.vault_path / 'credentials' / 'gmail_token.json'
        self.logs_path = self.vault_path / 'logs'

        # Ensure directories exist
        self.logs_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'credentials').mkdir(parents=True, exist_ok=True)

        self.creds = None
        self.service = None

        # Load credentials
        self._load_credentials()

    def _load_credentials(self) -> bool:
        """Load or create Gmail credentials."""
        creds = None

        # Try to load token file first
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                logger.info('Loaded existing Gmail credentials')
            except Exception as e:
                logger.error(f'Error loading token file: {e}')

        # If no valid credentials, try to refresh
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self._save_credentials(creds)
                    logger.info('Refreshed Gmail credentials')
                except Exception as e:
                    logger.error(f'Error refreshing credentials: {e}')
                    return False
            elif self.credentials_path.exists():
                logger.info('Credentials need authentication. Run --auth first.')
                return False
            else:
                logger.error(f'Credentials file not found: {self.credentials_path}')
                return False

        self.creds = creds
        self.service = build('gmail', 'v1', credentials=self.creds)
        return True

    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file."""
        self.token_path.write_text(creds.to_json())
        self.token_path.chmod(0o600)
        logger.info(f'Credentials saved to: {self.token_path}')

    def run_auth_flow(self):
        """Run OAuth2 authentication flow."""
        if not self.credentials_path.exists():
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
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path,
            scopes=self.SCOPES
        )
        creds = flow.run_local_server(port=0, open_browser=True)
        self._save_credentials(creds)
        print("\n✓ Authentication successful!")

    def send_email(self, to: str, subject: str, body: str,
                   body_html: str = None, cc: str = None,
                   bcc: str = None, attachments: List[str] = None,
                   dry_run: bool = False) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            body_html: HTML body (optional)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            attachments: List of file paths to attach
            dry_run: If True, don't actually send

        Returns:
            Dict with status and message_id
        """
        try:
            # Create message
            message = self._create_message(to, subject, body, body_html, cc, bcc, attachments)

            if dry_run:
                logger.info(f'[DRY RUN] Would send email to {to}')
                return {
                    'success': True,
                    'dry_run': True,
                    'message': f'Email prepared but not sent (dry run mode)',
                    'to': to,
                    'subject': subject
                }

            # Send email
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            # Log the action
            self._log_action('email_send', {
                'to': to,
                'subject': subject,
                'message_id': sent_message.get('id')
            })

            return {
                'success': True,
                'message_id': sent_message.get('id'),
                'thread_id': sent_message.get('threadId'),
                'to': to,
                'subject': subject
            }

        except HttpError as e:
            error_msg = f'Gmail API error: {e}'
            logger.error(error_msg)
            self._log_action('email_send_failed', {
                'to': to,
                'subject': subject,
                'error': str(e)
            })
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f'Error sending email: {e}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def create_draft(self, to: str, subject: str, body: str,
                     body_html: str = None, cc: str = None,
                     bcc: str = None, attachments: List[str] = None) -> Dict[str, Any]:
        """
        Create an email draft (for approval workflow).

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            body_html: HTML body (optional)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach

        Returns:
            Dict with draft_id and status
        """
        try:
            # Create message
            message = self._create_message(to, subject, body, body_html, cc, bcc, attachments)

            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': message}
            ).execute()

            # Log the action
            self._log_action('email_draft_created', {
                'to': to,
                'subject': subject,
                'draft_id': draft.get('id')
            })

            return {
                'success': True,
                'draft_id': draft.get('id'),
                'message_id': draft.get('message', {}).get('id'),
                'to': to,
                'subject': subject
            }

        except HttpError as e:
            error_msg = f'Gmail API error: {e}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f'Error creating draft: {e}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Send an existing draft.

        Args:
            draft_id: The draft ID to send

        Returns:
            Dict with status and message_id
        """
        try:
            # Get the draft
            draft = self.service.users().drafts().get(
                userId='me',
                id=draft_id
            ).execute()

            # Send the draft's message
            sent_message = self.service.users().messages().send(
                userId='me',
                body=draft['message']
            ).execute()

            # Delete the draft
            self.service.users().drafts().delete(
                userId='me',
                id=draft_id
            ).execute()

            # Log the action
            self._log_action('email_draft_sent', {
                'draft_id': draft_id,
                'message_id': sent_message.get('id')
            })

            return {
                'success': True,
                'message_id': sent_message.get('id'),
                'draft_id': draft_id
            }

        except HttpError as e:
            error_msg = f'Gmail API error: {e}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f'Error sending draft: {e}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def search_emails(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search emails.

        Args:
            query: Gmail search query
            max_results: Maximum results to return

        Returns:
            Dict with list of emails
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            email_list = []

            for msg in messages:
                full_msg = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
                email_list.append({
                    'id': msg['id'],
                    'thread_id': msg.get('threadId'),
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', '')
                })

            return {
                'success': True,
                'count': len(email_list),
                'emails': email_list
            }

        except HttpError as e:
            error_msg = f'Gmail API error: {e}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def _create_message(self, to: str, subject: str, body: str,
                        body_html: str = None, cc: str = None,
                        bcc: str = None, attachments: List[str] = None) -> Dict:
        """Create a MIME message and encode for Gmail API."""
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['subject'] = subject

        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc

        # Add body parts
        message.attach(MIMEText(body, 'plain'))
        if body_html:
            message.attach(MIMEText(body_html, 'html'))

        # Add attachments
        if attachments:
            for filepath in attachments:
                self._attach_file(message, filepath)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    def _attach_file(self, message: MIMEMultipart, filepath: str):
        """Attach a file to the message."""
        try:
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())

            encoders.encode_base64(part)

            # Set filename
            filename = os.path.basename(filepath)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )

            message.attach(part)
            logger.info(f'Attached file: {filepath}')

        except Exception as e:
            logger.error(f'Error attaching file {filepath}: {e}')
            raise

    def _log_action(self, action_type: str, details: Dict[str, Any]):
        """Log an action to the audit log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'email_mcp_server',
            'parameters': details,
            'result': 'success' if 'failed' not in action_type else 'failed'
        }

        log_file = self.logs_path / f'email_mcp_{datetime.now().strftime("%Y%m%d")}.json'

        # Append to log file
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


# Create MCP server instance
if MCP_AVAILABLE:
    app = Server("email-mcp")
else:
    app = None


def setup_mcp_server(email_service: EmailService):
    """Set up MCP server tools."""

    @app.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="email_send",
                description="Send an email via Gmail. Use for sending notifications, responses, and communications.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "body": {
                            "type": "string",
                            "description": "Plain text email body"
                        },
                        "body_html": {
                            "type": "string",
                            "description": "Optional HTML email body"
                        },
                        "cc": {
                            "type": "string",
                            "description": "CC recipients (comma-separated)"
                        },
                        "bcc": {
                            "type": "string",
                            "description": "BCC recipients (comma-separated)"
                        },
                        "attachments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to attach"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "If true, prepare but don't send"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            ),
            Tool(
                name="email_create_draft",
                description="Create an email draft for review/approval. Use in HITL workflow.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "body": {
                            "type": "string",
                            "description": "Plain text email body"
                        },
                        "body_html": {
                            "type": "string",
                            "description": "Optional HTML email body"
                        },
                        "cc": {
                            "type": "string",
                            "description": "CC recipients"
                        },
                        "attachments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to attach"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            ),
            Tool(
                name="email_send_draft",
                description="Send an existing draft by draft ID. Use after approval.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "The draft ID to send"
                        }
                    },
                    "required": ["draft_id"]
                }
            ),
            Tool(
                name="email_search",
                description="Search emails in Gmail. Use for finding previous conversations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Gmail search query (e.g., 'from:john invoice', 'is:unread')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        result = None

        try:
            if name == "email_send":
                result = email_service.send_email(
                    to=arguments.get("to"),
                    subject=arguments.get("subject"),
                    body=arguments.get("body"),
                    body_html=arguments.get("body_html"),
                    cc=arguments.get("cc"),
                    bcc=arguments.get("bcc"),
                    attachments=arguments.get("attachments"),
                    dry_run=arguments.get("dry_run", False)
                )

            elif name == "email_create_draft":
                result = email_service.create_draft(
                    to=arguments.get("to"),
                    subject=arguments.get("subject"),
                    body=arguments.get("body"),
                    body_html=arguments.get("body_html"),
                    cc=arguments.get("cc"),
                    attachments=arguments.get("attachments")
                )

            elif name == "email_send_draft":
                result = email_service.send_draft(
                    draft_id=arguments.get("draft_id")
                )

            elif name == "email_search":
                result = email_service.search_emails(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 10)
                )

            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Email MCP Server for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python email_mcp_server.py --auth           # Run OAuth authentication
  python email_mcp_server.py                  # Run as stdio MCP server
  python email_mcp_server.py --vault PATH     # Specify vault path

Setup:
  1. Enable Gmail API in Google Cloud Console
  2. Create OAuth2 credentials (Desktop app)
  3. Download credentials.json to credentials/ folder
  4. Run: python email_mcp_server.py --auth
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--auth',
        action='store_true',
        help='Run OAuth2 authentication flow'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run a test email (dry run)'
    )

    parser.add_argument(
        '--call-tool',
        type=str,
        help='Call a specific tool (for approval orchestrator)'
    )

    parser.add_argument(
        '--args',
        type=str,
        help='JSON arguments for the tool call'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create email service
    if not GMAIL_AVAILABLE:
        print("ERROR: Google API libraries required.")
        print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    email_service = EmailService(vault_path)

    # Run auth flow if requested
    if args.auth:
        email_service.run_auth_flow()
        return

    # Test mode
    if args.test:
        print("Testing email service...")
        result = email_service.send_email(
            to="test@example.com",
            subject="Test Email",
            body="This is a test email from Email MCP Server.",
            dry_run=True
        )
        print(json.dumps(result, indent=2))
        return

    # Tool call mode (for approval orchestrator)
    if args.call_tool:
        tool_args = json.loads(args.args) if args.args else {}
        
        # Don't print logging info - only output JSON result
        if args.call_tool == 'email_create_draft':
            result = email_service.create_draft(
                to=tool_args.get('to', ''),
                subject=tool_args.get('subject', ''),
                body=tool_args.get('body', ''),
                body_html=tool_args.get('body_html'),
                cc=tool_args.get('cc'),
                attachments=tool_args.get('attachments', [])
            )
        elif args.call_tool == 'email_send':
            result = email_service.send_email(
                to=tool_args.get('to', ''),
                subject=tool_args.get('subject', ''),
                body=tool_args.get('body', ''),
                body_html=tool_args.get('body_html'),
                cc=tool_args.get('cc'),
                bcc=tool_args.get('bcc'),
                attachments=tool_args.get('attachments', []),
                dry_run=tool_args.get('dry_run', False)
            )
        elif args.call_tool == 'email_send_draft':
            result = email_service.send_draft(
                draft_id=tool_args.get('draft_id', '')
            )
        elif args.call_tool == 'email_search':
            result = email_service.search_emails(
                query=tool_args.get('query', ''),
                max_results=tool_args.get('max_results', 10)
            )
        else:
            result = {'success': False, 'error': f'Unknown tool: {args.call_tool}'}
        
        # Only output JSON - no other prints
        print(json.dumps(result, indent=2))
        return

    # Check if MCP is available
    if not MCP_AVAILABLE:
        print("ERROR: MCP library required. Install with: pip install mcp")
        sys.exit(1)

    # Check authentication
    if not email_service.service:
        print("ERROR: Gmail authentication required.")
        print("Run: python email_mcp_server.py --auth")
        sys.exit(1)

    # Set up MCP server
    setup_mcp_server(email_service)

    print("Email MCP Server starting...")
    print("Ready to handle email tools via MCP protocol.")

    # Run the server using stdio
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    import asyncio
    asyncio.run(run())


if __name__ == '__main__':
    main()
