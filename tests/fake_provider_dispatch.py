"""Only local fixtures, for browser coverage of checks and workflow retries."""
import runpy
from pathlib import Path
import sys
name='fake_generation_check.py' if sys.argv[1]=='providers' else 'fake_ai_process.py'
runpy.run_path(str(Path(__file__).with_name(name)),run_name='__main__')
