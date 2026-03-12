"""
agents/web_research_agent.py
Phase 3, Day 5 – Web Research & Sentiment Analysis

Task 1-2: Searches Google News via SerpAPI for the company name / sector.
Task 3: Feeds top 5 headlines to LLM for sentiment analysis and risk extraction.
"""

import logging
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.helpers import get_env, safe_json_parse

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Task 2 (Day 5): Google News Search via SerpAPI
# ──────────────────────────────────────────────

def search_news(company_name: str, sector: str = "", num_results: int = 5) -> list[dict]:
    """
    Task 1 & 2 (Day 5): Search Google News for company and sector news.

    Returns a list of dicts with 'title', 'snippet', 'source', 'date', 'link'.
    Falls back to mock data if SerpAPI key is missing.
    """
    api_key = get_env("SERPAPI_KEY")

    if not api_key or api_key == "your_serpapi_key_here":
        logger.warning("SERPAPI_KEY not set – returning mock news data.")
        return _mock_news(company_name, sector)

    try:
        from serpapi import GoogleSearch

        query = f"{company_name}"
        if sector:
            query += f" OR {sector}"

        params = {
            "q": query,
            "tbm": "nws",
            "api_key": api_key,
            "num": num_results,
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        news = results.get("news_results", [])

        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
                "link": item.get("link", ""),
            }
            for item in news[:num_results]
        ]
    except ImportError:
        logger.error("serpapi package not installed.")
        return _mock_news(company_name, sector)
    except Exception as e:
        logger.error("SerpAPI search failed: %s", e)
        return _mock_news(company_name, sector)


def _mock_news(company_name: str, sector: str = "") -> list[dict]:
    """Return static mock news articles for demo purposes."""
    sector_label = sector or "Manufacturing"
    return [
        {
            "title": f"{company_name} reports steady revenue growth in Q4",
            "snippet": f"The company maintained stable operations with a 5% revenue increase, driven by strong domestic demand.",
            "source": "The Economic Times",
            "date": "2 days ago",
            "link": "#",
        },
        {
            "title": f"{sector_label} sector faces raw material cost pressures",
            "snippet": f"Rising input costs are putting margin pressure on companies in the {sector_label} sector amid global supply chain disruptions.",
            "source": "Business Standard",
            "date": "3 days ago",
            "link": "#",
        },
        {
            "title": f"RBI keeps repo rate unchanged; SME lending outlook positive",
            "snippet": "The Reserve Bank of India's decision to hold rates is expected to keep borrowing costs stable for small and medium enterprises.",
            "source": "Mint",
            "date": "5 days ago",
            "link": "#",
        },
        {
            "title": f"{company_name} secures new export order worth ₹12 Cr",
            "snippet": "The company announced a significant export agreement, bolstering its order book for the next two quarters.",
            "source": "Financial Express",
            "date": "1 week ago",
            "link": "#",
        },
        {
            "title": f"Credit demand in {sector_label} expected to grow 8% in FY25",
            "snippet": "Analysts project healthy credit growth in the sector as capital expenditure cycles resume post-pandemic.",
            "source": "CNBC TV18",
            "date": "1 week ago",
            "link": "#",
        },
    ]


# ──────────────────────────────────────────────
# Task 3 (Day 5): LLM Sentiment Analysis
# ──────────────────────────────────────────────

SENTIMENT_TEMPLATE = """
You are a senior credit analyst at an Indian bank.
Analyse the following news headlines and snippets about a borrower company and its sector.

News:
{news_text}

Provide your analysis as ONLY valid JSON with these fields:
- overall_sentiment: "positive" | "neutral" | "negative"
- sentiment_score: number from -1.0 (very negative) to 1.0 (very positive)
- key_positives: list of up to 3 strings (positive signals)
- key_risks: list of up to 3 strings (risk signals)
- summary: one-paragraph plain-English summary for a credit memo

Return ONLY valid JSON. No markdown, no explanation.
"""


class WebResearchAgent:
    """
    Phase 3: Searches news and performs LLM-based sentiment analysis.
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = get_env("GROQ_API_KEY")
        self.llm = ChatGroq(model=model, temperature=0, api_key=api_key)

    def analyse_sentiment(self, news_items: list[dict]) -> dict:
        """
        Task 3 (Day 5): Feed top 5 news to LLM for sentiment + risks.
        """
        if not news_items:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "key_positives": [],
                "key_risks": ["No news data available"],
                "summary": "No recent news found. Proceed with caution.",
            }

        news_text = "\n\n".join(
            f"Headline: {n['title']}\nSnippet: {n['snippet']}\nSource: {n['source']}"
            for n in news_items
        )

        prompt = PromptTemplate(
            input_variables=["news_text"],
            template=SENTIMENT_TEMPLATE,
        )
        chain = prompt | self.llm | StrOutputParser()

        try:
            raw = chain.invoke({"news_text": news_text})
            result = safe_json_parse(raw)
            if not result:
                raise ValueError("Empty parse result")
            return result
        except Exception as e:
            logger.error("Sentiment analysis failed: %s", e)
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "key_positives": [],
                "key_risks": ["LLM analysis unavailable"],
                "summary": "Sentiment analysis could not be completed. Please review news manually.",
            }

    def run(self, company_name: str, sector: str = "") -> dict:
        """
        Full pipeline: search → analyse → return results.
        """
        news = search_news(company_name, sector)
        sentiment = self.analyse_sentiment(news)
        return {
            "news": news,
            "sentiment": sentiment,
        }
