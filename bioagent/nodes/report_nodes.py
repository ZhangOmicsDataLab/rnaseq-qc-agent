from pathlib import Path
from bioagent.state import RNASeqQCState
from bioagent.reports.markdown import build_markdown_report


def write_report(state: RNASeqQCState) -> RNASeqQCState:
    report_dir = Path(state["output_dir"]) / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "rnaseq_qc_agent_report.md"
    report_text = build_markdown_report(state)

    report_path.write_text(report_text)

    return {
        **state,
        "report_path": str(report_path),
        "completed_steps": state.get("completed_steps", []) + ["write_report"],
    }

