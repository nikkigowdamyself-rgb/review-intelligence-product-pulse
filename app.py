import os, json, re
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

from workflow import analyze_reviews, generate_outputs
from mcp_client import call_mcp_tool

st.set_page_config(page_title="Review → Product Pulse", page_icon="🔎", layout="wide")
st.title("🔎 Review Intelligence → Product Pulse")
st.caption("ChatGPT mobile app · India voice-adoption lens · Human approval before any write action")

with st.sidebar:
    st.header("Configuration")
    st.write("Upload a public app-review CSV covering the last 8–12 weeks.")
    st.info("Expected columns: review text, date, rating (optional). Column mapping is available below.")
    api_key = st.text_input("OpenAI API key (optional)", type="password", help="If provided, uses an LLM for theme extraction and drafting. Without it, uses a transparent keyword-based demo mode.")
    model = st.text_input("Model", value="gpt-4.1-mini")
    st.caption("Do not upload private customer data or account/payment details.")

uploaded = st.file_uploader("Upload review CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.subheader("Map your CSV columns")
    cols = list(df.columns)
    c1,c2,c3 = st.columns(3)
    text_col = c1.selectbox("Review text column", cols, index=next((i for i,c in enumerate(cols) if any(k in c.lower() for k in ["review","content","text","comment"])),0))
    date_col = c2.selectbox("Review date column", ["(none)"]+cols, index=next((i+1 for i,c in enumerate(cols) if any(k in c.lower() for k in ["date","time","at"])),0))
    rating_col = c3.selectbox("Rating column (optional)", ["(none)"]+cols, index=next((i+1 for i,c in enumerate(cols) if "rating" in c.lower() or "score" in c.lower()),0))
    if st.button("Analyze reviews", type="primary"):
        clean = pd.DataFrame({"review_text": df[text_col].fillna("").astype(str)})
        clean["review_date"] = df[date_col] if date_col != "(none)" else ""
        clean["rating"] = df[rating_col] if rating_col != "(none)" else ""
        clean = clean[clean.review_text.str.strip().ne("")]
        if date_col != "(none)":
            parsed = pd.to_datetime(clean.review_date, errors="coerce", utc=True)
            cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(weeks=12)
            recent = clean[parsed >= cutoff].copy()
            if len(recent) >= 5:
                clean = recent
        with st.spinner("Analyzing feedback..."):
            analysis = analyze_reviews(clean, api_key=api_key, model=model)
            outputs = generate_outputs(analysis, api_key=api_key, model=model)
        st.session_state["analysis"] = analysis
        st.session_state["outputs"] = outputs
        st.session_state["review_count"] = len(clean)

if "analysis" in st.session_state:
    a = st.session_state["analysis"]
    o = st.session_state["outputs"]
    st.divider()
    st.subheader("1. Review intelligence")
    m1,m2,m3 = st.columns(3)
    m1.metric("Reviews analyzed", st.session_state["review_count"])
    m2.metric("Themes detected", len(a.get("themes", [])))
    m3.metric("Fee-related reviews", a.get("fee_issue", {}).get("review_count", 0))
    st.write("**Top themes**")
    st.dataframe(pd.DataFrame(a.get("themes", [])), use_container_width=True, hide_index=True)
    st.write("**Three verbatim review quotes**")
    for q in a.get("quotes", [])[:3]:
        st.markdown(f"> {q.get('quote','')}  \n— Review ID: `{q.get('review_id','not supplied')}`")
    st.write("**Fee/charge issue identified**")
    st.json(a.get("fee_issue", {}))
    st.caption("Quotes are copied from the uploaded dataset. Validate the issue and source links before publishing.")

    st.divider()
    st.subheader("2. Weekly product pulse (editable)")
    pulse = st.text_area("Internal update (≤250 words)", o.get("weekly_pulse",""), height=250)
    st.subheader("3. Customer fee explanation (editable)")
    explainer = st.text_area("Support snippet (≤6 bullets)", o.get("fee_explainer",""), height=220)
    sources = st.text_area("Two official source URLs (one per line)", "\n".join(o.get("source_links", [])), height=90)
    st.subheader("4. Approval gate")
    st.warning("Nothing is written until you explicitly approve. Approval writes a local Notes document and creates a local email draft; it does not send email.")
    approved = st.checkbox("I reviewed the themes, quotes, fee issue, source links, and approve creating the Notes entry and email draft.")
    if st.button("Approve & create Notes entry + email draft", type="primary", disabled=not approved):
        final_outputs = {
            "weekly_pulse": pulse,
            "fee_explainer": explainer,
            "source_links": [x.strip() for x in sources.splitlines() if x.strip()]
        }
        record = {
            "date": str(date.today()),
            "top_themes": a.get("themes", [])[:3],
            "weekly_pulse": pulse,
            "fee_explainer": explainer,
            "identified_fee_issue": a.get("fee_issue", {}),
            "explanation_bullets": [x.strip("- •") for x in explainer.splitlines() if x.strip().startswith(("-", "•"))],
            "source_links": final_outputs["source_links"],
            "quotes": a.get("quotes", [])
        }
        with st.spinner("Calling approved MCP tools..."):
            notes_result = call_mcp_tool("append_product_pulse", {"record": record})
            email_result = call_mcp_tool("create_email_draft", {"record": record})
        st.success("Approved MCP actions completed.")
        st.write("**MCP append result**")
        st.json(notes_result)
        st.write("**MCP email-draft result**")
        st.json(email_result)
        notes_path = notes_result.get("path", "See MCP result")
        email_path = email_result.get("path", "See MCP result")
        st.download_button("Download structured JSON entry", json.dumps(record, indent=2), file_name="weekly_product_pulse.json", mime="application/json")
        st.download_button("Download email draft text", Path(email_path).read_text(encoding="utf-8"), file_name="email_draft.txt", mime="text/plain")
else:
    st.info("Upload your review CSV to begin. The included sample CSV is synthetic and is only for testing the workflow—not evidence for your final submission.")
    sample = Path("data/sample_reviews_synthetic.csv")
    if sample.exists():
        st.download_button("Download synthetic demo CSV", sample.read_bytes(), file_name="sample_reviews_synthetic.csv", mime="text/csv")
