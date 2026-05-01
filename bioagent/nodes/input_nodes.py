from pathlib import Path

from bioagent.state import RNASeqQCState
from bioagent.utils.fastq_naming import (
    is_fastq_file,
    build_sample_table,
    infer_layout_from_samples,
)


def validate_input_dir(state: RNASeqQCState) -> RNASeqQCState:
    input_dir = Path(state["input_dir"])
    output_dir = Path(state["output_dir"])

    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))

    if not input_dir.exists():
        errors.append(f"Input directory does not exist: {input_dir}")

    elif not input_dir.is_dir():
        errors.append(f"Input path is not a directory: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    fastq_files = []

    if input_dir.exists() and input_dir.is_dir():
        for path in sorted(input_dir.iterdir()):
            if is_fastq_file(path):
                fastq_files.append(str(path))

    if not fastq_files:
        errors.append(f"No FASTQ files found in: {input_dir}")

    samples, unpaired_files, sample_warnings = build_sample_table(fastq_files)
    warnings.extend(sample_warnings)

    if unpaired_files:
        warnings.append(
            f"{len(unpaired_files)} FASTQ file(s) could not be assigned to R1/R2 pairs."
        )

    layout = infer_layout_from_samples(samples, unpaired_files)

    return {
        **state,
        "fastq_files": fastq_files,
        "sample_count": len(samples) if samples else len(fastq_files),
        "layout": layout,
        "samples": samples,
        "unpaired_files": unpaired_files,
        "errors": errors,
        "warnings": warnings,
        "completed_steps": state.get("completed_steps", []) + ["validate_input_dir"],
    }
