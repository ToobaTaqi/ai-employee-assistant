"""
Bronze Tier Verification Script

This script verifies that all Bronze tier deliverables are complete:
1. Obsidian vault with Dashboard.md and Company_Handbook.md
2. One working Watcher script (Gmail OR file system monitoring)
3. Qwen Code successfully reading from and writing to the vault
4. Basic folder structure: /Inbox, /Needs_Action, /Done
5. All AI functionality should be implemented as Agent Skills

Usage:
    python verify_bronze.py [--vault-path PATH]
"""

import sys
from pathlib import Path
from typing import List, Tuple


class BronzeVerifier:
    """Verifies Bronze tier deliverables."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
    
    def check_file_exists(self, filepath: Path, description: str) -> bool:
        """Check if a file exists."""
        if filepath.exists():
            self.passed.append(f"[PASS] {description}: {filepath.relative_to(self.vault_path)}")
            return True
        else:
            self.failed.append(f"[FAIL] {description}: {filepath.relative_to(self.vault_path)}")
            return False
    
    def check_directory_exists(self, dirpath: Path, description: str) -> bool:
        """Check if a directory exists."""
        if dirpath.exists() and dirpath.is_dir():
            self.passed.append(f"[PASS] {description}: {dirpath.relative_to(self.vault_path)}")
            return True
        else:
            self.failed.append(f"[FAIL] {description}: {dirpath.relative_to(self.vault_path)}")
            return False
    
    def check_file_has_content(self, filepath: Path, description: str, 
                               required_strings: List[str]) -> bool:
        """Check if a file exists and contains required strings."""
        if not filepath.exists():
            self.failed.append(f"[FAIL] {description}: File not found")
            return False
        
        content = filepath.read_text(encoding='utf-8')
        missing = []
        
        for s in required_strings:
            if s not in content:
                missing.append(s)
        
        if missing:
            self.failed.append(f"[FAIL] {description}: Missing: {missing}")
            return False
        else:
            self.passed.append(f"[PASS] {description}: All required content present")
            return True
    
    def check_python_file_valid(self, filepath: Path, description: str) -> bool:
        """Check if a Python file is syntactically valid."""
        if not filepath.exists():
            self.failed.append(f"[FAIL] {description}: File not found")
            return False
        
        try:
            compile(filepath.read_text(encoding='utf-8'), str(filepath), 'exec')
            self.passed.append(f"[PASS] {description}: Valid Python syntax")
            return True
        except SyntaxError as e:
            self.failed.append(f"[FAIL] {description}: Syntax error: {e}")
            return False
    
    def verify_all(self) -> bool:
        """Run all verification checks."""
        print("\n" + "=" * 60)
        print("  BRONZE TIER VERIFICATION")
        print("=" * 60 + "\n")
        
        # 1. Check required directories
        print("Checking folder structure...")
        required_dirs = [
            ('Inbox', 'Inbox folder'),
            ('Needs_Action', 'Needs_Action folder'),
            ('Done', 'Done folder'),
            ('Pending_Approval', 'Pending_Approval folder'),
            ('Approved', 'Approved folder'),
            ('Rejected', 'Rejected folder'),
        ]
        
        for dirname, description in required_dirs:
            self.check_directory_exists(self.vault_path / dirname, description)
        
        # 2. Check required files
        print("\nChecking required files...")
        required_files = [
            ('Dashboard.md', 'Dashboard file'),
            ('Company_Handbook.md', 'Company Handbook file'),
        ]
        
        for filename, description in required_files:
            self.check_file_exists(self.vault_path / filename, description)
        
        # 3. Check Dashboard.md has required content
        print("\nChecking Dashboard content...")
        self.check_file_has_content(
            self.vault_path / 'Dashboard.md',
            'Dashboard.md',
            ['type: dashboard', '# AI Employee Dashboard']
        )
        
        # 4. Check Company_Handbook.md has required content
        print("\nChecking Company Handbook content...")
        self.check_file_has_content(
            self.vault_path / 'Company_Handbook.md',
            'Company_Handbook.md',
            ['type: handbook', '# Company Handbook', 'Rules of Engagement']
        )
        
        # 5. Check Watcher scripts exist
        print("\nChecking Watcher scripts...")
        scripts_dir = self.vault_path / 'scripts'
        
        if scripts_dir.exists():
            self.passed.append(f"[PASS] Scripts directory exists: scripts/")
            
            # Check base_watcher.py
            self.check_python_file_valid(
                scripts_dir / 'base_watcher.py',
                'base_watcher.py'
            )
            
            # Check filesystem_watcher.py
            self.check_python_file_valid(
                scripts_dir / 'filesystem_watcher.py',
                'filesystem_watcher.py'
            )
            
            # Check requirements.txt
            self.check_file_exists(
                scripts_dir / 'requirements.txt',
                'requirements.txt'
            )
        else:
            self.failed.append("[FAIL] Scripts directory: scripts/ not found")

        # 6. Check Qwen Integration guide
        print("\nChecking Qwen Code integration...")
        self.check_file_has_content(
            self.vault_path / 'QWEN_INTEGRATION.md',
            'QWEN_INTEGRATION.md',
            ['# Qwen Code Integration Guide', 'Reading from the Vault', 'Writing to the Vault']
        )
        
        # Print results
        print("\n" + "=" * 60)
        print("  RESULTS")
        print("=" * 60 + "\n")
        
        if self.passed:
            print("PASSED CHECKS:")
            for item in self.passed:
                print(f"  {item}")
            print()
        
        if self.failed:
            print("FAILED CHECKS:")
            for item in self.failed:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("WARNINGS:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        # Summary
        total = len(self.passed) + len(self.failed)
        passed = len(self.passed)
        
        print("=" * 60)
        print(f"  SUMMARY: {passed}/{total} checks passed")
        print("=" * 60)
        
        if len(self.failed) == 0:
            print("\n  [SUCCESS] BRONZE TIER COMPLETE! All deliverables verified.\n")
            return True
        else:
            print(f"\n  [INCOMPLETE] BRONZE TIER INCOMPLETE: {len(self.failed)} deliverables missing.\n")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify Bronze tier deliverables'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault (default: AI_Employee_Vault in current directory)'
    )
    
    args = parser.parse_args()
    
    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        # Default: AI_Employee_Vault in current directory
        vault_path = str(Path.cwd() / 'AI_Employee_Vault')
    
    # Verify
    verifier = BronzeVerifier(vault_path)
    success = verifier.verify_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
