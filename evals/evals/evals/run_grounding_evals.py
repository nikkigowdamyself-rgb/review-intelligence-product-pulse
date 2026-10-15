
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "grounding_eval_dataset.json"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

with DATASET_PATH.open("r", encoding="utf-8") as file:
    test_cases = json.load(file)


def check_claim(case):
    """
    Initial rule-based baseline.
    This checks simple evidence and wording patterns.
    It is not a true semantic or LLM-based judge.
    """
    claim = case["claim"].lower()
    evidence = case["evidence"].lower()

    unsupported_signals = [
        "most users",
        "proves that",
        "increasing over time",
        "independently verified",
        "everyone",
        "all users"
    ]

    # Claims using strong language need stronger evidence.
    if any(signal in claim for signal in unsupported_signals):
        return False

    # For this starter dataset, conservative checks are intentional.
    if "one supplied review alleges" in claim:
        return "one supplied review alleges" in evidence

    if "usage limits and upgrade prompts" in claim:
        return (
            "message limits" in evidence
            and "upgrade" in evidence
        )

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
        "reason": case["reason"]
    })

total = len(results)
correct = sum(row["correct"] for row in results)
accuracy = correct / total if total else 0

summary = {
    "dataset_size": total,
    "correct_predictions": correct,
    "incorrect_predictions": total - correct,
    "grounding_check_accuracy": round(accuracy, 4),
    "warning": (
        "Rule-based baseline only. Accuracy on this small test set "
        "does not establish real-world hallucination detection."
    )
}

summary_path = REPORT_DIR / "grounding_evaluation_summary.json"
cases_path = REPORT_DIR / "grounding_evaluation_cases.csv"

with summary_path.open("w", encoding="utf-8") as file:
    json.dump(summary, file, indent=2)

with cases_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(json.dumps(summary, indent=2))
print(f"\nDetailed cases saved to: {cases_path}")
print(f"Summary saved to: {summary_path}")
