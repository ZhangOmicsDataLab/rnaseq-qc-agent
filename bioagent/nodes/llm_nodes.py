from bioagent.state import RNASeqQCState
from bioagent.llm.openai_client import summarise_qc_with_openai
from bioagent.llm.ollama_client import summarise_qc_with_ollama


def optional_llm_interpretation(state: RNASeqQCState) -> RNASeqQCState:
    config = state.get("config", {})
    llm_config = config.get("llm", {})

    if not llm_config.get("enabled", False):
        return {
            **state,
            "llm_interpretation": "",
            "completed_steps": state.get("completed_steps", [])
            + ["optional_llm_interpretation_skipped"],
        }

    provider = llm_config.get("provider", "ollama")
    warnings = list(state.get("warnings", []))

    fastqc_rows = state.get("qc_summary", {}).get("fastqc_summary_rows", [])
    general_stats = state.get("qc_summary", {}).get("multiqc_general_stats", [])

    provider_config = llm_config.get(provider, {})

    model = provider_config.get(
        "model",
        "llama3.2:1b" if provider == "ollama" else "gpt-5.2",
    )

    temperature = float(provider_config.get("temperature", 0.1))
    max_input_rows = int(provider_config.get("max_input_rows", 100))
    max_input_chars = int(provider_config.get("max_input_chars", 6000))

    qc_payload = {
        "input": {
            "fastq_file_count": len(state.get("fastq_files", [])),
            "sample_count": len(state.get("samples", {})),
            "layout": state.get("layout", "unknown"),
        },
        "samples": state.get("samples", {}),
        "unpaired_files": state.get("unpaired_files", []),
        "software_versions": state.get("software_versions", {}),
        "rule_based_interpretation": state.get("qc_interpretation", []),
        "fastqc_summary_rows": fastqc_rows[:max_input_rows],
        "multiqc_general_stats": general_stats[:max_input_rows],
        "warnings": state.get("warnings", []),
        "errors": state.get("errors", []),
    }

    try:
        if provider == "ollama":
            llm_text = summarise_qc_with_ollama(
                qc_payload=qc_payload,
                model=model,
                temperature=temperature,
                max_input_chars=max_input_chars,
            )

        elif provider == "openai":
            llm_text = summarise_qc_with_openai(
                qc_payload=qc_payload,
                model=model,
                temperature=temperature,
                max_input_chars=max_input_chars,
            )

        else:
            llm_text = ""
            warnings.append(
                f"Unsupported LLM provider '{provider}'. Use 'ollama' or 'openai'."
            )

    except Exception as e:
        llm_text = ""
        warnings.append(f"{provider} LLM interpretation failed: {e}")

    return {
        **state,
        "warnings": warnings,
        "llm_interpretation": llm_text,
        "completed_steps": state.get("completed_steps", [])
        + [f"optional_llm_interpretation_{provider}"],
    }
