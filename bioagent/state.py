from typing import TypedDict, List, Dict, Any


class RNASeqQCState(TypedDict):
    input_dir: str
    output_dir: str
    config: Dict[str, Any]

    fastq_files: List[str]
    sample_count: int
    layout: str

    samples: Dict[str, Dict[str, str]]
    unpaired_files: List[str]

    run_plan: List[str]
    approved: bool

    software_versions: Dict[str, str]

    completed_steps: List[str]
    errors: List[str]
    warnings: List[str]

    command_results: Dict[str, Any]
    qc_summary: Dict[str, Any]
    qc_interpretation: List[str]
    llm_interpretation: str

    report_path: str
    json_report_path: str
