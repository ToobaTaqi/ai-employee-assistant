"""
Dashboard Updater for AI Employee

Updates Dashboard.md with current system status, pending tasks,
completed items, and financial summary.

Usage:
    python dashboard_updater.py [--vault-path PATH]
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))


class DashboardUpdater:
    """Updates the main Dashboard.md file."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.dashboard_path = self.vault_path / 'Dashboard.md'
        self.logs_path = self.vault_path / 'logs'

    def count_files(self, folder: str) -> int:
        """Count markdown files in a folder."""
        folder_path = self.vault_path / folder
        if not folder_path.exists():
            return 0
        return len([f for f in folder_path.iterdir() if f.suffix == '.md'])

    def get_recent_completed(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently completed tasks."""
        done_path = self.vault_path / 'Done'
        if not done_path.exists():
            return []

        files = sorted(
            [f for f in done_path.iterdir() if f.suffix == '.md'],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]

        results = []
        for f in files:
            content = f.read_text(encoding='utf-8')
            # Extract subject from frontmatter or filename
            subject = f.stem.replace('_', ' ')
            if 'subject:' in content:
                for line in content.split('\n'):
                    if line.startswith('subject:'):
                        subject = line.split(':', 1)[1].strip().strip('"\'')
                        break

            results.append({
                'name': subject,
                'completed_at': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            })

        return results

    def get_financial_summary(self) -> Dict[str, Any]:
        """Get financial summary from Accounting folder."""
        accounting_path = self.vault_path / 'Accounting'
        if not accounting_path.exists():
            return {'business_balance': 0, 'personal_balance': 0, 'month_total': 0}

        # Parse transaction files
        total_income = 0
        total_expense = 0

        for f in accounting_path.iterdir():
            if f.suffix == '.md' and 'Transaction' in f.name:
                content = f.read_text(encoding='utf-8')
                # Simple parsing - look for amount patterns
                for line in content.split('\n'):
                    if '|' in line and '$' in line:
                        parts = line.split('|')
                        for part in parts:
                            if '$' in part:
                                try:
                                    amount_str = part.split('$')[1].strip().replace(',', '')
                                    amount = float(amount_str)
                                    if amount > 0:
                                        total_income += amount
                                    else:
                                        total_expense += abs(amount)
                                except ValueError:
                                    pass

        return {
            'business_balance': total_income - total_expense,
            'personal_balance': 0,  # Would need actual bank integration
            'month_income': total_income,
            'month_expense': total_expense
        }

    def get_alerts(self) -> List[str]:
        """Get active alerts."""
        alerts = []

        # Check for high-priority items
        needs_action_path = self.vault_path / 'Needs_Action'
        if needs_action_path.exists():
            count = self.count_files('Needs_Action')
            if count > 10:
                alerts.append(f'⚠️ High workload: {count} items pending')

        # Check for failed tasks
        logs_path = self.vault_path / 'logs'
        if logs_path.exists():
            # Check for recent errors in logs
            pass

        return alerts

    def update(self):
        """Update the Dashboard.md file."""
        now = datetime.now()

        # Gather data
        pending_count = self.count_files('Needs_Action')
        approval_count = self.count_files('Pending_Approval')
        completed_today = self.count_files('Done')
        recent_completed = self.get_recent_completed()
        financial = self.get_financial_summary()
        alerts = self.get_alerts()

        # Build recent completed section
        completed_text = ''
        if recent_completed:
            for item in recent_completed:
                completed_text += f"- {item['name']} ({item['completed_at']})\n"
        else:
            completed_text = '*No completed tasks yet*\n'

        # Build alerts section
        alerts_text = ''
        if alerts:
            for alert in alerts:
                alerts_text += f"- {alert}\n"
        else:
            alerts_text = '*No active alerts*\n'

        # Generate dashboard content
        content = f'''---
type: dashboard
last_updated: {now.isoformat()}
status: active
---

# AI Employee Dashboard

> **Last Updated:** {now.strftime('%Y-%m-%d %H:%M')}
> **Status:** Active Monitoring

---

## 📊 Quick Status

| Metric | Value |
|--------|-------|
| Pending Tasks | {pending_count} |
| Awaiting Approval | {approval_count} |
| Completed Today | {completed_today} |
| Revenue MTD | ${financial.get('month_income', 0):,.2f} |

---

## 📥 Inbox Summary

*Check Inbox folder for new items*

---

## ⏳ Needs Action

**{pending_count} items pending**

---

## ✅ Recently Completed

{completed_text}

---

## 📋 Active Projects

| Project | Status | Next Step |
|---------|--------|-----------|
| System Running | Active | Monitoring |

---

## 💰 Financial Snapshot

| Account | Balance | Last Updated |
|---------|---------|--------------|
| Business | ${financial.get('business_balance', 0):,.2f} | {now.strftime('%Y-%m-%d')} |
| Personal | ${financial.get('personal_balance', 0):,.2f} | - |

---

## 🔔 Alerts

{alerts_text}

---

## 📝 Notes

*Dashboard auto-updated by AI Employee*
'''

        # Write dashboard
        self.dashboard_path.write_text(content, encoding='utf-8')
        print(f'✓ Dashboard updated at {now.strftime("%H:%M:%S")}')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Dashboard Updater')
    parser.add_argument('--vault-path', type=str, default=None, help='Path to Obsidian vault')
    args = parser.parse_args()

    vault_path = args.vault_path if args.vault_path else str(Path(__file__).parent.parent)

    updater = DashboardUpdater(vault_path)
    updater.update()


if __name__ == '__main__':
    main()
