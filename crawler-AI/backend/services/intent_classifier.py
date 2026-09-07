import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List

from pydantic import BaseModel
from pydantic_ai import Agent

fact_checker_path = Path(__file__).parent.parent / "fact_checker"
if str(fact_checker_path) not in sys.path:
    sys.path.insert(0, str(fact_checker_path))
from llm import build_model, run_agent_with_retry, parse_json_robust


class UserIntent(str, Enum):
    JOB_SEARCH = "jobs"
    PRODUCT_RESEARCH = "products"
    EVENT_FINDER = "events"
    SERVICE_LOCATOR = "services"
    GENERAL_QNA = "general"


class IntentResult(BaseModel):
    intent: UserIntent
    confidence: float
    keywords: List[str]
    suggested_queries: List[str]


intent_prompt = """
Classify the user query into exactly one intent: jobs, products, events, services, or general.
- jobs: vacancies, careers, internships, hiring, recruitment, job openings
- products: buying, product research, reviews, comparisons, prices, specifications
- events: conferences, meetups, festivals, workshops, concerts, registration
- services: local/professional service providers, agencies, hosting, consulting
- general: facts, news, explanations, how-to, tutorials, guides
Return only JSON with intent, confidence (0-1), 3-5 relevant keywords, and 3-5 diverse search queries.
Do not add facts to the query that the user did not request. Preserve locations, dates, names, model numbers, and constraints exactly.
"""

intent_classifier_agent = Agent(
    name="IntentClassifierAgent", model=build_model(), system_prompt=intent_prompt, retries=3
)


class IntentClassifier:
    @staticmethod
    async def classify(query: str) -> IntentResult:
        import os
        if not os.getenv("GROQ_API_KEY"):
            return IntentClassifier.fallback_classify(query)
        try:
            result = await run_agent_with_retry(
                intent_classifier_agent,
                f"Current Date: {datetime.now().strftime('%Y-%m-%d')}\nUser Query: {query}",
            )
            output = result.output
            if isinstance(output, IntentResult):
                return output
            if isinstance(output, dict):
                return IntentResult(**output)
            return IntentResult(**parse_json_robust(str(output)))
        except Exception as exc:
            print(f"[IntentClassifier] Agent failed: {exc}; using deterministic fallback")
            return IntentClassifier.fallback_classify(query)

    @staticmethod
    def _has_word(text: str, phrase: str) -> bool:
        return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))

    @staticmethod
    def fallback_classify(query: str) -> IntentResult:
        text = re.sub(r"\s+", " ", query.lower()).strip()
        groups = {
            UserIntent.JOB_SEARCH: ["job", "jobs", "career", "hiring", "opening", "vacancy", "internship", "position", "recruitment", "apply"],
            UserIntent.PRODUCT_RESEARCH: ["buy", "purchase", "price", "cost", "amazon", "review", "rating", "specs", "comparison", "keyboard", "mouse", "phone", "laptop"],
            UserIntent.EVENT_FINDER: ["event", "conference", "meetup", "concert", "festival", "workshop", "booking", "register", "attend"],
            UserIntent.SERVICE_LOCATOR: ["service", "provider", "agency", "consulting", "hosting", "maintenance", "plumber", "barber", "dentist", "cleaner"],
        }
        scores = {intent: sum(IntentClassifier._has_word(text, word) for word in words) for intent, words in groups.items()}
        best_intent, best_score = max(scores.items(), key=lambda x: x[1])
        second_score = sorted(scores.values(), reverse=True)[1]
        if best_score == 0:
            intent, confidence = UserIntent.GENERAL_QNA, 0.60
        elif best_score == second_score:
            intent, confidence = UserIntent.GENERAL_QNA, 0.50
        else:
            intent = best_intent
            confidence = min(0.98, 0.78 + 0.08 * best_score)
        keywords = [w for w in re.findall(r"\b[\w.-]+\b", query) if len(w) > 2][:8]
        return IntentResult(
            intent=intent,
            confidence=confidence,
            keywords=keywords,
            suggested_queries=IntentClassifier._generate_search_queries(query, intent),
        )

    @staticmethod
    def _generate_search_queries(query: str, intent: UserIntent) -> List[str]:
        base = re.sub(r"\s+", " ", query).strip()
        current_year = datetime.now().year
        queries = [base]
        if intent == UserIntent.JOB_SEARCH:
            queries += [f"{base} openings", f"{base} hiring", f"site:linkedin.com/jobs {base}", f"site:indeed.com {base}"]
        elif intent == UserIntent.PRODUCT_RESEARCH:
            queries += [f"{base} reviews", f"{base} comparison", f"{base} price", f"best {base}"]
        elif intent == UserIntent.EVENT_FINDER:
            if str(current_year) not in base and str(current_year - 1) not in base:
                queries.append(f"{base} {current_year}")
            queries += [f"{base} registration", f"site:eventbrite.com {base}", f"site:meetup.com {base}"]
        elif intent == UserIntent.SERVICE_LOCATOR:
            queries += [f"{base} near me", f"{base} provider", f"{base} local", f"{base} reviews"]
        else:
            queries += [f"{base} explanation", f"{base} guide", f"{base} official documentation"]
        return list(dict.fromkeys(queries))[:5]

    @staticmethod
    def _extract_time_filter(query_lower: str) -> str:
        patterns = [
            ("posted this week", "posted"), ("this week", "this week"),
            ("posted in the last 7 days", "7 days ago"), ("last 7 days", "7 days ago"),
            ("last week", "last week"), ("this month", "this month"),
            ("last month", "last month"), ("posted today", "today"),
            ("posted yesterday", "yesterday"), ("just posted", "newly posted"),
            ("recent", "recent"), ("newly posted", "newly posted"), ("latest", "latest"),
        ]
        for phrase, replacement in patterns:
            if phrase in query_lower:
                return replacement
        return ""

    @staticmethod
    def _remove_time_filter(query: str) -> str:
        patterns = [
            r"\bposted this week\b", r"\bthis week\b", r"\bposted in the last 7 days\b",
            r"\blast 7 days\b", r"\blast week\b", r"\bthis month\b", r"\blast month\b",
            r"\bposted today\b", r"\bposted yesterday\b", r"\bjust posted\b",
            r"\brecent\b", r"\bnewly posted\b", r"\blatest\b",
        ]
        result = query
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", result).strip()
