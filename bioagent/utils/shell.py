import subprocess
from typing import List, Dict, Any


def run_command(cmd: List[str]) -> Dict[str, Any]:
    """
    Run a shell command safely using subprocess.

    cmd should be a list, for example:
    ["fastqc", "-o", "output", "sample.fastq.gz"]

    This is important on Windows because paths may contain spaces.
    """

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        return {
            "command": " ".join(str(x) for x in cmd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    except Exception as e:
        return {
            "command": " ".join(str(x) for x in cmd),
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
        }