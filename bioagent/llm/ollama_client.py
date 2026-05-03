import json
from typing import Any, Dict

import ollama


def summarise_qc_with_ollama(
    qc_payload: Dict[str, Any],
    model: str = "llama3.2:1b",
    temperature: float = 0.1,
    max_input_chars: int = 6000,
) -> str:
    """
    Use a local Ollama model to interpret RNA-seq QC evidence.

    Requirements:
    - Ollama CLI/server installed
    - Ollama server running
    - model pulled locally, e.g. `ollama pull llama3.2:1b`

    The model only receives structured QC evidence.
    It does not run commands.
    """

    system_prompt = """
You are a careful bioinformatics QC assistant.

Your task is to interpret RNA-seq QC results using only the evidence provided.

Rules:
- Do not invent results.
- Do not claim that a sample failed unless the evidence shows warnings or failures.
- Do not recommend arbitrary shell commands.
- Do not make biological conclusions from QC alone.
- Distinguish clear QC issues from possible concerns.
- If evidence is missing, say what is missing.

Structure your answer as:
1. Overall assessment
2. Main QC concerns
3. Sample-level issues if available
4. Recommended next steps
"""

    payload_text = json.dumps(qc_payload, indent=2)
    payload_text = payload_text[:max_input_chars]

    user_prompt = f"""
Please interpret the following RNA-seq QC summary.

QC summary JSON:
{payload_text}
"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        options={
            "temperature": temperature,
        },
    )

    return response["message"]["content"]

