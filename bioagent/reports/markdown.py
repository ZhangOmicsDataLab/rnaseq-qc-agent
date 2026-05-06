from collections import Counter, defaultdict
from pathlib import Path

from bioagent.state import RNASeqQCState


def build_markdown_report(state: RNASeqQCState) -> str:
    fastqc_result = state.get("command_results", {}).get("fastqc", {})
    multiqc_result = state.get("command_results", {}).get("multiqc", {})

    output_dir = Path(state["output_dir"])
    fastqc_dir = output_dir / "fastqc"
    multiqc_report = output_dir / "multiqc" / "multiqc_report.html"

    lines = [
        "# RNA-seq QC Agent Report",
        "",
        "## 1. Input summary",
        "",
        f"- Input directory: `{state['input_dir']}`",
        f"- Output directory: `{state['output_dir']}`",
        f"- Number of FASTQ files: {len(state.get('fastq_files', []))}",
        f"- Number of detected samples: {len(state.get('samples', {}))}",
        f"- Inferred layout: `{state.get('layout', 'unknown')}`",
        "",
    ]

    add_sample_table(lines, state)
    add_run_plan(lines, state)
    add_software_versions(lines, state)
    add_llm_settings

    lines.extend([
        "## 5. Completed steps",
        "",
    ])

    for step in state.get("completed_steps", []):
        lines.append(f"- {step}")

    lines.extend([
        "",
        "## 6. Outputs",
        "",
        f"- FastQC directory: `{fastqc_dir}`",
        f"- MultiQC report: `{multiqc_report}`",
        "",
        "## 7. Command status",
        "",
        f"- FastQC success: `{fastqc_result.get('success')}`",
        f"- MultiQC success: `{multiqc_result.get('success')}`",
        "",
    ])

    add_qc_interpretation(lines, state)
    add_llm_interpretation(lines, state)
    add_fastqc_module_summary(lines, state)
    add_warnings(lines, state)
    add_errors(lines, state)
    add_failed_command_details(lines, state)

    return "\n".join(lines)


def add_sample_table(lines: list[str], state: RNASeqQCState) -> None:
    samples = state.get("samples", {})
    unpaired_files = state.get("unpaired_files", [])

    lines.extend([
        "## 2. Detected samples",
        "",
    ])

    if not samples and not unpaired_files:
        lines.extend([
            "No samples detected.",
            "",
        ])
        return

    if samples:
        lines.extend([
            "| Sample | R1 | R2 | Status |",
            "|---|---|---|---|",
        ])

        for sample, reads in sorted(samples.items()):
            r1 = Path(reads.get("R1", "")).name if reads.get("R1") else ""
            r2 = Path(reads.get("R2", "")).name if reads.get("R2") else ""

            if r1 and r2:
                status = "paired"
            else:
                status = "incomplete"

            lines.append(f"| {sample} | {r1} | {r2} | {status} |")

        lines.append("")

    if unpaired_files:
        lines.extend([
            "Unpaired or unclassified FASTQ files:",
            "",
        ])

        for file in unpaired_files:
            lines.append(f"- `{file}`")

        lines.append("")


def add_run_plan(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## 3. Run plan",
        "",
    ])

    for step in state.get("run_plan", []):
        lines.append(f"- {step}")

    lines.append("")


def add_software_versions(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## 4. Software versions",
        "",
    ])

    versions = state.get("software_versions", {})

    if not versions:
        lines.extend([
            "Software versions were not recorded.",
            "",
        ])
        return

    for tool, version in versions.items():
        lines.append(f"- {tool}: `{version}`")

    lines.append("")


def add_qc_interpretation(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## 8. QC interpretation",
        "",
    ])

    interpretation = state.get("qc_interpretation", [])

    if not interpretation:
        lines.append("No QC interpretation was generated.")
    else:
        for item in interpretation:
            lines.append(f"- {item}")

    lines.append("")


def add_fastqc_module_summary(lines: list[str], state: RNASeqQCState) -> None:
    rows = state.get("qc_summary", {}).get("fastqc_summary_rows", [])

    lines.extend([
        "## 9. FastQC module status summary",
        "",
    ])

    if not rows:
        lines.extend([
            "No FastQC summary rows were parsed.",
            "",
        ])
        return

    module_status_counts = defaultdict(Counter)

    for row in rows:
        module_status_counts[row["module"]][row["status"]] += 1

    lines.extend([
        "| Module | PASS | WARN | FAIL |",
        "|---|---:|---:|---:|",
    ])

    for module, counts in sorted(module_status_counts.items()):
        lines.append(
            f"| {module} | {counts.get('PASS', 0)} | {counts.get('WARN', 0)} | {counts.get('FAIL', 0)} |"
        )

    lines.append("")


def add_warnings(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## 10. Warnings",
        "",
    ])

    warnings = state.get("warnings", [])

    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")

    lines.append("")


def add_errors(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## 11. Errors",
        "",
    ])

    errors = state.get("errors", [])

    if errors:
        for error in errors:
            lines.append(f"- {error}")
    else:
        lines.append("- None")

    lines.append("")


def add_failed_command_details(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## 12. Failed command details",
        "",
    ])

    failed = False

    for tool_name, tool_result in state.get("command_results", {}).items():
        if not tool_result.get("success", True):
            failed = True
            lines.extend([
                f"### {tool_name}",
                "",
                "Command:",
                "",
                "```bash",
                tool_result.get("command", ""),
                "```",
                "",
                "stderr:",
                "",
                "```text",
                tool_result.get("stderr", ""),
                "```",
                "",
            ])

    if not failed:
        lines.append("No failed commands recorded.")
        lines.append("")

def add_llm_settings(lines: list[str], state: RNASeqQCState) -> None:
    llm_config = state.get("config", {}).get("llm", {})
    enabled = llm_config.get("enabled", False)
    provider = llm_config.get("provider", "none")

    provider_config = llm_config.get(provider, {})
    model = provider_config.get("model", "not specified")

    lines.extend([
        "## LLM settings",
        "",
        f"- Enabled: `{enabled}`",
        f"- Provider: `{provider}`",
        f"- Model: `{model}`",
        "",
    ])


def add_llm_interpretation(lines: list[str], state: RNASeqQCState) -> None:
    lines.extend([
        "## LLM-assisted interpretation",
        "",
    ])

    llm_config = state.get("config", {}).get("llm", {})
    llm_enabled = llm_config.get("enabled", False)
    provider = llm_config.get("provider", "none")

    llm_text = state.get("llm_interpretation", "")

    if llm_text:
        lines.append(llm_text)
    elif not llm_enabled:
        lines.append(
            "LLM interpretation was disabled. The report uses rule-based QC interpretation only."
        )
    else:
        lines.append(
            f"LLM interpretation was enabled with provider `{provider}`, "
            "but no LLM output was generated. Check the warnings/errors section."
        )

    lines.append("")

