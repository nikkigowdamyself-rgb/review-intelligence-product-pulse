"""Local MCP server: approved writes to a Notes markdown file and an email draft file."""
import json
from pathlib import Path
from datetime import date
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("review-product-pulse")
ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

@mcp.tool()
def append_product_pulse(record: dict) -> dict:
    """Append a reviewed weekly product pulse and fee explainer to the local Notes document."""
    path = OUTPUTS / "weekly_product_notes.md"
    with path.open("a", encoding="utf-8") as f:
        f.write("\n\n---\n## Weekly Product Pulse — " + str(record.get("date", date.today())) + "\n\n")
        f.write("### Top themes\n")
        for t in record.get("top_themes", []):
            f.write(f"- **{t.get('theme','Theme')}** — {t.get('count',0)} reviews; {t.get('share_percent','n/a')}%.\n")
        f.write("\n### Weekly pulse\n\n" + str(record.get("weekly_pulse","")) + "\n\n")
        f.write("### Identified fee issue\n\n" + json.dumps(record.get("identified_fee_issue",{}), indent=2) + "\n\n")
        f.write("### Customer explanation\n\n" + str(record.get("fee_explainer","")) + "\n\n")
        f.write("### Source links\n")
        for url in record.get("source_links", []):
            f.write(f"- {url}\n")
        f.write("\n### Quotes\n")
        for q in record.get("quotes", []):
            f.write(f'- "{q.get("quote","")}" (review {q.get("review_id","")})\n')
    return {"status": "appended", "path": str(path), "date": str(record.get("date", date.today()))}

@mcp.tool()
def create_email_draft(record: dict) -> dict:
    """Create a local email draft file; never send email."""
    today = str(record.get("date", date.today()))
    path = OUTPUTS / f"email_draft_{today}.txt"
    subject = "Weekly Product Pulse + Customer Clarification — " + today
    body = ("Subject: " + subject + "\n\nWEEKLY PRODUCT PULSE\n\n" +
            str(record.get("weekly_pulse","")) +
            "\n\nREUSABLE CUSTOMER SUPPORT SNIPPET\n\n" +
            str(record.get("fee_explainer","")) +
            "\n\nSources:\n" + "\n".join(record.get("source_links", [])) +
            "\n\nDRAFT ONLY — NOT SENT")
    path.write_text(body, encoding="utf-8")
    return {"status": "draft_created", "path": str(path), "sent": False, "subject": subject}

if __name__ == "__main__":
    mcp.run(transport="stdio")
