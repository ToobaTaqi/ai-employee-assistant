"""
Base Watcher Module for AI Employee

This module provides the abstract base class for all watcher scripts.
Watchers monitor various inputs (email, WhatsApp, filesystem, etc.) and
create actionable markdown files in the Needs_Action folder.

Usage:
    Extend this class and implement check_for_updates() and create_action_file()
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all AI Employee watchers.
    
    Watchers run continuously, monitoring for new items that require
    AI processing. When new items are found, they create markdown
    files in the Needs_Action folder.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
        self.logger.info(f'{self.__class__.__name__} initialized')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {check_interval}s')
    
    def _setup_logging(self):
        """Configure logging for the watcher."""
        log_dir = self.vault_path / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'{self.__class__.__name__.lower()}_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new items that need processing.
        
        Returns:
            List of new items to process
            
        Example:
            For Gmail watcher: List of message objects
            For WhatsApp watcher: List of chat messages
            For Filesystem watcher: List of new files
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create a markdown action file for the given item.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file, or None if failed
            
        The action file should include:
            - YAML frontmatter with metadata
            - Item content/description
            - Suggested actions as checkboxes
        """
        pass
    
    def run(self):
        """
        Main run loop for the watcher.
        
        Continuously checks for updates and creates action files.
        Runs until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Watching for changes every {self.check_interval} seconds')
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                if filepath:
                                    self.logger.info(f'Created action file: {filepath.name}')
                            except Exception as e:
                                self.logger.error(f'Error creating action file: {e}')
                    else:
                        self.logger.debug('No new items')
                        
                except Exception as e:
                    self.logger.error(f'Error during check: {e}')
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise
    
    def generate_filename(self, prefix: str, unique_id: str) -> str:
        """
        Generate a unique filename for an action file.
        
        Args:
            prefix: File prefix (e.g., 'EMAIL', 'WHATSAPP', 'FILE')
            unique_id: Unique identifier for the item
            
        Returns:
            Filename string with .md extension
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_id = ''.join(c for c in unique_id if c.isalnum() or c in ('-', '_'))[:50]
        return f'{prefix}_{safe_id}_{timestamp}.md'
    
    def create_frontmatter(self, **kwargs) -> str:
        """
        Create YAML frontmatter for an action file.
        
        Args:
            **kwargs: Key-value pairs for frontmatter
            
        Returns:
            Formatted YAML frontmatter string
        """
        lines = ['---']
        lines.append(f'created: {datetime.now().isoformat()}')
        lines.append(f'status: pending')
        
        for key, value in kwargs.items():
            if isinstance(value, bool):
                lines.append(f'{key}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                lines.append(f'{key}: {value}')
            else:
                lines.append(f'{key}: {value}')
        
        lines.append('---')
        return '\n'.join(lines)
    
    def mark_processed(self, item_id: str):
        """
        Mark an item as processed to avoid duplicate processing.
        
        Args:
            item_id: Unique identifier of the item
        """
        self.processed_ids.add(item_id)
        self.logger.debug(f'Marked {item_id} as processed')
    
    def is_processed(self, item_id: str) -> bool:
        """
        Check if an item has already been processed.
        
        Args:
            item_id: Unique identifier of the item
            
        Returns:
            True if processed, False otherwise
        """
        return item_id in self.processed_ids


if __name__ == '__main__':
    # Example usage - this would be replaced by a concrete implementation
    print("BaseWatcher is an abstract class. Extend it to create a specific watcher.")
    print("See filesystem_watcher.py for an example implementation.")
