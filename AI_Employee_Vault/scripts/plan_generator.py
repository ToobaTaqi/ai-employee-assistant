"""
Plan Generator for AI Employee

This module generates structured task plans for Qwen Code to execute.
It analyzes action files in Needs_Action and creates detailed Plan.md files
with step-by-step instructions, dependencies, and success criteria.

Features:
- Automatic plan generation from action files
- Dependency tracking between tasks
- Priority-based ordering
- Time estimation
- Resource requirements

Usage:
    python plan_generator.py [--vault-path PATH]
    python plan_generator.py --action-file FILE  # Generate plan for specific file
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class PlanGenerator:
    """
    Generates structured task plans for AI Employee.

    Analyzes action files and creates detailed execution plans.
    """

    # Task type templates
    TASK_TEMPLATES = {
        'email': {
            'default_steps': [
                'Read and understand email content',
                'Identify sender intent and required response',
                'Check Company Handbook for response guidelines',
                'Draft response or determine action needed',
                'Create approval request if sensitive action required',
                'Send response or execute action after approval',
                'Archive email and update Dashboard'
            ],
            'time_estimate_minutes': 15,
            'requires_approval': ['invoice', 'payment', 'contract', 'agreement']
        },
        'whatsapp': {
            'default_steps': [
                'Read WhatsApp message',
                'Identify urgency and intent',
                'Check if response needed',
                'Draft response following Company Handbook',
                'Send response or create approval request',
                'Mark message as read in WhatsApp'
            ],
            'time_estimate_minutes': 10,
            'requires_approval': ['pricing', 'quote', 'order', 'payment']
        },
        'file_drop': {
            'default_steps': [
                'Read file content',
                'Categorize file type and purpose',
                'Extract key information',
                'Determine required actions',
                'Execute actions or create approval request',
                'File document appropriately',
                'Update relevant records'
            ],
            'time_estimate_minutes': 20,
            'requires_approval': ['invoice', 'contract', 'legal', 'financial']
        },
        'payment': {
            'default_steps': [
                'Verify payment details (amount, recipient, reference)',
                'Check against Company Handbook thresholds',
                'Verify invoice/receipt exists',
                'Create approval request (always required for payments)',
                'After approval, process payment via Odoo/banking',
                'Record transaction in Accounting',
                'Update Dashboard and notify requester'
            ],
            'time_estimate_minutes': 30,
            'requires_approval': True  # Always
        },
        'social_post': {
            'default_steps': [
                'Review post content and platform',
                'Check Company Handbook for brand guidelines',
                'Verify posting schedule (business hours)',
                'Create approval request',
                'After approval, post via MCP server',
                'Log post in Social Media log',
                'Monitor for engagement'
            ],
            'time_estimate_minutes': 15,
            'requires_approval': True  # Always
        }
    }

    # Priority multipliers for time estimation
    PRIORITY_MULTIPLIERS = {
        'critical': 0.5,   # Urgent - less time, more focus
        'high': 0.75,
        'medium': 1.0,
        'low': 1.5         # Can take more time
    }

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.plans_folder = self.vault_path / 'Plans'
        self.needs_action_folder = self.vault_path / 'Needs_Action'
        self.handbook_path = self.vault_path / 'Company_Handbook.md'

        # Ensure folders exist
        self.plans_folder.mkdir(parents=True, exist_ok=True)

        # Load handbook rules
        self.handbook_rules = self._load_handbook_rules()

    def _load_handbook_rules(self) -> Dict[str, Any]:
        """Load rules from Company Handbook."""
        rules = {
            'payment_threshold': 500,  # Default threshold
            'response_time_hours': 24,
            'business_hours': (9, 18),  # 9 AM to 6 PM
            'approval_required_actions': ['payment', 'social_post', 'new_contact_email']
        }

        if self.handbook_path.exists():
            content = self.handbook_path.read_text(encoding='utf-8')
            # Simple parsing - could be enhanced
            if '$500' in content or '500' in content:
                rules['payment_threshold'] = 500
            if '2 hours' in content:
                rules['response_time_hours'] = 2

        return rules

    def generate_plan(self, action_file: Path, plan_id: str = None) -> Optional[Path]:
        """
        Generate a detailed plan for an action file.

        Args:
            action_file: Path to the action file
            plan_id: Optional custom plan ID

        Returns:
            Path to created plan file, or None if failed
        """
        try:
            # Read action file
            content = action_file.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)
            body = self._get_body(content)

            # Determine task type
            task_type = frontmatter.get('type', 'generic')
            action_type = frontmatter.get('action_type', task_type)

            # Get template
            template = self.TASK_TEMPLATES.get(action_type, self.TASK_TEMPLATES.get(task_type, None))
            if not template:
                template = self.TASK_TEMPLATES['file_drop']

            # Extract key info
            priority = frontmatter.get('priority', 'medium')
            subject = frontmatter.get('subject', frontmatter.get('chat_name', action_file.stem))

            # Generate steps
            steps = self._generate_steps(template, frontmatter, body)

            # Check if approval needed
            requires_approval = self._check_approval_needed(template, frontmatter)

            # Estimate time
            time_estimate = self._estimate_time(template, priority)

            # Identify dependencies
            dependencies = self._identify_dependencies(frontmatter, body)

            # Define success criteria
            success_criteria = self._define_success_criteria(action_type, frontmatter)

            # Generate plan content
            plan_content = self._create_plan_content(
                plan_id=plan_id or f'PLAN_{action_file.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                action_file=action_file,
                task_type=action_type,
                subject=subject,
                steps=steps,
                time_estimate=time_estimate,
                priority=priority,
                requires_approval=requires_approval,
                dependencies=dependencies,
                success_criteria=success_criteria,
                frontmatter=frontmatter,
                body=body
            )

            # Write plan file
            # Generate safe filename (remove newlines and invalid chars)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = ''.join(c for c in subject[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            plan_filename = f'PLAN_{safe_subject}_{timestamp}.md'
            plan_path = self.plans_folder / plan_filename
            plan_path.write_text(plan_content, encoding='utf-8')

            return plan_path

        except Exception as e:
            print(f'Error generating plan: {e}')
            return None

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter."""
        if not content.strip().startswith('---'):
            return {}

        try:
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

            result = {}
            for line in frontmatter_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')

                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)

                    result[key] = value

            return result

        except Exception:
            return {}

    def _get_body(self, content: str) -> str:
        """Get markdown body without frontmatter."""
        if content.strip().startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx > 0:
                return content[end_idx + 3:].strip()
        return content

    def _generate_steps(self, template: Dict, frontmatter: Dict, body: str) -> List[Dict[str, Any]]:
        """Generate detailed steps from template."""
        steps = []

        for i, step_desc in enumerate(template.get('default_steps', [])):
            step = {
                'order': i + 1,
                'description': step_desc,
                'status': 'pending',
                'completed_at': None,
                'notes': ''
            }

            # Add step-specific details
            if 'approval' in step_desc.lower():
                step['requires_human'] = True

            if 'send' in step_desc.lower() or 'post' in step_desc.lower():
                step['requires_mcp'] = True

            steps.append(step)

        return steps

    def _check_approval_needed(self, template: Dict, frontmatter: Dict) -> bool:
        """Check if action requires human approval."""
        # Check explicit flag
        if frontmatter.get('needs_approval') == True or frontmatter.get('needs_approval') == 'true':
            return True

        # Check template rules
        if template.get('requires_approval') == True:
            return True

        # Check keywords
        requires_keywords = template.get('requires_approval', [])
        if isinstance(requires_keywords, list):
            subject = frontmatter.get('subject', '').lower()
            body_keywords = ' '.join(str(v) for v in frontmatter.values()).lower()
            for kw in requires_keywords:
                if kw.lower() in subject or kw.lower() in body_keywords:
                    return True

        # Check payment threshold
        amount = frontmatter.get('amount')
        if amount:
            try:
                if float(amount) > self.handbook_rules['payment_threshold']:
                    return True
            except (ValueError, TypeError):
                pass

        return False

    def _estimate_time(self, template: Dict, priority: str) -> int:
        """Estimate time in minutes."""
        base_time = template.get('time_estimate_minutes', 15)
        multiplier = self.PRIORITY_MULTIPLIERS.get(priority, 1.0)
        return int(base_time * multiplier)

    def _identify_dependencies(self, frontmatter: Dict, body: str) -> List[str]:
        """Identify task dependencies."""
        dependencies = []

        # Check for invoice references
        if 'invoice' in body.lower():
            dependencies.append('invoice_verification')

        # Check for payment references
        if 'payment' in body.lower() or 'pay' in body.lower():
            dependencies.append('approval_required')

        # Check for attachment processing
        if frontmatter.get('has_attachments') == True or frontmatter.get('attachment_count', 0) > 0:
            dependencies.append('attachment_download')

        return dependencies

    def _define_success_criteria(self, action_type: str, frontmatter: Dict) -> List[str]:
        """Define success criteria for the task."""
        criteria = []

        if action_type == 'email':
            criteria = [
                'Response sent or appropriate action taken',
                'Email archived appropriately',
                'Dashboard updated'
            ]
        elif action_type == 'whatsapp':
            criteria = [
                'Message responded to (if needed)',
                'Chat marked as read',
                'Action logged'
            ]
        elif action_type == 'file_drop':
            criteria = [
                'File content processed',
                'Required actions completed',
                'File archived appropriately'
            ]
        elif action_type == 'payment':
            criteria = [
                'Payment approved by human',
                'Payment processed successfully',
                'Transaction recorded in Accounting',
                'Stakeholder notified'
            ]
        elif action_type == 'social_post':
            criteria = [
                'Post approved by human',
                'Post published successfully',
                'Post logged in Social Media log'
            ]
        else:
            criteria = [
                'Task completed according to Company Handbook',
                'Results documented',
                'Stakeholders notified if needed'
            ]

        return criteria

    def _create_plan_content(self, **kwargs) -> str:
        """Create the full plan markdown content."""
        steps_text = '\n'.join(
            f"- [ ] **Step {s['order']}:** {s['description']}"
            for s in kwargs['steps']
        )

        dependencies_text = '\n'.join(f'- {dep}' for dep in kwargs['dependencies']) or '- None'

        success_text = '\n'.join(f'- {criteria}' for criteria in kwargs['success_criteria'])

        # Determine assigned agent
        assigned_agent = kwargs['frontmatter'].get('assigned_agent', 'Qwen Code')

        content = f'''---
id: {kwargs['plan_id']}
type: plan
created: {datetime.now().isoformat()}
status: pending
priority: {kwargs['priority']}
action_file: {kwargs['action_file'].name}
task_type: {kwargs['task_type']}
requires_approval: {str(kwargs['requires_approval']).lower()}
estimated_time_minutes: {kwargs['time_estimate']}
assigned_agent: {assigned_agent}
---

# Task Plan: {kwargs['subject']}

## Overview

| Property | Value |
|----------|-------|
| **Task Type** | {kwargs['task_type']} |
| **Priority** | {kwargs['priority'].upper()} |
| **Estimated Time** | {kwargs['time_estimate']} minutes |
| **Requires Approval** | {'Yes' if kwargs['requires_approval'] else 'No'} |
| **Assigned Agent** | {assigned_agent} |

## Action File

Source: `{kwargs['action_file'].name}`

## Execution Steps

{steps_text}

## Dependencies

{dependencies_text}

## Success Criteria

{success_text}

## Notes

*Add any additional context or observations during execution*

---

## Execution Log

| Timestamp | Step | Status | Notes |
|-----------|------|--------|-------|
| - | - | pending | - |

---

*Plan generated by AI Employee Plan Generator*
'''
        return content

    def generate_plans_for_all_pending(self) -> List[Path]:
        """Generate plans for all action files in Needs_Action."""
        plans = []

        if not self.needs_action_folder.exists():
            return plans

        for action_file in self.needs_action_folder.iterdir():
            if action_file.suffix != '.md':
                continue

            # Skip if already has a plan
            plan_exists = any(
                p.name.startswith(f'PLAN_{action_file.stem}')
                for p in self.plans_folder.iterdir()
            )

            if not plan_exists:
                plan_path = self.generate_plan(action_file)
                if plan_path:
                    plans.append(plan_path)
                    print(f'Generated plan: {plan_path.name}')

        return plans


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Plan Generator for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python plan_generator.py                        # Generate plans for all pending actions
  python plan_generator.py --action-file FILE     # Generate plan for specific file
  python plan_generator.py --vault-path PATH      # Specify vault path
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--action-file',
        type=str,
        default=None,
        help='Specific action file to generate plan for'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create generator
    generator = PlanGenerator(vault_path)

    if args.action_file:
        # Generate plan for specific file
        action_path = Path(args.action_file)
        if not action_path.exists():
            action_path = Path(vault_path) / 'Needs_Action' / args.action_file

        if action_path.exists():
            plan_path = generator.generate_plan(action_path)
            if plan_path:
                print(f'✓ Plan generated: {plan_path}')
            else:
                print('✗ Failed to generate plan')
        else:
            print(f'Action file not found: {action_path}')
    else:
        # Generate plans for all pending
        print('Generating plans for all pending actions...')
        plans = generator.generate_plans_for_all_pending()
        print(f'✓ Generated {len(plans)} plan(s)')


if __name__ == '__main__':
    main()
