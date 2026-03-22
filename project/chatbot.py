from __future__ import annotations

import argparse
import logging
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"
REQUEST_TIMEOUT_SECONDS = 90

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
EVAL_DIR = BASE_DIR / "eval"
ZERO_SHOT_TEMPLATE_PATH = PROMPTS_DIR / "zero_shot_template.txt"
ONE_SHOT_TEMPLATE_PATH = PROMPTS_DIR / "one_shot_template.txt"
DEFAULT_RESULTS_PATH = EVAL_DIR / "results.md"

DEFAULT_QUERIES = [
    "How do I track my order?",
    "My payment failed but money was deducted.",
    "How do I return a product?",
    "My discount code is not working.",
    "I received the wrong item in my package.",
    "My order is delayed and I need it urgently.",
    "How can I cancel my order before it ships?",
    "I want to exchange my shirt for a different size.",
    "The product arrived damaged. What should I do?",
    "Can I change my delivery address after placing the order?",
    "I was charged twice for the same order.",
    "I have not received my refund yet.",
    "Do you offer international shipping?",
    "How do I update my phone number on my account?",
    "The website says delivered, but I did not receive my package.",
    "Can I place an order without creating an account?",
    "How long does standard shipping usually take?",
    "I forgot to apply the coupon before paying. Can it still be added?",
    "Why was my order cancelled automatically?",
    "How do I know if a product is back in stock?",
]

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "but",
    "can",
    "did",
    "do",
    "for",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "not",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "what",
    "why",
    "you",
    "your",
}

EMPATHY_PHRASES = (
    "sorry",
    "understand",
    "happy to help",
    "glad to help",
)

ACTION_PHRASES = (
    "please",
    "check",
    "share",
    "contact",
    "return",
    "refund",
    "replace",
    "track",
    "confirm",
    "update",
    "cancel",
)


@dataclass
class ResponseScores:
    relevance: int
    coherence: int
    helpfulness: int

    @property
    def average(self) -> float:
        return round((self.relevance + self.coherence + self.helpfulness) / 3, 2)


@dataclass
class QueryResult:
    query: str
    zero_shot_response: str
    one_shot_response: str
    zero_shot_scores: ResponseScores
    one_shot_scores: ResponseScores


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare zero-shot and one-shot prompting for an offline Ollama chatbot."
    )
    parser.add_argument(
        "--queries-file",
        type=Path,
        help="Optional text file containing one customer query per line.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="Markdown file path for the generated evaluation results.",
    )
    return parser.parse_args()


def load_template(path: Path) -> str:
    try:
        template = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Prompt template not found: {path}") from exc
    except OSError as exc:
        raise OSError(f"Unable to read prompt template: {path}") from exc

    if "{query}" not in template:
        raise ValueError(f"Prompt template must contain '{{query}}': {path}")

    return template


def load_queries(queries_file: Path | None = None) -> list[str]:
    if queries_file is None:
        return DEFAULT_QUERIES

    try:
        lines = queries_file.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Queries file not found: {queries_file}") from exc
    except OSError as exc:
        raise OSError(f"Unable to read queries file: {queries_file}") from exc

    queries = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    if not queries:
        raise ValueError(f"No usable queries found in file: {queries_file}")

    return queries


def build_prompt(template: str, query: str) -> str:
    return template.replace("{query}", query.strip())


def query_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Failed to reach Ollama. Make sure Ollama is running locally and the "
            f"'{MODEL_NAME}' model is available. Original error: {exc}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("Ollama returned a non-JSON response.") from exc

    model_response = data.get("response", "").strip()
    if not model_response:
        raise RuntimeError("Ollama returned an empty response.")

    return model_response


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def clamp_score(value: int) -> int:
    return max(1, min(5, value))


def score_response(query: str, response: str) -> ResponseScores:
    if response.startswith("[Error]"):
        return ResponseScores(relevance=1, coherence=1, helpfulness=1)

    query_terms = {term for term in tokenize(query) if term not in STOP_WORDS}
    response_terms = set(tokenize(response))
    overlap_ratio = len(query_terms & response_terms) / max(1, len(query_terms))

    relevance = 2
    if overlap_ratio >= 0.2:
        relevance += 1
    if overlap_ratio >= 0.4:
        relevance += 1
    if any(term in response_terms for term in ("order", "refund", "return", "delivery", "shipping", "account", "coupon")):
        relevance += 1

    word_count = len(tokenize(response))
    sentence_count = len(re.findall(r"[.!?]", response))
    coherence = 2
    if 25 <= word_count <= 160:
        coherence += 1
    if sentence_count >= 2:
        coherence += 1
    if response.strip().endswith((".", "!", "?")):
        coherence += 1

    helpfulness = 2
    lower_response = response.lower()
    if any(phrase in lower_response for phrase in EMPATHY_PHRASES):
        helpfulness += 1
    if any(phrase in lower_response for phrase in ACTION_PHRASES):
        helpfulness += 1
    if "if" in lower_response or "please provide" in lower_response or "you can" in lower_response:
        helpfulness += 1

    return ResponseScores(
        relevance=clamp_score(relevance),
        coherence=clamp_score(coherence),
        helpfulness=clamp_score(helpfulness),
    )


def generate_response(prompt: str) -> str:
    try:
        return query_ollama(prompt)
    except RuntimeError as exc:
        return f"[Error] {exc}"


def evaluate_queries(
    queries: Iterable[str],
    zero_shot_template: str,
    one_shot_template: str,
) -> list[QueryResult]:
    query_list = list(queries)
    results: list[QueryResult] = []

    for index, query in enumerate(query_list, start=1):
        logging.info("Processing query %s of %s", index, len(query_list))

        zero_shot_prompt = build_prompt(zero_shot_template, query)
        one_shot_prompt = build_prompt(one_shot_template, query)

        zero_shot_response = generate_response(zero_shot_prompt)
        one_shot_response = generate_response(one_shot_prompt)

        results.append(
            QueryResult(
                query=query,
                zero_shot_response=zero_shot_response,
                one_shot_response=one_shot_response,
                zero_shot_scores=score_response(query, zero_shot_response),
                one_shot_scores=score_response(query, one_shot_response),
            )
        )

    return results


def format_scores(scores: ResponseScores) -> str:
    return (
        f"Relevance: {scores.relevance}/5 | "
        f"Coherence: {scores.coherence}/5 | "
        f"Helpfulness: {scores.helpfulness}/5 | "
        f"Average: {scores.average}/5"
    )


def build_summary_table(results: list[QueryResult]) -> str:
    zero_relevance = statistics.mean(result.zero_shot_scores.relevance for result in results)
    zero_coherence = statistics.mean(result.zero_shot_scores.coherence for result in results)
    zero_helpfulness = statistics.mean(result.zero_shot_scores.helpfulness for result in results)
    zero_average = statistics.mean(result.zero_shot_scores.average for result in results)

    one_relevance = statistics.mean(result.one_shot_scores.relevance for result in results)
    one_coherence = statistics.mean(result.one_shot_scores.coherence for result in results)
    one_helpfulness = statistics.mean(result.one_shot_scores.helpfulness for result in results)
    one_average = statistics.mean(result.one_shot_scores.average for result in results)

    return "\n".join(
        [
            "| Prompt Type | Relevance | Coherence | Helpfulness | Overall |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| Zero-shot | {zero_relevance:.2f} | {zero_coherence:.2f} | {zero_helpfulness:.2f} | {zero_average:.2f} |",
            f"| One-shot | {one_relevance:.2f} | {one_coherence:.2f} | {one_helpfulness:.2f} | {one_average:.2f} |",
        ]
    )


def write_results_markdown(results: list[QueryResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = [
        "# Offline Chatbot Evaluation Results",
        "",
        f"Generated: {generated_at}",
        f"Model: `{MODEL_NAME}`",
        f"Endpoint: `{OLLAMA_ENDPOINT}`",
        "",
        "Heuristic scoring rubric: 1 (weak) to 5 (strong) for relevance, coherence, and helpfulness.",
        "",
        "## Summary",
        build_summary_table(results),
        "",
    ]

    for index, result in enumerate(results, start=1):
        sections.extend(
            [
                f"## Query {index}",
                f"Customer Query: {result.query}",
                "",
                "Zero-shot Response:",
                result.zero_shot_response,
                "",
                f"Zero-shot Scores: {format_scores(result.zero_shot_scores)}",
                "",
                "One-shot Response:",
                result.one_shot_response,
                "",
                f"One-shot Scores: {format_scores(result.one_shot_scores)}",
                "",
                "---------------------------------",
                "",
            ]
        )

    output_path.write_text("\n".join(sections).strip() + "\n", encoding="utf-8")


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        zero_shot_template = load_template(ZERO_SHOT_TEMPLATE_PATH)
        one_shot_template = load_template(ONE_SHOT_TEMPLATE_PATH)
        queries = load_queries(args.queries_file)
        results = evaluate_queries(queries, zero_shot_template, one_shot_template)
        write_results_markdown(results, args.output)
    except Exception as exc:
        logging.error("%s", exc)
        return 1

    logging.info("Saved evaluation results to %s", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
