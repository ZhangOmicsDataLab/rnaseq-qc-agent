import argparse
from pathlib import Path

from rich import print

from bioagent.graph import build_graph
from bioagent.utils.config import load_config


def main():
    parser = argparse.ArgumentParser(
        description="Local LangGraph-based RNA-seq QC agent"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing FASTQ/FASTQ.gz files",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory",
    )

    parser.add_argument(
        "--config",
        required=False,
        default="config.yaml",
        help="YAML configuration file",
    )

    args = parser.parse_args()

    config = load_config(args.config)

    graph = build_graph()

    initial_state = {
        "input_dir": args.input,
        "output_dir": args.output,
        "config": config,

        "fastq_files": [],
        "sample_count": 0,
        "layout": "unknown",

        "samples": {},
        "unpaired_files": [],

        "run_plan": [],
        "approved": False,

        "software_versions": {},

        "completed_steps": [],
        "errors": [],
        "warnings": [],

        "command_results": {},
        "qc_summary": {},
        "qc_interpretation": [],

        "report_path": "",
    }

    result = graph.invoke(initial_state)

    print("\n[bold green]RNA-seq QC agent finished.[/bold green]")
    print(f"FASTQ files detected: {len(result['fastq_files'])}")
    print(f"Samples detected: {len(result['samples'])}")
    print(f"Layout: {result['layout']}")
    print(f"Report: {result['report_path']}")

    multiqc_report = Path(args.output) / "multiqc" / "multiqc_report.html"

    if multiqc_report.exists():
        print(f"MultiQC report: {multiqc_report}")

    if result["warnings"]:
        print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result["warnings"]:
            print(f"- {warning}")

    if result["errors"]:
        print("\n[bold red]Errors:[/bold red]")
        for error in result["errors"]:
            print(f"- {error}")

    failed_commands = [
        (tool_name, tool_result)
        for tool_name, tool_result in result.get("command_results", {}).items()
        if not tool_result.get("success", True)
    ]

    if failed_commands:
        print("\n[bold yellow]Failed command stderr:[/bold yellow]")
        for tool_name, tool_result in failed_commands:
            print(f"\n[bold]{tool_name} stderr:[/bold]")
            print(tool_result.get("stderr", ""))


if __name__ == "__main__":
    main()

