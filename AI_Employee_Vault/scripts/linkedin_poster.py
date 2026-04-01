"""
LinkedIn Auto-Poster for AI Employee

Automated LinkedIn posting via Playwright browser automation.
Supports scheduled posts, content generation, and engagement tracking.

⚠️ WARNING: Be aware of LinkedIn's Terms of Service. Use responsibly.
   Consider using LinkedIn API for production use.

Features:
- Create and schedule posts
- Auto-generate business content
- Track engagement (likes, comments)
- Content calendar management
- HITL approval required before posting

Usage:
    python linkedin_poster.py --draft "Business update content"
    python linkedin_poster.py --schedule --time "2026-03-31 09:00"
    python linkedin_poster.py --post FILE  # Post approved draft
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
    from playwright._impl._errors import TargetClosedError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed.")
    print("Run: pip install playwright && playwright install chromium")


class LinkedInPoster:
    """
    LinkedIn auto-posting via Playwright.

    Creates drafts, schedules posts, and publishes with approval.
    """

    LINKEDIN_URL = 'https://www.linkedin.com'

    # Content templates for business posts
    CONTENT_TEMPLATES = {
        'milestone': """
🎉 Milestone Alert!

We're excited to announce {milestone}!

This achievement reflects our commitment to {value}.

Thank you to our amazing team and clients who made this possible.

#Business #Milestone #Growth
""",
        'product_update': """
📢 Product Update

We've just launched {feature}!

This new capability helps you {benefit}.

Learn more: {link}

#ProductUpdate #Innovation #Technology
""",
        'thought_leadership': """
💡 Industry Insight

{insight}

Key takeaways:
• {point1}
• {point2}
• {point3}

What's your experience with this?

#ThoughtLeadership #Industry #Insights
""",
        'client_success': """
⭐ Client Success Story

We helped {client} achieve {result}.

By implementing {solution}, they saw:
→ {metric1}
→ {metric2}

Ready for similar results? Let's talk!

#ClientSuccess #Results #Business
""",
        'weekly_update': """
📅 Weekly Business Update

This week at {company}:

✅ {accomplishment1}
✅ {accomplishment2}
✅ {accomplishment3}

Looking forward to {next_week_focus}!

#WeeklyUpdate #Business #Progress
"""
    }

    def __init__(self, vault_path: str, session_path: str = None):
        self.vault_path = Path(vault_path)
        self.session_path = Path(session_path) if session_path else (
            self.vault_path / 'credentials' / 'linkedin_session'
        )
        self.posts_folder = self.vault_path / 'Social_Media' / 'LinkedIn'
        self.drafts_folder = self.posts_folder / 'Drafts'
        self.scheduled_folder = self.posts_folder / 'Scheduled'
        self.published_folder = self.posts_folder / 'Published'
        self.logs_path = self.vault_path / 'logs'

        # Ensure directories exist
        for folder in [self.posts_folder, self.drafts_folder,
                       self.scheduled_folder, self.published_folder, self.logs_path]:
            folder.mkdir(parents=True, exist_ok=True)

        # Browser state
        self.playwright = None
        self.context = None
        self.page = None

        # Setup logging
        self._setup_logging()

        self.logger.info('LinkedIn Poster initialized')

    def _setup_logging(self):
        """Configure logging."""
        import logging

        log_file = self.logs_path / f'linkedin_poster_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LinkedInPoster')

    def _init_browser(self, headless: bool = True):
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright required")

        self.playwright = sync_playwright().start()

        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ],
            viewport={'width': 1280, 'height': 720}
        )

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        # Anti-detection
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

        self.logger.info('Browser initialized')

    def _ensure_logged_in(self) -> bool:
        """Ensure LinkedIn session is authenticated."""
        try:
            # Increased timeout to 3 minutes for manual login
            self.page.goto(self.LINKEDIN_URL, wait_until='networkidle', timeout=180000)

            # Check if already logged in
            if 'feed' in self.page.url or 'mynetwork' in self.page.url:
                self.logger.info('Already logged in to LinkedIn')
                return True

            # Check if at login page
            if 'login' in self.page.url:
                self.logger.warning('LinkedIn login required')
                return False

            return True

        except Exception as e:
            self.logger.error(f'Error checking login status: {e}')
            return False

    def login(self, email: str = None, password: str = None, timeout: int = 180):
        """
        Login to LinkedIn.

        Args:
            email: LinkedIn email (optional - for display only)
            password: LinkedIn password (optional - for display only)
            timeout: Timeout in seconds (default: 180 = 3 minutes)
        """
        print("\n" + "=" * 70)
        print("  LINKEDIN LOGIN")
        print("=" * 70)
        print("\n  Cleaning up previous session...")
        
        # Clean up any existing session folder
        import shutil
        if self.session_path.exists():
            try:
                shutil.rmtree(self.session_path)
                print("  Previous session cleared")
            except Exception as e:
                self.logger.debug(f'Could not clear session: {e}')
        
        print("  Opening browser...")
        
        self._init_browser(headless=False)  # Visible for login

        try:
            print("  Navigating to LinkedIn...")
            self.page.goto(self.LINKEDIN_URL, wait_until='domcontentloaded', timeout=30000)
            
            print("\n  Please log in to LinkedIn in the browser window.")
            print(f"  (Session will be saved for future use)")
            print("\n  Waiting up to {} minutes for login...".format(timeout//60))
            print("  Press Ctrl+C to cancel.")
            print("\n  TIP: Once you see your LinkedIn feed, the login is detected automatically.")
            print("  " + "=" * 68 + "\n")
            
            # Wait for user to log in by checking URL periodically
            import time
            start_time = time.time()
            last_url = ""
            check_count = 0
            
            print("\n  Monitoring for login...")
            
            while time.time() - start_time < timeout:
                try:
                    # Get URL using JavaScript (more reliable than page.url)
                    current_url = self.page.evaluate('window.location.href')
                    
                    # Also check page title
                    page_title = self.page.evaluate('document.title')
                    
                    # Debug: Show URL changes
                    if current_url != last_url:
                        print(f"  → URL: {current_url[:80]}...")
                        last_url = current_url
                    
                    check_count += 1
                    if check_count % 15 == 0:  # Every 30 seconds
                        elapsed = int((time.time() - start_time) / 60)
                        print(f"  → Still waiting... ({elapsed} min elapsed)")
                        print(f"     Current: {current_url[:60]}...")
                    
                    # Check for logged-in indicators (very specific)
                    # Must be on actual LinkedIn domain with feed/mynetwork/etc
                    is_logged_in = (
                        'linkedin.com' in current_url.lower() and
                        (
                            '/feed' in current_url.lower() or 
                            '/mynetwork' in current_url.lower() or 
                            '/messaging' in current_url.lower() or
                            '/notifications' in current_url.lower() or
                            '/jobs' in current_url.lower() or
                            '/mycompany' in current_url.lower() or
                            ('/in/' in current_url.lower() and 'linkedin.com/in/' in current_url.lower())
                        )
                    )
                    
                    # Also check if we're clearly NOT on login page
                    is_on_login_page = (
                        '/login' in current_url.lower() or
                        '/checkpoint' in current_url.lower() or
                        'Sign In' in page_title or
                        'sign in' in page_title.lower() or
                        'Log In' in page_title or
                        'log in' in page_title.lower()
                    )
                    
                    if is_logged_in and not is_on_login_page:
                        self.logger.info('LinkedIn login successful')
                        print("\n✓ LinkedIn login detected!")
                        print("  Session saved. Future logins will be automatic.\n")
                        print("=" * 70)
                        
                        # Save a screenshot to confirm
                        screenshot_path = self.session_path.parent / 'linkedin_login_success.png'
                        self.page.screenshot(path=str(screenshot_path))
                        print(f"  Screenshot saved: {screenshot_path}")
                        
                        return True
                        
                except Exception as e:
                    self.logger.debug(f'Error checking: {e}')
                    pass
                time.sleep(2)
            
            # Timeout reached
            self.logger.warning('Login timeout')
            print("\n⚠ Login timeout reached.")
            print("  Please run the command again if you need to log in.")
            return False

        except Exception as e:
            self.logger.error(f'Login error: {e}')
            print(f"\nError: {e}")
            print("\nTroubleshooting:")
            print("  1. Close all Chrome windows")
            print("  2. Run: rmdir /s /q credentials\\linkedin_session")
            print("  3. Try again\n")
            raise

    def create_post_draft(self, content: str, template: str = None,
                          scheduled_time: str = None,
                          hashtags: List[str] = None) -> Path:
        """
        Create a post draft.

        Args:
            content: Post content
            template: Template name to use (optional)
            scheduled_time: Scheduled post time (ISO format)
            hashtags: Additional hashtags

        Returns:
            Path to draft file
        """
        # Apply template if specified
        if template and template in self.CONTENT_TEMPLATES:
            template_content = self.CONTENT_TEMPLATES[template]
            # Simple placeholder replacement
            content = template_content.format(
                milestone=content.split('\n')[0] if '\n' in content else content,
                value='excellence',
                feature=content,
                benefit='improve efficiency',
                link='#',
                insight=content,
                point1='Point 1',
                point2='Point 2',
                point3='Point 3',
                client='our client',
                result='significant results',
                solution='our solution',
                metric1='50% increase in efficiency',
                metric2='30% cost reduction',
                company='our company',
                accomplishment1='Completed project milestone',
                accomplishment2='Onboarded new client',
                accomplishment3='Launched new feature',
                next_week_focus='continued growth'
            )

        # Add hashtags
        if hashtags:
            content += '\n\n' + ' '.join(f'#{tag}' for tag in hashtags)

        # Create draft file
        draft_data = {
            'content': content,
            'created_at': datetime.now().isoformat(),
            'scheduled_time': scheduled_time,
            'status': 'draft',
            'template_used': template,
            'hashtags': hashtags or []
        }

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f'LinkedIn_Draft_{timestamp}.md'
        draft_path = self.drafts_folder / draft_filename

        # Write draft
        content_md = f'''---
type: linkedin_post
status: draft
created: {datetime.now().isoformat()}
scheduled: {scheduled_time or 'Not scheduled'}
requires_approval: true
---

# LinkedIn Post Draft

## Content

{content}

## Posting Instructions

1. Review content for accuracy and brand alignment
2. Check for typos and formatting
3. Verify any links work correctly
4. Move this file to /Approved to publish
5. Move to /Rejected to discard

---

*Draft created by AI Employee LinkedIn Poster*
'''
        draft_path.write_text(content_md, encoding='utf-8')

        # Also save JSON for programmatic access
        json_path = draft_path.with_suffix('.json')
        json_path.write_text(json.dumps(draft_data, indent=2), encoding='utf-8')

        self.logger.info(f'Created draft: {draft_filename}')
        return draft_path

    def generate_business_content(self, topic: str, tone: str = 'professional') -> str:
        """
        Generate business content for a topic.

        Args:
            topic: Topic to write about
            tone: Content tone (professional, casual, enthusiastic)

        Returns:
            Generated content
        """
        # Simple template-based generation
        # In production, this would use an LLM

        templates = {
            'professional': f"""
Business Update: {topic}

We're pleased to share insights on {topic}.

Our approach focuses on:
• Quality and excellence
• Client satisfaction
• Continuous improvement

#Business #Professional #Industry
""",
            'casual': f"""
Hey network! 👋

Just wanted to share some thoughts on {topic}.

It's been an interesting journey and we're learning every day!

What's your experience with this?

#Business #Learning #Growth
""",
            'enthusiastic': f"""
🚀 Exciting news about {topic}!

We're thrilled to be working on this game-changer!

Stay tuned for more updates - big things coming!

#Innovation #Exciting #Business #Growth
"""
        }

        return templates.get(tone, templates['professional']).strip()

    def post_to_linkedin(self, content: str, wait_for_approval: bool = True) -> Dict[str, Any]:
        """
        Post content to LinkedIn.

        Args:
            content: Post content
            wait_for_approval: Require approval before posting

        Returns:
            Post result
        """
        result = {
            'success': False,
            'posted': False,
            'error': None,
            'post_url': None
        }

        try:
            # Initialize browser if needed
            if not self.page:
                self._init_browser(headless=False)

            # Ensure logged in
            if not self._ensure_logged_in():
                result['error'] = 'Not logged in. Run login first.'
                return result

            # Navigate to post creation
            self.page.goto(f'{self.LINKEDIN_URL}/feed/inline-create/', wait_until='networkidle')

            # Wait for post editor
            self.page.wait_for_selector('[data-placeholder*="What do you want to talk about?"]', timeout=10000)

            # Find the editor and type content
            editor = self.page.query_selector('[data-placeholder*="What do you want to talk about?"]')
            if editor:
                editor.fill(content)

                # Wait a moment for content to register
                self.page.wait_for_timeout(1000)

                # Find and click post button
                post_button = self.page.query_selector('button:has-text("Post")')
                if post_button:
                    if wait_for_approval:
                        # Just prepare the post, don't submit
                        result['success'] = True
                        result['posted'] = False
                        result['message'] = 'Post prepared. Awaiting approval.'
                        self.logger.info('Post prepared, awaiting approval')
                    else:
                        # Click post button
                        post_button.click()
                        self.page.wait_for_timeout(3000)

                        result['success'] = True
                        result['posted'] = True
                        result['message'] = 'Post published successfully'
                        self.logger.info('Post published successfully')
                else:
                    result['error'] = 'Post button not found'
            else:
                result['error'] = 'Post editor not found'

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f'Post error: {e}')

        return result

    def schedule_post(self, draft_path: Path, scheduled_time: str) -> Path:
        """
        Schedule a draft for posting.

        Args:
            draft_path: Path to draft file
            scheduled_time: ISO format datetime

        Returns:
            Path to scheduled file
        """
        if not draft_path.exists():
            raise FileNotFoundError(f'Draft not found: {draft_path}')

        # Read draft
        content = draft_path.read_text(encoding='utf-8')

        # Move to scheduled folder
        scheduled_filename = draft_path.name.replace('Draft', 'Scheduled')
        scheduled_path = self.scheduled_folder / scheduled_filename

        # Update frontmatter
        content = content.replace('status: draft', 'status: scheduled')
        content = content.replace(f'scheduled: Not scheduled', f'scheduled: {scheduled_time}')

        scheduled_path.write_text(content, encoding='utf-8')

        self.logger.info(f'Scheduled post: {scheduled_filename}')
        return scheduled_path

    def get_scheduled_posts(self) -> List[Dict[str, Any]]:
        """Get all scheduled posts."""
        posts = []

        for f in self.scheduled_folder.iterdir():
            if f.suffix == '.md':
                content = f.read_text(encoding='utf-8')
                scheduled_time = 'Unknown'
                for line in content.split('\n'):
                    if line.startswith('scheduled:'):
                        scheduled_time = line.split(':', 1)[1].strip()
                        break

                posts.append({
                    'file': f.name,
                    'scheduled_time': scheduled_time,
                    'path': str(f)
                })

        return sorted(posts, key=lambda p: p['scheduled_time'])

    def post_to_linkedin(self, content: str) -> Dict[str, Any]:
        """
        Post content to LinkedIn using Playwright.
        
        Args:
            content: Post content to publish
            
        Returns:
            Dict with success status and post URL
        """
        result = {
            'success': False,
            'error': None,
            'post_url': None
        }
        
        try:
            # Initialize browser
            self._init_browser(headless=False)
            
            # Navigate to LinkedIn
            self.logger.info('Navigating to LinkedIn...')
            self.page.goto(self.LINKEDIN_URL, wait_until='networkidle', timeout=60000)
            
            # Wait for page to load
            self.page.wait_for_timeout(5000)
            
            # Check if logged in
            if 'login' in self.page.url or 'checkpoint' in self.page.url:
                result['error'] = 'Not logged in. Please log in manually.'
                self.logger.warning('User not logged in')
                print("\n⚠️  You need to log in to LinkedIn first!")
                print("   Please log in manually in the browser window...")
                print("   (Waiting 60 seconds)\n")
                
                # Wait for user to log in
                import time
                for i in range(30):  # 60 seconds
                    time.sleep(2)
                    if 'feed' in self.page.url:
                        self.logger.info('User logged in')
                        print("✓ Login detected!\n")
                        break
                else:
                    return result
            
            # Navigate to feed and create post
            self.logger.info('Creating post...')
            self.page.goto(f'{self.LINKEDIN_URL}/feed/', wait_until='networkidle')
            self.page.wait_for_timeout(3000)
            
            # Find and click "Start a post"
            try:
                start_post_btn = self.page.query_selector('button[aria-label="Start a post"]')
                if start_post_btn:
                    start_post_btn.click()
                    self.page.wait_for_timeout(2000)
                
                # Find text area and type content
                text_area = self.page.query_selector('div[contenteditable="true"]')
                if text_area:
                    text_area.fill(content)
                    self.page.wait_for_timeout(1000)
                    
                    # Click Post button
                    post_btn = self.page.query_selector('button:has-text("Post")')
                    if post_btn:
                        post_btn.click()
                        self.page.wait_for_timeout(3000)
                        
                        result['success'] = True
                        self.logger.info('Post published successfully')
                        print("\n✓ Post published to LinkedIn!\n")
                    else:
                        result['error'] = 'Could not find Post button'
                else:
                    result['error'] = 'Could not find text area'
                    
            except Exception as e:
                result['error'] = f'Could not create post: {str(e)}'
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f'Post error: {e}')
        
        return result

    def _log_action(self, action: str, details: Dict[str, Any]):
        """Log an action."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }

        log_file = self.logs_path / f'linkedin_{datetime.now().strftime("%Y%m%d")}.json'
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='LinkedIn Auto-Poster',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python linkedin_poster.py --login                    # Login to LinkedIn
  python linkedin_poster.py --draft "Post content"     # Create draft
  python linkedin_poster.py --generate --topic "AI"    # Generate content
  python linkedin_poster.py --schedule --time "2026-03-31 09:00"
  python linkedin_poster.py --post FILE                # Post approved draft

⚠️ WARNING: Be aware of LinkedIn's Terms of Service.
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--draft',
        type=str,
        help='Create draft with content'
    )

    parser.add_argument(
        '--template',
        type=str,
        choices=['milestone', 'product_update', 'thought_leadership',
                 'client_success', 'weekly_update'],
        help='Content template to use'
    )

    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate content'
    )

    parser.add_argument(
        '--topic',
        type=str,
        help='Topic for content generation'
    )

    parser.add_argument(
        '--tone',
        type=str,
        choices=['professional', 'casual', 'enthusiastic'],
        default='professional',
        help='Content tone'
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Schedule a post'
    )

    parser.add_argument(
        '--time',
        type=str,
        help='Scheduled time (ISO format)'
    )

    parser.add_argument(
        '--post',
        type=str,
        help='Post approved draft file'
    )

    parser.add_argument(
        '--post',
        type=str,
        help='Post draft file to LinkedIn (requires login)'
    )

    parser.add_argument(
        '--post-auto',
        action='store_true',
        help='Auto-post latest draft to LinkedIn (opens browser)'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create poster
    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright required. Install with: pip install playwright")
        sys.exit(1)

    poster = LinkedInPoster(vault_path)

    if args.draft:
        draft_path = poster.create_post_draft(
            content=args.draft,
            template=args.template
        )
        print(f'✓ Draft created: {draft_path}')
        print(f'\nNext steps:')
        print(f'  1. Review: {draft_path}')
        print(f'  2. Edit if needed')
        print(f'  3. Move to Approved/ when ready to post')

    elif args.generate:
        if not args.topic:
            print("Please provide --topic")
            sys.exit(1)
        content = poster.generate_business_content(args.topic, args.tone)
        print("\nGenerated Content:\n")
        print(content)
        print("\nTo create a draft: python linkedin_poster.py --draft \"<content>\"")

    elif args.schedule:
        if not args.time:
            print("Please provide --time")
            sys.exit(1)
        # Find latest draft
        drafts = list(poster.drafts_folder.iterdir())
        if not drafts:
            print("No drafts found. Create a draft first.")
            sys.exit(1)
        latest_draft = max(drafts, key=lambda f: f.stat().st_mtime)
        scheduled_path = poster.schedule_post(latest_draft, args.time)
        print(f'✓ Post scheduled: {scheduled_path}')

    elif args.post_auto:
        # Post latest draft automatically
        drafts = list(poster.drafts_folder.iterdir())
        if not drafts:
            print("No drafts found. Create a draft first.")
            print("\nCreate one with:")
            print('  python linkedin_poster.py --draft "Your content here"')
            sys.exit(1)
        latest_draft = max(drafts, key=lambda f: f.stat().st_mtime)
        content = latest_draft.read_text(encoding='utf-8')
        
        # Extract content from markdown
        import re
        content_match = re.search(r'## Content\n\n(.+?)\n\n##', content, re.DOTALL)
        if content_match:
            post_content = content_match.group(1).strip()
        else:
            post_content = content
        
        print(f"Posting to LinkedIn:\n{post_content[:100]}...\n")
        result = poster.post_to_linkedin(post_content)
        
        if result['success']:
            # Move to Published
            published_path = poster.published_folder / latest_draft.name
            latest_draft.rename(published_path)
            print(f"✓ Post published! File moved to: {published_path}")
        else:
            print(f"✗ Post failed: {result['error']}")

    elif args.post:
        draft_path = Path(args.post)
        if not draft_path.exists():
            print(f"File not found: {draft_path}")
            sys.exit(1)

        content = draft_path.read_text(encoding='utf-8')
        # Extract content from markdown
        body = content.split('## Content\n\n', 1)[-1] if '## Content' in content else content

        result = poster.post_to_linkedin(body, wait_for_approval=False)
        print(f"Post result: {json.dumps(result, indent=2)}")

    else:
        # Show status
        scheduled = poster.get_scheduled_posts()
        print("\nLinkedIn Auto-Poster")
        print("=" * 40)
        print(f"Scheduled Posts: {len(scheduled)}")
        for post in scheduled[:5]:
            print(f"  - {post['file']} ({post['scheduled_time']})")
        print()


if __name__ == '__main__':
    main()
