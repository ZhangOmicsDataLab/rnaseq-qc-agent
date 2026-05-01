from pathlib import Path
from zipfile import ZipFile

from bioagent.state import RNASeqQCState


def parse_fastqc_summaries(state: RNASeqQCState) -> RNASeqQCState:
    fastqc_dir = Path(state["output_dir"]) / "fastqc"

    summary_rows = []
    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))

    if not fastqc_dir.exists():
        errors.append(f"FastQC output directory not found: {fastqc_dir}")
        return {
            **state,
            "errors": errors,
            "warnings": warnings,
            "completed_steps": state.get("completed_steps", []) + ["parse_fastqc_summaries"],
        }

    zip_files = sorted(fastqc_dir.glob("*_fastqc.zip"))

    if not zip_files:
        warnings.append(f"No FastQC zip files found in: {fastqc_dir}")

    for zip_path in zip_files:
        try:
            rows = parse_one_fastqc_zip(zip_path)
            summary_rows.extend(rows)

        except Exception as e:
            warnings.append(f"Could not parse {zip_path.name}: {e}")

    qc_summary = {
        **state.get("qc_summary", {}),
        "fastqc_summary_rows": summary_rows,
        "fastqc_zip_count": len(zip_files),
    }

    return {
        **state,
        "qc_summary": qc_summary,
        "errors": errors,
        "warnings": warnings,
        "completed_steps": state.get("completed_steps", []) + ["parse_fastqc_summaries"],
    }


def parse_one_fastqc_zip(zip_path: Path) -> list[dict]:
    rows = []

    with ZipFile(zip_path, "r") as zip_file:
        summary_names = [
            name for name in zip_file.namelist()
            if name.endswith("/summary.txt")
        ]

        if not summary_names:
            raise ValueError("summary.txt not found inside FastQC zip")

        summary_name = summary_names[0]

        with zip_file.open(summary_name) as handle:
            for raw_line in handle:
                line = raw_line.decode("utf-8").strip()

                if not line:
                    continue

                parts = line.split("\t")

                if len(parts) != 3:
                    continue

                status, module, filename = parts

                rows.append(
                    {
                        "fastqc_zip": zip_path.name,
                        "filename": filename,
                        "module": module,
                        "status": status,
                    }
                )

    return rows


def interpret_qc_summary(state: RNASeqQCState) -> RNASeqQCState:
    rows = state.get("qc_summary", {}).get("fastqc_summary_rows", [])

    interpretation = []

    if not rows:
        interpretation.append("No FastQC summary rows were available for interpretation.")

    fail_rows = [row for row in rows if row["status"] == "FAIL"]
    warn_rows = [row for row in rows if row["status"] == "WARN"]

    if not fail_rows and not warn_rows and rows:
        interpretation.append("All parsed FastQC modules passed.")

    if fail_rows:
        interpretation.append(
            f"{len(fail_rows)} FastQC module checks failed across all files."
        )

    if warn_rows:
        interpretation.append(
            f"{len(warn_rows)} FastQC module checks produced warnings across all files."
        )

    module_counts = count_status_by_module(rows)

    for module, counts in sorted(module_counts.items()):
        fail_count = counts.get("FAIL", 0)
        warn_count = counts.get("WARN", 0)

        if fail_count > 0:
            interpretation.append(
                f"Module '{module}' failed in {fail_count} file(s)."
            )
        elif warn_count > 0:
            interpretation.append(
                f"Module '{module}' generated warnings in {warn_count} file(s)."
            )

    return {
        **state,
        "qc_interpretation": interpretation,
        "completed_steps": state.get("completed_steps", []) + ["interpret_qc_summary"],
    }


def count_status_by_module(rows: list[dict]) -> dict:
    counts = {}

    for row in rows:
        module = row["module"]
        status = row["status"]

        if module not in counts:
            counts[module] = {}

        counts[module][status] = counts[module].get(status, 0) + 1

    return counts
