
import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "eval_dataset.json"
OUTPUT_DIR = BASE_DIR / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

with DATASET_PATH.open("r", encoding="utf-8") as f:
    cases = json.load(f)

FEE_KEYWORDS = [
    "charged without my intent",
    "without my intent",
    "charged unexpectedly",
    "unintended paid subscription",
    "refund after cancellation",
]


def predict_fee_issue(text):
    text = text.lower()

    # A charge after cancellation is a strong fee-related signal.
    if (
        "cancel" in text
        and any(word in text for word in [
            "billed", "charged", "payment taken"
        ])
    ):
        return True

    # Explicit claims of an unintended charge or activation.
    if any(phrase in text for phrase in [
        "without my intent",
        "charged unexpectedly",
        "unintended paid subscription",
        "activated without my consent",
        "refund after cancellation"
    ]):
        return True

    # Trial questions, upgrade prompts and refund intent alone
    # do not prove an unexpected charge.
    return False


def predict_theme(text):
    text = text.lower()

    # Prioritize the underlying complaint over refund language.
    if any(phrase in text for phrase in [
        "answers are wrong",
        "inaccurate",
        "wrong answer",
        "ignores instructions",
        "ignores simple instructions"
    ]):
        return "Answer quality / accuracy"

    if any(phrase in text for phrase in [
        "cannot find",
        "can't find",
        "settings menu",
        "navigation"
    ]):
        return "Usability / navigation"

    if any(phrase in text for phrase in [
        "free plan",
        "messages quickly",
        "upgrade to continue",
        "hit a limit",
        "message limit",
        "usage limit"
    ]):
        return "Usage limits / upgrade prompts"

    if any(phrase in text for phrase in [
        "subscription",
        "refund",
        "charged",
        "billed",
        "auto-renew",
        "free trial",
        "paying",
        "cancelled"
    ]):
        return "Subscription / billing confusion"

    return "Other / unclassified"

    text = text.lower()
    return any(keyword in text for keyword in FEE_KEYWORDS)


def predict_fee_issue(text):
    text = text.lower()

    # A charge after cancellation is a strong fee-related signal.
    if (
        "cancel" in text
        and any(word in text for word in [
            "billed", "charged", "payment taken"
        ])
    ):
        return True

    # Explicit claims of an unintended charge or activation.
    if any(phrase in text for phrase in [
        "without my intent",
        "charged unexpectedly",
        "unintended paid subscription",
        "activated without my consent",
        "refund after cancellation"
    ]):
        return True

    # Trial questions, upgrade prompts and refund intent alone
    # do not prove an unexpected charge.
    return False


def predict_theme(text):
    text = text.lower()

    # Prioritize the underlying complaint over refund language.
    if any(phrase in text for phrase in [
        "answers are wrong",
        "inaccurate",
        "wrong answer",
        "ignores instructions",
        "ignores simple instructions"
    ]):
        return "Answer quality / accuracy"

    if any(phrase in text for phrase in [
        "cannot find",
        "can't find",
        "settings menu",
        "navigation"
    ]):
        return "Usability / navigation"

    if any(phrase in text for phrase in [
        "free plan",
        "messages quickly",
        "upgrade to continue",
        "hit a limit",
        "message limit",
        "usage limit"
    ]):
        return "Usage limits / upgrade prompts"

    if any(phrase in text for phrase in [
        "subscription",
        "refund",
        "charged",
        "billed",
        "auto-renew",
        "free trial",
        "paying",
        "cancelled"
    ]):
        return "Subscription / billing confusion"

    return "Other / unclassified"

    text = text.lower()

    if any(w in text for w in [
        "inaccurate", "wrong answer", "ignores instructions"
    ]):
        return "Answer quality / accuracy"

    if any(w in text for w in [
        "settings", "cannot find", "navigation", "menu"
    ]):
        return "Usability / navigation"

    if any(w in text for w in [
        "subscription", "refund", "charged", "auto-renew",
        "free trial", "paying"
    ]):
        return "Subscription / billing confusion"

    if any(w in text for w in [
        "free plan", "messages", "upgrade", "message limit"
    ]):
        return "Usage limits / upgrade prompts"

    return "Other / unclassified"

def calculate_scores(actual, predicted):
    tp = sum(a and p for a, p in zip(actual, predicted))
    fp = sum((not a) and p for a, p in zip(actual, predicted))
    fn = sum(a and (not p) for a, p in zip(actual, predicted))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    return precision, recall, f1

results = []

for case in cases:
    text = case["review_text"]
    predicted_fee = predict_fee_issue(text)
    predicted_theme = predict_theme(text)

    results.append({
        "id": case["id"],
        "expected_fee_issue": case["expected_fee_issue"],
        "predicted_fee_issue": predicted_fee,
        "fee_correct": predicted_fee == case["expected_fee_issue"],
        "expected_theme": case["expected_theme"],
        "predicted_theme": predicted_theme,
        "theme_correct": predicted_theme == case["expected_theme"],
        "review_text": text,
    })

actual = [r["expected_fee_issue"] for r in results]
predicted = [r["predicted_fee_issue"] for r in results]

precision, recall, f1 = calculate_scores(actual, predicted)
theme_accuracy = sum(r["theme_correct"] for r in results) / len(results)

summary = {
    "dataset_size": len(results),
    "fee_issue_precision": round(precision, 3),
    "fee_issue_recall": round(recall, 3),
    "fee_issue_f1": round(f1, 3),
    "theme_accuracy": round(theme_accuracy, 3),
    "note": "Small illustrative dataset; keyword baseline only."
}

with (OUTPUT_DIR / "evaluation_summary.json").open(
    "w", encoding="utf-8"
) as f:
    json.dump(summary, f, indent=2)

with (OUTPUT_DIR / "evaluation_cases.csv").open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(json.dumps(summary, indent=2))
print("Evaluation reports generated.")
