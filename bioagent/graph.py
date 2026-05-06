from langgraph.graph import StateGraph, START, END

from bioagent.state import RNASeqQCState
from bioagent.nodes.input_nodes import validate_input_dir
from bioagent.nodes.planning_nodes import (
    prepare_run_plan,
    request_cli_approval,
    should_continue_after_approval,
)
from bioagent.nodes.qc_nodes import (
    should_continue_after_validation,
    run_fastqc,
    run_multiqc,
)
from bioagent.nodes.version_nodes import record_versions
from bioagent.nodes.parsing_nodes import (
    parse_fastqc_summaries,
    parse_multiqc_data,
    interpret_qc_summary,
)

from bioagent.nodes.llm_nodes import optional_llm_interpretation
from bioagent.nodes.report_nodes import write_report


def build_graph():
    builder = StateGraph(RNASeqQCState)

    builder.add_node("validate_input_dir", validate_input_dir)
    builder.add_node("prepare_run_plan", prepare_run_plan)
    builder.add_node("request_cli_approval", request_cli_approval)
    builder.add_node("record_versions", record_versions)
    builder.add_node("run_fastqc", run_fastqc)
    builder.add_node("run_multiqc", run_multiqc)
    builder.add_node("parse_fastqc_summaries", parse_fastqc_summaries)
    builder.add_node("parse_multiqc_data", parse_multiqc_data)
    builder.add_node("interpret_qc_summary", interpret_qc_summary)
    builder.add_node("optional_llm_interpretation", optional_llm_interpretation)
    builder.add_node("write_report", write_report)

    builder.add_edge(START, "validate_input_dir")

    builder.add_conditional_edges(
        "validate_input_dir",
        should_continue_after_validation,
        {
            "prepare_run_plan": "prepare_run_plan",
            "write_report": "write_report",
        },
    )

    builder.add_edge("prepare_run_plan", "request_cli_approval")

    builder.add_conditional_edges(
        "request_cli_approval",
        should_continue_after_approval,
        {
            "record_versions": "record_versions",
            "write_report": "write_report",
        },
    )

    builder.add_edge("record_versions", "run_fastqc")
    builder.add_edge("run_fastqc", "run_multiqc")
    builder.add_edge("run_multiqc", "parse_fastqc_summaries")
    builder.add_edge("parse_fastqc_summaries", "parse_multiqc_data")
    builder.add_edge("parse_multiqc_data", "interpret_qc_summary")
    builder.add_edge("interpret_qc_summary", "optional_llm_interpretation")
    builder.add_edge("optional_llm_interpretation", "write_report")
    builder.add_edge("write_report", END)
    return builder.compile()
