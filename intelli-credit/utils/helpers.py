"""
utils/helpers.py
Shared helper utilities for IntelliCredit.
"""

import os
import json
import re
from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: str = "") -> str:
    """Safely retrieve an environment variable."""
    return os.getenv(key, default)


def safe_json_parse(text: str) -> dict:
    """
    Attempt to parse a JSON string from LLM output.
    Strips markdown code fences if present.
    """
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find the first JSON-like block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


def format_currency(amount: float, symbol: str = "₹") -> str:
    """Format a number as Indian currency (lakhs/crores)."""
    if amount >= 10_000_000:
        return f"{symbol}{amount/10_000_000:.2f} Cr"
    elif amount >= 100_000:
        return f"{symbol}{amount/100_000:.2f} L"
    else:
        return f"{symbol}{amount:,.0f}"


def risk_label(score: float) -> str:
    """Convert numeric score to risk label."""
    if score >= 75:
        return "Low Risk"
    elif score >= 50:
        return "Moderate Risk"
    elif score >= 30:
        return "High Risk"
    else:
        return "Very High Risk"


def risk_color(score: float) -> str:
    """Return a color hex for a given score."""
    if score >= 75:
        return "#22c55e"   # green
    elif score >= 50:
        return "#f59e0b"   # amber
    elif score >= 30:
        return "#ef4444"   # red
    else:
        return "#7f1d1d"   # dark red
