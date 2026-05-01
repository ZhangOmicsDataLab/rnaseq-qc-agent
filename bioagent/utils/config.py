from pathlib import Path
from typing import Any, Dict

import yaml


DEFAULT_CONFIG = {
    "run": {
        "threads": 2,
        "require_approval": False,
        "overwrite": True,
    },
    "tools": {
        "fastqc": {
            "enabled": True,
            "extra_args": [],
        },
        "multiqc": {
            "enabled": True,
            "force": True,
            "data_format": "tsv",
        },
    },
    "report": {
        "include_command_stderr": True,
        "include_software_versions": True,
        "include_sample_table": True,
        "include_qc_interpretation": True,
    },
}


def load_config(config_path: str | None) -> Dict[str, Any]:
    if config_path is None:
        return DEFAULT_CONFIG

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r") as handle:
        user_config = yaml.safe_load(handle) or {}

    return merge_dicts(DEFAULT_CONFIG, user_config)


def merge_dicts(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(default)

    for key, value in user.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value

    return merged

