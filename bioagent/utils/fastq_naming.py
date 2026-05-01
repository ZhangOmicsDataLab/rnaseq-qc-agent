from pathlib import Path
from typing import Dict, List, Tuple


FASTQ_EXTENSIONS = (
    ".fastq.gz",
    ".fq.gz",
    ".fastq",
    ".fq",
)


def is_fastq_file(path: Path) -> bool:
    return path.name.endswith(FASTQ_EXTENSIONS)


def strip_fastq_extension(filename: str) -> str:
    for ext in FASTQ_EXTENSIONS:
        if filename.endswith(ext):
            return filename[: -len(ext)]
    return filename


def infer_sample_and_read(filename: str) -> Tuple[str, str | None]:
    """
    Infer sample name and read direction from common FASTQ naming schemes.

    Supported examples:
    sample1_R1.fastq.gz
    sample1_R2.fastq.gz
    sample1_1.fastq.gz
    sample1_2.fastq.gz
    sample1.R1.fastq.gz
    sample1.R2.fastq.gz
    sample1_R1_001.fastq.gz
    sample1_R2_001.fastq.gz
    """

    stem = strip_fastq_extension(filename)

    patterns = [
        ("_R1_001", "R1"),
        ("_R2_001", "R2"),
        ("_R1", "R1"),
        ("_R2", "R2"),
        (".R1", "R1"),
        (".R2", "R2"),
        ("_1", "R1"),
        ("_2", "R2"),
    ]

    for pattern, read in patterns:
        if pattern in stem:
            sample = stem.replace(pattern, "")
            return sample, read

    return stem, None


def build_sample_table(fastq_files: List[str]) -> Tuple[Dict[str, Dict[str, str]], List[str], List[str]]:
    samples: Dict[str, Dict[str, str]] = {}
    unpaired_files: List[str] = []
    warnings: List[str] = []

    for file_path in fastq_files:
        path = Path(file_path)
        sample_name, read = infer_sample_and_read(path.name)

        if read is None:
            unpaired_files.append(str(path))
            continue

        if sample_name not in samples:
            samples[sample_name] = {}

        if read in samples[sample_name]:
            warnings.append(
                f"Duplicate {read} file detected for sample '{sample_name}': {path.name}"
            )

        samples[sample_name][read] = str(path)

    for sample_name, reads in samples.items():
        if "R1" not in reads:
            warnings.append(f"Sample '{sample_name}' has R2 but no R1.")
        if "R2" not in reads:
            warnings.append(f"Sample '{sample_name}' has R1 but no R2.")

    return samples, unpaired_files, warnings


def infer_layout_from_samples(
    samples: Dict[str, Dict[str, str]],
    unpaired_files: List[str],
) -> str:
    paired = [s for s, reads in samples.items() if "R1" in reads and "R2" in reads]
    incomplete = [s for s, reads in samples.items() if not ("R1" in reads and "R2" in reads)]

    if paired and not incomplete and not unpaired_files:
        return "paired-end"

    if paired and (incomplete or unpaired_files):
        return "mixed_or_incomplete_paired-end"

    if unpaired_files and not paired:
        return "single-end_or_unknown"

    return "unknown"

