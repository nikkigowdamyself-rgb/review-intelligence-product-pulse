

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "grounding_eval_dataset.json"
REPORT_DIR = BASE_DIR / "reports"


def check_claim(case):
    """
    Rule-based grounding baseline.
    This is not a full AI hallucination detector.
    """
    claim = case["claim"].lower()
    evidence = case["evidence"].lower()

    unsupported_signals = [
        "most users",
        "proves that",
        "increasing over time",
        "independently verified",
        "everyone",
        "all users",
    ]

    if any(signal in claim for signal in unsupported_signals):
        return False

    if "one supplied review alleges" in claim:
        return "one supplied review alleges" in evidence

    if "usage limits and upgrade prompts" in claim:
        return (
            "message limits" in evidence
            and "upgrade" in evidence
        )

    return False


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}. "
            "Make sure grounding_eval_dataset.json is "
            "in the same folder as this script."
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        test_cases = json.load(file)

    results = []

    for case in test_cases:
        expected = case["expected_supported"]
        predicted = check_claim(case)

        results.append({
            "id": case["id"],
            "claim": case["claim"],
            "expected_supported": expected,
            "predicted_supported": predicted,
            "correct": expected == predicted,
            "reason": case["reason"],
        })

    total = len(results)
    correct = sum(row["correct"] for row in results)

    summary = {
        "dataset_size": total,
        "correct_predictions": correct,
        "incorrect_predictions": total - correct,
        "grounding_check_accuracy": round(
            correct / total, 4
        ) if total else 0.0,
        "evaluator_type": "rule-based baseline",
        "warning": (
            "Results on this small labelled dataset do not "
            "establish real-world hallucination detection accuracy."
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = REPORT_DIR / "grounding_evaluation_summary.json"
    cases_path = REPORT_DIR / "grounding_evaluation_cases.csv"

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    if results:
        with cases_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=results[0].keys()
            )
            writer.writeheader()
            writer.writerows(results)

    print("GROUNDING EVALUATION SUMMARY")
    print(json.dumps(summary, indent=2))
    print(f"\nSummary saved to: {summary_path}")
    print(f"Cases saved to: {cases_path}")


if __name__ == "__main__":
    main()
