"""
Approval Workflow Orchestrator for AI Employee

This module implements the Human-in-the-Loop (HITL) approval workflow.
It watches the /Approved and /Rejected folders for moved files and
executes the corresponding actions.

Workflow:
1. AI creates approval request in /Pending_Approval
2. Human reviews and moves file to /Approved or /Rejected
3. Orchestrator detects the move and executes/rejects the action
4. Result is logged and file moved to /Done

Supported Action Types:
- email_send: Send email via Email MCP
- email_send_draft: Send drafted email
- payment: Process payment (via Odoo MCP in Gold tier)
- social_post: Post to social media
- file_operation: File management operations

Usage:
    python approval_orchestrator.py [--vault-path PATH] [--interval SECONDS]
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class ApprovalAction:
    """Represents an approval request action."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text(encoding='utf-8')
        self.frontmatter = self._parse_frontmatter()
        self.action_type = self.frontmatter.get('action', 'unknown')
        self.status = self.frontmatter.get('status', 'pending')

    def _parse_frontmatter(self) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown file."""
        content = self.content.strip()
        if not content.startswith('---'):
            return {}

        try:
            # Simple YAML parser for frontmatter
            lines = content.split('\n')
            frontmatter_lines = []
            in_frontmatter = False

            for line in lines:
                if line.strip() == '---':
                    if in_frontmatter:
                        break
                    in_frontmatter = True
                    continue
                if in_frontmatter:
                    frontmatter_lines.append(line)

            # Parse key: value pairs
            result = {}
            for line in frontmatter_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    # Type conversion
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit():
                        value = float(value)

                    result[key] = value

            return result

        except Exception as e:
            return {}

    def get_body(self) -> str:
        """Get the markdown body (without frontmatter)."""
        content = self.content.strip()
        if content.startswith('---'):
            # Find end of frontmatter
            end_idx = content.find('---', 3)
            if end_idx > 0:
                return content[end_idx + 3:].strip()
        return content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'filepath': str(self.filepath),
            'action_type': self.action_type,
            'status': self.status,
            'frontmatter': self.frontmatter,
            'body': self.get_body()
        }


class ApprovalOrchestrator:
    """
    Orchestrates the HITL approval workflow.

    Watches /Approved and /Rejected folders for moved files
    and executes corresponding actions.
    """

    def __init__(self, vault_path: str, check_interval: int = 10):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Folder paths
        self.pending_folder = self.vault_path / 'Pending_Approval'
        self.approved_folder = self.vault_path / 'Approved'
        self.rejected_folder = self.vault_path / 'Rejected'
        self.done_folder = self.vault_path / 'Done'
        self.logs_path = self.vault_path / 'logs'

        # Ensure folders exist
        for folder in [self.pending_folder, self.approved_folder,
                       self.rejected_folder, self.done_folder, self.logs_path]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Track processed files
        self.processed_files: set = set()

        # Action handlers registry
        self.action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

        self.logger.info(f'Approval Orchestrator initialized')
        self.logger.info(f'Vault path: {self.vault_path}')

    def _setup_logging(self):
        """Configure logging."""
        import logging

        log_file = self.logs_path / f'approval_orchestrator_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ApprovalOrchestrator')

    def _register_default_handlers(self):
        """Register default action handlers."""
        self.action_handlers = {
            'email_send': self._handle_email_send,
            'email_send_draft': self._handle_email_send_draft,
            'email_create_draft': self._handle_email_create_draft,
            'payment': self._handle_payment,
            'social_post': self._handle_social_post,
            'file_operation': self._handle_file_operation,
            'generic': self._handle_generic
        }

    def check_approved_files(self) -> List[ApprovalAction]:
        """Check for newly approved files."""
        approved_actions = []

        try:
            for filepath in self.approved_folder.iterdir():
                if filepath.suffix != '.md':
                    continue

                # Skip already processed
                if str(filepath) in self.processed_files:
                    continue

                # Skip if file is too new (still being written)
                try:
                    if (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).total_seconds() < 2:
                        continue
                except Exception:
                    continue

                try:
                    action = ApprovalAction(filepath)
                    approved_actions.append(action)
                    self.logger.info(f'Found approved action: {action.action_type}')
                except Exception as e:
                    self.logger.error(f'Error reading approval file {filepath}: {e}')

        except Exception as e:
            self.logger.error(f'Error checking approved folder: {e}')

        return approved_actions

    def check_rejected_files(self) -> List[ApprovalAction]:
        """Check for newly rejected files."""
        rejected_actions = []

        try:
            for filepath in self.rejected_folder.iterdir():
                if filepath.suffix != '.md':
                    continue

                # Skip already processed
                if str(filepath) in self.processed_files:
                    continue

                try:
                    action = ApprovalAction(filepath)
                    rejected_actions.append(action)
                    self.logger.info(f'Found rejected action: {action.action_type}')
                except Exception as e:
                    self.logger.error(f'Error reading rejection file {filepath}: {e}')

        except Exception as e:
            self.logger.error(f'Error checking rejected folder: {e}')

        return rejected_actions

    def execute_approved(self, action: ApprovalAction) -> Dict[str, Any]:
        """Execute an approved action."""
        self.logger.info(f'Executing approved action: {action.action_type}')

        # Find handler
        handler = self.action_handlers.get(action.action_type, self._handle_generic)

        try:
            result = handler(action)

            # Log success
            self._log_execution(action, result)

            # Move to Done
            self._move_to_done(action.filepath)

            # Mark as processed
            self.processed_files.add(str(action.filepath))

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'action_type': action.action_type
            }
            self._log_execution(action, error_result)
            return error_result

    def process_rejected(self, action: ApprovalAction) -> Dict[str, Any]:
        """Process a rejected action."""
        self.logger.info(f'Processing rejected action: {action.action_type}')

        result = {
            'success': False,
            'status': 'rejected',
            'action_type': action.action_type,
            'message': 'Action rejected by human'
        }

        # Log rejection
        self._log_execution(action, result, status='rejected')

        # Move to Done with rejection note
        self._add_rejection_note(action.filepath)
        self._move_to_done(action.filepath, suffix='_rejected')

        # Mark as processed
        self.processed_files.add(str(action.filepath))

        return result

    def _handle_email_send(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle email send action."""
        fm = action.frontmatter

        # Call email MCP server
        result = self._call_mcp_tool('email_mcp_server', 'email_send', {
            'to': fm.get('to', ''),
            'subject': fm.get('subject', ''),
            'body': fm.get('body', action.get_body()),
            'body_html': fm.get('body_html'),
            'cc': fm.get('cc'),
            'bcc': fm.get('bcc'),
            'attachments': fm.get('attachments', [])
        })

        return result

    def _handle_email_send_draft(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle send draft action."""
        fm = action.frontmatter
        draft_id = fm.get('draft_id')

        if not draft_id:
            return {'success': False, 'error': 'No draft_id provided'}

        return self._call_mcp_tool('email_mcp_server', 'email_send_draft', {
            'draft_id': draft_id
        })

    def _handle_email_create_draft(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle create draft action."""
        fm = action.frontmatter

        return self._call_mcp_tool('email_mcp_server', 'email_create_draft', {
            'to': fm.get('to', ''),
            'subject': fm.get('subject', ''),
            'body': fm.get('body', action.get_body()),
            'body_html': fm.get('body_html'),
            'cc': fm.get('cc'),
            'attachments': fm.get('attachments', [])
        })

    def _handle_payment(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle payment action (placeholder for Odoo MCP in Gold tier)."""
        fm = action.frontmatter

        self.logger.info(f'Payment action: {fm.get("amount")} to {fm.get("recipient")}')

        # For now, log that payment would be processed
        result = {
            'success': True,
            'status': 'logged',
            'message': 'Payment logged (Odoo integration required for actual payment)',
            'amount': fm.get('amount'),
            'recipient': fm.get('recipient'),
            'reference': fm.get('reference')
        }

        # Log to accounting
        self._log_payment(fm)

        return result

    def _handle_social_post(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle social media post action (placeholder for Gold tier)."""
        fm = action.frontmatter

        self.logger.info(f'Social post action: {fm.get("platform")}')

        result = {
            'success': True,
            'status': 'logged',
            'message': f'Social post logged for {fm.get("platform")} (integration required)',
            'platform': fm.get('platform'),
            'content': fm.get('content', action.get_body())
        }

        return result

    def _handle_file_operation(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle file operation action."""
        fm = action.frontmatter
        operation = fm.get('operation', 'move')

        src = fm.get('source')
        dest = fm.get('destination')

        if not src or not dest:
            return {'success': False, 'error': 'Missing source or destination'}

        src_path = Path(src)
        dest_path = Path(dest)

        try:
            if operation == 'move':
                shutil.move(str(src_path), str(dest_path))
            elif operation == 'copy':
                shutil.copy2(str(src_path), str(dest_path))
            elif operation == 'delete':
                src_path.unlink()
            elif operation == 'mkdir':
                dest_path.mkdir(parents=True, exist_ok=True)

            return {
                'success': True,
                'operation': operation,
                'source': src,
                'destination': dest
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_generic(self, action: ApprovalAction) -> Dict[str, Any]:
        """Handle generic action (log only)."""
        self.logger.info(f'Generic approved action: {action.filepath.name}')

        return {
            'success': True,
            'status': 'logged',
            'message': f'Action approved and logged: {action.filepath.name}',
            'action_type': action.action_type
        }

    def _call_mcp_tool(self, server_name: str, tool_name: str,
                       arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP server tool."""
        try:
            # Find the MCP server script
            mcp_servers_dir = self.vault_path / 'mcp_servers'
            server_script = mcp_servers_dir / f'{server_name}.py'

            if not server_script.exists():
                return {
                    'success': False,
                    'error': f'MCP server not found: {server_name}'
                }

            # For now, use subprocess to call the server
            # In production, you'd use proper MCP client library
            cmd = [
                sys.executable,
                str(server_script),
                '--vault-path', str(self.vault_path),
                '--call-tool', tool_name,
                '--args', json.dumps(arguments)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'MCP server timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _log_execution(self, action: ApprovalAction, result: Dict[str, Any],
                       status: str = 'approved'):
        """Log action execution."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action.action_type,
            'file': str(action.filepath),
            'status': status,
            'result': result
        }

        log_file = self.logs_path / f'approval_{datetime.now().strftime("%Y%m%d")}.json'

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

    def _log_payment(self, frontmatter: Dict[str, Any]):
        """Log payment to accounting."""
        accounting_path = self.vault_path / 'Accounting'
        accounting_path.mkdir(parents=True, exist_ok=True)

        # Append to current month log
        month_file = accounting_path / f'Payments_{datetime.now().strftime("%Y_%m")}.md'

        entry = f'''
## Payment Approved - {datetime.now().strftime('%Y-%m-%d %H:%M')}

| Field | Value |
|-------|-------|
| Amount | {frontmatter.get('amount', 'N/A')} |
| Recipient | {frontmatter.get('recipient', 'N/A')} |
| Reference | {frontmatter.get('reference', 'N/A')} |
| Approved At | {datetime.now().isoformat()} |

'''

        if month_file.exists():
            content = month_file.read_text(encoding='utf-8')
            content += entry
            month_file.write_text(content, encoding='utf-8')
        else:
            month_file.write_text(f'# Payments Log - {datetime.now().strftime("%B %Y")}\n{entry}',
                                  encoding='utf-8')

    def _move_to_done(self, filepath: Path, suffix: str = ''):
        """Move file to Done folder."""
        try:
            dest = self.done_folder / f'{filepath.stem}{suffix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            shutil.move(str(filepath), str(dest))
            self.logger.info(f'Moved to Done: {dest.name}')
        except Exception as e:
            self.logger.error(f'Error moving file to Done: {e}')

    def _add_rejection_note(self, filepath: Path):
        """Add rejection note to file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            content += f'\n\n---\n\n## Rejected\n\nThis action was rejected by human approver.\n\n**Rejected at:** {datetime.now().isoformat()}\n'
            filepath.write_text(content, encoding='utf-8')
        except Exception as e:
            self.logger.error(f'Error adding rejection note: {e}')

    def run(self):
        """Main run loop."""
        self.logger.info('Starting Approval Orchestrator')
        self.logger.info(f'Checking every {self.check_interval} seconds')

        print(f'''
╔══════════════════════════════════════════════════════════╗
║         Approval Workflow Orchestrator                    ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: {str(self.vault_path)[:55]}{"..." if len(str(self.vault_path)) > 55 else ""}
║  Check Interval: {self.check_interval}s
║                                                            ║
║  Monitoring folders:                                       ║
║    - /Approved (execute actions)                           ║
║    - /Rejected (log rejections)                            ║
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
''')

        try:
            while True:
                # Check approved files
                approved_actions = self.check_approved_files()
                for action in approved_actions:
                    result = self.execute_approved(action)
                    self.logger.info(f'Action result: {result.get("success", False)}')

                # Check rejected files
                rejected_actions = self.check_rejected_files()
                for action in rejected_actions:
                    result = self.process_rejected(action)
                    self.logger.info(f'Rejection processed')

                # Sleep
                import time
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Approval Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Approval Workflow Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python approval_orchestrator.py                   # Run orchestrator
  python approval_orchestrator.py --interval 5      # Check every 5 seconds
  python approval_orchestrator.py --vault PATH      # Specify vault path

Workflow:
  1. AI creates approval request in /Pending_Approval
  2. Human moves file to /Approved or /Rejected
  3. Orchestrator executes or logs the decision
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Check interval in seconds (default: 10)'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create and run orchestrator
    orchestrator = ApprovalOrchestrator(
        vault_path=vault_path,
        check_interval=args.interval
    )

    orchestrator.run()


if __name__ == '__main__':
    main()
