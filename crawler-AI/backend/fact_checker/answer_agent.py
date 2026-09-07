import sys
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import List, Optional

fact_checker_path = Path(__file__).parent.parent / "fact_checker"
if str(fact_checker_path) not in sys.path:
    sys.path.insert(0, str(fact_checker_path))

from llm import build_model, run_agent_with_retry, parse_json_robust


class JobListing(BaseModel):
    title: str = Field(description="Job title/role name")
    company: str = Field(description="Hiring company")
    location: str = Field(description="Job location")
    salary_range: Optional[str] = Field(default="Not specified")
    apply_url: str = Field(description="URL of the source/application page")
    match_score: int = Field(description="0-100 match to the user's query")


class ProductInfo(BaseModel):
    name: str
    price: str = "Not specified"
    rating: str = "Not specified"
    description: str
    source_url: str


class EventInfo(BaseModel):
    name: str
    date: str = "Not specified"
    location: str = "Not specified"
    description: str
    url: str


class AnswerResponse(BaseModel):
    main_answer: str
    key_points: List[str] = Field(default_factory=list)
    action_prompt: str = "Would you like to search for more details?"
    jobs: List[JobListing] = Field(default_factory=list)
    products: List[ProductInfo] = Field(default_factory=list)
    events: List[EventInfo] = Field(default_factory=list)


answer_prompt = """
You are the final answer agent for a web-search and crawling system.

RULES FOR GROUNDING:
1. The crawled sources are the ONLY authority for current, web-dependent facts.
2. Never invent jobs, products, prices, ratings, event dates, companies, salaries, URLs, or availability.
3. If a requested fact is absent from the sources, explicitly say it was not found.
4. Do not treat a search-result title/snippet as proof when the crawled page contradicts it.
5. Prefer direct source content over snippets, and prefer multiple independent sources for important claims.
6. For time-sensitive queries, use the supplied current date and report the source's date when available.
7. If sources are empty or unusable, do NOT fabricate a current answer. State that live evidence could not be retrieved and provide only clearly labelled general background if useful.
8. Every factual statement derived from a source should include [N], where N is that source's number.
9. Structured jobs/products/events must contain ONLY items actually supported by the supplied sources. Never manufacture missing fields; use "Not specified".
10. Do not claim that you opened, verified, bought, booked, or contacted anything.

For general knowledge questions, answer from reliable retrieved content first. If the sources do not answer the question, clearly distinguish general knowledge from web-verified findings.

Return ONLY valid JSON matching the requested schema.
"""

answer_agent = Agent(
    name="AnswerAgent",
    model=build_model(),
    system_prompt=answer_prompt,
    retries=3,
)


class AnswerAgentService:
    @staticmethod
    async def synthesize(query: str, intent: str, ranked_pages: List[dict]) -> AnswerResponse:
        import os
        if not os.getenv("GROQ_API_KEY"):
            return AnswerAgentService.fallback_synthesize(query, intent, ranked_pages)
        try:
            from datetime import datetime
            source_blocks = []
            for idx, source in enumerate(ranked_pages, start=1):
                source_blocks.append(
                    f"Source [{idx}]\n"
                    f"Title: {source.get('title', '')}\n"
                    f"URL: {source.get('url', '')}\n"
                    f"Relevance: {source.get('relevance_score', 0)}\n"
                    f"Authority: {source.get('authority_score', 0)}\n"
                    f"Snippet: {source.get('snippet', '')}\n"
                    f"Crawled content:\n{source.get('content', '')[:8000]}"
                )
            input_text = (
                f"Current date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"User query: {query}\nIntent: {intent}\n\n"
                + "\n\n".join(source_blocks)
            )
            result = await run_agent_with_retry(answer_agent, input_text)
            output = result.output
            if isinstance(output, AnswerResponse):
                return output
            if isinstance(output, dict):
                return AnswerResponse(**output)
            if isinstance(output, str):
                return AnswerResponse(**parse_json_robust(output))
            raise ValueError("Invalid answer output format")
        except Exception as exc:
            print(f"Answer synthesis failed: {exc}; using grounded fallback")
            return AnswerAgentService.fallback_synthesize(query, intent, ranked_pages)

    @staticmethod
    def fallback_synthesize(query: str, intent: str, ranked_pages: List[dict]) -> AnswerResponse:
        usable = [p for p in ranked_pages if p.get("url") and p.get("content")]
        if not usable:
            return AnswerResponse(
                main_answer=(
                    f"I could not retrieve usable live sources for '{query}'. "
                    "I won't invent a current answer. Please retry the search."
                ),
                key_points=["No usable live sources were retrieved."],
                action_prompt="Please retry the search or provide a specific source.",
            )

        lines = [f"I found the following source-backed information for '{query}':\n"]
        for idx, page in enumerate(usable[:5], start=1):
            content = " ".join(page.get("content", "").split())
            lines.append(f"[{idx}] {page.get('title', 'Source')}: {content[:900]}")
        return AnswerResponse(
            main_answer="\n\n".join(lines),
            key_points=[p.get("title", "Source") for p in usable[:5]],
            action_prompt="Would you like me to refine the search or focus on one of these sources?",
        )
