
import csv
import json
from pathlib import Path

# Locate files relative to this script
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "grounding_eval_dataset.json"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load the evaluation dataset
if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_PATH}. "
        "Create evals/grounding_eval_dataset.json first."
    )

with DATASET_PATH.open("r", encoding="utf-8") as file:
    test_cases = json.load(file)


def check_claim(case):
    """
    Simple rule-based baseline.
    This is not a semantic AI judge and cannot reliably
    detect every hallucination.
    """
    claim = case["claim"].lower()
    evidence = case["evidence"].lower()

    # Flag unsupported high-confidence or broad claims.
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

    # Check a limited number of known claim patterns.
    if "one supplied review alleges" in claim:
        return "one supplied review alleges" in evidence

    if "usage limits and upgrade prompts" in claim:
        return (
            "message limits" in evidence
            and "upgrade" in evidence
        )

    # Unknown claims are conservatively marked unsupported.
    return False


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
incorrect = total - correct
accuracy = correct / total if total else 0.0

summary = {
    "dataset_size": total,
    "correct_predictions": correct,
    "incorrect_predictions": incorrect,
    "grounding_check_accuracy": round(accuracy, 4),
    "evaluator_type": "rule-based baseline",
    "warning": (
        "Results on this small labelled dataset do not establish "
        "real-world hallucination detection performance."
    ),
}

summary_path = REPORT_DIR / "grounding_evaluation_summary.json"
cases_path = REPORT_DIR / "grounding_evaluation_cases.csv"

# Save summary JSON
with summary_path.open("w", encoding="utf-8") as file:
    json.dump(summary, file, indent=2)

# Save detailed CSV
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
