"""
Task Scheduler for AI Employee

Central orchestrator that schedules and manages all AI Employee tasks.
Supports cron-like scheduling, one-time tasks, and event-driven execution.

Features:
- Cron-like scheduling (daily, weekly, monthly)
- One-time scheduled tasks
- Event-driven task triggers
- Task queue management
- Integration with all watchers and processors

Scheduled Tasks:
- Daily Briefing (8:00 AM)
- Process Needs_Action (every 30 min)
- Weekly Audit (Sunday 10:00 PM)
- Dashboard Update (every 15 min)

Usage:
    python task_scheduler.py [--vault-path PATH]
    
For Windows Task Scheduler:
    schtasks /Create /TN "AI_Employee_Scheduler" /TR "python task_scheduler.py" /SC ONSTART /RU SYSTEM
    
For Linux cron:
    echo "* * * * * cd /path && python task_scheduler.py --daemon" | crontab -
"""

import os
import sys
import json
import time
import argparse
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    id: str
    name: str
    description: str
    schedule: str  # cron-like: "*/30 * * * *" or "daily 08:00"
    command: str  # Python command to execute
    priority: str = 'medium'
    enabled: bool = True
    last_run: str = None
    next_run: str = None
    run_count: int = 0
    fail_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        return cls(**data)


class TaskScheduler:
    """
    Central task scheduler for AI Employee.

    Manages scheduled tasks, executes them at appropriate times,
    and maintains task history.
    """

    # Default scheduled tasks
    DEFAULT_TASKS = [
        ScheduledTask(
            id='daily_briefing',
            name='Daily Briefing',
            description='Generate daily CEO briefing',
            schedule='daily 08:00',
            command='python scripts/briefing_generator.py --type daily',
            priority='high',
            enabled=True
        ),
        ScheduledTask(
            id='process_needs_action',
            name='Process Needs Action',
            description='Process pending items in Needs_Action folder',
            schedule='*/30 * * * *',  # Every 30 minutes
            command='python scripts/plan_generator.py',
            priority='high',
            enabled=True
        ),
        ScheduledTask(
            id='update_dashboard',
            name='Update Dashboard',
            description='Update Dashboard.md with current status',
            schedule='*/15 * * * *',  # Every 15 minutes
            command='python scripts/dashboard_updater.py',
            priority='medium',
            enabled=True
        ),
        ScheduledTask(
            id='weekly_audit',
            name='Weekly Business Audit',
            description='Generate weekly business and accounting audit',
            schedule='weekly sunday 22:00',
            command='python scripts/briefing_generator.py --type weekly',
            priority='high',
            enabled=True
        ),
        ScheduledTask(
            id='cleanup_old_files',
            name='Cleanup Old Files',
            description='Archive old completed tasks',
            schedule='daily 03:00',
            command='python scripts/cleanup_archiver.py',
            priority='low',
            enabled=True
        ),
        ScheduledTask(
            id='health_check',
            name='System Health Check',
            description='Check all watchers and services are running',
            schedule='hourly',
            command='python scripts/health_check.py',
            priority='critical',
            enabled=True
        )
    ]

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.config_path = self.vault_path / 'scheduler_config.json'
        self.history_path = self.vault_path / 'logs' / 'task_history.json'
        self.logs_path = self.vault_path / 'logs'

        # Ensure directories exist
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Setup logging first (before _load_tasks uses self.logger)
        self._setup_logging()

        # Load or initialize tasks
        self.tasks: Dict[str, ScheduledTask] = {}
        self._load_tasks()

        # Task history
        self.task_history: List[Dict[str, Any]] = []
        self._load_history()

        # Running state
        self.running = False

        self.logger.info(f'Task Scheduler initialized with {len(self.tasks)} tasks')

    def _setup_logging(self):
        """Configure logging."""
        import logging

        log_file = self.logs_path / f'task_scheduler_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TaskScheduler')

    def _load_tasks(self):
        """Load tasks from config or use defaults."""
        if self.config_path.exists():
            try:
                config = json.loads(self.config_path.read_text(encoding='utf-8'))
                for task_data in config.get('tasks', []):
                    # Convert string dates back to None for fresh parsing
                    if task_data.get('last_run'):
                        task_data['last_run'] = None
                    if task_data.get('next_run'):
                        task_data['next_run'] = None
                    task = ScheduledTask.from_dict(task_data)
                    self.tasks[task.id] = task
                self.logger.info(f'Loaded {len(self.tasks)} tasks from config')
            except Exception as e:
                self.logger.error(f'Error loading config: {e}')
                self._use_default_tasks()
        else:
            self._use_default_tasks()

    def _use_default_tasks(self):
        """Use default task definitions."""
        for task in self.DEFAULT_TASKS:
            self.tasks[task.id] = task
        self._save_tasks()

    def _save_tasks(self):
        """Save tasks to config file."""
        config = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'tasks': []
        }
        for task in self.tasks.values():
            task_dict = task.to_dict()
            # Convert datetime objects to strings for JSON serialization
            if task_dict.get('last_run') and not isinstance(task_dict['last_run'], str):
                task_dict['last_run'] = task_dict['last_run'].isoformat()
            if task_dict.get('next_run') and not isinstance(task_dict['next_run'], str):
                task_dict['next_run'] = task_dict['next_run'].isoformat()
            config['tasks'].append(task_dict)
        self.config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')

    def _load_history(self):
        """Load task execution history."""
        if self.history_path.exists():
            try:
                self.task_history = json.loads(self.history_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                self.task_history = []

    def _save_history(self):
        """Save task execution history."""
        # Keep only last 1000 entries
        history = self.task_history[-1000:]
        self.history_path.write_text(json.dumps(history, indent=2), encoding='utf-8')

    def _parse_schedule(self, schedule: str) -> Optional[datetime]:
        """
        Parse schedule string and return next run time.

        Supports:
        - Cron format: "*/30 * * * *" (minute, hour, day, month, weekday)
        - Daily: "daily HH:MM"
        - Weekly: "weekly day HH:MM"
        - Hourly: "hourly"
        """
        now = datetime.now()

        # Cron format (5 fields)
        if schedule.count(' ') == 4:
            return self._parse_cron(schedule, now)

        # Daily format
        if schedule.startswith('daily '):
            time_str = schedule.split()[1]
            hour, minute = map(int, time_str.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        # Weekly format
        if schedule.startswith('weekly '):
            parts = schedule.split()
            day_name = parts[1].lower()
            time_str = parts[2]
            hour, minute = map(int, time_str.split(':'))

            days_ahead = self._days_until(day_name, now)
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)

            if next_run <= now:
                next_run += timedelta(weeks=1)

            return next_run

        # Hourly format
        if schedule == 'hourly':
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            return next_run

        self.logger.warning(f'Unknown schedule format: {schedule}')
        return None

    def _parse_cron(self, cron_expr: str, now: datetime) -> datetime:
        """Parse cron expression and return next run time."""
        minute, hour, day, month, weekday = cron_expr.split()

        # Simple cron parser (supports *, */N, N)
        def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
            if field == '*':
                return list(range(min_val, max_val + 1))
            elif field.startswith('*/'):
                step = int(field[2:])
                return list(range(min_val, max_val + 1, step))
            elif ',' in field:
                return [int(x) for x in field.split(',')]
            elif '-' in field:
                start, end = map(int, field.split('-'))
                return list(range(start, end + 1))
            else:
                return [int(field)]

        minutes = parse_field(minute, 0, 59)
        hours = parse_field(hour, 0, 23)
        days = parse_field(day, 1, 31)
        months = parse_field(month, 1, 12)
        weekdays = parse_field(weekday, 0, 6)

        # Find next matching time
        check = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

        for _ in range(525600):  # Max 1 year of minutes
            if (check.month in months and
                check.day in days and
                check.weekday() in weekdays and
                check.hour in hours and
                check.minute in minutes):
                return check
            check += timedelta(minutes=1)

        return now + timedelta(days=1)  # Fallback

    def _days_until(self, day_name: str, now: datetime) -> int:
        """Calculate days until a given day name."""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target = days.index(day_name.lower()) if day_name.lower() in days else 0
        current = now.weekday()

        days_ahead = target - current
        if days_ahead < 0:
            days_ahead += 7
        return days_ahead

    def _should_run(self, task: ScheduledTask) -> bool:
        """Check if a task should run now."""
        if not task.enabled:
            return False

        if not task.next_run:
            # Calculate initial next_run
            task.next_run = self._parse_schedule(task.schedule)
            return False

        try:
            next_run = datetime.fromisoformat(task.next_run)
            return datetime.now() >= next_run
        except Exception:
            return False

    def _execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute a scheduled task."""
        self.logger.info(f'Executing task: {task.name}')

        result = {
            'task_id': task.id,
            'task_name': task.name,
            'started_at': datetime.now().isoformat(),
            'status': 'running'
        }

        try:
            # Execute command
            cmd = task.command.split()
            full_cmd = cmd

            # Run from vault directory
            process = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.vault_path)
            )

            result['completed_at'] = datetime.now().isoformat()
            result['return_code'] = process.returncode
            result['stdout'] = process.stdout
            result['stderr'] = process.stderr

            if process.returncode == 0:
                result['status'] = 'completed'
                task.run_count += 1
                self.logger.info(f'Task completed: {task.name}')
            else:
                result['status'] = 'failed'
                task.fail_count += 1
                self.logger.error(f'Task failed: {task.name} - {process.stderr}')

        except subprocess.TimeoutExpired:
            result['status'] = 'failed'
            result['error'] = 'Task timeout (5 minutes)'
            task.fail_count += 1
            self.logger.error(f'Task timeout: {task.name}')

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            task.fail_count += 1
            self.logger.error(f'Task error: {task.name} - {e}')

        # Update task
        task.last_run = datetime.now().isoformat()
        task.next_run = self._parse_schedule(task.schedule)

        # Record history
        self.task_history.append(result)
        self._save_history()

        return result

    def add_task(self, task: ScheduledTask):
        """Add a new scheduled task."""
        self.tasks[task.id] = task
        task.next_run = self._parse_schedule(task.schedule)
        self._save_tasks()
        self.logger.info(f'Added task: {task.name}')

    def remove_task(self, task_id: str):
        """Remove a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            self.logger.info(f'Removed task: {task_id}')

    def enable_task(self, task_id: str):
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_tasks()

    def disable_task(self, task_id: str):
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_tasks()

    def get_task_status(self) -> List[Dict[str, Any]]:
        """Get status of all tasks."""
        return [
            {
                'id': task.id,
                'name': task.name,
                'schedule': task.schedule,
                'enabled': task.enabled,
                'last_run': task.last_run,
                'next_run': task.next_run,
                'run_count': task.run_count,
                'fail_count': task.fail_count,
                'status': 'enabled' if task.enabled else 'disabled'
            }
            for task in self.tasks.values()
        ]

    def run_once(self):
        """Run all due tasks once."""
        self.logger.info('Running scheduled tasks check...')

        executed = []
        for task in self.tasks.values():
            if self._should_run(task):
                result = self._execute_task(task)
                executed.append(result)

        # Save task state
        self._save_tasks()

        return executed

    def run_daemon(self):
        """Run scheduler as daemon (continuous loop)."""
        self.running = True
        self.logger.info('Starting Task Scheduler daemon...')
        self.logger.info(f'Managing {len(self.tasks)} tasks')

        print(f'''
╔══════════════════════════════════════════════════════════╗
║            AI Employee Task Scheduler                     ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: {str(self.vault_path)[:55]}{"..." if len(str(self.vault_path)) > 55 else ""}
║  Tasks: {len(self.tasks)}
║  Check Interval: 60 seconds
║                                                            ║
║  Scheduled Tasks:                                          ║
''')

        for task in self.tasks.values():
            status = '✓' if task.enabled else '✗'
            print(f'║    {status} {task.name}: {task.schedule}')

        print(f'''║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
''')

        try:
            while self.running:
                self.run_once()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            self.logger.info('Task Scheduler stopped by user')
            self.running = False
        except Exception as e:
            self.logger.error(f'Scheduler error: {e}')
            self.running = False
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Task Scheduler for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python task_scheduler.py                    # Run scheduler daemon
  python task_scheduler.py --run-once         # Run due tasks once
  python task_scheduler.py --status           # Show task status
  python task_scheduler.py --add-task JSON    # Add new task
  python task_scheduler.py --vault PATH       # Specify vault path

For Windows Task Scheduler:
  schtasks /Create /TN "AI_Employee" /TR "python task_scheduler.py --run-once" /SC MINUTE /MO 5
  
For Linux cron:
  */5 * * * * cd /path && python task_scheduler.py --run-once
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run due tasks once and exit'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (continuous)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show task status'
    )

    parser.add_argument(
        '--add-task',
        type=str,
        help='Add task from JSON string'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create scheduler
    scheduler = TaskScheduler(vault_path)

    if args.status:
        # Show status
        status = scheduler.get_task_status()
        print('\nScheduled Tasks:')
        print('-' * 80)
        for task in status:
            print(f"\n  {task['name']} ({task['id']})")
            print(f"    Schedule: {task['schedule']}")
            print(f"    Status: {task['status']}")
            print(f"    Last Run: {task['last_run'] or 'Never'}")
            print(f"    Next Run: {task['next_run'] or 'Pending'}")
            print(f"    Runs: {task['run_count']} | Failures: {task['fail_count']}")
        print()

    elif args.add_task:
        # Add new task
        try:
            task_data = json.loads(args.add_task)
            task = ScheduledTask.from_dict(task_data)
            scheduler.add_task(task)
            print(f'✓ Added task: {task.name}')
        except Exception as e:
            print(f'✗ Error adding task: {e}')

    elif args.run_once:
        # Run once
        print('Running scheduled tasks...')
        results = scheduler.run_once()
        if results:
            print(f'Executed {len(results)} task(s)')
            for result in results:
                status = '✓' if result['status'] == 'completed' else '✗'
                print(f"  {status} {result['task_name']}: {result['status']}")
        else:
            print('No tasks due')

    else:
        # Run daemon (default)
        scheduler.run_daemon()


if __name__ == '__main__':
    main()
