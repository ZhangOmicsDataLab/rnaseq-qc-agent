from pathlib import Path

from bioagent.state import RNASeqQCState
from bioagent.tools.shell import run_command


def should_continue_after_validation(state: RNASeqQCState) -> str:
    if state.get("errors"):
        return "write_report"

    return "prepare_run_plan"


def run_fastqc(state: RNASeqQCState) -> RNASeqQCState:
    config = state.get("config", {})
    threads = str(config.get("run", {}).get("threads", 2))

    output_dir = Path(state["output_dir"]) / "fastqc"
    output_dir.mkdir(parents=True, exist_ok=True)

    extra_args = config.get("tools", {}).get("fastqc", {}).get("extra_args", [])

    command = [
        "fastqc",
        "-o",
        str(output_dir),
        "--threads",
        threads,
    ] + extra_args + state["fastq_files"]

    result = run_command(command)

    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))

    if not result["success"]:
        errors.append("FastQC failed. See command_results['fastqc']['stderr'].")

    return {
        **state,
        "errors": errors,
        "warnings": warnings,
        "command_results": {
            **state.get("command_results", {}),
            "fastqc": result,
        },
        "completed_steps": state.get("completed_steps", []) + ["run_fastqc"],
    }


def run_multiqc(state: RNASeqQCState) -> RNASeqQCState:
    config = state.get("config", {})

    fastqc_dir = Path(state["output_dir"]) / "fastqc"
    multiqc_dir = Path(state["output_dir"]) / "multiqc"
    multiqc_dir.mkdir(parents=True, exist_ok=True)

    force = config.get("tools", {}).get("multiqc", {}).get("force", True)
    data_format = config.get("tools", {}).get("multiqc", {}).get("data_format", "tsv")

    command = [
        "multiqc",
        str(fastqc_dir),
        "-o",
        str(multiqc_dir),
    ]

    if force:
        command.append("--force")

    if data_format:
        command.extend(["--data-format", data_format])

    result = run_command(command)

    errors = list(state.get("errors", []))

    if not result["success"]:
        errors.append("MultiQC failed. See command_results['multiqc']['stderr'].")

    return {
        **state,
        "errors": errors,
        "command_results": {
            **state.get("command_results", {}),
            "multiqc": result,
        },
        "completed_steps": state.get("completed_steps", []) + ["run_multiqc"],
    }

