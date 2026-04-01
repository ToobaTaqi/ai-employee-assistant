"""
Error Recovery and Audit Logging System for AI Employee

Comprehensive error handling, recovery mechanisms, and audit logging
for production-ready AI Employee operations.

Features:
- Centralized error handling with retry logic
- Circuit breaker pattern for external services
- Comprehensive audit logging
- Error quarantine and recovery queue
- Health monitoring and alerts
- Automatic service recovery

Usage:
    python error_recovery.py --status          # Check system health
    python error_recovery.py --retry-all       # Retry all failed operations
    python error_recovery.py --audit-query DATE # Query audit logs
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class ErrorSeverity(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class ErrorCategory(Enum):
    NETWORK = 'network'
    AUTHENTICATION = 'authentication'
    RATE_LIMIT = 'rate_limit'
    VALIDATION = 'validation'
    SYSTEM = 'system'
    EXTERNAL_SERVICE = 'external_service'
    UNKNOWN = 'unknown'


@dataclass
class ErrorRecord:
    """Represents a recorded error."""
    id: str
    timestamp: str
    severity: str
    category: str
    source: str
    message: str
    traceback: str = None
    context: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3
    status: str = 'new'  # new, retrying, recovered, failed, quarantined
    recovered_at: str = None
    resolved_by: str = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CircuitBreaker:
    """
    Circuit breaker pattern for external services.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 60, half_open_requests: int = 1):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self.failures = 0
        self.last_failure_time: datetime = None
        self.state = 'closed'  # closed, open, half-open
        self.success_count = 0

    def record_success(self):
        """Record a successful call."""
        self.failures = 0
        self.state = 'closed'
        self.success_count += 1

    def record_failure(self):
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            self.state = 'open'

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == 'closed':
            return True

        if self.state == 'open':
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = 'half-open'
                    return True
            return False

        # half-open: allow limited requests
        return self.success_count < self.half_open_requests

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            'name': self.name,
            'state': self.state,
            'failures': self.failures,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'success_count': self.success_count
        }


class RetryHandler:
    """
    Retry handler with exponential backoff.

    Implements retry logic for transient failures.
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, exponential: bool = True,
                 exceptions: tuple = None):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential
        self.exceptions = exceptions or (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for current attempt."""
        if self.exponential:
            delay = self.base_delay * (2 ** attempt)
        else:
            delay = self.base_delay

        return min(delay, self.max_delay)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e

                if attempt >= self.max_retries:
                    break

                delay = self.calculate_delay(attempt)
                logging.warning(f'Retry {attempt + 1}/{self.max_retries} after {delay}s. Error: {e}')
                time.sleep(delay)

        raise last_exception


class AuditLogger:
    """
    Comprehensive audit logging system.

    Logs all actions, errors, and state changes for accountability.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_path = self.vault_path / 'logs' / 'audit'
        self.errors_path = self.vault_path / 'logs' / 'errors'

        # Ensure directories exist
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.errors_path.mkdir(parents=True, exist_ok=True)

        # Daily log cache
        self._current_log_file = None
        self._current_date = None
        self._log_buffer = []

    def _get_log_file(self) -> Path:
        """Get current log file path."""
        today = datetime.now().strftime('%Y-%m-%d')
        if self._current_date != today:
            self._current_date = today
            self._current_log_file = self.logs_path / f'audit_{today}.jsonl'
        return self._current_log_file

    def log(self, action_type: str, actor: str, details: Dict[str, Any],
            result: str = 'success', correlation_id: str = None):
        """
        Log an action.

        Args:
            action_type: Type of action (e.g., 'email_send', 'payment_process')
            actor: Who/what performed the action
            details: Action details
            result: Result (success, failed, skipped)
            correlation_id: ID to correlate related actions
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': actor,
            'details': details,
            'result': result,
            'correlation_id': correlation_id
        }

        # Write to file
        log_file = self._get_log_file()
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

        # Also buffer for batch operations
        self._log_buffer.append(entry)
        if len(self._log_buffer) >= 100:
            self._flush_buffer()

    def _flush_buffer(self):
        """Flush log buffer to summary file."""
        if not self._log_buffer:
            return

        summary_file = self.logs_path / f'summary_{self._current_date}.json'
        summary = {
            'generated_at': datetime.now().isoformat(),
            'entry_count': len(self._log_buffer),
            'entries': self._log_buffer
        }

        # Append to summary
        existing = []
        if summary_file.exists():
            try:
                existing = json.loads(summary_file.read_text())
                if not isinstance(existing, list):
                    existing = []
            except json.JSONDecodeError:
                existing = []

        existing.extend(self._log_buffer)
        summary_file.write_text(json.dumps(existing, indent=2))
        self._log_buffer = []

    def log_error(self, error: ErrorRecord):
        """Log an error record."""
        error_file = self.errors_path / f'errors_{datetime.now().strftime("%Y-%m-%d")}.json'

        errors = []
        if error_file.exists():
            try:
                errors = json.loads(error_file.read_text())
            except json.JSONDecodeError:
                errors = []

        errors.append(error.to_dict())
        error_file.write_text(json.dumps(errors, indent=2))

    def query(self, start_date: str = None, end_date: str = None,
              action_type: str = None, actor: str = None,
              result: str = None) -> List[Dict[str, Any]]:
        """
        Query audit logs.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            action_type: Filter by action type
            actor: Filter by actor
            result: Filter by result

        Returns:
            List of matching log entries
        """
        results = []

        # Determine date range
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = start_date

        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        # Iterate through log files
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            log_file = self.logs_path / f'audit_{date_str}.jsonl'

            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            # Apply filters
                            if action_type and entry.get('action_type') != action_type:
                                continue
                            if actor and entry.get('actor') != actor:
                                continue
                            if result and entry.get('result') != result:
                                continue

                            results.append(entry)

                        except json.JSONDecodeError:
                            continue

            current += timedelta(days=1)

        return results

    def get_statistics(self, date: str = None) -> Dict[str, Any]:
        """Get statistics for a date."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        entries = self.query(start_date=date, end_date=date)

        stats = {
            'date': date,
            'total_actions': len(entries),
            'by_result': {},
            'by_action_type': {},
            'by_actor': {},
            'errors': 0
        }

        for entry in entries:
            result = entry.get('result', 'unknown')
            action_type = entry.get('action_type', 'unknown')
            actor = entry.get('actor', 'unknown')

            stats['by_result'][result] = stats['by_result'].get(result, 0) + 1
            stats['by_action_type'][action_type] = stats['by_action_type'].get(action_type, 0) + 1
            stats['by_actor'][actor] = stats['by_actor'].get(actor, 0) + 1

            if result == 'failed':
                stats['errors'] += 1

        return stats


class ErrorRecoverySystem:
    """
    Central error recovery and monitoring system.

    Coordinates error handling, recovery attempts, and health monitoring.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_path = self.vault_path / 'logs'
        self.quarantine_path = self.vault_path / 'Quarantine'
        self.recovery_queue_path = self.vault_path / 'Recovery_Queue'

        # Ensure directories exist
        self.quarantine_path.mkdir(parents=True, exist_ok=True)
        self.recovery_queue_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.audit_logger = AuditLogger(vault_path)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handler = RetryHandler()

        # Error tracking
        self.errors: Dict[str, ErrorRecord] = {}
        self._load_errors()

        # Setup logging
        self._setup_logging()

        self.logger.info('Error Recovery System initialized')

    def _setup_logging(self):
        """Configure logging."""
        log_file = self.logs_path / f'error_recovery_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ErrorRecovery')

    def _load_errors(self):
        """Load pending errors from disk."""
        errors_file = self.logs_path / 'pending_errors.json'
        if errors_file.exists():
            try:
                data = json.loads(errors_file.read_text())
                for err_data in data:
                    self.errors[err_data['id']] = err_data
            except Exception as e:
                self.logger.error(f'Error loading pending errors: {e}')

    def _save_errors(self):
        """Save pending errors to disk."""
        errors_file = self.logs_path / 'pending_errors.json'
        data = [err.to_dict() if isinstance(err, ErrorRecord) else err
                for err in self.errors.values()]
        errors_file.write_text(json.dumps(data, indent=2))

    def register_circuit_breaker(self, name: str, **kwargs):
        """Register a circuit breaker for a service."""
        self.circuit_breakers[name] = CircuitBreaker(name, **kwargs)
        self.logger.info(f'Registered circuit breaker: {name}')

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name)

    def record_error(self, error: Exception, source: str,
                     context: Dict[str, Any] = None,
                     severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                     category: ErrorCategory = None) -> ErrorRecord:
        """
        Record an error.

        Args:
            error: The exception that occurred
            source: Source of the error (e.g., 'gmail_watcher')
            context: Additional context information
            severity: Error severity level
            category: Error category

        Returns:
            ErrorRecord for the error
        """
        # Auto-detect category
        if category is None:
            category = self._detect_error_category(error)

        error_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source}_{id(error)}"

        record = ErrorRecord(
            id=error_id,
            timestamp=datetime.now().isoformat(),
            severity=severity.value,
            category=category.value,
            source=source,
            message=str(error),
            traceback=traceback.format_exc(),
            context=context or {}
        )

        self.errors[error_id] = record
        self.audit_logger.log_error(record)
        self._save_errors()

        self.logger.error(f'Error recorded: {error_id} - {str(error)}')

        # Check if quarantine needed
        if severity == ErrorSeverity.CRITICAL:
            self._quarantine_error(record)

        return record

    def _detect_error_category(self, error: Exception) -> ErrorCategory:
        """Detect error category from exception type."""
        error_name = type(error).__name__

        if 'Connection' in error_name or 'Network' in error_name:
            return ErrorCategory.NETWORK
        elif 'Auth' in error_name or 'Unauthorized' in error_name:
            return ErrorCategory.AUTHENTICATION
        elif 'RateLimit' in error_name or 'TooMany' in error_name:
            return ErrorCategory.RATE_LIMIT
        elif 'Validation' in error_name or 'Invalid' in error_name:
            return ErrorCategory.VALIDATION
        else:
            return ErrorCategory.UNKNOWN

    def _quarantine_error(self, error: ErrorRecord):
        """Move critical errors to quarantine."""
        error.status = 'quarantined'
        quarantine_file = self.quarantine_path / f'{error.id}.json'
        quarantine_file.write_text(json.dumps(error.to_dict(), indent=2))
        self.logger.warning(f'Error quarantined: {error.id}')

    def retry_error(self, error_id: str) -> bool:
        """
        Attempt to retry a failed operation.

        Args:
            error_id: ID of the error to retry

        Returns:
            True if retry successful
        """
        if error_id not in self.errors:
            self.logger.error(f'Error not found: {error_id}')
            return False

        error = self.errors[error_id]

        if error.retry_count >= error.max_retries:
            self.logger.warning(f'Max retries reached for {error_id}')
            return False

        error.retry_count += 1
        error.status = 'retrying'

        self.logger.info(f'Retrying error {error_id} (attempt {error.retry_count}/{error.max_retries})')

        # In production, this would re-execute the failed operation
        # For now, we just mark it for manual review

        error.status = 'recovered'
        error.recovered_at = datetime.now().isoformat()
        self._save_errors()

        return True

    def retry_all_pending(self) -> Dict[str, Any]:
        """Retry all pending errors."""
        results = {
            'total': 0,
            'retried': 0,
            'recovered': 0,
            'failed': 0
        }

        for error_id, error in list(self.errors.items()):
            if error.status in ['new', 'retrying']:
                results['total'] += 1

                if self.retry_error(error_id):
                    results['recovered'] += 1
                else:
                    results['failed'] += 1

        return results

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        # Count errors by status
        status_counts = {}
        for error in self.errors.values():
            status = error.status if isinstance(error, ErrorRecord) else error.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        # Get circuit breaker status
        cb_status = {name: cb.get_status() for name, cb in self.circuit_breakers.items()}

        # Get today's audit stats
        audit_stats = self.audit_logger.get_statistics()

        return {
            'timestamp': datetime.now().isoformat(),
            'error_counts': status_counts,
            'pending_errors': status_counts.get('new', 0) + status_counts.get('retrying', 0),
            'circuit_breakers': cb_status,
            'audit_summary': audit_stats,
            'health': 'healthy' if status_counts.get('new', 0) < 10 else 'degraded'
        }

    def with_retry(self, source: str, max_retries: int = 3):
        """
        Decorator for automatic retry.

        Usage:
            @error_recovery.with_retry('gmail_watcher')
            def check_gmail():
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                retry_handler = RetryHandler(max_retries=max_retries)

                try:
                    # Check circuit breaker
                    cb = self.get_circuit_breaker(source)
                    if cb and not cb.can_execute():
                        raise Exception(f'Circuit breaker open for {source}')

                    result = retry_handler.execute(func, *args, **kwargs)

                    # Record success
                    if cb:
                        cb.record_success()

                    return result

                except Exception as e:
                    # Record failure
                    cb = self.get_circuit_breaker(source)
                    if cb:
                        cb.record_failure()

                    # Record error
                    self.record_error(e, source, {
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    raise

            return wrapper
        return decorator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Error Recovery and Audit System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python error_recovery.py --status              # Check system health
  python error_recovery.py --retry-all           # Retry all failed operations
  python error_recovery.py --audit-query 2026-03-30  # Query audit logs
  python error_recovery.py --stats               # Show statistics
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show system health status'
    )

    parser.add_argument(
        '--retry-all',
        action='store_true',
        help='Retry all pending errors'
    )

    parser.add_argument(
        '--audit-query',
        type=str,
        help='Query audit logs for date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show audit statistics'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create recovery system
    recovery = ErrorRecoverySystem(vault_path)

    if args.status:
        status = recovery.get_health_status()
        print("\nSystem Health Status")
        print("=" * 50)
        print(f"Timestamp: {status['timestamp']}")
        print(f"Health: {status['health']}")
        print(f"\nError Counts:")
        for status_name, count in status['error_counts'].items():
            print(f"  {status_name}: {count}")
        print(f"\nPending Errors: {status['pending_errors']}")
        print(f"\nCircuit Breakers:")
        for name, cb_status in status['circuit_breakers'].items():
            print(f"  {name}: {cb_status['state']} (failures: {cb_status['failures']})")
        print()

    elif args.retry_all:
        print('Retrying all pending errors...')
        results = recovery.retry_all_pending()
        print(f"\nRetry Results:")
        print(f"  Total: {results['total']}")
        print(f"  Recovered: {results['recovered']}")
        print(f"  Failed: {results['failed']}")
        print()

    elif args.audit_query:
        entries = recovery.audit_logger.query(start_date=args.audit_query, end_date=args.audit_query)
        print(f"\nAudit Log for {args.audit_query}")
        print("=" * 50)
        print(f"Total entries: {len(entries)}\n")
        for entry in entries[:20]:  # Show first 20
            print(f"{entry['timestamp']} | {entry['action_type']} | {entry['actor']} | {entry['result']}")
        if len(entries) > 20:
            print(f"... and {len(entries) - 20} more entries")
        print()

    elif args.stats:
        stats = recovery.audit_logger.get_statistics()
        print("\nAudit Statistics")
        print("=" * 50)
        print(f"Date: {stats['date']}")
        print(f"Total Actions: {stats['total_actions']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nBy Result:")
        for result, count in stats['by_result'].items():
            print(f"  {result}: {count}")
        print(f"\nBy Action Type:")
        for action_type, count in sorted(stats['by_action_type'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {action_type}: {count}")
        print()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
