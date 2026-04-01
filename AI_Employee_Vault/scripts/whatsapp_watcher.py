"""
WhatsApp Watcher for AI Employee

This watcher monitors WhatsApp Web for new messages and creates
corresponding action files in the Needs_Action folder for the AI Employee to process.

Features:
- Uses Playwright for WhatsApp Web automation
- Session persistence (stay logged in across restarts)
- Keyword-based priority detection
- Monitors individual chats and groups
- Screenshot capture for unread messages

⚠️ WARNING: Be aware of WhatsApp's Terms of Service. Use at your own risk.
   Consider using WhatsApp Business API for production use.

Setup:
1. Install Playwright: pip install playwright
2. Install browsers: playwright install chromium
3. First run will open browser for QR code scan
4. Session saved to credentials/whatsapp_session/

Usage:
    python whatsapp_watcher.py [--vault-path PATH] [--interval SECONDS]
    python whatsapp_watcher.py --fresh-session  # Force new QR login
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    from playwright._impl._errors import TargetClosedError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed.")
    print("Run: pip install playwright && playwright install chromium")


class WhatsAppMessage:
    """Represents a WhatsApp message."""

    def __init__(self, chat_name: str, message_text: str, timestamp: datetime,
                 is_group: bool = False, sender: str = None):
        self.chat_name = chat_name
        self.message_text = message_text
        self.timestamp = timestamp
        self.is_group = is_group
        self.sender = sender  # For group messages
        self.message_id = f"{chat_name}_{timestamp.strftime('%Y%m%d%H%M%S')}"

    def get_priority_keywords(self, keywords: List[str]) -> List[str]:
        """Check if message contains priority keywords."""
        text = self.message_text.lower()
        return [kw for kw in keywords if kw.lower() in text]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for action file."""
        return {
            'chat_name': self.chat_name,
            'message_text': self.message_text,
            'timestamp': self.timestamp.isoformat(),
            'is_group': self.is_group,
            'sender': self.sender,
            'message_id': self.message_id
        }


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages and creates action files.

    Features:
    - Session persistence
    - Keyword-based priority detection
    - Group and individual chat monitoring
    - Screenshot capture capability
    """

    # Keywords that indicate high priority
    PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'invoice', 'payment', 'help', 'emergency',
        'deadline', 'important', 'action required', 'review', 'approve',
        'pricing', 'quote', 'order', 'buy', 'purchase'
    ]

    # WhatsApp Web URL
    WHATSAPP_WEB_URL = 'https://web.whatsapp.com'

    def __init__(self, vault_path: str, session_path: str = None,
                 check_interval: int = 30, headless: bool = True,
                 monitored_chats: List[str] = None, login_timeout: int = 180):
        """
        Initialize the WhatsApp watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 30)
            headless: Run browser in headless mode (default: True)
            monitored_chats: List of chat names to monitor (None = all)
            login_timeout: Timeout for QR code login in seconds (default: 180)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright required. Install with:\n"
                "pip install playwright\n"
                "playwright install chromium"
            )

        super().__init__(vault_path, check_interval)

        self.session_path = Path(session_path) if session_path else (
            self.vault_path / 'credentials' / 'whatsapp_session'
        )
        self.headless = headless
        self.monitored_chats = monitored_chats
        self.login_timeout = login_timeout

        # Ensure session directory exists
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Browser state
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Track processed messages
        self.processed_messages: set = set()

        # Load priority keywords from handbook if available
        self._load_priority_keywords()

        self.logger.info(f'Session path: {self.session_path}')
        self.logger.info(f'Headless: {headless}')
        self.logger.info(f'Login timeout: {login_timeout}s')

    def _load_priority_keywords(self):
        """Load priority keywords from Company Handbook if available."""
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if handbook_path.exists():
            content = handbook_path.read_text(encoding='utf-8')
            # Could parse handbook for custom keywords
            # For now, use defaults
            pass

    def _init_browser(self):
        """Initialize Playwright browser with persistent context."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright required")

        # Only initialize if not already initialized
        if self.playwright and self.page and self.context:
            try:
                # Test if page is still alive
                self.page.title()
                self.logger.info('Browser already initialized and active')
                return
            except Exception:
                # Page is dead, clean up and reinitialize
                self.logger.info('Browser page dead, cleaning up...')
                self._cleanup(full_cleanup=True)

        try:
            self.playwright = sync_playwright().start()

            # Launch browser with persistent context
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ],
                viewport={'width': 1280, 'height': 720}
            )

            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

            # Add anti-detection script
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)

            self.logger.info('Browser initialized successfully')

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f'Failed to initialize browser: {e}')
            
            # If session is locked, try to clean it up
            if 'closed' in error_msg.lower() or 'locked' in error_msg.lower():
                self.logger.warning('Browser session may be locked. Attempting cleanup...')
                try:
                    self._cleanup(full_cleanup=True)
                    # Wait a moment for locks to release
                    import time
                    time.sleep(2)
                except Exception:
                    pass
            
            raise

    def _ensure_whatsapp_loaded(self) -> bool:
        """Ensure WhatsApp Web is loaded and authenticated."""
        try:
            # Navigate to WhatsApp Web with extended timeout
            self.page.goto(self.WHATSAPP_WEB_URL, wait_until='networkidle', timeout=120000)

            # Check if we're at the QR code screen (not authenticated)
            qr_selector = '[data-testid="qr-container"]'
            if self.page.query_selector(qr_selector):
                self.logger.warning('WhatsApp not authenticated. Please scan QR code.')
                authenticated = self._wait_for_qr_scan(timeout=self.login_timeout)
                if not authenticated:
                    self.logger.error('QR code scan timeout')
                    return False

            # Wait for chat list to appear using multiple fallback selectors
            # WhatsApp Web updates frequently, so we try several selectors
            chat_list_selectors = [
                '[data-testid="chat-list"]',           # Primary selector
                'div[role="navigation"]',               # Fallback 1
                '#pane-side',                          # Fallback 2 (main sidebar)
                'div[xtab="true"]',                    # Fallback 3
                '[aria-label="Chat list"]',            # Fallback 4
            ]

            self.logger.info('Waiting for chat list to load...')
            chat_list_found = False

            for selector in chat_list_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=10000)
                    self.logger.info(f'Chat list found with selector: {selector}')
                    chat_list_found = True
                    break
                except Exception:
                    continue

            if not chat_list_found:
                # Last resort: check if any chat-like element exists
                all_chats = self.page.query_selector_all('div[role="listitem"]')
                if all_chats:
                    self.logger.info(f'Found {len(all_chats)} chat items without standard selector')
                    chat_list_found = True
                else:
                    self.logger.error('Chat list not found. Page may still be loading.')
                    # Take screenshot for debugging
                    screenshot_path = self.logs_path / f'whatsapp_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    self.page.screenshot(path=str(screenshot_path))
                    self.logger.info(f'Screenshot saved to: {screenshot_path}')
                    return False

            self.logger.info('WhatsApp Web loaded and authenticated')
            return True

        except Exception as e:
            self.logger.error(f'Error loading WhatsApp: {e}')
            return False

    def _wait_for_qr_scan(self, timeout: int = 180) -> bool:
        """
        Wait for user to scan QR code.

        Args:
            timeout: Timeout in seconds (default: 180 = 3 minutes)

        Returns:
            True if QR scanned successfully, False if timeout
        """
        print("\n" + "=" * 70)
        print("  WHATSAPP AUTHENTICATION REQUIRED")
        print("=" * 70)
        print("\n  A browser window is open showing a QR code.")
        print("  Please scan it with your WhatsApp mobile app:")
        print("\n  On your phone:")
        print("    1. Open WhatsApp app")
        print("    2. Tap Settings (iOS) or ⋮ Menu (Android)")
        print("    3. Tap 'Linked Devices'")
        print("    4. Tap 'Link a Device'")
        print("    5. Point your camera at the QR code on your screen")
        print(f"\n  ⏱️  You have {timeout} seconds ({timeout//60} minutes)")
        print("=" * 70 + "\n")

        # Wait for QR to be scanned (chat list appears)
        # Use multiple selectors since WhatsApp Web updates frequently
        chat_list_selectors = [
            '[data-testid="chat-list"]',
            'div[role="navigation"]',
            '#pane-side',
        ]

        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                for selector in chat_list_selectors:
                    if self.page.query_selector(selector):
                        print("\n✓ WhatsApp authenticated successfully!")
                        print("  Session saved. Future logins will be automatic.\n")
                        return True
                time.sleep(2)  # Check every 2 seconds

            # Timeout reached
            print("\n✗ Authentication timeout!")
            print("  Restart the watcher to try again:")
            print("  python whatsapp_watcher.py --visible\n")
            return False

        except Exception as e:
            self.logger.error(f'QR scan error: {e}')
            print("\n✗ Authentication error!")
            print("  Check console for details.\n")
            return False

    def _get_unread_chats(self) -> List[Dict[str, Any]]:
        """Get list of chats with unread messages."""
        try:
            unread_chats = []

            # Find all chat rows in the sidebar
            chat_rows = self.page.query_selector_all('div[role="row"][style*="height"]')
            self.logger.info(f'Found {len(chat_rows)} chat rows')
            
            for i, chat_row in enumerate(chat_rows):
                # Get full text content of this row for debugging
                row_text = chat_row.inner_text()[:200]
                self.logger.debug(f'Chat row {i} content: {row_text}')
                
                # Check if this row has unread messages - try MULTIPLE approaches
                unread_indicators = []
                
                # Approach 1: aria-label containing "unread"
                unread_aria = chat_row.query_selector_all('[aria-label*="unread"]')
                if unread_aria:
                    unread_indicators.extend(unread_aria)
                    self.logger.info(f'Chat {i}: Found {len(unread_aria)} unread via aria-label')
                
                # Approach 2: Look for unread badge by class
                unread_badges = chat_row.query_selector_all('.x1vvkbs')
                if unread_badges:
                    unread_indicators.extend(unread_badges)
                    self.logger.info(f'Chat {i}: Found {len(unread_badges)} unread via class')
                
                # Approach 3: Check for green dot or other unread indicators
                unread_dots = chat_row.query_selector_all('[data-testid="unread"]')
                if unread_dots:
                    unread_indicators.extend(unread_dots)
                    self.logger.info(f'Chat {i}: Found {len(unread_dots)} unread via testid')
                
                if not unread_indicators:
                    self.logger.debug(f'Chat {i}: No unread indicators found')
                    continue  # This chat has no unread messages
                
                self.logger.info(f'Chat {i} has {len(unread_indicators)} total unread indicators')
                
                try:
                    # Get chat name from span[dir="auto"]
                    name_elem = chat_row.query_selector('span[dir="auto"]')
                    chat_name = name_elem.inner_text().strip() if name_elem else 'Unknown'
                    
                    # Skip if name is empty or looks like a number (unread count)
                    if not chat_name or chat_name.isdigit():
                        self.logger.info(f'Skipping chat {i} - name is number: {chat_name}')
                        continue
                    
                    self.logger.info(f'Chat {i} name: {chat_name}')
                    
                    # Get last message PREVIEW from the chat row itself
                    # WhatsApp shows the last message preview in the chat list
                    all_spans = chat_row.query_selector_all('span')
                    last_message = ''
                    
                    for span in all_spans:
                        try:
                            text = span.inner_text().strip()
                            self.logger.debug(f'Span text: {text[:50]}')
                            # Skip empty, timestamps, and UI text
                            if not text or len(text) < 3:
                                continue
                            if any(x in text.upper() for x in ['AM', 'PM', '/']):
                                continue
                            if 'Type a message' in text or 'search' in text.lower():
                                continue
                            # This looks like actual message content
                            if len(text) > 3:
                                last_message = text
                                self.logger.info(f'Chat {i} last message: {last_message[:50]}')
                                break
                        except Exception as e:
                            self.logger.debug(f'Error reading span: {e}')
                            continue
                    
                    # Check if group
                    is_group = chat_row.query_selector('[data-testid="group-chat-icon"]') is not None
                    
                    unread_chats.append({
                        'name': chat_name,
                        'last_message': last_message,
                        'is_group': is_group,
                        'element': chat_row
                    })
                    
                    self.logger.info(f'[OK] Unread chat #{i}: {chat_name} - Message: {last_message[:30] if last_message else "EMPTY"}')
                    
                except Exception as e:
                    self.logger.info(f'Error parsing chat row {i}: {e}')
                    continue
            
            self.logger.info(f'Total unread chats: {len(unread_chats)}')
            return unread_chats

        except Exception as e:
            self.logger.error(f'Error getting unread chats: {e}')
            return []

    def _get_chat_messages(self, chat_name: str) -> List[WhatsAppMessage]:
        """Open a chat and get recent messages."""
        messages = []

        try:
            # Click on the chat - try multiple selectors
            chat_elem = None
            chat_selectors = [
                f'span[title="{chat_name}"]',
                f'div[title="{chat_name}"]',
                f'span[dir="auto"]:has-text("{chat_name}")',
            ]

            for selector in chat_selectors:
                chat_elem = self.page.query_selector(selector)
                if chat_elem:
                    break

            # Try partial match if exact match fails
            if not chat_elem:
                all_chats = self.page.query_selector_all('span[title]')
                for chat in all_chats:
                    title = chat.get_attribute('title', '')
                    if chat_name.lower() in title.lower():
                        chat_elem = chat
                        break

            # Last resort: click by aria-label
            if not chat_elem:
                chat_elem = self.page.query_selector(f'[aria-label="{chat_name}"]')

            if not chat_elem:
                self.logger.warning(f'Chat not found: {chat_name}')
                self.logger.debug(f'Available chats: {[c.inner_text()[:50] for c in self.page.query_selector_all("span[title]")[:5]]}')
                return messages

            # Click the chat to open the conversation
            try:
                chat_elem.click()
                self.logger.info(f'Clicked on chat: {chat_name}')
            except Exception as e:
                self.logger.error(f'Failed to click chat: {e}')
                return messages
            
            # Wait for conversation to load - look for ANY content change
            self.page.wait_for_timeout(3000)
            
            # Verify we're now in a conversation view
            # The URL should change or we should see message-related elements
            current_url = self.page.url
            self.logger.info(f'Current URL after click: {current_url}')
            
            # Get message elements from the page
            # After clicking a chat, messages appear in the main area
            message_elements = []
            
            # Try to find the main conversation area by various means
            conv_containers = self.page.query_selector_all('div[id="main"], div[role="main"], div[data-testid="main"]')
            
            if conv_containers:
                conv_container = conv_containers[0]
                self.logger.info('Found main conversation area')
                
                # Look for actual message containers, not just any div
                # Messages have specific structure in WhatsApp Web
                message_elements = conv_container.query_selector_all('div[data-testid="message-container"]')
                
                if not message_elements:
                    # Try alternative: look for elements with message-like aria-labels
                    all_divs = conv_container.query_selector_all('div')
                    for div in all_divs:
                        try:
                            aria = div.get_attribute('aria-label')
                            # Real messages have content, not UI instructions
                            if aria and len(aria) > 10:
                                if 'Type a message' not in aria and 'search' not in aria.lower():
                                    message_elements.append(div)
                        except Exception:
                            pass
                
                self.logger.info(f'Found {len(message_elements)} message elements')
            
            # If still nothing, try getting message containers directly from the page
            if not message_elements:
                message_elements = self.page.query_selector_all('div[data-testid="message-container"]')
                self.logger.info(f'Found {len(message_elements)} messages with data-testid')
            
            # Get only the LAST 5 messages (most recent)
            for msg_elem in message_elements[-5:]:
                try:
                    message_text = ''
                    
                    # Try to get text from the message element
                    try:
                        # First try data-testid
                        text_elem = msg_elem.query_selector('span[data-testid="message-text"]')
                        if text_elem:
                            message_text = text_elem.inner_text()
                        
                        # If no text found, try getting from aria-label
                        if not message_text:
                            aria = msg_elem.get_attribute('aria-label')
                            if aria and len(aria) > 10:
                                message_text = aria
                            
                        # Last resort: get inner text
                        if not message_text:
                            all_text = msg_elem.inner_text()
                            if all_text and len(all_text) > 3:
                                message_text = all_text.split('\n')[0]  # Get first line
                    except Exception as e:
                        self.logger.debug(f'Error extracting text: {e}')
                        continue

                    # Filter out empty messages and timestamps
                    if not message_text or len(message_text.strip()) < 2:
                        continue
                    
                    # Skip if it's just a timestamp
                    if any(x in message_text.upper() for x in ['AM', 'PM']) and len(message_text) < 15:
                        continue

                    self.logger.info(f'Extracted message: {message_text[:50]}')

                    # Get sender (for groups)
                    sender = None
                    sender_elem = msg_elem.query_selector('span[data-testid="message-sender"]')
                    if sender_elem:
                        sender = sender_elem.inner_text()

                    # Get timestamp
                    timestamp = datetime.now()
                    time_elem = msg_elem.query_selector('span[data-testid="message-meta-preprocess"]')
                    if time_elem:
                        timestamp = datetime.now()  # Could parse time_elem.inner_text() if needed

                    if message_text:
                        messages.append(WhatsAppMessage(
                            chat_name=chat_name,
                            message_text=message_text,
                            timestamp=timestamp,
                            is_group=sender is not None,
                            sender=sender
                        ))
                except Exception as e:
                    self.logger.debug(f'Error parsing message: {e}')
                    continue

        except Exception as e:
            self.logger.error(f'Error getting messages from chat {chat_name}: {e}')

        return messages

    def check_for_updates(self) -> List[WhatsAppMessage]:
        """
        Check for new unread WhatsApp messages.

        Returns:
            List of WhatsAppMessage objects for new messages
        """
        new_messages = []

        # Initialize browser if needed
        if not self.page or not self.context:
            self.logger.info('Browser not initialized, initializing...')
            try:
                self._init_browser()
            except Exception as e:
                self.logger.error(f'Failed to initialize browser: {e}')
                return []

        try:
            # Ensure WhatsApp is loaded
            if not self._ensure_whatsapp_loaded():
                self.logger.warning('WhatsApp not loaded, will retry next cycle')
                self._cleanup()
                return []

            # Get unread chats (includes last message preview)
            unread_chats = self._get_unread_chats()

            self.logger.info(f'Found {len(unread_chats)} unread chat(s)')

            for chat in unread_chats:
                # Skip if not in monitored list
                if self.monitored_chats and chat['name'] not in self.monitored_chats:
                    self.logger.info(f'Skipping {chat["name"]} - not in monitored list')
                    continue

                self.logger.info(f'Processing unread chat: {chat["name"]}')
                self.logger.info(f'Last message: {chat["last_message"][:50] if chat["last_message"] else "EMPTY"}')

                # Create a message object from the preview
                msg = WhatsAppMessage(
                    chat_name=chat['name'],
                    message_text=chat['last_message'],
                    timestamp=datetime.now(),
                    is_group=chat['is_group'],
                    sender=None
                )

                # Skip if already processed
                if self.is_processed(msg.message_id):
                    self.logger.info(f'Skipping already processed: {msg.message_id}')
                    continue

                # Check if message contains priority keywords
                keywords = msg.get_priority_keywords(self.PRIORITY_KEYWORDS)
                if keywords:  # Only process messages with priority keywords
                    new_messages.append(msg)
                    self.logger.info(f'Priority message from {chat["name"]}: {msg.message_text[:50]}...')
                else:
                    self.logger.info(f'No priority keywords in message from {chat["name"]}: {msg.message_text[:30] if msg.message_text else "EMPTY"}...')

            self.logger.info(f'Total new messages to process: {len(new_messages)}')
            return new_messages

        except TargetClosedError:
            self.logger.error('Browser closed unexpectedly. Will reinitialize on next cycle.')
            # Don't cleanup here - let _init_browser handle it
            return []
        except Exception as e:
            self.logger.error(f'Error checking WhatsApp: {e}')
            # Don't cleanup on every error - keep browser alive
            return []

    def create_action_file(self, message: WhatsAppMessage) -> Optional[Path]:
        """
        Create a markdown action file for the WhatsApp message.

        Args:
            message: WhatsAppMessage to create action file for

        Returns:
            Path to created action file, or None if failed
        """
        try:
            # Check for priority keywords
            priority_keywords = message.get_priority_keywords(self.PRIORITY_KEYWORDS)
            priority = 'high' if len(priority_keywords) > 1 else 'medium'

            # Determine if approval needed
            needs_approval = any(kw in priority_keywords for kw in ['invoice', 'payment', 'approve', 'pricing'])

            # Create frontmatter
            frontmatter = self.create_frontmatter(
                type='whatsapp',
                chat_name=message.chat_name,
                sender=message.sender or 'N/A',
                message_id=message.message_id,
                timestamp=message.timestamp.isoformat(),
                priority=priority,
                needs_approval=str(needs_approval).lower(),
                is_group=str(message.is_group).lower()
            )

            # Build suggested actions
            suggested_actions = self._get_suggested_actions(message, priority_keywords)
            actions_text = '\n'.join(f'- [ ] {action}' for action in suggested_actions)

            # Create content
            content = f'''{frontmatter}

# WhatsApp Message Received

## Message Information

| Field | Value |
|-------|-------|
| **Chat** | {message.chat_name} |
| **Sender** | {message.sender if message.is_group else message.chat_name} |
| **Time** | {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')} |
| **Type** | {'Group' if message.is_group else 'Individual'} |
| **Message ID** | `{message.message_id}` |

## Priority Assessment

- **Priority Level**: {priority.upper()}
- **Keywords Detected**: {', '.join(priority_keywords) if priority_keywords else 'None'}
- **Needs Approval**: {'Yes' if needs_approval else 'No'}

## Message Content

> {message.message_text}

## Suggested Actions

{actions_text}

## Response Draft

*Type your response here. The AI can send via WhatsApp MCP or you can copy manually.*

---

*Action file created by WhatsApp Watcher*
'''

            # Generate filename
            safe_chat = ''.join(c for c in message.chat_name if c.isalnum() or c in (' ', '-', '_'))[:30]
            filename = self.generate_filename('WHATSAPP', f'{safe_chat}_{message.message_id[:8]}')
            filepath = self.needs_action / filename

            # Write action file
            filepath.write_text(content, encoding='utf-8')

            # Mark as processed
            self.mark_processed(message.message_id)

            return filepath

        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')
            return None

    def _get_suggested_actions(self, message: WhatsAppMessage, keywords: List[str]) -> List[str]:
        """Get suggested actions based on message content."""
        actions = []

        # Always add read/respond
        actions.append('Read and understand message')
        actions.append('Determine if response is needed')

        # Add keyword-specific actions
        if 'invoice' in keywords or 'payment' in keywords:
            actions.extend([
                'Extract payment details (amount, due date)',
                'Create invoice or check payment status',
                'Update accounting records'
            ])
        elif 'urgent' in keywords or 'asap' in keywords or 'emergency' in keywords:
            actions.extend([
                'Respond immediately',
                'Escalate to human if critical'
            ])
        elif 'help' in keywords:
            actions.extend([
                'Assess what help is needed',
                'Provide information or escalate'
            ])
        elif 'pricing' in keywords or 'quote' in keywords:
            actions.extend([
                'Prepare pricing information or quote',
                'Send product/service details'
            ])
        elif 'order' in keywords or 'buy' in keywords or 'purchase' in keywords:
            actions.extend([
                'Process order request',
                'Confirm availability and pricing',
                'Create sales record'
            ])

        # Add response
        actions.append('Draft and send response')

        return actions

    def _cleanup(self, full_cleanup=False):
        """
        Clean up browser resources.
        
        Args:
            full_cleanup: If True, fully close browser. If False, just reset references.
        """
        if not full_cleanup:
            # For normal operation, just reset references but keep browser alive
            # This prevents the browser from being killed between cycles
            self.page = None
            self.context = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            return
            
        # Full cleanup (only used when stopping or on fatal errors)
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.debug(f'Cleanup error (ignored): {e}')

        self.page = None
        self.context = None
        self.playwright = None

    def clear_session(self):
        """Clear saved WhatsApp session (force new QR login)."""
        self._cleanup()

        if self.session_path.exists():
            shutil.rmtree(self.session_path)
            self.logger.info(f'Cleared session: {self.session_path}')

        self.logger.info('Session cleared. QR scan required on next run.')

    def run(self):
        """Main run loop with cleanup on exit."""
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Checking every {self.check_interval} seconds')

        print(f'''
╔══════════════════════════════════════════════════════════╗
║            WhatsApp Watcher Started                       ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: {str(self.vault_path)[:55]}{"..." if len(str(self.vault_path)) > 55 else ""}
║  Check Interval: {self.check_interval}s
║  Browser: {"Visible" if not self.headless else "Headless"}
║  Login Timeout: {self.login_timeout}s ({self.login_timeout//60} min)
║  Monitored Chats: {", ".join(self.monitored_chats) if self.monitored_chats else "All"}
║                                                            ║
║  First run: Scan QR code when browser opens                ║
║  Session saved to: {self.session_path}
║                                                            ║
║  Action files created in: {self.needs_action}
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
''')

        try:
            while True:
                items = self.check_for_updates()

                if items:
                    self.logger.info(f'Found {len(items)} priority message(s)')

                    for item in items:
                        try:
                            filepath = self.create_action_file(item)
                            if filepath:
                                self.logger.info(f'[OK] Created action file: {filepath.name}')
                            else:
                                self.logger.info(f'Failed to create action file for: {item.message_id}')
                        except Exception as e:
                            self.logger.error(f'Error creating action file: {e}')
                else:
                    self.logger.info('No new priority messages found')

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise
        finally:
            self._cleanup()


# Import time here to avoid circular import
import time


def main():
    """Main entry point for the WhatsApp watcher."""
    parser = argparse.ArgumentParser(
        description='WhatsApp Watcher for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python whatsapp_watcher.py                    # Run watcher
  python whatsapp_watcher.py --interval 60      # Check every 60 seconds
  python whatsapp_watcher.py --fresh-session    # Force new QR login
  python whatsapp_watcher.py --visible          # Run with visible browser

Setup Instructions:
  1. Install: pip install playwright
  2. Install browsers: playwright install chromium
  3. Run watcher - browser will open for QR scan
  4. Session saved for future runs

⚠️ WARNING: Be aware of WhatsApp's Terms of Service.
   Consider using WhatsApp Business API for production.
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
        default=30,
        help='Check interval in seconds (default: 30)'
    )

    parser.add_argument(
        '--session-path',
        type=str,
        default=None,
        help='Path to store browser session data'
    )

    parser.add_argument(
        '--fresh-session',
        action='store_true',
        help='Clear existing session and force new QR login'
    )

    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )

    parser.add_argument(
        '--chats',
        type=str,
        nargs='+',
        default=None,
        help='Specific chat names to monitor (default: all)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=180,
        help='QR code login timeout in seconds (default: 180 = 3 minutes)'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create watcher
    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        session_path=args.session_path,
        check_interval=args.interval,
        headless=not args.visible,
        monitored_chats=args.chats,
        login_timeout=args.timeout
    )

    # Clear session if requested
    if args.fresh_session:
        watcher.clear_session()

    print(f'''
╔══════════════════════════════════════════════════════════╗
║            WhatsApp Watcher Started                       ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: {vault_path[:55]}{"..." if len(vault_path) > 55 else ""}
║  Check Interval: {args.interval}s
║  Browser: {"Visible" if args.visible else "Headless"}
║  Login Timeout: {args.timeout}s ({args.timeout//60} min)
║  Monitored Chats: {", ".join(args.chats) if args.chats else "All"}
║                                                            ║
║  First run: Scan QR code when browser opens                ║
║  Session saved to: {watcher.session_path}
║                                                            ║
║  Action files created in: {watcher.needs_action}
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
''')

    watcher.run()


if __name__ == '__main__':
    main()
