import json
from pathlib import Path

from bioagent.state import RNASeqQCState


def build_json_summary(state: RNASeqQCState) -> dict:
    return {
        "input": {
            "input_dir": state["input_dir"],
            "output_dir": state["output_dir"],
            "fastq_file_count": len(state.get("fastq_files", [])),
            "sample_count": len(state.get("samples", {})),
            "layout": state.get("layout", "unknown"),
        },
        "samples": state.get("samples", {}),
        "unpaired_files": state.get("unpaired_files", []),
        "run_plan": state.get("run_plan", []),
        "software_versions": state.get("software_versions", {}),
        "completed_steps": state.get("completed_steps", []),
        "warnings": state.get("warnings", []),
        "errors": state.get("errors", []),
        "qc_interpretation": state.get("qc_interpretation", []),
        "llm_interpretation": state.get("llm_interpretation", ""),
        "qc_summary": state.get("qc_summary", {}),
        "llm_settings": state.get("config", {}).get("llm", {}),
        "outputs": {
            "markdown_report": state.get("report_path", ""),
            "json_report": state.get("json_report_path", ""),
            "multiqc_report": str(Path(state["output_dir"]) / "multiqc" / "multiqc_report.html"),
        },
    }


def write_json_summary(state: RNASeqQCState) -> str:
    report_dir = Path(state["output_dir"]) / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "rnaseq_qc_agent_summary.json"
    summary = build_json_summary(state)

    with json_path.open("w") as handle:
        json.dump(summary, handle, indent=2)

    return str(json_path)


