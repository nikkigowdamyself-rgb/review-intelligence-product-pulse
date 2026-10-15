import json, os, re
from pathlib import Path
from datetime import date
import pandas as pd

ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

THEME_KEYWORDS = {
    "Voice input / discoverability": ["voice", "mic", "microphone", "dictation", "speak", "speech", "audio"],
    "Answer quality / accuracy": ["wrong", "incorrect", "inaccurate", "hallucinat", "mistake", "answer", "accuracy"],
    "Reliability / crashes / speed": ["crash", "slow", "freeze", "loading", "bug", "error", "lag"],
    "Subscription / billing confusion": ["charge", "charged", "billing", "bill", "subscription", "renew", "refund", "payment", "fee", "cancel", "price"],
    "Usability / navigation": ["confusing", "hard to find", "interface", "button", "navigation", "design", "update"]
}

def _llm_json(prompt, api_key, model):
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":"You analyze customer reviews carefully. Use only supplied evidence. Never invent quotes, review counts, causes, fee terms, or URLs. Return valid JSON."},
                {"role":"user","content":prompt}
            ]
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"_error": str(e)}

def analyze_reviews(df, api_key="", model="gpt-4.1-mini"):
    reviews = []
    for i,row in df.reset_index(drop=True).iterrows():
        reviews.append({"review_id": str(i+1), "text": str(row["review_text"])[:2500], "date": str(row.get("review_date","")), "rating": str(row.get("rating",""))})
    prompt = """Analyze these app reviews for ChatGPT mobile app users. Group into no more than 5 themes and rank the top 3 by evidence/count. Return JSON keys:
themes: array of {theme, count, share_percent, evidence_summary, representative_review_ids}
quotes: array of exactly 3 {quote, review_id}, each quote verbatim from supplied text
fee_issue: {issue, review_count, evidence_review_ids, confidence, evidence_summary}
Important: choose a fee/charge issue only if reviews explicitly mention a fee, charge, subscription, renewal, refund, payment, or price. If no recurring issue is evidenced, issue must say "No recurring fee issue established from this dataset", review_count 0, confidence "low". Do not force a fee finding. Do not use external knowledge for the findings.
Reviews JSON: """ + json.dumps(reviews, ensure_ascii=False)
    result = _llm_json(prompt, api_key, model)
    if result and "_error" not in result:
        result["mode"] = "LLM"
        return result
    # Transparent baseline fallback: keyword matching, not semantic clustering.
    assigned = {k: [] for k in THEME_KEYWORDS}
    fee_terms = THEME_KEYWORDS["Subscription / billing confusion"]
    fee_reviews = []
    for r in reviews:
        text = r["text"].lower()
        matched = [theme for theme, kws in THEME_KEYWORDS.items() if any(k in text for k in kws)]
        for theme in matched[:1]:
            assigned[theme].append(r)
        if any(k in text for k in fee_terms):
            fee_reviews.append(r)
    themes = []
    for theme, rs in assigned.items():
        if rs:
            themes.append({"theme": theme, "count": len(rs), "share_percent": round(100*len(rs)/max(1,len(reviews)),1),
                           "evidence_summary": "Keyword-based preliminary grouping; manually validate.",
                           "representative_review_ids": [x["review_id"] for x in rs[:3]]})
    themes = sorted(themes, key=lambda x:x["count"], reverse=True)[:5]
    quotes = [{"quote":r["text"],"review_id":r["review_id"]} for r in reviews[:3]]
    fee_issue = {
        "issue": "Possible subscription/billing confusion" if fee_reviews else "No recurring fee issue established from this dataset",
        "review_count": len(fee_reviews),
        "evidence_review_ids": [r["review_id"] for r in fee_reviews[:10]],
        "confidence": "low" if not fee_reviews else "medium",
        "evidence_summary": "Keyword matches only; inspect cited reviews before treating this as a finding."
    }
    return {"themes": themes, "quotes": quotes, "fee_issue": fee_issue, "mode": "keyword fallback"}

def generate_outputs(analysis, api_key="", model="gpt-4.1-mini"):
    prompt = """Create two outputs from this review analysis. Return JSON keys weekly_pulse and fee_explainer and source_links.
weekly_pulse must be <=250 words, structured with Summary, Evidence (use quotes verbatim), Key observation, and 3 action ideas. Distinguish evidence from hypotheses.
fee_explainer must contain <=6 bullets and explain only the issue actually evidenced. If no recurring fee issue is established, explicitly say validation is blocked and do not fabricate a fee explanation. Use these official sources only if relevant:
https://help.openai.com/en/articles/7232927-canceling-your-chatgpt-subscription
https://help.openai.com/en/articles/7232895-how-do-i-request-a-refund-for-chatgpt-plus
https://help.openai.com/en/articles/20001043
Include the exact text 'Last checked: """ + str(date.today()) + """'.
Analysis JSON: """ + json.dumps(analysis, ensure_ascii=False)
    result = _llm_json(prompt, api_key, model)
    if result and "_error" not in result and "weekly_pulse" in result:
        result.setdefault("source_links", [
            "https://help.openai.com/en/articles/7232927-canceling-your-chatgpt-subscription",
            "https://help.openai.com/en/articles/7232895-how-do-i-request-a-refund-for-chatgpt-plus"
        ])
        return result
    themes = analysis.get("themes", [])[:3]
    theme_text = "; ".join(f"{t['theme']} ({t['count']} reviews)" for t in themes) or "No reliable themes detected"
    quotes = analysis.get("quotes", [])[:3]
    qtext = "\n".join(f'- "{q["quote"]}" (review {q["review_id"]})' for q in quotes)
    fee = analysis.get("fee_issue", {})
    pulse = f"""Summary: Top themes in the uploaded sample: {theme_text}.

Evidence:
{qtext}

Key observation: {fee.get('evidence_summary','Review evidence requires validation')} Fee-related signal: {fee.get('issue','Not established')} (n={fee.get('review_count',0)}). The baseline mode uses keyword matching; validate the sample and counts before sharing.

Action ideas:
1. Inspect the highest-volume theme's cited reviews and reproduce the underlying user journey.
2. Run 5–6 follow-up user interviews to distinguish discoverability, comprehension, and product reliability.
3. Track theme share and a relevant task-success metric weekly; compare after any UX change."""
    if fee.get("review_count",0) > 0:
        explainer = """- Confirm where the subscription was purchased: ChatGPT web, Apple App Store, or Google Play.
- Manage or cancel the subscription on the platform that billed it.
- Uninstalling the app does not cancel a subscription.
- Cancellation stops future renewals; it does not automatically refund a prior charge.
- Refund requests follow the relevant platform and OpenAI Help Center process.
- Check the purchase receipt and active subscriptions before concluding that a charge is duplicated.

Last checked: """ + str(date.today())
    else:
        explainer = """- No recurring fee/charge confusion was established from the current review sample.
- Do not publish a fee explanation as a finding until fee-related reviews are verified.
- If subscription billing is later confirmed, first identify the purchase platform and the specific point of confusion.

Last checked: """ + str(date.today())
    return {"weekly_pulse": pulse[:4000], "fee_explainer": explainer,
            "source_links": [
                "https://help.openai.com/en/articles/7232927-canceling-your-chatgpt-subscription",
                "https://help.openai.com/en/articles/7232895-how-do-i-request-a-refund-for-chatgpt-plus"
            ]}

def append_to_notes(record):
    path = OUTPUTS / "weekly_product_notes.md"
    with path.open("a", encoding="utf-8") as f:
        f.write("\n\n---\n## Weekly Product Pulse — " + record["date"] + "\n\n")
        f.write("### Top themes\n")
        for t in record.get("top_themes", []):
            f.write(f"- **{t.get('theme','Theme')}** — {t.get('count',0)} reviews; {t.get('share_percent','n/a')}%.\n")
        f.write("\n### Weekly pulse\n\n" + record.get("weekly_pulse","") + "\n\n")
        f.write("### Identified fee issue\n\n" + json.dumps(record.get("identified_fee_issue",{}), indent=2) + "\n\n")
        f.write("### Customer explanation\n\n" + record.get("fee_explainer","") + "\n\n")
        f.write("### Source links\n")
        for url in record.get("source_links", []):
            f.write(f"- {url}\n")
        f.write("\n### Quotes\n")
        for q in record.get("quotes", []):
            f.write(f'- "{q.get("quote","")}" (review {q.get("review_id","")})\n')
    return str(path)

def create_email_draft(record):
    path = OUTPUTS / ("email_draft_" + record["date"] + ".txt")
    subject = "Weekly Product Pulse + Customer Clarification — " + record["date"]
    body = subject + "\n\nWEEKLY PRODUCT PULSE\n\n" + record.get("weekly_pulse","") + "\n\nREUSABLE CUSTOMER SUPPORT SNIPPET\n\n" + record.get("fee_explainer","") + "\n\nSources:\n" + "\n".join(record.get("source_links", [])) + "\n\nDRAFT ONLY — NOT SENT"
    path.write_text("Subject: " + subject + "\n\n" + body, encoding="utf-8")
    return str(path)
