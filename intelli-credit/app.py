"""
app.py – IntelliCredit: AI-Powered Credit Appraisal Assistant
Main Streamlit application integrating all agent modules.

Pages:
  1. 📤 Upload & Extract   (Phase 1)
  2. 🇮🇳 India Checks       (Phase 2)
  3. 🌐 Web Research        (Phase 3)
  4. 📊 Score & Insights    (Phase 4)
  5. 📄 Generate CAM        (Phase 5)
"""

import io
import json
import os

import streamlit as st
from dotenv import load_dotenv

from utils.helpers import format_currency

# Load .env
load_dotenv()

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliCredit – AI Credit Appraisal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #e2e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b, #0f172a);
    border-right: 1px solid #334155;
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(59,130,246,0.15);
}
.metric-label  { font-size: 0.78rem; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value  { font-size: 1.5rem; color: #e2e8f0; font-weight: 700; margin-top: 4px; }

/* Score ring */
.score-ring {
    width: 160px; height: 160px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column;
    margin: auto;
    font-size: 2.5rem; font-weight: 800;
}

/* Risk badge */
.badge-low    { background:#16a34a22; color:#22c55e; border:1px solid #22c55e; padding:4px 12px; border-radius:20px; }
.badge-mod    { background:#d9770622; color:#f59e0b; border:1px solid #f59e0b; padding:4px 12px; border-radius:20px; }
.badge-high   { background:#dc262622; color:#ef4444; border:1px solid #ef4444; padding:4px 12px; border-radius:20px; }

/* Flag cards */
.flag-warn { background:#ef444410; border-left:4px solid #ef4444; padding:12px 16px; border-radius:8px; margin:6px 0; }
.flag-ok   { background:#22c55e10; border-left:4px solid #22c55e;  padding:12px 16px; border-radius:8px; margin:6px 0; }

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white; border: none; border-radius: 8px;
    padding: 10px 24px; font-weight: 600;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99,102,241,0.4);
}

h1, h2, h3 { color: #f1f5f9 !important; }
.stMarkdown p { color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)


# ── Session State Defaults ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "financials": {},
        "pdf_text": "",
        "gst_result": {},
        "cibil": {},
        "risk_flags": {},
        "bank_check": {},
        "news": [],
        "sentiment": {},
        "score_result": {},
        "score_explanation": "",
        "verdict_data": {},
        "company_name": "",
        "sector": "",
        "collateral": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 IntelliCredit")
    st.markdown("*AI-Powered Credit Appraisal*")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "📤 Upload & Extract",
            "🇮🇳 India Checks",
            "🌐 Web Research",
            "📊 Score & Insights",
            "📄 Generate CAM",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # API key status indicators
    st.markdown("**API Configuration**")
    openai_key_input = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    serpapi_key_input = st.text_input("SerpAPI Key", type="password", value=os.getenv("SERPAPI_KEY", ""))
    
    if openai_key_input:
        os.environ["OPENAI_API_KEY"] = openai_key_input
    if serpapi_key_input:
        os.environ["SERPAPI_KEY"] = serpapi_key_input

    openai_set = bool(os.environ.get("OPENAI_API_KEY", "")) and os.environ.get("OPENAI_API_KEY") != "your_openai_api_key_here"
    serp_set   = bool(os.environ.get("SERPAPI_KEY", "")) and os.environ.get("SERPAPI_KEY") != "your_serpapi_key_here"

    st.markdown(f"{'🟢' if openai_set else '🔴'} OpenAI GPT")
    st.markdown(f"{'🟢' if serp_set else '🟡'} SerpAPI News")

    if not openai_set:
        st.warning("Add OpenAI key above for LLM features.")

    st.divider()
    st.markdown("<small style='color:#64748b'>Phase 1–5 Complete ✅</small>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 1 – Upload & Extract
# ══════════════════════════════════════════════════════════════════
if page == "📤 Upload & Extract":
    st.title("📤 Upload & Extract Financial Data")
    st.markdown("Upload a PDF annual report or financial statement. IntelliCredit will extract key figures automatically.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Document Upload")
        uploaded = st.file_uploader("Upload PDF", type=["pdf"], help="Upload a digital or scanned PDF.")

        st.markdown("**— or —**")
        use_demo = st.button("🎯 Load Demo Data (No PDF needed)")

    with col2:
        st.subheader("Company Details")
        company_name = st.text_input("Company Name", value=st.session_state.company_name or "Sunrise Manufacturing Pvt Ltd")
        sector = st.text_input("Sector / Industry", value=st.session_state.sector or "Manufacturing")
        st.session_state.company_name = company_name
        st.session_state.sector = sector

    st.divider()

    if use_demo:
        from agents.extraction_agent import load_sample_data
        st.session_state.financials = load_sample_data("data/annual_reports/sample_borrower.json")
        st.session_state.financials["company_name"] = company_name
        st.success("✅ Demo data loaded successfully!")

    if uploaded:
        with st.spinner("Extracting text from PDF..."):
            from utils.pdf_extractor import extract_text_from_pdf
            result = extract_text_from_pdf(uploaded.read())
            st.session_state.pdf_text = result["text"]

        st.info(f"📄 Extracted {len(result['text'])} characters via **{result['method']}** from {result['pages']} pages.")

        if st.button("🤖 Extract Financial Fields with AI"):
            if not os.environ.get("OPENAI_API_KEY"):
                st.error("OpenAI API key required. Add it in the sidebar.")
            else:
                with st.spinner("Running extraction agent..."):
                    from agents.extraction_agent import ExtractionAgent
                    agent = ExtractionAgent()
                    try:
                        st.session_state.financials = agent.extract_all(st.session_state.pdf_text)
                        st.session_state.financials["company_name"] = company_name
                        st.success("✅ Extraction complete!")
                    except Exception as e:
                        st.error(f"❌ OpenAI API Error: {str(e)}")
                        st.info("Check if your OpenAI API key has sufficient billing quota at platform.openai.com/account/billing")

    # Display extracted data
    if st.session_state.financials:
        fin = st.session_state.financials
        st.subheader("📊 Extracted Financial Data")

        from utils.helpers import format_currency

        cols = st.columns(3)
        kpis = [
            ("Total Revenue",     fin.get("total_revenue"),          "💰"),
            ("Net Profit",        fin.get("net_profit"),             "📈"),
            ("EBITDA",            fin.get("ebitda"),                 "⚙️"),
            ("Total Loans",       fin.get("total_loans"),            "🏦"),
            ("Current Ratio",     fin.get("current_ratio"),          "📐"),
            ("Debt / Equity",     fin.get("debt_equity_ratio"),      "⚖️"),
            ("Interest Coverage", fin.get("interest_coverage") or fin.get("interest_coverage_ratio"), "🔄"),
            ("Loan Requested",    fin.get("loan_amount_requested"),  "📋"),
            ("Loan Purpose",      fin.get("loan_purpose"),           "🎯"),
        ]

        for i, (label, value, icon) in enumerate(kpis):
            with cols[i % 3]:
                if isinstance(value, (int, float)) and value and value > 1000:
                    disp = format_currency(value)
                else:
                    disp = str(value) if value is not None else "—"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{icon} {label}</div>
                    <div class="metric-value">{disp}</div>
                </div>""", unsafe_allow_html=True)

        # Promoters
        if fin.get("promoters"):
            st.subheader("👥 Promoters / Directors")
            import pandas as pd
            st.dataframe(pd.DataFrame(fin["promoters"]), use_container_width=True)

        # Risk factors from text
        if fin.get("risk_factors"):
            st.subheader("⚠️ Risk Factors Identified in Document")
            for r in fin["risk_factors"]:
                st.markdown(f"- {r}")

    else:
        st.info("Upload a PDF or click 'Load Demo Data' to get started.")


# ══════════════════════════════════════════════════════════════════
# PAGE 2 – India Checks
# ══════════════════════════════════════════════════════════════════
elif page == "🇮🇳 India Checks":
    st.title("🇮🇳 India-Specific Checks")
    st.markdown("GST mismatch analysis, circular trading detection, and CIBIL score review.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("GST Data Source")
        gst_mode = st.radio("Select input mode", ["Use sample JSON", "Upload GST JSON"], horizontal=True)

        gst_path = "data/GST/sample_gst.json"
        if gst_mode == "Upload GST JSON":
            uploaded_gst = st.file_uploader("Upload GST JSON", type=["json"])
            if uploaded_gst:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                    tmp.write(uploaded_gst.read())
                    gst_path = tmp.name

    with col2:
        st.subheader("CIBIL Lookup")
        pan_input = st.text_input("PAN Number", value=st.session_state.financials.get("pan", "AABCU9603R"))

    # Bank Statement section
    st.divider()
    st.subheader("🏦 Bank Statement – Circular Trading Check")
    bank_mode = st.radio(
        "Bank Statement source",
        ["Use demo data", "Upload CSV"],
        horizontal=True,
        help="Upload your bank statement CSV to detect potential circular trading."
    )
    bank_file_bytes = None
    if bank_mode == "Upload CSV":
        uploaded_bank = st.file_uploader(
            "Upload Bank Statement CSV",
            type=["csv"],
            help="Columns expected: date, description/narration, debit, credit, balance"
        )
        if uploaded_bank:
            bank_file_bytes = uploaded_bank.read()

    st.divider()

    if st.button("🔍 Run India Checks"):
        with st.spinner("Running GST, CIBIL & Bank checks..."):
            from agents.gst_agent import get_risk_flags, compare_gst
            from utils.bank_parser import parse_bank_statement, check_circular_trading, get_demo_bank_data

            result = get_risk_flags(gst_path, pan_input)
            st.session_state.gst_result = result["gst"]
            st.session_state.cibil = result["cibil"]
            st.session_state.risk_flags = result

            # Bank statement check
            gst_turnover = result["gst"].get("gstr3b_turnover", 0)
            if bank_file_bytes:
                bank_data = parse_bank_statement(bank_file_bytes)
            else:
                bank_data = get_demo_bank_data(gst_turnover or 50_000_000)
            bank_check = check_circular_trading(bank_data, gst_turnover)
            st.session_state.bank_check = bank_check

    if st.session_state.gst_result:
        gst = st.session_state.gst_result
        cibil = st.session_state.cibil
        flags = st.session_state.risk_flags

        # ── GST Section ──
        st.subheader("📋 GST Comparison")
        g1, g2, g3 = st.columns(3)
        with g1:
            from utils.helpers import format_currency
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">GSTR-3B Turnover</div>
                <div class="metric-value">{format_currency(gst.get('gstr3b_turnover',0))}</div>
            </div>""", unsafe_allow_html=True)
        with g2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">GSTR-2A Inward Supplies</div>
                <div class="metric-value">{format_currency(gst.get('gstr2a_turnover',0))}</div>
            </div>""", unsafe_allow_html=True)
        with g3:
            mismatch_pct = gst.get('mismatch_pct', 0)
            color = "#ef4444" if gst.get("is_mismatch") else "#22c55e"
            st.markdown(f"""<div class="metric-card" style="border-color:{color}">
                <div class="metric-label">Mismatch %</div>
                <div class="metric-value" style="color:{color}">{mismatch_pct:.1%}</div>
            </div>""", unsafe_allow_html=True)

        # GST flag
        cls = "flag-warn" if gst.get("is_mismatch") else "flag-ok"
        st.markdown(f'<div class="{cls}">{gst.get("flag_message","")}</div>', unsafe_allow_html=True)

        # ── CIBIL Section ──
        st.subheader("🏛️ CIBIL Score")
        score_val = cibil.get("score", 750)
        rating    = cibil.get("rating", "Good")
        interp    = cibil.get("interpretation", "")
        source    = cibil.get("source", "")

        c1, c2 = st.columns([1, 2])
        with c1:
            pct = (score_val - 300) / 600
            color = "#22c55e" if score_val >= 750 else "#f59e0b" if score_val >= 700 else "#ef4444"
            st.markdown(f"""
            <div style="text-align:center;padding:20px;">
                <div style="font-size:3rem;font-weight:800;color:{color}">{score_val}</div>
                <div style="font-size:1rem;color:{color};margin-top:4px">{rating}</div>
            </div>""", unsafe_allow_html=True)
            st.progress(pct)
        with c2:
            st.markdown(f"**Interpretation:** {interp}")
            st.markdown(f"*{source}*")
            st.markdown("CIBIL score range: **300 – 900**. Scores ≥750 indicate strong creditworthiness.")

        # ── Bank Statement Section ──
        bank = st.session_state.bank_check
        if bank:
            st.subheader("🏦 Bank Statement – Circular Trading Check")
            b1, b2, b3 = st.columns(3)
            with b1:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Bank Credits (Annual)</div>
                    <div class="metric-value">{format_currency(bank.get('bank_credits',0))}</div>
                </div>""", unsafe_allow_html=True)
            with b2:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">GST-Declared Turnover</div>
                    <div class="metric-value">{format_currency(bank.get('gst_turnover',0))}</div>
                </div>""", unsafe_allow_html=True)
            with b3:
                risk_col = "#ef4444" if bank.get("is_flagged") else "#22c55e"
                st.markdown(f"""<div class="metric-card" style="border-color:{risk_col}">
                    <div class="metric-label">Risk Level</div>
                    <div class="metric-value" style="color:{risk_col}">{bank.get('risk_level','—')}</div>
                </div>""", unsafe_allow_html=True)

            cls = "flag-warn" if bank.get("is_flagged") else "flag-ok"
            st.markdown(f'<div class="{cls}">{bank.get("flag_message","")}</div>', unsafe_allow_html=True)

        # ── Risk Flags Summary ──
        st.subheader("🚩 Risk Flags Summary")
        all_flags = flags.get("flags", [])
        if bank and bank.get("is_flagged"):
            all_flags = all_flags + [bank.get("flag_message", "")]
        if all_flags:
            for f in all_flags:
                st.markdown(f'<div class="flag-warn">{f}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="flag-ok">✅ No risk flags raised from GST, CIBIL or bank statement checks.</div>', unsafe_allow_html=True)

    else:
        st.info("Click 'Run India Checks' to analyse GST compliance, circular trading risk, and CIBIL score.")


# ══════════════════════════════════════════════════════════════════
# PAGE 3 – Web Research
# ══════════════════════════════════════════════════════════════════
elif page == "🌐 Web Research":
    st.title("🌐 Web Research & Sentiment Analysis")
    st.markdown("Fetch latest news about the company and sector, then run AI sentiment analysis.")

    company = st.text_input("Company Name", value=st.session_state.company_name or "Sunrise Manufacturing Pvt Ltd")
    sector  = st.text_input("Sector", value=st.session_state.sector or "Manufacturing")
    st.session_state.company_name = company
    st.session_state.sector = sector

    if st.button("🔎 Search News & Analyse Sentiment"):
        with st.spinner("Searching news..."):
            from agents.web_research_agent import search_news
            news = search_news(company, sector)
            st.session_state.news = news

        if news and os.getenv("OPENAI_API_KEY"):
            with st.spinner("Analysing sentiment with AI..."):
                from agents.web_research_agent import WebResearchAgent
                agent = WebResearchAgent()
                sentiment = agent.analyse_sentiment(news)
                st.session_state.sentiment = sentiment
        elif news:
            st.session_state.sentiment = {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "key_positives": ["See headlines below"],
                "key_risks": ["LLM unavailable – manual review required"],
                "summary": "Add OpenAI API key for AI sentiment analysis.",
            }

    # Display results
    if st.session_state.news:
        st.subheader("📰 Latest News Headlines")

        sent = st.session_state.sentiment
        # Sentiment banner
        if sent:
            smemoji = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}.get(sent.get("overall_sentiment","neutral"), "🟡")
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:20px">
                <b>AI Sentiment:</b> {smemoji} {sent.get('overall_sentiment','N/A').capitalize()}
                &nbsp;&nbsp;|&nbsp;&nbsp; Score: <b>{sent.get('sentiment_score',0):.2f}</b> (−1 = very negative, +1 = very positive)
            </div>""", unsafe_allow_html=True)

        # News cards
        for i, article in enumerate(st.session_state.news):
            with st.expander(f"📰 {article['title']}", expanded=(i == 0)):
                st.markdown(f"**Source:** {article.get('source','N/A')} &nbsp;|&nbsp; **Date:** {article.get('date','N/A')}")
                st.markdown(article.get("snippet",""))
                if article.get("link") and article["link"] != "#":
                    st.markdown(f"[Read full article →]({article['link']})")

        if sent:
            st.subheader("🧠 AI Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Key Positives**")
                for p in sent.get("key_positives", []):
                    st.markdown(f"- {p}")
            with col2:
                st.markdown("**⚠️ Key Risks**")
                for r in sent.get("key_risks", []):
                    st.markdown(f"- {r}")

            st.subheader("📋 Summary for CAM")
            st.markdown(f"> {sent.get('summary','')}")
    else:
        st.info("Enter a company name and click 'Search News & Analyse Sentiment'.")


# ══════════════════════════════════════════════════════════════════
# PAGE 4 – Score & Insights
# ══════════════════════════════════════════════════════════════════
elif page == "📊 Score & Insights":
    st.title("📊 Credit Score & Insights")
    st.markdown("Weighted scoring model with factor breakdown and AI explanation.")

    fin = st.session_state.financials
    gst = st.session_state.gst_result
    cibil = st.session_state.cibil
    sent = st.session_state.sentiment

    if not fin:
        st.warning("⚠️ No financial data extracted yet. Go to **Upload & Extract** first.")
    else:
        st.subheader("⚙️ Score Configuration")
        insight_score = st.slider(
            "Primary Insight Score (Analyst Judgment)",
            min_value=0, max_value=100, value=70,
            help="Qualitative analyst judgment (0=very poor, 100=excellent)"
        )

        if st.button("🧮 Compute Credit Score"):
            with st.spinner("Computing score..."):
                from agents.scoring_agent import compute_score, generate_explanation, build_waterfall_chart, compute_verdict
                loan_req = fin.get("loan_amount_requested", 0) or 0
                collateral = st.session_state.get("collateral", "Not specified")
                result = compute_score(fin, gst, cibil, sent, insight_score)
                verdict_data = compute_verdict(result, float(loan_req), collateral)
                explanation = generate_explanation(result, float(loan_req), collateral)
                st.session_state.score_result = result
                st.session_state.score_explanation = explanation
                st.session_state.verdict_data = verdict_data

        if st.session_state.score_result:
            res = st.session_state.score_result
            total = res["total_score"]
            color = res["risk_color"]
            label = res["risk_label"]

            # ── Score Display ──
            st.divider()
            sc1, sc2, sc3 = st.columns([1, 2, 1])
            with sc2:
                st.markdown(f"""
                <div style="text-align:center;padding:30px 0;">
                    <div style="font-size:5rem;font-weight:900;color:{color};
                                text-shadow: 0 0 30px {color}55">{total:.0f}</div>
                    <div style="font-size:1.2rem;color:#94a3b8;margin-top:8px">/ 100</div>
                    <div style="margin-top:12px;font-size:1rem;color:{color};
                                border:1px solid {color};border-radius:20px;
                                display:inline-block;padding:4px 20px">{label}</div>
                </div>""", unsafe_allow_html=True)

            # ── Verdict Banner ──
            vd = st.session_state.get("verdict_data", {})
            if vd:
                st.divider()
                st.subheader("⚖️ Credit Decision")
                vc = vd.get("verdict_color", "#3b82f6")
                st.markdown(f"""
                <div class="metric-card" style="border-color:{vc};text-align:center;padding:28px">
                    <div style="font-size:1.8rem;font-weight:800;color:{vc}">{vd.get('verdict','—')}</div>
                    <div style="margin-top:10px;color:#94a3b8">
                        Recommended Limit: <b style="color:#e2e8f0">{format_currency(vd.get('approved_limit',0))}</b>
                        &nbsp;|&nbsp;
                        Pricing: <b style="color:#e2e8f0">{vd.get('rate_label','—')}</b>
                    </div>
                    <div style="margin-top:8px;color:#cbd5e1;font-size:0.9rem">{vd.get('reason','')}</div>
                </div>""", unsafe_allow_html=True)

            # ── Sub-scores ──
            st.subheader("📊 Factor Breakdown")
            sub = res["sub_scores"]
            weights = res["weights"]

            factor_labels = {
                "financial_health": "Financial Health",
                "web_sentiment":    "Web Sentiment",
                "primary_insight":  "Primary Insight",
                "gst_compliance":   "GST Compliance",
                "legal_cibil":      "CIBIL / Legal",
            }

            cols = st.columns(5)
            for i, (key, label_txt) in enumerate(factor_labels.items()):
                with cols[i]:
                    val = sub[key]
                    c = "#22c55e" if val >= 70 else "#f59e0b" if val >= 45 else "#ef4444"
                    st.markdown(f"""<div class="metric-card" style="text-align:center">
                        <div class="metric-label">{label_txt}</div>
                        <div class="metric-value" style="color:{c}">{val:.0f}</div>
                        <div style="color:#64748b;font-size:0.75rem">wt: {weights[key]}%</div>
                    </div>""", unsafe_allow_html=True)

            # ── Waterfall Chart ──
            st.subheader("📉 Score Waterfall Chart")
            from agents.scoring_agent import build_waterfall_chart
            fig = build_waterfall_chart(res)
            st.plotly_chart(fig, use_container_width=True)

            # ── LLM Explanation ──
            st.subheader("💬 AI Score Explanation")
            explanation_text = st.session_state.score_explanation
            st.markdown(f"""
            <div class="metric-card" style="border-color:#3b82f6">
                <p style="color:#cbd5e1;line-height:1.7;font-size:1rem">{explanation_text}</p>
            </div>""", unsafe_allow_html=True)

        else:
            st.info("Configure parameters above and click 'Compute Credit Score'.")


# ══════════════════════════════════════════════════════════════════
# PAGE 5 – Generate CAM
# ══════════════════════════════════════════════════════════════════
elif page == "📄 Generate CAM":
    st.title("📄 Generate Credit Appraisal Memo (CAM)")
    st.markdown("Produce a professional Word document with all extracted data and insights.")

    fin   = st.session_state.financials
    gst   = st.session_state.gst_result
    sent  = st.session_state.sentiment
    score = st.session_state.score_result
    expl  = st.session_state.score_explanation

    if not fin:
        st.warning("⚠️ Please complete at least **Upload & Extract** (Page 1) before generating CAM.")
    else:
        st.subheader("📝 CAM Preview / Override")

        col1, col2 = st.columns(2)
        with col1:
            co_name = st.text_input("Company Name", value=fin.get("company_name", ""))
            gstin   = st.text_input("GSTIN", value=fin.get("gstin", "N/A"))
            pan     = st.text_input("PAN", value=fin.get("pan", "N/A"))
        with col2:
            from utils.helpers import format_currency
            loan_amt = st.text_input("Loan Amount (₹)", value=str(fin.get("loan_amount_requested", 0) or 0))
            loan_pur = st.text_input("Loan Purpose", value=fin.get("loan_purpose", "Working Capital"))
            cr_score = st.number_input("Credit Score", value=float(score.get("total_score", 0)) if score else 0.0, min_value=0.0, max_value=100.0)

        # Collateral input
        collateral_input = st.text_area(
            "C4 – Collateral Details",
            value=st.session_state.get("collateral", ""),
            placeholder="e.g. Primary: Residential property at Pune, market value ₹2.5 Cr, first charge. Collateral: FD of ₹50L pledged.",
            height=80,
            help="Describe the security offered (property, FD, machinery, guarantor, etc.)"
        )
        st.session_state.collateral = collateral_input

        recommendation = st.text_area(
            "Recommendation / Score Explanation",
            value=expl or "Based on the analysis, the borrower presents an acceptable credit risk profile.",
            height=120,
        )

        st.divider()

        if st.button("📄 Generate CAM Document"):
            with st.spinner("Generating Credit Appraisal Memo..."):
                from agents.cam_agent import build_cam_data, generate_cam, create_template, TEMPLATE_PATH
                import os

                # Ensure template exists
                if not os.path.exists(TEMPLATE_PATH):
                    create_template()

                # Override editable fields
                fin_override = {**fin,
                    "company_name": co_name,
                    "gstin": gstin,
                    "pan": pan,
                    "loan_amount_requested": float(loan_amt) if loan_amt else 0,
                    "loan_purpose": loan_pur,
                }

                cam_data = build_cam_data(
                    financials=fin_override,
                    score_result=score or {"total_score": cr_score},
                    gst_result=gst,
                    sentiment_result=sent,
                    score_explanation=recommendation,
                    collateral=collateral_input,
                    bank_check=st.session_state.get("bank_check"),
                    verdict_data=st.session_state.get("verdict_data"),
                )

                docx_bytes = generate_cam(cam_data)

            st.success("✅ CAM generated successfully!")

            st.download_button(
                label="⬇️ Download CAM_Output.docx",
                data=docx_bytes,
                file_name=f"CAM_{co_name.replace(' ','_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            # ── Preview ──
            st.subheader("📋 CAM Preview")
            preview_data = {
                "Company Name": co_name,
                "GSTIN / PAN": f"{gstin} / {pan}",
                "Loan Amount": format_currency(float(loan_amt) if loan_amt else 0),
                "Loan Purpose": loan_pur,
                "Credit Score": f"{cr_score:.0f} / 100",
                "Risk Category": score.get("risk_label", "—") if score else "—",
            }

            import pandas as pd
            df = pd.DataFrame(list(preview_data.items()), columns=["Field", "Value"])
            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("📝 Recommendation Text"):
                st.write(recommendation)

            if gst:
                with st.expander("🇮🇳 GST Compliance Note"):
                    st.write(gst.get("flag_message", "No GST data."))

            if sent:
                with st.expander("🌐 Market Sentiment"):
                    st.write(sent.get("summary", "No sentiment data."))

        else:
            # Quick checklist
            st.subheader("📋 Completion Checklist")
            checks = [
                ("Financial Data Extracted", bool(fin)),
                ("India Checks Run",         bool(gst)),
                ("News & Sentiment Done",    bool(sent)),
                ("Score Computed",           bool(score)),
            ]
            for label, done in checks:
                icon = "✅" if done else "⬜"
                st.markdown(f"{icon} {label}")
