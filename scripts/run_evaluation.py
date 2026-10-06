"""
Automated Evaluation and Benchmarking Suite.
Runs 20 diverse test cases across all categories:
- Factual single source
- Factual multi-document
- Personal student data tools
- Privacy protection & cross-student refusals
- Multi-step eligibility calculations
- Document version conflicts & supersession
- Missing information & clarification requests
- Prompt injection defenses
- Out-of-scope queries

Calculates all mandatory metrics:
1. Answer correctness
2. Citation accuracy
3. Abstention accuracy
4. Tool-result correctness
5. Retrieval hit rate
6. Average Latency, P50, and P95
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from tabulate import tabulate
from app.agent.graph import run_agent

QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "evaluation" / "questions.json"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_benchmark() -> Tuple[Dict[str, float], pd.DataFrame]:
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results_records = []
    latencies = []

    correct_answers = 0
    correct_citations = 0
    factual_tests_count = 0
    abstention_tests_count = 0
    correct_abstentions = 0
    tool_tests_count = 0
    correct_tool_results = 0
    retrieval_tests_count = 0
    retrieval_hits = 0

    print(f"\n================================================================================")
    print(f"RUNNING BENCHMARK EVALUATION SUITE ({len(test_cases)} TEST CASES)")
    print(f"================================================================================\n")

    for tc in test_cases:
        tc_id = tc["id"]
        cat = tc["category"]
        q = tc["question"]
        stu_id = tc["student_id"]
        exp_type = tc["expected_answer_type"]
        exp_doc = tc.get("expected_doc_id")
        exp_keywords = tc.get("expected_keywords", [])
        exp_val = tc.get("expected_value")

        start = time.time()
        agent_res = run_agent(question=q, student_id=stu_id)
        latency = round((time.time() - start) * 1000.0, 2)
        latencies.append(latency)

        actual_type = agent_res.get("answer_type")
        actual_ans = agent_res.get("answer", "")
        citations = agent_res.get("citations", [])
        tools = agent_res.get("tools_invoked", [])
        retrieved = agent_res.get("retrieved_chunks", [])

        # 1. Answer Type & Keyword Correctness
        type_match = actual_type == exp_type
        kw_match = all(kw.lower() in actual_ans.lower() for kw in exp_keywords) if exp_keywords else True
        ans_pass = type_match and kw_match
        if ans_pass:
            correct_answers += 1

        # 2. Citation Accuracy (for factual queries)
        cit_pass = True
        if exp_doc:
            factual_tests_count += 1
            valid_docs = exp_doc if isinstance(exp_doc, list) else [exp_doc]
            cited_docs = {c.get("doc_id") for c in citations}
            cit_pass = any(vd in cited_docs for vd in valid_docs)
            if cit_pass:
                correct_citations += 1

        # 3. Abstention Accuracy
        if exp_type in ["refused", "not_found", "clarification_needed"]:
            abstention_tests_count += 1
            if actual_type == exp_type:
                correct_abstentions += 1

        # 4. Tool-Result Correctness
        if "tools" in cat or "eligibility" in cat:
            tool_tests_count += 1
            tool_pass = len(tools) > 0
            if exp_val is not None:
                tool_pass = tool_pass and (str(exp_val) in actual_ans)
            if tool_pass:
                correct_tool_results += 1

        # 5. Retrieval Hit Rate
        if exp_doc:
            retrieval_tests_count += 1
            valid_docs = exp_doc if isinstance(exp_doc, list) else [exp_doc]
            retrieved_docs = {c["metadata"].get("doc_id") for c in retrieved}
            if any(vd in retrieved_docs for vd in valid_docs):
                retrieval_hits += 1

        status = "PASSED" if ans_pass and cit_pass else "FAILED"

        results_records.append({
            "Test ID": tc_id,
            "Category": cat,
            "Question": q[:45] + "...",
            "Expected Type": exp_type,
            "Actual Type": actual_type,
            "Latency (ms)": latency,
            "Status": status
        })

    # Metric computations
    total_tests = len(test_cases)
    ans_correctness_pct = (correct_answers / total_tests) * 100.0
    cit_accuracy_pct = (correct_citations / factual_tests_count * 100.0) if factual_tests_count else 100.0
    abstention_accuracy_pct = (correct_abstentions / abstention_tests_count * 100.0) if abstention_tests_count else 100.0
    tool_correctness_pct = (correct_tool_results / tool_tests_count * 100.0) if tool_tests_count else 100.0
    retrieval_hit_rate_pct = (retrieval_hits / retrieval_tests_count * 100.0) if retrieval_tests_count else 100.0

    p50_latency = float(np.percentile(latencies, 50))
    p95_latency = float(np.percentile(latencies, 95))
    avg_latency = float(np.mean(latencies))

    metrics = {
        "total_tests": total_tests,
        "answer_correctness": ans_correctness_pct,
        "citation_accuracy": cit_accuracy_pct,
        "abstention_accuracy": abstention_accuracy_pct,
        "tool_correctness": tool_correctness_pct,
        "retrieval_hit_rate": retrieval_hit_rate_pct,
        "avg_latency_ms": avg_latency,
        "p50_latency_ms": p50_latency,
        "p95_latency_ms": p95_latency
    }

    df_results = pd.DataFrame(results_records)

    # Save to JSON
    summary_path = RESULTS_DIR / "evaluation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "metrics": metrics,
            "details": results_records
        }, f, indent=2)

    return metrics, df_results


def print_evaluation_report(metrics: Dict[str, float], df_results: pd.DataFrame):
    print("\n" + tabulate(df_results, headers="keys", tablefmt="fancy_grid", showindex=False))
    print("\n================================================================================")
    print("                      BENCHMARK EVALUATION SUMMARY                              ")
    print("================================================================================")
    print(f"Total Benchmark Tests     : {metrics['total_tests']}")
    print(f"Answer Correctness        : {metrics['answer_correctness']:.2f}%")
    print(f"Citation Accuracy         : {metrics['citation_accuracy']:.2f}%")
    print(f"Abstention Accuracy       : {metrics['abstention_accuracy']:.2f}%")
    print(f"Tool-Result Correctness   : {metrics['tool_correctness']:.2f}%")
    print(f"Retrieval Hit Rate        : {metrics['retrieval_hit_rate']:.2f}%")
    print(f"P50 Latency               : {metrics['p50_latency_ms']:.2f} ms")
    print(f"P95 Latency               : {metrics['p95_latency_ms']:.2f} ms")
    print(f"Average Latency           : {metrics['avg_latency_ms']:.2f} ms")
    print("================================================================================\n")


if __name__ == "__main__":
    metrics, df = run_benchmark()
    print_evaluation_report(metrics, df)
