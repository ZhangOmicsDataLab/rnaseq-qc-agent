import subprocess
from pathlib import Path
from typing import Dict, Any, List


def run_command(
    command: List[str],
    workdir: str | Path = ".",
    timeout: int | None = None,
) -> Dict[str, Any]:
    """
    Run an approved command safely.

    Important:
    - command is a list, not a string
    - shell=False is used implicitly
    - stdout and stderr are captured
    """

    try:
        result = subprocess.run(
            command,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

        return {
            "command": " ".join(command),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    except Exception as e:
        return {
            "command": " ".join(command),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }
