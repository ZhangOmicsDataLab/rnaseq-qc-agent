import json
from typing import Any, Dict

from openai import OpenAI


def summarise_qc_with_openai(
    qc_payload: Dict[str, Any],
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    max_input_chars: int = 12000,
) -> str:
    """
    Use OpenAI / ChatGPT to interpret RNA-seq QC evidence.

    This requires:
    - openai Python package
    - OPENAI_API_KEY environment variable
    - available OpenAI API credit

    The model only receives structured QC evidence.
    It does not run commands.
    """

    client = OpenAI()

    system_instructions = """
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

    user_input = f"""
Please interpret the following RNA-seq QC summary.

QC summary JSON:
{payload_text}
"""

    response = client.responses.create(
        model=model,
        instructions=system_instructions.strip(),
        input=user_input.strip(),
        temperature=temperature,
    )

    return response.output_text

