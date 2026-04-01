"""
Briefing Generator for AI Employee

Generates daily and weekly briefings including:
- Monday Morning CEO Briefing
- Daily Status Reports
- Weekly Business Audit

Usage:
    python briefing_generator.py --type daily
    python briefing_generator.py --type weekly
    python briefing_generator.py --type ceo
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))


class BriefingGenerator:
    """Generates executive briefings."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.briefings_path = self.vault_path / 'Briefings'
        self.accounting_path = self.vault_path / 'Accounting'
        self.done_path = self.vault_path / 'Done'
        self.handbook_path = self.vault_path / 'Company_Handbook.md'

        # Ensure briefings folder exists
        self.briefings_path.mkdir(parents=True, exist_ok=True)

    def get_week_start(self, date: datetime) -> datetime:
        """Get the Monday of the week containing date."""
        return date - timedelta(days=date.weekday())

    def get_period_files(self, folder: str, days: int = 7) -> List[Path]:
        """Get files modified in the last N days."""
        folder_path = self.vault_path / folder
        if not folder_path.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        files = []

        for f in folder_path.iterdir():
            if f.suffix == '.md':
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime >= cutoff:
                    files.append(f)

        return files

    def parse_transaction_files(self) -> Dict[str, Any]:
        """Parse accounting transaction files."""
        transactions = []

        if not self.accounting_path.exists():
            return {
                'total_revenue': 0,
                'total_expenses': 0,
                'transactions': []
            }

        for f in self.accounting_path.iterdir():
            if f.suffix == '.md' and ('Transaction' in f.name or 'Payment' in f.name):
                content = f.read_text(encoding='utf-8')
                # Parse transactions from markdown table
                for line in content.split('\n'):
                    if '|' in line and '$' in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 3:
                            try:
                                # Extract amount
                                amount_str = ''
                                for part in parts:
                                    if '$' in part:
                                        amount_str = part.split('$')[1].strip().replace(',', '')
                                        break

                                if amount_str:
                                    amount = float(amount_str)
                                    transactions.append({
                                        'description': parts[0] if parts else 'Unknown',
                                        'amount': amount,
                                        'date': f.stat().st_mtime
                                    })
                            except (ValueError, IndexError):
                                pass

        total_revenue = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_expenses = abs(sum(t['amount'] for t in transactions if t['amount'] < 0))

        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net': total_revenue - total_expenses,
            'transactions': transactions
        }

    def parse_completed_tasks(self, days: int = 7) -> List[Dict[str, Any]]:
        """Parse completed tasks from Done folder."""
        tasks = []
        files = self.get_period_files('Done', days)

        for f in files:
            content = f.read_text(encoding='utf-8')
            subject = f.stem.replace('_', ' ')

            # Try to extract subject from frontmatter
            for line in content.split('\n'):
                if line.startswith('subject:'):
                    subject = line.split(':', 1)[1].strip().strip('"\'')
                    break

            tasks.append({
                'name': subject,
                'completed_at': datetime.fromtimestamp(f.stat().st_mtime),
                'file': f.name
            })

        return sorted(tasks, key=lambda t: t['completed_at'], reverse=True)

    def get_business_goals(self) -> Dict[str, Any]:
        """Get business goals from Company Handbook."""
        goals = {
            'revenue_target': 10000,
            'current_mtd': 0,
            'key_metrics': []
        }

        if self.handbook_path.exists():
            content = self.handbook_path.read_text(encoding='utf-8')
            # Simple parsing
            if '$10,000' in content or '10000' in content:
                goals['revenue_target'] = 10000

        # Update with actual data
        accounting = self.parse_transaction_files()
        goals['current_mtd'] = accounting['total_revenue']

        return goals

    def identify_bottlenecks(self, tasks: List[Dict]) -> List[Dict]:
        """Identify potential bottlenecks from task patterns."""
        bottlenecks = []

        # Check for items stuck in Needs_Action
        needs_action_path = self.vault_path / 'Needs_Action'
        if needs_action_path.exists():
            old_cutoff = datetime.now() - timedelta(days=3)
            for f in needs_action_path.iterdir():
                if f.suffix == '.md':
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime < old_cutoff:
                        bottlenecks.append({
                            'task': f.stem,
                            'age_days': (datetime.now() - mtime).days,
                            'issue': 'Pending for more than 3 days'
                        })

        return bottlenecks

    def generate_daily_briefing(self) -> Path:
        """Generate daily briefing."""
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')

        # Gather data
        accounting = self.parse_transaction_files()
        tasks = self.parse_completed_tasks(days=1)
        goals = self.get_business_goals()

        # Generate content
        content = f'''---
generated: {now.isoformat()}
period: {date_str}
type: daily_briefing
---

# Daily Briefing - {date_str}

## Executive Summary

{self._generate_summary(accounting, tasks)}

## Today's Activity

### Completed Tasks
{self._format_tasks(tasks)}

### Financial Activity
- Revenue: ${accounting['total_revenue']:,.2f}
- Expenses: ${accounting['total_expenses']:,.2f}
- Net: ${accounting['net']:,.2f}

## MTD Progress

| Metric | Target | Actual | Progress |
|--------|--------|--------|----------|
| Revenue | ${goals['revenue_target']:,.2f} | ${goals['current_mtd']:,.2f} | {goals['current_mtd']/goals['revenue_target']*100:.1f}% |

## Pending Items

{self._get_pending_summary()}

## Recommendations

{self._generate_recommendations(accounting, tasks)}

---
*Generated by AI Employee Briefing Generator*
'''

        # Write briefing
        filepath = self.briefings_path / f'{date_str}_Daily_Briefing.md'
        filepath.write_text(content, encoding='utf-8')
        return filepath

    def generate_weekly_briefing(self) -> Path:
        """Generate weekly business audit (CEO Briefing)."""
        now = datetime.now()
        week_start = self.get_week_start(now)
        week_end = week_start + timedelta(days=6)

        date_range = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"

        # Gather data
        accounting = self.parse_transaction_files(days=7)
        tasks = self.parse_completed_tasks(days=7)
        goals = self.get_business_goals()
        bottlenecks = self.identify_bottlenecks(tasks)

        # Generate content
        content = f'''---
generated: {now.isoformat()}
period: {date_range}
type: weekly_briefing
---

# Monday Morning CEO Briefing

> **Week of:** {date_range}
> **Generated:** {now.strftime('%Y-%m-%d %H:%M')}

---

## Executive Summary

{self._generate_weekly_summary(accounting, tasks, bottlenecks)}

---

## Revenue Report

| Metric | Amount |
|--------|--------|
| **This Week** | ${accounting['total_revenue']:,.2f} |
| **MTD** | ${goals['current_mtd']:,.2f} |
| **Target** | ${goals['revenue_target']:,.2f} |
| **Progress** | {goals['current_mtd']/goals['revenue_target']*100:.1f}% |

### Revenue Trend
{self._format_revenue_trend(accounting)}

---

## Completed Tasks This Week

{self._format_weekly_tasks(tasks)}

---

## Bottlenecks Identified

{self._format_bottlenecks(bottlenecks)}

---

## Proactive Suggestions

{self._generate_weekly_recommendations(accounting, bottlenecks)}

---

## Upcoming Deadlines

| Date | Event |
|------|-------|
| {now.strftime('%Y-%m-%d')} + 7 days | Weekly Review |
| {now.strftime('%Y-%m-%d')} + 30 days | Monthly Close |

---

## Action Items for This Week

1. Review and approve pending items in /Pending_Approval
2. Address identified bottlenecks
3. Review financial performance vs. targets

---

*Generated by AI Employee - Monday Morning CEO Briefing*
'''

        # Write briefing
        filepath = self.briefings_path / f'{now.strftime("%Y-%m-%d")}_Weekly_Briefing.md'
        filepath.write_text(content, encoding='utf-8')
        return filepath

    def _generate_summary(self, accounting: Dict, tasks: List) -> str:
        """Generate executive summary."""
        if accounting['net'] > 0:
            return f"Positive day with net gain of ${accounting['net']:,.2f}. {len(tasks)} tasks completed."
        elif accounting['net'] < 0:
            return f"Net expenses of ${abs(accounting['net']):,.2f}. {len(tasks)} tasks completed."
        else:
            return f"Quiet day. {len(tasks)} tasks completed."

    def _generate_weekly_summary(self, accounting: Dict, tasks: List, bottlenecks: List) -> str:
        """Generate weekly executive summary."""
        parts = []

        # Revenue assessment
        if accounting['total_revenue'] > 0:
            parts.append(f"Strong week with ${accounting['total_revenue']:,.2f} revenue.")
        else:
            parts.append("Revenue week pending.")

        # Task assessment
        parts.append(f"{len(tasks)} tasks completed.")

        # Bottleneck assessment
        if bottlenecks:
            parts.append(f"{len(bottlenecks)} bottleneck(s) identified requiring attention.")

        return ' '.join(parts)

    def _format_tasks(self, tasks: List) -> str:
        """Format tasks list."""
        if not tasks:
            return '*No tasks completed*\n'

        lines = []
        for task in tasks[:10]:  # Limit to 10
            time_str = task['completed_at'].strftime('%H:%M')
            lines.append(f"- [x] {task['name']} ({time_str})")
        return '\n'.join(lines)

    def _format_weekly_tasks(self, tasks: List) -> str:
        """Format weekly tasks table."""
        if not tasks:
            return '*No tasks completed this week*\n'

        lines = ['| Task | Completed |', '|------|-----------|']
        for task in tasks[:15]:
            date_str = task['completed_at'].strftime('%Y-%m-%d')
            lines.append(f"| {task['name'][:40]} | {date_str} |")
        return '\n'.join(lines)

    def _format_bottlenecks(self, bottlenecks: List) -> str:
        """Format bottlenecks table."""
        if not bottlenecks:
            return '*No bottlenecks identified*\n'

        lines = ['| Task | Age | Issue |', '|------|-----|-------|']
        for b in bottlenecks:
            lines.append(f"| {b['task'][:30]} | {b['age_days']} days | {b['issue']} |")
        return '\n'.join(lines)

    def _format_revenue_trend(self, accounting: Dict) -> str:
        """Format revenue trend."""
        # Simple trend - would be enhanced with historical data
        if accounting['total_revenue'] > 0:
            return "📈 Revenue generated this week"
        else:
            return "➡️ No revenue recorded this week"

    def _get_pending_summary(self) -> str:
        """Get pending items summary."""
        needs_action_path = self.vault_path / 'Needs_Action'
        if not needs_action_path.exists():
            return '*No pending items*'

        count = len([f for f in needs_action_path.iterdir() if f.suffix == '.md'])
        return f'**{count} items** awaiting processing\n'

    def _generate_recommendations(self, accounting: Dict, tasks: List) -> str:
        """Generate daily recommendations."""
        recs = []

        if accounting['total_expenses'] > 100:
            recs.append("- Review high expenses")

        if len(tasks) > 5:
            recs.append("- High task volume - prioritize critical items")

        if not recs:
            recs.append("- Continue current operations")

        return '\n'.join(recs)

    def _generate_weekly_recommendations(self, accounting: Dict, bottlenecks: List) -> str:
        """Generate weekly recommendations."""
        recs = []

        # Revenue recommendations
        if accounting['total_revenue'] == 0:
            recs.append("1. **Revenue Focus**: No revenue recorded this week. Review pipeline and follow up on leads.")

        # Bottleneck recommendations
        if bottlenecks:
            recs.append(f"2. **Address Bottlenecks**: {len(bottlenecks)} items stuck. Review and unblock.")

        # Expense recommendations
        if accounting['total_expenses'] > accounting['total_revenue'] * 0.5:
            recs.append("3. **Expense Review**: Expenses high relative to revenue. Audit subscriptions and costs.")

        if not recs:
            recs.append("1. **Continue Momentum**: All metrics healthy. Maintain current pace.")

        return '\n'.join(recs)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Briefing Generator')
    parser.add_argument('--type', choices=['daily', 'weekly', 'ceo'], default='daily',
                       help='Briefing type (daily, weekly, ceo)')
    parser.add_argument('--vault-path', type=str, default=None, help='Path to Obsidian vault')
    args = parser.parse_args()

    vault_path = args.vault_path if args.vault_path else str(Path(__file__).parent.parent)

    generator = BriefingGenerator(vault_path)

    if args.type == 'daily':
        filepath = generator.generate_daily_briefing()
        print(f'✓ Daily briefing generated: {filepath}')
    elif args.type in ['weekly', 'ceo']:
        filepath = generator.generate_weekly_briefing()
        print(f'✓ Weekly CEO briefing generated: {filepath}')


if __name__ == '__main__':
    main()
