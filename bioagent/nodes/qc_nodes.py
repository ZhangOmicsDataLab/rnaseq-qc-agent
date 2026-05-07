from pathlib import Path

from bioagent.utils.shell import run_command


def should_continue_after_validation(state):
    """
    Decide whether to continue after input validation.
    """

    errors = state.get("errors", [])

    if errors:
        return "write_report"

    return "prepare_run_plan"


def run_fastqc(state):
    """
    Run FastQC on all detected FASTQ files.
    """

    config = state.get("config", {})
    tools_config = config.get("tools", {})
    fastqc_config = tools_config.get("fastqc", {})
    run_config = config.get("run", {})

    command_results = dict(state.get("command_results", {}))
    completed_steps = list(state.get("completed_steps", []))
    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))

    if not fastqc_config.get("enabled", True):
        warnings.append("FastQC is disabled in config.yaml.")
        completed_steps.append("run_fastqc_skipped")

        return {
            **state,
            "warnings": warnings,
            "completed_steps": completed_steps,
            "command_results": command_results,
        }

    fastq_files = state.get("fastq_files", [])

    if not fastq_files:
        errors.append("No FASTQ files available for FastQC.")

        return {
            **state,
            "errors": errors,
            "warnings": warnings,
            "completed_steps": completed_steps,
            "command_results": command_results,
        }

    output_dir = Path(state["output_dir"])
    fastqc_output_dir = output_dir / "fastqc"
    fastqc_output_dir.mkdir(parents=True, exist_ok=True)

    threads = run_config.get("threads", 2)
    fastqc_command = fastqc_config.get("command", "fastqc")
    extra_args = fastqc_config.get("extra_args", [])

    cmd = [
        fastqc_command,
        "-o",
        str(fastqc_output_dir),
        "-t",
        str(threads),
    ]

    cmd.extend(extra_args)
    cmd.extend([str(path) for path in fastq_files])

    result = run_command(cmd)
    command_results["fastqc"] = result

    if result.get("returncode") != 0:
        errors.append("FastQC failed. See command_results['fastqc']['stderr'].")
    else:
        completed_steps.append("run_fastqc")

    return {
        **state,
        "errors": errors,
        "warnings": warnings,
        "completed_steps": completed_steps,
        "command_results": command_results,
    }


def run_multiqc(state):
    """
    Run MultiQC on the FastQC output directory.
    """

    config = state.get("config", {})
    tools_config = config.get("tools", {})
    multiqc_config = tools_config.get("multiqc", {})

    command_results = dict(state.get("command_results", {}))
    completed_steps = list(state.get("completed_steps", []))
    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))

    if not multiqc_config.get("enabled", True):
        warnings.append("MultiQC is disabled in config.yaml.")
        completed_steps.append("run_multiqc_skipped")

        return {
            **state,
            "warnings": warnings,
            "completed_steps": completed_steps,
            "command_results": command_results,
        }

    output_dir = Path(state["output_dir"])
    fastqc_output_dir = output_dir / "fastqc"
    multiqc_output_dir = output_dir / "multiqc"
    multiqc_output_dir.mkdir(parents=True, exist_ok=True)

    if not fastqc_output_dir.exists():
        errors.append(f"FastQC output directory does not exist: {fastqc_output_dir}")

        return {
            **state,
            "errors": errors,
            "warnings": warnings,
            "completed_steps": completed_steps,
            "command_results": command_results,
        }

    multiqc_command = multiqc_config.get("command", "multiqc")
    force = multiqc_config.get("force", True)

    cmd = [
        multiqc_command,
        str(fastqc_output_dir),
        "-o",
        str(multiqc_output_dir),
    ]

    if force:
        cmd.append("--force")

    result = run_command(cmd)
    command_results["multiqc"] = result

    if result.get("returncode") != 0:
        errors.append("MultiQC failed. See command_results['multiqc']['stderr'].")
    else:
        completed_steps.append("run_multiqc")

    return {
        **state,
        "errors": errors,
        "warnings": warnings,
        "completed_steps": completed_steps,
        "command_results": command_results,
    }