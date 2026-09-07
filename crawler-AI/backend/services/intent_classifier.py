import sys
import json
from pathlib import Path
from pydantic import BaseModel
from pydantic_ai import Agent
from enum import Enum
from typing import List

# Setup path to import build_model from fact_checker subdirectory
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
You are an AI query intent classifier and search query optimizer. Analyze the user's query and:

1. Classify it into ONE of these intents:
   - 'jobs': job openings, vacancies, careers, internships, hiring, remote jobs, recruitment
   - 'products': shopping, reviews, comparisons, prices, specifications, best buys, recommendations
   - 'events': conferences, meetups, festivals, workshops, concerts, bookings, registrations
   - 'services': service providers, local services, hosting, consulting, professional services
   - 'general': facts, news, how-to, descriptions, tutorials, guides, and everything else

2. Extract 3-5 main keywords from the query relevant to the intent

3. Generate 3-5 DIVERSE search queries using these strategies:
   - Direct query (e.g., "python jobs")
   - Site-specific (e.g., "site:linkedin.com python jobs")
   - Refined/specific (e.g., "python developer jobs remote 2026")
   - Alternative phrasing (e.g., "hiring python engineers")
   - Modifiers based on intent:
     * For 'jobs': add "remote", "salary", location, level (senior/junior)
     * For 'products': add "best", "reviews", "compare", "price"
     * For 'events': add "2026", location, registration
     * For 'services': add location, "near me", specific needs

Return ONLY a valid JSON object matching this schema:
{
  "intent": "jobs" | "products" | "events" | "services" | "general",
  "confidence": float,
  "keywords": ["keyword1", "keyword2", ...],
  "suggested_queries": ["query1", "query2", ...]
}
Do not include any other text or explanation. Just return raw JSON.
"""

intent_classifier_agent = Agent(
    name="IntentClassifierAgent",
    model=build_model(),
    system_prompt=intent_prompt,
    retries=3
)

class IntentClassifier:
    @staticmethod
    async def classify(query: str) -> IntentResult:
        import os
        if not os.getenv("GROQ_API_KEY"):
            print("[IntentClassifier] GROQ_API_KEY not found. Running fallback rule-based classifier.")
            return IntentClassifier.fallback_classify(query)
        try:
            from datetime import datetime
            current_date = datetime.now().strftime("%B %Y")
            formatted_query = f"Current Date: {current_date}\nUser Query: {query}"
            
            result = await run_agent_with_retry(intent_classifier_agent, formatted_query)
            output = result.output
            if isinstance(output, IntentResult):
                return output
            elif isinstance(output, dict):
                return IntentResult(**output)
            elif isinstance(output, str):
                parsed = parse_json_robust(output)
                return IntentResult(**parsed)
            raise ValueError("Invalid output format")
        except Exception as e:
            print(f"Agent classification failed: {e}. Running fallback rule-based classifier.")
            return IntentClassifier.fallback_classify(query)

    @staticmethod
    def fallback_classify(query: str) -> IntentResult:
        query_lower = query.lower()
        intent = UserIntent.GENERAL_QNA
        confidence = 0.6
        words = query.split()
        keywords = [word.strip("?,.!") for word in words if len(word) > 3]
        
        # Strong indicators (high confidence)
        job_strong = ["job", "career", "hiring", "opening", "vacancy", "internship", "position", "role", "recruitment", "apply"]
        product_strong = ["buy", "purchase", "price", "cost", "amazon", "review", "rating", "specs", "comparison"]
        event_strong = ["event", "conference", "meetup", "concert", "festival", "booking", "register", "attend", "schedule"]
        service_strong = ["service", "provider", "agency", "company hire", "consulting", "hosting", "maintenance"]
        
        # Weak indicators (supplementary keywords)
        job_weak = ["developer", "engineer", "designer", "analyst", "manager", "remote", "work", "recruit"]
        product_weak = ["best", "keyboard", "mouse", "phone", "laptop", "pc", "product"]
        event_weak = ["pycon", "conference", "workshop", "seminar", "live"]
        service_weak = ["plumber", "barber", "dentist", "clinic", "cleaner"]
        
        strong_match_count = 0
        weak_match_count = 0
        
        # Check for job intent
        job_strong_matches = sum(1 for k in job_strong if k in query_lower)
        job_weak_matches = sum(1 for k in job_weak if k in query_lower)
        
        if job_strong_matches >= 1:
            intent = UserIntent.JOB_SEARCH
            confidence = 0.85 + (job_strong_matches * 0.05)
        elif job_strong_matches + job_weak_matches >= 2:
            intent = UserIntent.JOB_SEARCH
            confidence = 0.72
        
        # Check for product intent (only if not already classified as job)
        if intent == UserIntent.GENERAL_QNA:
            product_strong_matches = sum(1 for k in product_strong if k in query_lower)
            product_weak_matches = sum(1 for k in product_weak if k in query_lower)
            
            if product_strong_matches >= 1:
                intent = UserIntent.PRODUCT_RESEARCH
                confidence = 0.85 + (product_strong_matches * 0.05)
            elif product_strong_matches + product_weak_matches >= 2:
                intent = UserIntent.PRODUCT_RESEARCH
                confidence = 0.72
        
        # Check for event intent
        if intent == UserIntent.GENERAL_QNA:
            event_strong_matches = sum(1 for k in event_strong if k in query_lower)
            event_weak_matches = sum(1 for k in event_weak if k in query_lower)
            
            if event_strong_matches >= 1:
                intent = UserIntent.EVENT_FINDER
                confidence = 0.85 + (event_strong_matches * 0.05)
            elif event_strong_matches + event_weak_matches >= 2:
                intent = UserIntent.EVENT_FINDER
                confidence = 0.72
        
        # Check for service intent
        if intent == UserIntent.GENERAL_QNA:
            service_strong_matches = sum(1 for k in service_strong if k in query_lower)
            service_weak_matches = sum(1 for k in service_weak if k in query_lower)
            
            if service_strong_matches >= 1:
                intent = UserIntent.SERVICE_LOCATOR
                confidence = 0.85 + (service_strong_matches * 0.05)
            elif service_strong_matches + service_weak_matches >= 2:
                intent = UserIntent.SERVICE_LOCATOR
                confidence = 0.72
        
        # Generate intent-specific search queries
        suggested_queries = IntentClassifier._generate_search_queries(query, intent)
        
        return IntentResult(
            intent=intent,
            confidence=min(0.99, confidence),
            keywords=keywords[:5],
            suggested_queries=suggested_queries
        )
    
    @staticmethod
    def _generate_search_queries(query: str, intent: UserIntent) -> List[str]:
        """Generate diverse search queries based on intent."""
        queries = []
        query_lower = query.lower()
        
        if intent == UserIntent.JOB_SEARCH:
            # Clean up the query for better searching
            import re
            # Remove common filler words
            clean_query = re.sub(r'\b(find\s+me|looking\s+for|i\s+want|i\s+need|jobs?)\b', '', query_lower, flags=re.IGNORECASE).strip()
            # Remove time filter phrases temporarily for main searches
            time_keywords = ['posted this week', 'this week', 'last 7 days', 'last week', 'this month', 'posted today', 'recently', 'just posted']
            for keyword in time_keywords:
                clean_query = clean_query.replace(keyword, '').strip()
            
            # Use original if cleaning removed too much
            if not clean_query or len(clean_query) < 3:
                clean_query = query_lower.replace('posted this week', '').replace('this week', '').strip()
            if not clean_query or len(clean_query) < 3:
                clean_query = query
            
            # Generate diverse search queries - shorter, more effective
            queries.append(clean_query[:40])  # Base query, limited length
            queries.append(f"site:indeed.com {clean_query[:35]}")
            queries.append(f"site:linkedin.com {clean_query[:35]}")
            
            # Add variants
            if "remote" not in clean_query:
                queries.append(f"{clean_query[:30]} remote")
            else:
                queries.append(f"{clean_query[:35]} jobs")
            
            # One more variant with job board
            queries.append(f"{clean_query[:30]} openings")
            
        elif intent == UserIntent.PRODUCT_RESEARCH:
            # Generate product-specific queries
            if "review" not in query_lower:
                queries.append(f"{query} review")
            if "best" not in query_lower:
                queries.append(f"best {query}")
            if "price" not in query_lower:
                queries.append(f"{query} price")
            queries.append(f"{query} comparison")
            queries.append(f"site:amazon.com {query}")
            
        elif intent == UserIntent.EVENT_FINDER:
            # Generate event-specific queries
            queries.append(query)
            if "2024" not in query_lower and "2025" not in query_lower:
                from datetime import datetime
                current_year = datetime.now().year
                queries.append(f"{query} {current_year}")
            if "register" not in query_lower:
                queries.append(f"{query} registration")
            queries.append(f"site:eventbrite.com {query}")
            queries.append(f"site:meetup.com {query}")
            
        elif intent == UserIntent.SERVICE_LOCATOR:
            # Generate service-specific queries
            if "near me" not in query_lower:
                queries.append(f"{query} near me")
            if "cost" not in query_lower and "price" not in query_lower:
                queries.append(f"{query} cost")
            queries.append(f"{query} services")
            queries.append(f"{query} provider")
            queries.append(f"{query} local")
        
        else:  # GENERAL_QNA
            # Generate general queries
            if "how" not in query_lower:
                queries.append(f"how to {query}")
            if "what" not in query_lower:
                queries.append(f"what is {query}")
            queries.append(f"{query} tutorial")
            queries.append(f"{query} guide")
        
        # Return up to 5 unique queries
        return list(dict.fromkeys(queries))[:5]
    
    @staticmethod
    def _extract_time_filter(query_lower: str) -> str:
        """Extract time-related keywords from query."""
        time_keywords = [
            ("posted this week", "posted"),
            ("this week", "this week"),
            ("posted in the last 7 days", "7 days ago"),
            ("last 7 days", "7 days ago"),
            ("last week", "last week"),
            ("this month", "this month"),
            ("last month", "last month"),
            ("posted today", "today"),
            ("posted yesterday", "yesterday"),
            ("just posted", "newly posted"),
            ("recent", "recent"),
            ("newly posted", "newly posted"),
            ("latest", "latest"),
        ]
        
        for phrase, replacement in time_keywords:
            if phrase in query_lower:
                return replacement
        return ""
    
    @staticmethod
    def _remove_time_filter(query: str) -> str:
        """Remove time-related keywords from query for cleaner searches."""
        time_patterns = [
            " posted this week",
            " this week",
            " posted in the last 7 days",
            " last 7 days",
            " last week",
            " this month",
            " last month",
            " posted today",
            " posted yesterday",
            " just posted",
            " recent",
            " newly posted",
            " latest",
        ]
        
        result = query
        for pattern in time_patterns:
            result = result.replace(pattern, "").replace(pattern.lstrip(), "")
        return result.strip()
