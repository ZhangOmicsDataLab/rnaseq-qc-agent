from pathlib import Path

from bioagent.state import RNASeqQCState
from bioagent.reports.markdown import build_markdown_report
from bioagent.reports.json_report import write_json_summary


def write_report(state: RNASeqQCState) -> RNASeqQCState:
    report_dir = Path(state["output_dir"]) / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "rnaseq_qc_agent_report.md"
    report_text = build_markdown_report(state)
    report_path.write_text(report_text)

    config = state.get("config", {})
    write_json = config.get("report", {}).get("write_json_summary", True)

    json_report_path = state.get("json_report_path", "")

    if write_json:
        temp_state = {
            **state,
            "report_path": str(report_path),
        }
        json_report_path = write_json_summary(temp_state)

    return {
        **state,
        "report_path": str(report_path),
        "json_report_path": json_report_path,
        "completed_steps": state.get("completed_steps", []) + ["write_report"],
    }

