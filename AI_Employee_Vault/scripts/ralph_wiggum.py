"""
Ralph Wiggum Persistence Loop for AI Employee

Implements the "Ralph Wiggum" pattern - a stop hook that keeps Qwen Code
iterating until multi-step tasks are complete.

How it works:
1. Orchestrator creates a state file with the task prompt
2. Qwen works on the task
3. Qwen tries to exit
4. Stop hook checks: Is task file in /Done?
5. YES → Allow exit (complete)
6. NO → Block exit, re-inject prompt (loop continues)

This pattern solves the "lazy agent" problem by ensuring tasks complete
even if they require multiple iterations.

Usage:
    python ralph_wiggum.py --prompt "Process all files in Needs_Action"
    python ralph_wiggum.py --state-file PATH.md
    python ralph_wiggum.py --check-completion PATH.md
"""

import os
import sys
import json
import time
import argparse
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class RalphWiggumLoop:
    """
    Implements the Ralph Wiggum persistence loop pattern.

    Keeps Qwen Code working until a task is demonstrably complete.
    """

    # Completion markers
    COMPLETION_MARKERS = [
        '<task_complete>',
        'TASK_COMPLETE',
        '[COMPLETE]',
        '✓ Task completed',
        'Task finished successfully'
    ]

    # Maximum iterations before forcing stop
    DEFAULT_MAX_ITERATIONS = 10

    def __init__(self, vault_path: str, max_iterations: int = None):
        self.vault_path = Path(vault_path)
        self.state_path = self.vault_path / 'Processing' / 'ralph_state.json'
        self.logs_path = self.vault_path / 'logs'
        self.max_iterations = max_iterations or self.DEFAULT_MAX_ITERATIONS

        # Ensure directories exist
        self.logs_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'Processing').mkdir(parents=True, exist_ok=True)

        # State
        self.current_prompt = None
        self.iteration_count = 0
        self.start_time = None
        self.task_file = None

        # Setup logging
        self._setup_logging()

        self.logger.info(f'Ralph Wiggum Loop initialized')
        self.logger.info(f'Max iterations: {self.max_iterations}')

    def _setup_logging(self):
        """Configure logging."""
        import logging

        log_file = self.logs_path / f'ralph_wiggum_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('RalphWiggum')

    def create_state(self, prompt: str, task_file: str = None) -> Path:
        """
        Create a state file for the task.

        Args:
            prompt: The task prompt for Qwen
            task_file: Optional reference to task file being processed

        Returns:
            Path to state file
        """
        state = {
            'prompt': prompt,
            'task_file': task_file,
            'created_at': datetime.now().isoformat(),
            'iteration': 0,
            'status': 'pending',
            'last_output': None,
            'completion_detected': False
        }

        self.state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
        self.logger.info(f'Created state file: {self.state_path}')

        return self.state_path

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load current state."""
        if not self.state_path.exists():
            return None

        try:
            return json.loads(self.state_path.read_text(encoding='utf-8'))
        except Exception as e:
            self.logger.error(f'Error loading state: {e}')
            return None

    def save_state(self, state: Dict[str, Any]):
        """Save current state."""
        self.state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')

    def check_completion_file_based(self) -> bool:
        """
        Check if task is complete using file movement pattern.

        Task is complete if:
        - Task file moved from Needs_Action to Done
        - Or approval file moved to Done
        """
        state = self.load_state()
        if not state:
            return False

        task_file = state.get('task_file')
        if not task_file:
            # No specific file to track - check if Needs_Action is empty
            needs_action = self.vault_path / 'Needs_Action'
            if needs_action.exists():
                pending_files = [f for f in needs_action.iterdir() if f.suffix == '.md']
                return len(pending_files) == 0
            return True

        # Check if file moved to Done
        task_path = Path(task_file)
        if task_path.exists():
            # File still in original location - not complete
            return False

        # Check if file exists in Done
        done_folder = self.vault_path / 'Done'
        if done_folder.exists():
            # Look for file with similar name
            original_name = task_path.name
            for f in done_folder.iterdir():
                if original_name.split('.')[0] in f.name:
                    self.logger.info(f'Task file found in Done: {f.name}')
                    return True

        # Check if file was rejected
        rejected_folder = self.vault_path / 'Rejected'
        if rejected_folder.exists():
            for f in rejected_folder.iterdir():
                if original_name.split('.')[0] in f.name:
                    self.logger.info(f'Task file found in Rejected: {f.name}')
                    return True  # Consider rejected as "processed"

        return False

    def check_completion_output_based(self, output: str) -> bool:
        """
        Check if task is complete based on Qwen's output.

        Looks for completion markers in the output.
        """
        output_upper = output.upper()

        for marker in self.COMPLETION_MARKERS:
            if marker.upper() in output_upper:
                self.logger.info(f'Completion marker detected: {marker}')
                return True

        return False

    def should_continue(self, qwen_output: str = None) -> bool:
        """
        Determine if Ralph loop should continue.

        Returns True if task is NOT complete and should continue.
        """
        state = self.load_state()
        if not state:
            self.logger.warning('No state file found - cannot determine completion')
            return False

        # Check iteration limit
        if state.get('iteration', 0) >= self.max_iterations:
            self.logger.warning(f'Max iterations ({self.max_iterations}) reached')
            return False

        # Check file-based completion
        if self.check_completion_file_based():
            self.logger.info('Task complete (file-based check)')
            state['completion_detected'] = True
            state['status'] = 'completed'
            self.save_state(state)
            return False

        # Check output-based completion
        if qwen_output and self.check_completion_output_based(qwen_output):
            self.logger.info('Task complete (output-based check)')
            state['completion_detected'] = True
            state['status'] = 'completed'
            state['last_output'] = qwen_output[:1000]  # Store snippet
            self.save_state(state)
            return False

        # Continue loop
        state['iteration'] = state.get('iteration', 0) + 1
        state['last_output'] = qwen_output[:1000] if qwen_output else None
        state['status'] = 'in_progress'
        self.save_state(state)

        return True

    def run_qwen_with_prompt(self, prompt: str, timeout: int = 300) -> str:
        """
        Run Qwen Code with the given prompt and capture output.

        Args:
            prompt: The prompt to send to Qwen
            timeout: Timeout in seconds

        Returns:
            Qwen's output
        """
        self.logger.info(f'Running Qwen with prompt: {prompt[:100]}...')

        try:
            # Try different Qwen executables based on platform
            import platform
            import shutil
            
            # First, try to find qwen in PATH
            qwen_path = shutil.which('qwen')
            qwen_cmd = shutil.which('qwen.cmd')
            
            if qwen_path:
                qwen_executable = qwen_path
            elif qwen_cmd:
                qwen_executable = qwen_cmd
            else:
                # Fallback to default names
                if platform.system() == 'Windows':
                    qwen_executable = 'qwen.cmd'
                else:
                    qwen_executable = 'qwen'
            
            self.logger.info(f'Using Qwen executable: {qwen_executable}')

            # Run Qwen Code
            process = subprocess.run(
                [qwen_executable, prompt],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.vault_path)
            )

            output = process.stdout + process.stderr
            self.logger.info(f'Qwen completed. Output length: {len(output)}')
            return output

        except subprocess.TimeoutExpired:
            self.logger.error('Qwen timed out')
            return 'ERROR: Task timed out'
        except FileNotFoundError as e:
            self.logger.error(f'Qwen Code not found: {e}')
            self.logger.error('Please ensure Qwen Code is installed and in PATH')
            self.logger.error('Try running: qwen --version')
            return 'ERROR: Qwen Code not installed. Run: qwen --version to verify'
        except Exception as e:
            self.logger.error(f'Error running Qwen: {e}')
            return f'ERROR: {str(e)}'

    def run_loop(self, prompt: str, task_file: str = None) -> Dict[str, Any]:
        """
        Run the full Ralph Wiggum loop.

        Args:
            prompt: Initial prompt for Qwen
            task_file: Optional task file being processed

        Returns:
            Result dictionary with status and output
        """
        self.logger.info('Starting Ralph Wiggum loop')
        self.start_time = datetime.now()

        # Create initial state
        self.create_state(prompt, task_file)

        result = {
            'prompt': prompt,
            'task_file': task_file,
            'started_at': self.start_time.isoformat(),
            'iterations': 0,
            'status': 'running',
            'outputs': []
        }

        current_prompt = prompt

        while True:
            # Run Qwen
            output = self.run_qwen_with_prompt(current_prompt)
            result['outputs'].append({
                'iteration': result['iterations'],
                'output': output[:2000],  # Store snippet
                'timestamp': datetime.now().isoformat()
            })
            result['iterations'] += 1

            # Check if should continue
            if not self.should_continue(output):
                result['status'] = 'completed'
                break

            # Prepare next iteration prompt
            current_prompt = f"""
Continue working on the previous task. The task is not yet complete.

Previous prompt was:
{prompt}

Please continue where you left off. Remember to move completed files to /Done
when finished.
"""

        # Finalize
        result['completed_at'] = datetime.now().isoformat()
        result['duration_seconds'] = (datetime.now() - self.start_time).total_seconds()

        # Save result
        result_path = self.logs_path / f'ralph_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')

        self.logger.info(f'Ralph Wiggum loop completed. Iterations: {result["iterations"]}')

        return result

    def check_task_completion(self, task_file: str) -> bool:
        """
        Check if a specific task file has been processed.

        Args:
            task_file: Path to the task file to check

        Returns:
            True if task is complete
        """
        task_path = Path(task_file)

        # If file doesn't exist in original location, check Done/Rejected
        if not task_path.exists():
            done_folder = self.vault_path / 'Done'
            rejected_folder = self.vault_path / 'Rejected'

            for folder in [done_folder, rejected_folder]:
                if folder.exists():
                    for f in folder.iterdir():
                        if task_path.name.split('.')[0] in f.name:
                            return True

        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Persistence Loop',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python ralph_wiggum.py --prompt "Process all files in Needs_Action"
  python ralph_wiggum.py --state-file PATH.md
  python ralph_wiggum.py --check-completion PATH.md
  python ralph_wiggum.py --run-loop "Your task prompt here"

The Ralph Wiggum pattern keeps Qwen Code working until tasks are complete.
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        help='Task prompt for Qwen'
    )

    parser.add_argument(
        '--state-file',
        type=str,
        help='Path to state file to check'
    )

    parser.add_argument(
        '--check-completion',
        type=str,
        help='Check if a task file is complete'
    )

    parser.add_argument(
        '--run-loop',
        type=str,
        help='Run full Ralph loop with given prompt'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum iterations before stopping'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create loop instance
    loop = RalphWiggumLoop(vault_path, max_iterations=args.max_iterations)

    if args.check_completion:
        # Check completion
        is_complete = loop.check_task_completion(args.check_completion)
        if is_complete:
            print('✓ Task is COMPLETE')
            sys.exit(0)
        else:
            print('✗ Task is NOT complete')
            sys.exit(1)

    elif args.state_file:
        # Check state file
        state = loop.load_state()
        if state:
            print(f'State: {state.get("status", "unknown")}')
            print(f'Iteration: {state.get("iteration", 0)}')
            print(f'Completion: {state.get("completion_detected", False)}')
        else:
            print('No state file found')

    elif args.run_loop:
        # Run full loop
        print(f'Starting Ralph Wiggum loop...')
        print(f'Task: {args.run_loop[:100]}...')
        print(f'Max iterations: {args.max_iterations}')

        result = loop.run_loop(args.run_loop)

        print(f'\nLoop completed!')
        print(f'  Iterations: {result["iterations"]}')
        print(f'  Duration: {result["duration_seconds"]:.1f}s')
        print(f'  Status: {result["status"]}')

    elif args.prompt:
        # Simple prompt mode
        print(f'Creating state for prompt...')
        state_path = loop.create_state(args.prompt)
        print(f'State file created: {state_path}')
        print(f'\nTo run the loop, use: python ralph_wiggum.py --run-loop "{args.prompt}"')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
