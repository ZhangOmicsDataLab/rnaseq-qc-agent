from pathlib import Path

import streamlit as st

from bioagent.graph import build_graph
from bioagent.utils.config import load_config


st.set_page_config(
    page_title="RNA-seq QC Agent",
    layout="wide",
)


st.title("RNA-seq QC Agent")

st.write(
    "A local LangGraph-based RNA-seq QC assistant using FastQC, MultiQC, "
    "and optional LLM interpretation through Ollama or OpenAI."
)


with st.sidebar:
    st.header("Run settings")

    input_dir = st.text_input(
        "Input FASTQ directory",
        value="demo/fastq",
        help="Folder containing FASTQ/FASTQ.gz files. Use a local folder path, not file upload.",
    )

    output_dir = st.text_input(
        "Output directory",
        value="results/streamlit_run",
        help="Folder where FastQC, MultiQC, Markdown report, and JSON summary will be written.",
    )

    config_path = st.text_input(
        "Config file",
        value="config.yaml",
        help="Path to the YAML configuration file.",
    )

    st.header("LLM settings")

    llm_enabled = st.checkbox(
        "Enable LLM interpretation",
        value=False,
        help="If disabled, the agent will only use rule-based QC interpretation.",
    )

    llm_provider = st.selectbox(
        "LLM provider",
        options=["ollama", "openai"],
        index=0,
        help="Use Ollama for local models or OpenAI for ChatGPT/API models.",
    )

    ollama_model = st.text_input(
        "Ollama model",
        value="llama3.2:1b",
        help="Local Ollama model. You have confirmed llama3.2:1b works.",
    )

    openai_model = st.text_input(
        "OpenAI model",
        value="gpt-5.2",
        help="OpenAI model name. Requires OPENAI_API_KEY and API credit.",
    )

    run_button = st.button("Run QC agent")


def make_initial_state(
    input_dir: str,
    output_dir: str,
    config_path: str,
    llm_enabled: bool,
    llm_provider: str,
    openai_model: str,
    ollama_model: str,
) -> dict:
    """
    Build the initial LangGraph state for the Streamlit app.

    This mirrors the CLI app.py initial state, but disables terminal approval
    because Streamlit is already an interactive interface.
    """

    config = load_config(config_path)

    # In Streamlit, avoid terminal input approval.
    config.setdefault("run", {})
    config["run"]["require_approval"] = False

    # Override LLM settings from the GUI.
    config.setdefault("llm", {})
    config["llm"]["enabled"] = llm_enabled
    config["llm"]["provider"] = llm_provider

    config["llm"].setdefault("ollama", {})
    config["llm"]["ollama"]["model"] = ollama_model
    config["llm"]["ollama"].setdefault("temperature", 0.1)
    config["llm"]["ollama"].setdefault("max_input_rows", 100)
    config["llm"]["ollama"].setdefault("max_input_chars", 6000)

    config["llm"].setdefault("openai", {})
    config["llm"]["openai"]["model"] = openai_model
    config["llm"]["openai"].setdefault("temperature", 0.1)
    config["llm"]["openai"].setdefault("max_input_rows", 200)
    config["llm"]["openai"].setdefault("max_input_chars", 12000)

    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "config": config,

        "fastq_files": [],
        "sample_count": 0,
        "layout": "unknown",

        "samples": {},
        "unpaired_files": [],

        "run_plan": [],
        "approved": False,

        "software_versions": {},

        "completed_steps": [],
        "errors": [],
        "warnings": [],

        "command_results": {},
        "qc_summary": {},
        "qc_interpretation": [],
        "llm_interpretation": "",

        "report_path": "",
        "json_report_path": "",
    }


def render_download_button(path: Path, label: str, mime: str) -> None:
    """
    Render a Streamlit download button if the file exists.
    """

    if path.exists() and path.is_file():
        st.download_button(
            label=label,
            data=path.read_text(),
            file_name=path.name,
            mime=mime,
        )
    else:
        st.warning(f"File not found: {path}")


def render_sample_table(samples: dict) -> None:
    """
    Display detected paired-end samples as a table.
    """

    if not samples:
        st.write("No paired-end samples detected.")
        return

    sample_rows = []

    for sample, reads in sorted(samples.items()):
        sample_rows.append(
            {
                "sample": sample,
                "R1": Path(reads.get("R1", "")).name if reads.get("R1") else "",
                "R2": Path(reads.get("R2", "")).name if reads.get("R2") else "",
                "status": "paired" if reads.get("R1") and reads.get("R2") else "incomplete",
            }
        )

    st.dataframe(sample_rows, use_container_width=True)


def render_run_result(result: dict) -> None:
    """
    Render all result sections after the LangGraph workflow finishes.
    """

    st.header("Run summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("FASTQ files", len(result.get("fastq_files", [])))
    col2.metric("Samples", len(result.get("samples", {})))
    col3.metric("Layout", result.get("layout", "unknown"))

    st.subheader("LLM settings")

    llm_config = result.get("config", {}).get("llm", {})
    provider = llm_config.get("provider", "none")
    enabled = llm_config.get("enabled", False)
    provider_config = llm_config.get(provider, {})
    model = provider_config.get("model", "not specified")

    st.write(f"Enabled: `{enabled}`")
    st.write(f"Provider: `{provider}`")
    st.write(f"Model: `{model}`")

    st.subheader("Completed steps")
    completed_steps = result.get("completed_steps", [])

    if completed_steps:
        for step in completed_steps:
            st.write(f"- {step}")
    else:
        st.write("No completed steps recorded.")

    warnings = result.get("warnings", [])
    errors = result.get("errors", [])

    if warnings:
        st.subheader("Warnings")
        for warning in warnings:
            st.warning(warning)

    if errors:
        st.subheader("Errors")
        for error in errors:
            st.error(error)

    st.subheader("Detected samples")
    render_sample_table(result.get("samples", {}))

    unpaired_files = result.get("unpaired_files", [])

    if unpaired_files:
        st.subheader("Unpaired or unclassified FASTQ files")
        for file in unpaired_files:
            st.write(f"- `{file}`")

    st.subheader("Rule-based QC interpretation")

    interpretation = result.get("qc_interpretation", [])

    if interpretation:
        for item in interpretation:
            st.write(f"- {item}")
    else:
        st.write("No rule-based QC interpretation generated.")

    st.subheader("LLM-assisted interpretation")

    llm_text = result.get("llm_interpretation", "")

    if llm_text:
        st.markdown(llm_text)
    else:
        if enabled:
            st.write(
                "LLM interpretation was enabled, but no output was generated. "
                "Check warnings/errors above."
            )
        else:
            st.write(
                "LLM interpretation was disabled. "
                "The report uses rule-based QC interpretation only."
            )

    st.subheader("Output files")

    output_dir = Path(result.get("output_dir", ""))
    report_path = Path(result.get("report_path", ""))
    json_path = Path(result.get("json_report_path", ""))
    multiqc_report = output_dir / "multiqc" / "multiqc_report.html"

    st.write(f"Markdown report: `{report_path}`")
    st.write(f"JSON summary: `{json_path}`")
    st.write(f"MultiQC report: `{multiqc_report}`")

    col_a, col_b = st.columns(2)

    with col_a:
        if report_path.exists():
            render_download_button(
                path=report_path,
                label="Download Markdown report",
                mime="text/markdown",
            )

    with col_b:
        if json_path.exists():
            render_download_button(
                path=json_path,
                label="Download JSON summary",
                mime="application/json",
            )

    if multiqc_report.exists():
        st.info(
            "MultiQC report was created. Open it from the path above in your browser or file manager."
        )
    else:
        st.warning("MultiQC report was not found.")


if run_button:
    st.info("Running RNA-seq QC agent...")

    try:
        graph = build_graph()

        initial_state = make_initial_state(
            input_dir=input_dir,
            output_dir=output_dir,
            config_path=config_path,
            llm_enabled=llm_enabled,
            llm_provider=llm_provider,
            openai_model=openai_model,
            ollama_model=ollama_model,
        )

        with st.spinner("Running FastQC, MultiQC, parsing, and report generation..."):
            result = graph.invoke(initial_state)

        st.session_state["last_result"] = result

        st.success("RNA-seq QC agent finished.")

    except Exception as e:
        st.error(f"RNA-seq QC agent failed: {e}")
        st.exception(e)


if "last_result" in st.session_state:
    render_run_result(st.session_state["last_result"])
