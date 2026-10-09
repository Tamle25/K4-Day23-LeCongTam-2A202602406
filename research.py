"""research.py - STUDENT IMPLEMENTS.  The main script.   Guide: GUIDE.md, part 3.

Usage:  python research.py "survey about world model"
Result: reports/<slug>.md   reports/<slug>.sources.json   reports/<slug>.meta.json
"""
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

from agents import FINALIZER_PATH, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH, WORKDIR, build_lead_agent
from model import _env, make_model
from sandbox import download, open_sandbox, upload

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"
VALIDATOR_SOURCE = ROOT / "check_citations.py"
FINALIZER_SOURCE = ROOT / "finalize_citations.py"  # provided: uploaded next to your validator


def slugify(topic):
    """Turn a topic into a safe file name: lower case, runs of non-word characters become one "-", max 60 chars,
    never empty (fall back to "topic"). The topic is user input: "../../x" must not escape reports/."""
    text = str(topic or "").strip().lower()
    slug = re.sub(r"[^\w]+", "-", text).strip("-")
    slug = slug[:60].rstrip("-")
    return slug if slug else "topic"


def build_prompt(topic):
    """The user message sent to the lead agent."""
    return (
        f"Conduct a comprehensive, deeply researched literature survey on: '{topic}'.\n\n"
        "Strict workflow:\n"
        "1. Plan with `write_todos` and decompose the topic into at least 3-4 independent sub-questions.\n"
        "2. Delegate each sub-question to `researcher` subagents using `task` with full context and target note paths.\n"
        f"3. CRITICAL FOR RUBRIC: Ensure your research covers AT LEAST 3 distinct source families among: 'arxiv', 'hf-search' (or 'hf-daily'), and 'web'. You MUST explicitly assign subagents to search Hugging Face papers via `hf_search_papers` and `hf_daily_papers` in addition to arXiv and web search. Aggregate all findings into {SOURCES_PATH}.\n"
        f"4. Write the synthesis report to {REPORT_PATH} following REPORT_TEMPLATE.md (DO NOT write `## References`). The text must cite sources from at least 3 families.\n"
        f"5. Run `python3 {FINALIZER_PATH}` with `execute` to generate `## References` and sync citations.\n"
        f"6. Run `python3 {VALIDATOR_PATH}` with `execute` and resolve any issues until it outputs OK.\n"
        "7. Spot-check 2-3 key claims with `citation-checker`.\n"
    )


def summarize(messages, elapsed, model_name):
    """Return {"model", "elapsed_s", "subagent_calls", "tool_calls": {name: count}, "tokens": {"input", "output"}}."""
    tool_counts = Counter()
    input_tokens = 0
    output_tokens = 0

    for msg in messages:
        t_calls = getattr(msg, "tool_calls", None)
        if t_calls is None and isinstance(msg, dict):
            t_calls = msg.get("tool_calls")
        if t_calls:
            for tc in t_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    tool_counts[name] += 1

        usage = getattr(msg, "usage_metadata", None)
        if usage is None and isinstance(msg, dict):
            usage = msg.get("usage_metadata")
        if usage and isinstance(usage, dict):
            input_tokens += int(usage.get("input_tokens", 0) or 0)
            output_tokens += int(usage.get("output_tokens", 0) or 0)

    subagent_calls = tool_counts.get("task", 0)

    return {
        "model": str(model_name),
        "elapsed_s": round(float(elapsed), 1),
        "subagent_calls": subagent_calls,
        "tool_calls": dict(tool_counts),
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
        },
    }


def save_outputs(backend, topic, messages, elapsed, model_name, reports_dir=REPORTS):
    """Download the report from the sandbox and write the three files into reports_dir. Return the report path."""
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic)

    files = download(backend, [REPORT_PATH, SOURCES_PATH])
    report_bytes = files.get(REPORT_PATH)
    sources_bytes = files.get(SOURCES_PATH)

    if not report_bytes or not report_bytes.strip():
        raise RuntimeError(f"Report is missing or empty at {REPORT_PATH}")
    if not sources_bytes or not sources_bytes.strip():
        raise RuntimeError(f"sources.json is missing or empty at {SOURCES_PATH}")

    try:
        sources_data = json.loads(sources_bytes.decode("utf-8"))
        if not isinstance(sources_data, list):
            raise ValueError("sources.json must be a JSON array")
    except Exception as exc:
        raise RuntimeError(f"sources.json is invalid JSON: {exc}")

    distinct_families = sorted(list({s.get("source") for s in sources_data if isinstance(s, dict) and s.get("source")}))

    meta = {
        "topic": topic,
        **summarize(messages, elapsed, model_name),
        "n_sources": len(sources_data),
        "source_families": distinct_families,
    }

    report_file = reports_path / f"{slug}.md"
    sources_file = reports_path / f"{slug}.sources.json"
    meta_file = reports_path / f"{slug}.meta.json"

    sources_file.write_text(json.dumps(sources_data, ensure_ascii=False, indent=2), encoding="utf-8")
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    report_file.write_text(report_bytes.decode("utf-8"), encoding="utf-8")

    return report_file


def main(topic):
    """Return the process exit code (0 ok, 1 failed run, 2 no topic)."""
    topic_clean = (topic or "").strip()
    if not topic_clean:
        print("Usage: python research.py <topic>", file=sys.stderr)
        return 2

    model = make_model()
    model_name = _env("LAB_MODEL", "OPENAI_DEPLOYMENT_MODEL") or getattr(model, "model_name", None) or "unknown"
    start = time.monotonic()

    try:
        with open_sandbox() as backend:
            backend.execute(f"mkdir -p {WORKDIR}/research/notes {WORKDIR}/report")
            upload(
                backend,
                {
                    VALIDATOR_PATH: VALIDATOR_SOURCE.read_bytes(),
                    FINALIZER_PATH: FINALIZER_SOURCE.read_bytes(),
                },
            )
            agent = build_lead_agent(backend, model)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": build_prompt(topic_clean)}]},
                config={"recursion_limit": 1000},
            )
            # Run finalizer in sandbox to guarantee citation consistency before download (RUBRIC 78)
            fin_res = backend.execute(f"python3 {FINALIZER_PATH} {REPORT_PATH} {SOURCES_PATH}")
            print(f"[sandbox] Finalizer: {fin_res.output.strip()}")
            val_res = backend.execute(f"python3 {VALIDATOR_PATH} {REPORT_PATH} {SOURCES_PATH}")
            print(f"[sandbox] Validator: {val_res.output.strip()}")
            elapsed = time.monotonic() - start
            messages = result.get("messages", []) if isinstance(result, dict) else []
            saved_report = save_outputs(backend, topic_clean, messages, elapsed, model_name)
            print(f"Report saved to: {saved_report}")
            return 0
    except RuntimeError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(" ".join(sys.argv[1:])))
