from bioagent.state import RNASeqQCState


def prepare_run_plan(state: RNASeqQCState) -> RNASeqQCState:
    plan = [
        "Record software versions",
        "Run FastQC on detected FASTQ files",
        "Run MultiQC on FastQC output",
        "Parse QC summary files",
        "Generate Markdown report",
    ]

    return {
        **state,
        "run_plan": plan,
        "completed_steps": state.get("completed_steps", []) + ["prepare_run_plan"],
    }


def request_cli_approval(state: RNASeqQCState) -> RNASeqQCState:
    config = state.get("config", {})
    require_approval = config.get("run", {}).get("require_approval", False)

    if not require_approval:
        return {
            **state,
            "approved": True,
            "completed_steps": state.get("completed_steps", []) + ["request_cli_approval"],
        }

    print("\nRNA-seq QC run plan")
    print("===================\n")
    print(f"Input directory: {state['input_dir']}")
    print(f"Output directory: {state['output_dir']}")
    print(f"Detected layout: {state.get('layout', 'unknown')}")
    print(f"Number of FASTQ files: {len(state.get('fastq_files', []))}")
    print(f"Number of detected samples: {len(state.get('samples', {}))}")

    print("\nPlanned steps:")
    for i, step in enumerate(state.get("run_plan", []), start=1):
        print(f"{i}. {step}")

    if state.get("warnings"):
        print("\nWarnings:")
        for warning in state["warnings"]:
            print(f"- {warning}")

    answer = input("\nProceed with analysis? [y/N]: ").strip().lower()

    approved = answer == "y"

    errors = list(state.get("errors", []))
    if not approved:
        errors.append("User did not approve the run. Analysis stopped before execution.")

    return {
        **state,
        "approved": approved,
        "errors": errors,
        "completed_steps": state.get("completed_steps", []) + ["request_cli_approval"],
    }


def should_continue_after_approval(state: RNASeqQCState) -> str:
    if state.get("errors"):
        return "write_report"

    if not state.get("approved", False):
        return "write_report"

    return "record_versions"

