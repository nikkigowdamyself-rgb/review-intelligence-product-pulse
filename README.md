# Review Intelligence → Weekly Product Pulse

A Streamlit prototype for the Milestone 4 workflow using ChatGPT mobile-app reviews, with the Milestone 1 focus on voice-input adoption in India.

## What it does
1. Accepts a public reviews CSV and lets you map text/date/rating columns.
2. Filters to the last 12 weeks when usable dates are present.
3. Groups reviews into at most five themes, ranks themes, and selects three verbatim quotes.
4. Checks whether a recurring fee/charge issue is actually evidenced.
5. Drafts a weekly internal pulse (maximum 250 words) and a customer explanation (maximum six bullets).
6. Requires explicit human approval, then calls a local Model Context Protocol (MCP) server through its stdio client to append a Notes document and create a local email draft.
7. Does not send email.

## Important evidence limitation
The included `data/sample_reviews_synthetic.csv` is synthetic test data, not real customer evidence. Replace it with a public review export before submitting. Do not present synthetic quotes or counts as real findings. The no-API-key fallback is keyword-based and should be described as a baseline, not semantic AI clustering. For stronger results, set an OpenAI API key in the sidebar.

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Optional: enter an OpenAI API key in the sidebar. It is used only for analysis/drafting during the current app session; do not commit keys to GitHub.

## Approval gate
The checkbox “I reviewed ... and approve” must be checked before the write button becomes available. Only after clicking **Approve & create Notes entry + email draft** does the Streamlit app start the local MCP server, initialize an MCP client session, and call two MCP tools:
- `append_product_pulse` appends to `outputs/weekly_product_notes.md`
- `create_email_draft` creates `outputs/email_draft_YYYY-MM-DD.txt`

These local files simulate internal Notes/Docs and Gmail draft destinations. The MCP protocol and approval gate are real in this prototype; the external Google Docs/Notion and Gmail integrations are not connected. For production, replace the two MCP server tool implementations with authenticated Google Docs/Notion and Gmail draft API calls, preserving the same approval gate immediately before execution. No email is sent.

## What fee issue was identified?
No fee issue should be asserted until the real uploaded CSV has been analyzed. Subscription renewal, cancellation, refund, or duplicate-charge confusion are candidate patterns to test, not pre-filled findings. If the sample does not support a recurring fee issue, the app explicitly reports that no recurring issue is established.

## Source links to validate the support snippet
- https://help.openai.com/en/articles/7232927-canceling-your-chatgpt-subscription
- https://help.openai.com/en/articles/7232895-how-do-i-request-a-refund-for-chatgpt-plus
- https://help.openai.com/en/articles/20001043

## Deliverables checklist
- [ ] Replace synthetic demo CSV with public review data from the last 8–12 weeks.
- [ ] Validate top themes and all quotes against the original review page.
- [ ] Confirm the fee issue appears repeatedly in actual reviews.
- [ ] Check the two official sources and update “Last checked”.
- [ ] Approve once, then capture screenshots of the app, Notes entry, and email draft.
- [ ] Deploy Streamlit for a working prototype link.
- [ ] Push source code to GitHub without API keys or private data.
