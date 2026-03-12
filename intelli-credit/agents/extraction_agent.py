"""
agents/extraction_agent.py
Phase 1, Day 3 – Structured Data Extraction via LLM

Uses LangChain PromptTemplate + ChatOpenAI to extract key financial fields
from raw text and returns them as a structured Python dictionary.
"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.helpers import get_env, safe_json_parse

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Prompt Templates
# ──────────────────────────────────────────────

FINANCIAL_EXTRACTION_TEMPLATE = """
You are a financial analyst assistant specializing in Indian credit appraisal.
Extract the following fields from the provided text and return ONLY valid JSON.

Fields to extract:
- company_name (string)
- financial_year (string, e.g. "2023-24")
- total_revenue (number, in INR)
- net_profit (number, in INR)
- ebitda (number, in INR, if available)
- total_loans (number, in INR)
- current_ratio (number)
- debt_equity_ratio (number)
- interest_coverage_ratio (number)
- total_assets (number, in INR)
- net_worth (number, in INR)
- loan_amount_requested (number, in INR, if mentioned)
- loan_purpose (string, if mentioned)

If a field is not found, use null.

Text:
{text}

Return ONLY a JSON object with these fields. No explanation, no markdown.
"""

PROMOTER_EXTRACTION_TEMPLATE = """
You are a financial analyst assistant.
Extract information about the promoters / directors from the text below.
Return ONLY valid JSON as a list of objects with fields:
  - name (string)
  - designation (string)
  - din (string, if available)
  - shareholding_percent (number, if available)

Text:
{text}

Return ONLY a JSON array. No explanation, no markdown.
"""

RISK_EXTRACTION_TEMPLATE = """
You are a senior credit analyst. Based on the following text from a company's financial document,
identify the top 5 key risk factors. Return ONLY a JSON array of strings, each string being a concise risk factor.

Text:
{text}

Return ONLY a JSON array of strings. No explanation, no markdown.
"""

# ──────────────────────────────────────────────
# Agent Class
# ──────────────────────────────────────────────

class ExtractionAgent:
    """
    Task 1 & 2 (Day 3): LLM-powered structured data extraction.
    Use extract_all() for a complete extraction run.
    """

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0):
        api_key = get_env("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )

    def _run_chain(self, template: str, text: str) -> str:
        """Run a prompt | llm | parser chain and return raw string output."""
        prompt = PromptTemplate(input_variables=["text"], template=template)
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({"text": text[:4000]})  # stay within token limits
        return result

    def extract_financials(self, text: str) -> dict:
        """
        Task 1 (Day 3): Extract financial KPIs from raw PDF text.
        Returns a dictionary of financial fields.
        """
        raw = self._run_chain(FINANCIAL_EXTRACTION_TEMPLATE, text)
        data = safe_json_parse(raw)
        logger.info("Extracted %d financial fields", len(data))
        return data

    def extract_promoters(self, text: str) -> list:
        """Extract promoter / director information."""
        raw = self._run_chain(PROMOTER_EXTRACTION_TEMPLATE, text)
        result = safe_json_parse(raw)
        # The LLM might return a list wrapped in a dict key
        if isinstance(result, list):
            return result
        return result.get("promoters", result.get("directors", []))

    def extract_risks(self, text: str) -> list[str]:
        """Extract textual risk factors from financial documents."""
        raw = self._run_chain(RISK_EXTRACTION_TEMPLATE, text)
        result = safe_json_parse(raw)
        if isinstance(result, list):
            return [str(r) for r in result]
        return []

    def extract_all(self, text: str) -> dict:
        """
        Task 2 (Day 3): Single-call full extraction.
        Returns a merged dict with all extracted data.
        """
        financials = self.extract_financials(text)
        promoters = self.extract_promoters(text)
        risks = self.extract_risks(text)
        return {
            **financials,
            "promoters": promoters,
            "risk_factors": risks,
        }


# ──────────────────────────────────────────────
# Demo fallback: load from JSON if no PDF given
# ──────────────────────────────────────────────

def load_sample_data(json_path: str = "data/annual_reports/sample_borrower.json") -> dict:
    """Load pre-structured borrower data for demo/testing purposes."""
    import json, os
    if os.path.exists(json_path):
        with open(json_path) as f:
            raw = json.load(f)
        # Flatten for compatibility
        flat = {"company_name": raw.get("company"), **raw.get("financials", {})}
        flat["loan_amount_requested"] = raw.get("loan_request", {}).get("amount")
        flat["loan_purpose"] = raw.get("loan_request", {}).get("purpose")
        flat["promoters"] = raw.get("promoters", [])
        return flat
    return {}
