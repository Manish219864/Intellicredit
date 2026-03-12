"""
utils/bank_parser.py
Bank Statement Parser – Circular Trading / Revenue Inflation Detection

Accepts a CSV bank statement and compares total credits against
GST-declared turnover to flag potential revenue inflation or circular trading.

Expected CSV columns (flexible matching):
  date, description/narration, debit, credit, balance
"""

import io
import logging
from typing import Union

logger = logging.getLogger(__name__)

CIRCULAR_TRADING_THRESHOLD = 0.15  # 15% excess credits over GST turnover → flag

# ─────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────

def parse_bank_statement(file: Union[bytes, io.BytesIO, str]) -> dict:
    """
    Parse a CSV bank statement and return aggregated credit/debit totals.

    Returns:
        {
            "total_credits":  float,   # sum of all credit entries (INR)
            "total_debits":   float,
            "num_transactions": int,
            "rows":           list[dict],
            "error":          str | None
        }
    """
    try:
        import pandas as pd

        if isinstance(file, bytes):
            df = pd.read_csv(io.BytesIO(file))
        elif isinstance(file, io.BytesIO):
            df = pd.read_csv(file)
        else:
            df = pd.read_csv(file)

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Find credit column (flexible naming)
        credit_col = _find_col(df.columns, ["credit", "credits", "deposit", "cr_amount", "cr"])
        debit_col  = _find_col(df.columns, ["debit", "debits", "withdrawal", "dr_amount", "dr"])

        if not credit_col:
            return {"total_credits": 0, "total_debits": 0, "num_transactions": len(df),
                    "rows": df.to_dict("records"), "error": "Could not identify 'credit' column."}

        df[credit_col] = pd.to_numeric(df[credit_col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
        total_credits  = float(df[credit_col].sum())
        total_debits   = 0.0

        if debit_col:
            df[debit_col] = pd.to_numeric(df[debit_col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
            total_debits = float(df[debit_col].sum())

        return {
            "total_credits": total_credits,
            "total_debits": total_debits,
            "num_transactions": len(df),
            "rows": df.head(20).to_dict("records"),   # preview only
            "error": None,
        }

    except Exception as e:
        logger.error("Bank statement parsing failed: %s", e)
        return {"total_credits": 0, "total_debits": 0, "num_transactions": 0, "rows": [], "error": str(e)}


def _find_col(columns, candidates: list) -> str | None:
    """Return the first column name that matches any candidate string."""
    for c in columns:
        for cand in candidates:
            if cand in c:
                return c
    return None


# ─────────────────────────────────────────────────────
# Circular Trading / Revenue Inflation Check
# ─────────────────────────────────────────────────────

def check_circular_trading(bank_data: dict, gst_turnover: float) -> dict:
    """
    Compare bank statement total credits against GST-declared turnover.

    A significant excess of bank credits over GST turnover suggests:
      • Revenue inflation / circular trading
      • Unrecorded liabilities or pass-through entries

    Args:
        bank_data:    output from parse_bank_statement()
        gst_turnover: GSTR-3B taxable turnover (INR) — from gst_agent

    Returns:
        {
            "bank_credits":      float,
            "gst_turnover":      float,
            "excess":            float,   # bank_credits - gst_turnover
            "excess_pct":        float,   # excess / gst_turnover
            "is_flagged":        bool,
            "risk_level":        str,     # "Low" | "Medium" | "High"
            "flag_message":      str,
        }
    """
    bank_credits = bank_data.get("total_credits", 0)

    if gst_turnover <= 0:
        return {
            "bank_credits": bank_credits,
            "gst_turnover": gst_turnover,
            "excess": 0,
            "excess_pct": 0,
            "is_flagged": False,
            "risk_level": "Low",
            "flag_message": "GST turnover is zero – circular trading check skipped.",
        }

    excess     = bank_credits - gst_turnover
    excess_pct = excess / gst_turnover if gst_turnover else 0

    is_flagged = excess_pct > CIRCULAR_TRADING_THRESHOLD

    if excess_pct <= 0.05:
        risk_level = "Low"
    elif excess_pct <= 0.15:
        risk_level = "Medium"
    elif excess_pct <= 0.35:
        risk_level = "High"
    else:
        risk_level = "Very High"

    if is_flagged:
        flag_message = (
            f"🚨 Circular Trading / Revenue Inflation Risk: "
            f"Bank credits (₹{bank_credits:,.0f}) exceed GST-declared turnover "
            f"(₹{gst_turnover:,.0f}) by {excess_pct:.1%}. "
            f"Excess: ₹{excess:,.0f}. "
            f"Threshold: {CIRCULAR_TRADING_THRESHOLD:.0%}. Risk Level: {risk_level}."
        )
    else:
        flag_message = (
            f"✅ Bank credits and GST turnover are consistent. "
            f"Deviation: {excess_pct:.1%} (threshold: {CIRCULAR_TRADING_THRESHOLD:.0%})."
        )

    return {
        "bank_credits": bank_credits,
        "gst_turnover": gst_turnover,
        "excess": excess,
        "excess_pct": round(excess_pct, 4),
        "is_flagged": is_flagged,
        "risk_level": risk_level,
        "flag_message": flag_message,
    }


# ─────────────────────────────────────────────────────
# Sample / Demo bank data
# ─────────────────────────────────────────────────────

def get_demo_bank_data(gst_turnover: float = 50_000_000) -> dict:
    """
    Returns a plausible demo bank summary (slightly over GST to show mild flag).
    """
    demo_credits = gst_turnover * 1.08   # 8% excess – within threshold, clean
    return {
        "total_credits": demo_credits,
        "total_debits": demo_credits * 0.85,
        "num_transactions": 248,
        "rows": [],
        "error": None,
        "_demo": True,
    }
