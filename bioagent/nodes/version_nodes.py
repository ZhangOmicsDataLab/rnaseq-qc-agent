import platform
import sys

from bioagent.state import RNASeqQCState
from bioagent.tools.shell import run_command


def record_versions(state: RNASeqQCState) -> RNASeqQCState:
    versions = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
    }

    fastqc_result = run_command(["fastqc", "--version"])
    multiqc_result = run_command(["multiqc", "--version"])

    versions["fastqc"] = extract_version_output(fastqc_result)
    versions["multiqc"] = extract_version_output(multiqc_result)

    output_result = {
        "fastqc_version_command": fastqc_result,
        "multiqc_version_command": multiqc_result,
    }

    return {
        **state,
        "software_versions": versions,
        "command_results": {
            **state.get("command_results", {}),
            **output_result,
        },
        "completed_steps": state.get("completed_steps", []) + ["record_versions"],
    }


def extract_version_output(result: dict) -> str:
    stdout = result.get("stdout", "").strip()
    stderr = result.get("stderr", "").strip()

    if stdout:
        return stdout

    if stderr:
        return stderr

    return "unknown"

