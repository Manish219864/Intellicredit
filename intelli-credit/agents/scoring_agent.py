"""
agents/scoring_agent.py
Phase 4, Day 6 – Scoring Engine & Explainability

Task 1: Define factor weights
Task 2: Compute weighted score (0–100)
Task 3: Plotly waterfall chart
Task 4: LLM-generated natural-language explanation
"""

import logging
from typing import Optional

import plotly.graph_objects as go
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.helpers import get_env, risk_label, risk_color

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Task 1 (Day 6): Score Weights
# ──────────────────────────────────────────────

WEIGHTS = {
    "financial_health": 40,   # Financial ratios & KPIs
    "web_sentiment":    20,   # News / sector sentiment
    "primary_insight":  15,   # Analyst-provided qualitative insight
    "gst_compliance":   15,   # GST mismatch penalty
    "legal_cibil":      10,   # CIBIL score
}

# ──────────────────────────────────────────────
# Task 2 (Day 6): Score Computation
# ──────────────────────────────────────────────

def _compute_financial_health(financials: dict) -> float:
    """
    Convert financial ratios to a 0–100 sub-score.
    Uses: current_ratio, debt_equity_ratio, interest_coverage, net_profit margin.
    """
    score = 50.0  # baseline

    current_ratio = financials.get("current_ratio") or financials.get("current_ratio", 0)
    d_e_ratio = financials.get("debt_equity_ratio") or 0
    icr = financials.get("interest_coverage_ratio") or financials.get("interest_coverage") or 0
    net_profit = financials.get("net_profit") or 0
    revenue = financials.get("total_revenue") or 1  # avoid div/0

    # Current ratio: ideal 1.5–2.5
    try:
        cr = float(current_ratio)
        if cr >= 2.0:
            score += 15
        elif cr >= 1.5:
            score += 10
        elif cr >= 1.0:
            score += 5
        else:
            score -= 10
    except (TypeError, ValueError):
        pass

    # Debt/Equity: lower is better
    try:
        de = float(d_e_ratio)
        if de <= 1.0:
            score += 15
        elif de <= 2.0:
            score += 7
        elif de <= 3.0:
            score += 0
        else:
            score -= 10
    except (TypeError, ValueError):
        pass

    # Interest Coverage: >3 is good
    try:
        ic = float(icr)
        if ic >= 4:
            score += 15
        elif ic >= 3:
            score += 10
        elif ic >= 1.5:
            score += 5
        else:
            score -= 15
    except (TypeError, ValueError):
        pass

    # Net profit margin
    try:
        margin = float(net_profit) / float(revenue)
        if margin >= 0.10:
            score += 15
        elif margin >= 0.05:
            score += 8
        elif margin >= 0:
            score += 2
        else:
            score -= 15
    except (TypeError, ValueError, ZeroDivisionError):
        pass

    return max(0.0, min(100.0, score))


def _compute_gst_score(gst_result: dict) -> float:
    """Convert GST mismatch result to a 0–100 sub-score."""
    if not gst_result:
        return 60.0  # neutral if no data
    mismatch_pct = gst_result.get("mismatch_pct", 0)
    if mismatch_pct <= 0.05:
        return 100.0
    elif mismatch_pct <= 0.10:
        return 70.0
    elif mismatch_pct <= 0.20:
        return 40.0
    else:
        return 10.0


def _compute_cibil_score(cibil: dict) -> float:
    """Convert CIBIL score to a 0–100 sub-score."""
    raw = cibil.get("score", 700)
    # Map 300–900 range to 0–100
    return max(0.0, min(100.0, (raw - 300) / 6.0))


def _sentiment_to_score(sentiment: dict) -> float:
    """Convert LLM sentiment result to a 0–100 sub-score."""
    score_map = {"positive": 85.0, "neutral": 55.0, "negative": 25.0}
    label = sentiment.get("overall_sentiment", "neutral")
    base = score_map.get(label, 55.0)
    # Fine-tune with numeric score (-1 to 1)
    numeric = float(sentiment.get("sentiment_score", 0))
    return max(0.0, min(100.0, base + numeric * 10))


def compute_score(
    financials: dict,
    gst_result: dict,
    cibil: dict,
    sentiment: dict,
    primary_insight_score: float = 70.0,
) -> dict:
    """
    Task 2 (Day 6): Compute overall credit score (0–100).

    Args:
        financials: extracted financial KPIs
        gst_result: output from gst_agent.compare_gst()
        cibil: output from gst_agent.get_mock_cibil()
        sentiment: output from web_research_agent
        primary_insight_score: manually provided qualitative score (0–100)

    Returns dict with individual sub-scores, weighted contributions, and total.
    """
    sub_scores = {
        "financial_health": _compute_financial_health(financials),
        "web_sentiment": _sentiment_to_score(sentiment),
        "primary_insight": float(primary_insight_score),
        "gst_compliance": _compute_gst_score(gst_result),
        "legal_cibil": _compute_cibil_score(cibil),
    }

    total = sum(
        sub_scores[factor] * (WEIGHTS[factor] / 100)
        for factor in WEIGHTS
    )

    contributions = {
        factor: round(sub_scores[factor] * (WEIGHTS[factor] / 100), 2)
        for factor in WEIGHTS
    }

    return {
        "total_score": round(total, 1),
        "sub_scores": sub_scores,
        "contributions": contributions,
        "weights": WEIGHTS,
        "risk_label": risk_label(total),
        "risk_color": risk_color(total),
    }


# ──────────────────────────────────────────────
# Task 3 (Day 6): Plotly Waterfall Chart
# ──────────────────────────────────────────────

def build_waterfall_chart(score_result: dict) -> go.Figure:
    """
    Task 3 (Day 6): Waterfall chart showing contribution of each factor.
    """
    contributions = score_result["contributions"]
    labels = list(contributions.keys())
    values = list(contributions.values())

    pretty_labels = {
        "financial_health": "Financial Health",
        "web_sentiment": "Web Sentiment",
        "primary_insight": "Primary Insight",
        "gst_compliance": "GST Compliance",
        "legal_cibil": "CIBIL / Legal",
    }

    display_labels = [pretty_labels.get(k, k) for k in labels]

    # Color: positive contribution = green, negative = red
    bar_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in values]

    fig = go.Figure(
        go.Waterfall(
            name="Score Breakdown",
            orientation="v",
            measure=["relative"] * len(labels) + ["total"],
            x=display_labels + ["Total Score"],
            textposition="outside",
            text=[f"+{v:.1f}" if v >= 0 else f"{v:.1f}" for v in values]
                 + [f"{score_result['total_score']:.1f}"],
            y=values + [score_result["total_score"]],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#22c55e"}},
            decreasing={"marker": {"color": "#ef4444"}},
            totals={"marker": {"color": "#3b82f6"}},
        )
    )

    fig.update_layout(
        title={
            "text": "Credit Score – Factor Contribution",
            "x": 0.5,
            "xanchor": "center",
        },
        yaxis_title="Score Points",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font={"color": "#e2e8f0"},
        showlegend=False,
        height=420,
    )

    return fig


# ──────────────────────────────────────────────
# Task 4 (Day 6): LLM Explanation
# ──────────────────────────────────────────────

EXPLANATION_TEMPLATE = """
You are a senior credit analyst at an Indian bank writing a recommendation for a Credit Appraisal Memo (CAM).
Based on the scoring data below, write a 3-4 sentence recommendation that includes:
1. A clear VERDICT: APPROVE, CONDITIONAL APPROVE, or REJECT.
2. If APPROVE or CONDITIONAL APPROVE: recommended loan limit (as a % of requested amount) and suggested interest rate premium (e.g., Base Rate + 75 bps).
3. The single biggest positive driver and the single biggest risk factor.
4. If REJECT: one concise sentence citing the dominant negative factors despite any positives.

Scoring Data:
- Overall Score: {total_score}/100 ({risk_label})
- Loan Amount Requested: ₹{loan_amount_requested}
- Financial Health sub-score: {financial_health:.1f}/100 (weight 40%)
- GST Compliance sub-score: {gst_compliance:.1f}/100 (weight 15%)
- Web Sentiment sub-score: {web_sentiment:.1f}/100 (weight 20%)
- Primary Insight sub-score: {primary_insight:.1f}/100 (weight 15%)
- CIBIL / Legal sub-score: {legal_cibil:.1f}/100 (weight 10%)
- Collateral available: {collateral}

Verdict rules:
  score >= 75  → APPROVE at 100% of requested amount, Base Rate + 0-50 bps
  50-74        → CONDITIONAL APPROVE at 75-90% of requested amount, Base Rate + 50-150 bps
  30-49        → REFER TO CREDIT COMMITTEE (high risk)
  < 30         → REJECT

Write in a professional tone suitable for a bank credit committee. Be specific and cite factor names.
"""


def compute_verdict(score_result: dict, loan_amount_requested: float = 0,
                      collateral: str = "Not specified") -> dict:
    """
    Standalone verdict engine — does NOT require LLM.
    Returns a structured verdict dict suitable for the CAM and UI.

    Returns:
        {
            "verdict":          str,   # APPROVE / CONDITIONAL APPROVE / REFER / REJECT
            "verdict_color":    str,   # hex color
            "approved_limit":   float, # recommended loan limit in INR
            "rate_premium_bps": int,   # basis points above base rate
            "rate_label":       str,   # e.g. "Base Rate + 100 bps"
            "reason":           str,   # plain-English one-liner
        }
    """
    total = score_result.get("total_score", 0)
    sub   = score_result.get("sub_scores", {})

    # Find the weakest and strongest factors
    if sub:
        worst_factor = min(sub, key=lambda k: sub[k])
        best_factor  = max(sub, key=lambda k: sub[k])
    else:
        worst_factor = "financials"
        best_factor  = "financials"

    factor_names = {
        "financial_health": "Financial Health",
        "web_sentiment":    "Web Sentiment",
        "primary_insight":  "Primary Insight (site visit)",
        "gst_compliance":   "GST Compliance",
        "legal_cibil":      "CIBIL / Legal standing",
    }

    if total >= 75:
        verdict         = "APPROVE"
        verdict_color   = "#22c55e"
        approved_limit  = loan_amount_requested
        rate_bps        = 50
        reason          = (
            f"Strong {factor_names.get(best_factor, best_factor)} supports approval at "
            f"full requested limit."
        )
    elif total >= 50:
        verdict         = "CONDITIONAL APPROVE"
        verdict_color   = "#f59e0b"
        mult            = 0.75 + (total - 50) * 0.006  # 0.75 at 50 → 0.90 at 75
        approved_limit  = loan_amount_requested * mult
        rate_bps        = int(200 - (total - 50) * 2)   # 200 bps at 50 → 100 bps at 75
        reason          = (
            f"Moderate risk profile. {factor_names.get(worst_factor, worst_factor)} "
            f"is the primary concern. Recommend approval at reduced limit with enhanced "
            f"monitoring and collateral verification."
        )
    elif total >= 30:
        verdict         = "REFER TO CREDIT COMMITTEE"
        verdict_color   = "#ef4444"
        approved_limit  = 0
        rate_bps        = 0
        reason          = (
            f"High risk — {factor_names.get(worst_factor, worst_factor)} score is critically "
            f"low ({sub.get(worst_factor, 0):.0f}/100). Refer for senior credit committee review "
            f"with enhanced due diligence."
        )
    else:
        verdict         = "REJECT"
        verdict_color   = "#7f1d1d"
        approved_limit  = 0
        rate_bps        = 0
        reason          = (
            f"Rejected due to {factor_names.get(worst_factor, worst_factor)} "
            f"({sub.get(worst_factor, 0):.0f}/100) despite "
            f"{factor_names.get(best_factor, best_factor)} "
            f"({sub.get(best_factor, 0):.0f}/100). Risk profile is unacceptable."
        )

    rate_label = f"Base Rate + {rate_bps} bps" if rate_bps > 0 else "N/A (not approved)"

    return {
        "verdict":          verdict,
        "verdict_color":    verdict_color,
        "approved_limit":   round(approved_limit, 0),
        "rate_premium_bps": rate_bps,
        "rate_label":       rate_label,
        "reason":           reason,
    }


def generate_explanation(score_result: dict, loan_amount_requested: float = 0,
                         collateral: str = "Not specified") -> str:
    """
    Task 4 (Day 6): Generate a natural-language explanation of the score.
    Uses compute_verdict() for a rule-based fallback when LLM is unavailable.
    """
    api_key = get_env("OPENAI_API_KEY")

    # Always compute the rule-based verdict first (used in fallback)
    verdict_data = compute_verdict(score_result, loan_amount_requested, collateral)

    sub = score_result.get("sub_scores", {})
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key=api_key)
        prompt = PromptTemplate(
            input_variables=["total_score", "risk_label",
                             "financial_health", "gst_compliance",
                             "web_sentiment", "primary_insight", "legal_cibil",
                             "loan_amount_requested", "collateral"],
            template=EXPLANATION_TEMPLATE,
        )
        chain = prompt | llm | StrOutputParser()
        explanation = chain.invoke({
            "total_score":            score_result["total_score"],
            "risk_label":             score_result["risk_label"],
            "financial_health":       sub.get("financial_health", 0),
            "gst_compliance":         sub.get("gst_compliance", 0),
            "web_sentiment":          sub.get("web_sentiment", 0),
            "primary_insight":        sub.get("primary_insight", 0),
            "legal_cibil":            sub.get("legal_cibil", 0),
            "loan_amount_requested":  f"{loan_amount_requested:,.0f}",
            "collateral":             collateral,
        })
        return explanation.strip()
    except Exception as e:
        logger.error("LLM explanation failed: %s", e)
        # Rule-based fallback using compute_verdict()
        total = score_result["total_score"]
        label = score_result["risk_label"]
        v     = verdict_data
        return (
            f"VERDICT: {v['verdict']}\n"
            f"Credit Score: {total:.1f}/100 ({label}).\n"
            f"{v['reason']}\n"
            f"Recommended Limit: ₹{v['approved_limit']:,.0f}  |  "
            f"Pricing: {v['rate_label']}"
        )
