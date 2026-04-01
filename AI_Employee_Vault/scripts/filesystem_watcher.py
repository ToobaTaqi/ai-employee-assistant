"""
File System Watcher for AI Employee

This watcher monitors a "drop folder" for new files. When files are added,
it creates corresponding action files in the Needs_Action folder for
the AI Employee to process.

Use Cases:
- Drop invoices for processing
- Drop documents for summarization
- Drop images for analysis
- Drop any file that needs AI attention

Setup:
1. Configure VAULT_PATH below or pass as argument
2. Run: python filesystem_watcher.py
3. Drop files into the Inbox folder
4. Watcher creates action files in Needs_Action

Usage:
    python filesystem_watcher.py [--vault-path PATH] [--interval SECONDS]
"""

import os
import sys
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class FileDropItem:
    """Represents a file dropped for processing."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.name = filepath.name
        self.size = filepath.stat().st_size
        self.created = filepath.stat().st_ctime
        self.modified = filepath.stat().st_mtime
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate MD5 hash of file for deduplication."""
        hash_md5 = hashlib.md5()
        with open(self.filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_extension(self) -> str:
        """Get file extension (lowercase, without dot)."""
        return self.filepath.suffix.lower().lstrip('.')
    
    def get_category(self) -> str:
        """Categorize file by extension."""
        categories = {
            'document': ['pdf', 'doc', 'docx', 'txt', 'md', 'rtf'],
            'spreadsheet': ['xls', 'xlsx', 'csv', 'ods'],
            'presentation': ['ppt', 'pptx', 'odp'],
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
            'data': ['json', 'xml', 'yaml', 'yml'],
            'archive': ['zip', 'rar', '7z', 'tar', 'gz'],
            'code': ['py', 'js', 'ts', 'java', 'cpp', 'c', 'h', 'go', 'rs'],
        }
        
        ext = self.get_extension()
        for category, extensions in categories.items():
            if ext in extensions:
                return category
        return 'other'


class FilesystemWatcher(BaseWatcher):
    """
    Watches a drop folder for new files and creates action files.
    
    When a file is detected in the Inbox folder:
    1. Creates a metadata markdown file in Needs_Action
    2. Copies the original file to a processing folder
    3. Logs the action for audit trail
    """
    
    def __init__(self, vault_path: str, check_interval: int = 30, 
                 drop_folder: str = 'Inbox', process_folder: str = 'Processing'):
        """
        Initialize the filesystem watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 30)
            drop_folder: Name of the drop folder (default: Inbox)
            process_folder: Name of the processing folder (default: Processing)
        """
        super().__init__(vault_path, check_interval)
        
        self.drop_folder = self.vault_path / drop_folder
        self.process_folder = self.vault_path / process_folder
        
        # Ensure folders exist
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        self.process_folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed files by hash
        self.processed_hashes: set = set()
        
        self.logger.info(f'Drop folder: {self.drop_folder}')
        self.logger.info(f'Process folder: {self.process_folder}')
    
    def check_for_updates(self) -> List[FileDropItem]:
        """
        Check for new files in the drop folder.
        
        Returns:
            List of FileDropItem objects for new files
        """
        new_items = []
        
        try:
            # Get all files in drop folder (not directories)
            files = [f for f in self.drop_folder.iterdir() if f.is_file()]
            
            for filepath in files:
                try:
                    item = FileDropItem(filepath)
                    
                    # Skip if already processed
                    if self.is_processed(item.hash):
                        self.logger.debug(f'Skipping already processed: {item.name}')
                        continue
                    
                    # Skip action files (our own markdown files)
                    if item.name.startswith(('FILE_', 'ACTION_')) and item.get_extension() == 'md':
                        continue
                    
                    new_items.append(item)
                    self.logger.info(f'Found new file: {item.name} ({item.size} bytes)')
                    
                except Exception as e:
                    self.logger.error(f'Error processing file {filepath}: {e}')
            
        except Exception as e:
            self.logger.error(f'Error checking drop folder: {e}')
        
        return new_items
    
    def create_action_file(self, item: FileDropItem) -> Optional[Path]:
        """
        Create a markdown action file for the dropped file.
        
        Args:
            item: FileDropItem to create action file for
            
        Returns:
            Path to created action file, or None if failed
        """
        try:
            # Copy file to processing folder
            dest_path = self.process_folder / item.name
            shutil.copy2(item.filepath, dest_path)
            self.logger.info(f'Copied {item.name} to processing folder')
            
            # Generate suggested actions based on file type
            suggested_actions = self._get_suggested_actions(item)
            
            # Create action file content
            content = self._create_content(item, dest_path, suggested_actions)
            
            # Generate filename
            filename = self.generate_filename('FILE', f'{item.name}_{item.hash[:8]}')
            filepath = self.needs_action / filename
            
            # Write action file
            filepath.write_text(content, encoding='utf-8')
            
            # Mark as processed
            self.mark_processed(item.hash)
            
            # Remove original from drop folder (optional - comment out to keep)
            # item.filepath.unlink()
            
            return filepath
            
        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')
            return None
    
    def _get_suggested_actions(self, item: FileDropItem) -> List[str]:
        """
        Get suggested actions based on file type.
        
        Args:
            item: FileDropItem to analyze
            
        Returns:
            List of suggested action strings
        """
        category = item.get_category()
        ext = item.get_extension()
        
        actions = {
            'document': [
                '[ ] Read and summarize content',
                '[ ] Extract key information',
                '[ ] Categorize and file appropriately',
                '[ ] Respond if action required'
            ],
            'spreadsheet': [
                '[ ] Analyze data content',
                '[ ] Generate summary statistics',
                '[ ] Check for errors or inconsistencies',
                '[ ] Update dashboard if relevant'
            ],
            'image': [
                '[ ] Analyze image content',
                '[ ] Extract text if present (OCR)',
                '[ ] Describe for accessibility',
                '[ ] File appropriately'
            ],
            'data': [
                '[ ] Parse and validate structure',
                '[ ] Extract relevant information',
                '[ ] Update records if needed',
                '[ ] Generate report'
            ],
            'invoice': [
                '[ ] Extract vendor information',
                '[ ] Extract amount and due date',
                '[ ] Categorize expense',
                '[ ] Schedule payment if approved'
            ],
            'other': [
                '[ ] Review file content',
                '[ ] Determine required action',
                '[ ] Process or delegate as needed',
                '[ ] File appropriately'
            ]
        }
        
        # Special handling for invoices
        if 'invoice' in item.name.lower() or 'receipt' in item.name.lower():
            return actions.get('invoice', actions['other'])
        
        return actions.get(category, actions['other'])
    
    def _create_content(self, item: FileDropItem, dest_path: Path, 
                       suggested_actions: List[str]) -> str:
        """
        Create the markdown content for the action file.
        
        Args:
            item: FileDropItem being processed
            dest_path: Path to copied file in processing folder
            suggested_actions: List of suggested action checkboxes
            
        Returns:
            Complete markdown content string
        """
        frontmatter = self.create_frontmatter(
            type='file_drop',
            original_name=item.name,
            file_size=item.size,
            file_hash=item.hash,
            file_category=item.get_category(),
            file_extension=item.get_extension(),
            processing_path=str(dest_path.relative_to(self.vault_path))
        )
        
        actions_text = '\n'.join(suggested_actions)
        
        content = f'''{frontmatter}

# File Dropped for Processing

## File Information

| Property | Value |
|----------|-------|
| Original Name | {item.name} |
| Size | {self._format_size(item.size)} |
| Type | {item.get_category()} ({item.get_extension()}) |
| Dropped At | {datetime.fromtimestamp(item.created).isoformat()} |
| Hash | `{item.hash}` |

## Processing Path

`{dest_path.relative_to(self.vault_path)}`

## Suggested Actions

{actions_text}

## Notes

*Add any additional context or instructions here*

---

*Action file created by Filesystem Watcher*
'''
        return content
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'


def main():
    """Main entry point for the filesystem watcher."""
    parser = argparse.ArgumentParser(
        description='File System Watcher for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python filesystem_watcher.py
  python filesystem_watcher.py --vault-path "C:/Users/USER/ObsidianVault"
  python filesystem_watcher.py --interval 60
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
        '--drop-folder',
        type=str,
        default='Inbox',
        help='Name of drop folder (default: Inbox)'
    )
    
    parser.add_argument(
        '--process-folder',
        type=str,
        default='Processing',
        help='Name of processing folder (default: Processing)'
    )
    
    args = parser.parse_args()
    
    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        # Default: parent directory of scripts folder
        vault_path = str(Path(__file__).parent.parent)
    
    # Create and run watcher
    watcher = FilesystemWatcher(
        vault_path=vault_path,
        check_interval=args.interval,
        drop_folder=args.drop_folder,
        process_folder=args.process_folder
    )
    
    print(f'''
╔══════════════════════════════════════════════════════════╗
║           File System Watcher Started                     ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: {vault_path[:55]}{"..." if len(vault_path) > 55 else ""}
║  Drop Folder: {args.drop_folder}
║  Check Interval: {args.interval}s
║                                                            ║
║  Drop files into: {watcher.drop_folder}
║  Action files created in: {watcher.needs_action}
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
''')
    
    watcher.run()


if __name__ == '__main__':
    main()
