"""
WhatsApp Debug Script

This script opens WhatsApp Web and captures:
1. Full page screenshot
2. HTML structure of chat list
3. All available selectors

Run this to help identify the correct selectors for your WhatsApp Web version.

Usage:
    python whatsapp_debug.py
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright


def debug_whatsapp():
    """Debug WhatsApp Web structure."""
    
    vault_path = Path(__file__).parent.parent
    session_path = vault_path / 'credentials' / 'whatsapp_session'
    debug_path = vault_path / 'logs' / 'whatsapp_debug'
    
    debug_path.mkdir(parents=True, exist_ok=True)
    session_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("  WHATSAPP WEB DEBUGGER")
    print("=" * 70)
    print("\nThis will:")
    print("1. Open WhatsApp Web")
    print("2. Wait for you to scan QR code (if needed)")
    print("3. Capture HTML structure")
    print("4. Save screenshot and HTML for analysis")
    print("\nPress Ctrl+C at any time to stop\n")
    
    with sync_playwright() as p:
        # Launch browser
        print("Launching browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,  # Visible so you can see what's happening
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ],
            viewport={'width': 1280, 'height': 800}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Navigate to WhatsApp
        print("Navigating to WhatsApp Web...")
        page.goto('https://web.whatsapp.com', wait_until='networkidle')
        
        # Wait for user to scan QR if needed
        print("\nIf you see a QR code, please scan it with your phone.")
        print("Waiting 60 seconds for authentication...\n")
        
        # Check for QR code
        qr_present = page.query_selector('[data-testid="qr-container"]')
        if qr_present:
            print("QR code detected. Waiting for scan...")
        
        # Wait for chat list to appear
        for i in range(60):
            time.sleep(1)
            
            # Check various selectors that might indicate chat list
            selectors_to_try = [
                'div[role="listitem"]',
                '[data-testid="chat-list"]',
                '#pane-side',
                'div._ak4n',
                'div.x1idzvv',
                '[aria-label="Chat list"]',
            ]
            
            for selector in selectors_to_try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
        
        # Take screenshot
        screenshot_path = debug_path / f'whatsapp_{time.strftime("%Y%m%d_%H%M%S")}.png'
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n✓ Screenshot saved: {screenshot_path}")
        
        # Get HTML of different sections
        print("\n--- ANALYZING PAGE STRUCTURE ---\n")
        
        # Try to get the main app container
        app_selectors = [
            '#app',
            '#main',
            '#pane-side',
            'body',
        ]
        
        for selector in app_selectors:
            elem = page.query_selector(selector)
            if elem:
                html = elem.inner_html()
                html_path = debug_path / f'whatsapp_html_{selector.replace("#", "").replace("[", "_").replace("]", "_")}.txt'
                html_path.write_text(html[:100000], encoding='utf-8')  # Limit to 100KB
                print(f"✓ HTML saved for selector '{selector}': {html_path}")
        
        # Get all chat-like elements
        print("\n--- SEARCHING FOR CHAT ELEMENTS ---\n")
        
        chat_selectors = [
            'div[role="listitem"]',
            'div[role="row"]',
            'div[tabindex]',
            'div._ak4n',
            'div.x1idzvv',
            'div.x1lliihq',
            '[data-testid="chat-item"]',
            '[data-testid="chat-list"] > div',
        ]
        
        for selector in chat_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"✓ Found {len(elements)} elements with: {selector}")
                    
                    # Get text content of first few
                    for i, elem in enumerate(elements[:3]):
                        text = elem.inner_text()[:100].replace('\n', ' | ')
                        print(f"    [{i}] {text}")
                        
                        # Get classes
                        classes = elem.get_attribute('class')
                        if classes:
                            print(f"        Classes: {classes[:100]}")
            except Exception as e:
                print(f"✗ Selector '{selector}' failed: {e}")
        
        # Get unread-specific elements
        print("\n--- SEARCHING FOR UNREAD INDICATORS ---\n")
        
        unread_selectors = [
            '[aria-label*="unread"]',
            '[aria-label*="new"]',
            'span[data-testid="unread"]',
            '.x1vvkbs',
            'span.x140p0ai',
            'span.x1gufx9m',
        ]
        
        for selector in unread_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"✓ Found {len(elements)} unread elements with: {selector}")
                    
                    # Try to get parent
                    for i, elem in enumerate(elements[:3]):
                        # Go up the tree
                        parent = elem
                        for level in range(5):
                            parent = parent.query_selector('xpath=..')
                            if parent:
                                role = parent.get_attribute('role')
                                if role:
                                    print(f"    [{i}] Level {level+1}: role={role}")
                                    break
            except Exception as e:
                print(f"✗ Selector '{selector}' failed: {e}")
        
        # Get all unique classes in the page
        print("\n--- EXTRACTING ALL CLASSES ---\n")
        
        all_classes = page.evaluate('''() => {
            const classes = new Set();
            document.querySelectorAll('*').forEach(el => {
                if (el.className) {
                    el.className.split(' ').forEach(c => classes.add(c));
                }
            });
            return Array.from(classes).sort();
        }''')
        
        classes_path = debug_path / f'whatsapp_all_classes_{time.strftime("%Y%m%d_%H%M%S")}.txt'
        classes_path.write_text('\n'.join(all_classes), encoding='utf-8')
        print(f"✓ All classes saved: {classes_path}")
        
        print("\n" + "=" * 70)
        print("  DEBUG COMPLETE")
        print("=" * 70)
        print(f"\nFiles saved to: {debug_path}")
        print("\nNext steps:")
        print("1. Open the screenshot to see the page")
        print("2. Look at the HTML files to find chat list structure")
        print("3. Identify the correct selectors for chat items and unread badges")
        print("4. Update whatsapp_watcher.py with the new selectors")
        print("\nKeeping browser open for 30 more seconds for manual inspection...")
        
        time.sleep(30)
        print("\nDone!")


if __name__ == '__main__':
    try:
        debug_whatsapp()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
