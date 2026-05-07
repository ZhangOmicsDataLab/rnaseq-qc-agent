from bioagent.utils.shell import run_command


def record_versions(state):
    config = state.get("config", {})
    tools_config = config.get("tools", {})

    software_versions = {}
    command_results = dict(state.get("command_results", {}))
    warnings = list(state.get("warnings", []))
    completed_steps = list(state.get("completed_steps", []))

    fastqc_config = tools_config.get("fastqc", {})
    multiqc_config = tools_config.get("multiqc", {})

    # FastQC version
    if fastqc_config.get("enabled", True):
        configured_fastqc_version = fastqc_config.get("version")

        if configured_fastqc_version:
            software_versions["fastqc"] = configured_fastqc_version
            command_results["fastqc_version_command"] = {
                "command": "configured in config.yaml",
                "returncode": 0,
                "stdout": configured_fastqc_version,
                "stderr": "",
            }
        else:
            fastqc_command = fastqc_config.get("command", "fastqc")
            result = run_command([fastqc_command, "--version"])
            command_results["fastqc_version_command"] = result

            if result.get("returncode") == 0:
                software_versions["fastqc"] = result.get("stdout", "").strip()
            else:
                software_versions["fastqc"] = "unknown"
                warnings.append(
                    "Could not determine FastQC version. "
                    "If using Windows run_fastqc.bat, set tools.fastqc.version in config.yaml."
                )
    else:
        software_versions["fastqc"] = "disabled"

    # MultiQC version
    if multiqc_config.get("enabled", True):
        multiqc_command = multiqc_config.get("command", "multiqc")
        result = run_command([multiqc_command, "--version"])
        command_results["multiqc_version_command"] = result

        if result.get("returncode") == 0:
            software_versions["multiqc"] = result.get("stdout", "").strip()
        else:
            software_versions["multiqc"] = "unknown"
            warnings.append("Could not determine MultiQC version.")
    else:
        software_versions["multiqc"] = "disabled"

    completed_steps.append("record_versions")

    return {
        **state,
        "software_versions": software_versions,
        "command_results": command_results,
        "warnings": warnings,
        "completed_steps": completed_steps,
    }