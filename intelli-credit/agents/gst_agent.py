"""
agents/gst_agent.py
Phase 2, Day 4 – India-Specific GST Mismatch Check

Compares GSTR-3B (outward supplies filed by taxpayer)
against GSTR-2A (auto-populated inward supplies) and
flags a mismatch if turnover deviation exceeds 10%.

Also provides a mock CIBIL score for demonstration.
"""

import json
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

MISMATCH_THRESHOLD = 0.10  # 10%


# ──────────────────────────────────────────────
# Task 1 (Day 4): GST Mismatch Check
# ──────────────────────────────────────────────

def load_gst_data(path: str) -> dict:
    """Load GST data from a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load GST data from %s: %s", path, e)
        return {}


def compare_gst(gstr3b: dict, gstr2a: dict) -> dict:
    """
    Task 1 (Day 4): Compare GSTR-3B turnover vs GSTR-2A inward supplies.

    Args:
        gstr3b: dict with at least 'taxable_turnover'
        gstr2a: dict with at least 'inward_supplies_turnover'

    Returns:
        {
            "gstr3b_turnover": float,
            "gstr2a_turnover": float,
            "difference": float,
            "mismatch_pct": float,
            "is_mismatch": bool,
            "flag_message": str,
        }
    """
    t3b = float(gstr3b.get("taxable_turnover", 0))
    t2a = float(gstr2a.get("inward_supplies_turnover", 0))

    if t3b == 0:
        return {
            "gstr3b_turnover": 0,
            "gstr2a_turnover": t2a,
            "difference": 0,
            "mismatch_pct": 0,
            "is_mismatch": False,
            "flag_message": "GSTR-3B turnover is zero – cannot compute mismatch.",
        }

    diff = abs(t3b - t2a)
    mismatch_pct = diff / t3b

    is_mismatch = mismatch_pct > MISMATCH_THRESHOLD

    flag_message = (
        f"⚠️ GST Mismatch Detected: GSTR-3B turnover (₹{t3b:,.0f}) vs "
        f"GSTR-2A inward supplies (₹{t2a:,.0f}). "
        f"Deviation: {mismatch_pct:.1%} (threshold: {MISMATCH_THRESHOLD:.0%})."
        if is_mismatch
        else f"✅ GST figures are consistent. Deviation: {mismatch_pct:.1%}."
    )

    return {
        "gstr3b_turnover": t3b,
        "gstr2a_turnover": t2a,
        "difference": diff,
        "mismatch_pct": round(mismatch_pct, 4),
        "is_mismatch": is_mismatch,
        "flag_message": flag_message,
    }


def check_gst_from_json(json_path: str) -> dict:
    """
    Convenience wrapper: load a combined GST JSON and run comparison.

    The JSON is expected to have 'gstr3b' and 'gstr2a' keys.
    """
    data = load_gst_data(json_path)
    gstr3b = data.get("gstr3b", {})
    gstr2a = data.get("gstr2a", {})
    return compare_gst(gstr3b, gstr2a)


# ──────────────────────────────────────────────
# Task 2 (Day 4): Mock CIBIL Score
# ──────────────────────────────────────────────

def get_mock_cibil(pan: str = "") -> dict:
    """
    Task 2 (Day 4): Return a placeholder CIBIL score.
    In production this would call a bureau API.
    """
    # Deterministic but varied mock score based on PAN
    base = 700
    if pan:
        offset = sum(ord(c) for c in pan) % 51  # 0 – 50
        score = base + offset
    else:
        score = 750

    if score >= 750:
        rating = "Good"
        interpretation = "Low default risk"
    elif score >= 700:
        rating = "Fair"
        interpretation = "Moderate risk – monitor closely"
    else:
        rating = "Poor"
        interpretation = "High risk – perform enhanced due diligence"

    return {
        "score": score,
        "rating": rating,
        "interpretation": interpretation,
        "source": "Simulated (CIBIL API placeholder)",
    }


# ──────────────────────────────────────────────
# Task 3 (Day 4): Combined Risk Flags
# ──────────────────────────────────────────────

def get_risk_flags(gst_json_path: str = "data/GST/sample_gst.json",
                   pan: str = "") -> dict:
    """
    Returns combined India-specific risk flags for UI display.
    """
    gst_result = check_gst_from_json(gst_json_path)
    cibil = get_mock_cibil(pan)

    flags = []
    if gst_result.get("is_mismatch"):
        flags.append(gst_result["flag_message"])
    if cibil["score"] < 700:
        flags.append(f"⚠️ CIBIL score is {cibil['score']} ({cibil['rating']}) – {cibil['interpretation']}.")

    return {
        "gst": gst_result,
        "cibil": cibil,
        "flags": flags,
        "has_flags": len(flags) > 0,
    }
