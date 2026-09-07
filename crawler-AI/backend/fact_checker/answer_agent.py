import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent

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
    match_score: int = Field(description="0-100 query match based only on the supplied evidence and user constraints")


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
    actionable: bool = False
    action_type: str = "none"
    action_prompt: str = ""
    actionable_steps: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    jobs: List[JobListing] = Field(default_factory=list)
    products: List[ProductInfo] = Field(default_factory=list)
    events: List[EventInfo] = Field(default_factory=list)


answer_prompt = """
You are the final answer and action-planning agent for an intelligent web-search and crawling system.

The user query, classified intent, and ranked crawled web sources are supplied to you.

GROUNDING RULES:
1. Use crawled sources as the authority for current/web-dependent facts.
2. Never invent jobs, companies, salaries, prices, ratings, event dates, availability, URLs, or application details.
3. If a field is absent from evidence, use \"Not specified\".
4. Every source-derived factual claim in main_answer/key_points should include [N] for its source number.
5. Prefer crawled page content over search snippets.
6. If sources are empty/unusable, do not fabricate a current answer. State that live evidence could not be retrieved.
7. Never claim that you opened, applied, booked, purchased, contacted, or verified something beyond the supplied evidence.

ACTION RULES:
8. Decide whether the user's request is actionable. Set actionable=true only when the user can meaningfully do something with the result.
9. action_type must be one of: apply, buy, register, contact, compare, decide, explore, none.
10. For jobs, actionable=true when matching openings are found. action_type=\"apply\". action_prompt should invite the user to choose a listing to apply to, and actionable_steps should explain practical next steps such as reviewing requirements and opening the supplied application/source page.
11. For products, use actionable=true/action_type=\"buy\" when the query is a buying recommendation; provide practical checks such as comparing price, warranty, compatibility, or specifications. Do not claim current availability unless supported.
12. For events, use actionable=true/action_type=\"register\" when registration/attendance is relevant; give evidence-backed next steps.
13. For services, use actionable=true/action_type=\"contact\" when providers are found; suggest comparing providers, checking availability, and contacting them through supplied information.
14. For procedural/how-to questions classified as general, actionable=true/action_type=\"explore\" or \"decide\" when concrete next steps are useful.
15. For pure factual/general questions with no meaningful next action, actionable=false, action_type=\"none\", and actionable_steps may be empty.
16. Follow-up questions must be useful and specific to the current query and retrieved findings. Generate 2-4 questions that naturally continue the task, such as comparison, filtering, eligibility, location, budget, or application questions. Never ask generic \"Do you have any other questions?\".
17. Do not create follow-ups that require facts not present in the sources unless they are phrased as a request to search for that information.

STRUCTURED RESULTS:
- For jobs/products/events, extract up to 5 items actually supported by the sources.
- For job match_score, estimate relevance to the user's explicit constraints from 0-100; it is a derived relevance score, not a factual claim.
- Keep application/source URLs exactly as supplied.

Return ONLY valid JSON matching this schema:
{
  \"main_answer\": \"...\",
  \"key_points\": [\"...\"],
  \"actionable\": true,
  \"action_type\": \"apply|buy|register|contact|compare|decide|explore|none\",
  \"action_prompt\": \"...\",
  \"actionable_steps\": [\"...\"],
  \"follow_up_questions\": [\"...\"],
  \"jobs\": [],
  \"products\": [],
  \"events\": []
}
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
                response = output
            elif isinstance(output, dict):
                response = AnswerResponse(**output)
            elif isinstance(output, str):
                response = AnswerResponse(**parse_json_robust(output))
            else:
                raise ValueError("Invalid answer output format")
            return AnswerAgentService._normalize_action_response(response, intent, ranked_pages)
        except Exception as exc:
            print(f"Answer synthesis failed: {exc}; using grounded fallback")
            return AnswerAgentService.fallback_synthesize(query, intent, ranked_pages)

    @staticmethod
    def _normalize_action_response(response: AnswerResponse, intent: str, ranked_pages: List[dict]) -> AnswerResponse:
        """Keep action behavior consistent even when the LLM returns incomplete optional fields."""
        has_evidence = any(p.get("url") and p.get("content") for p in ranked_pages)
        if not has_evidence:
            response.actionable = False
            response.action_type = "none"
            response.action_prompt = ""
            response.actionable_steps = []
            return response

        if intent == "jobs" and response.jobs:
            response.actionable = True
            response.action_type = "apply"
            if not response.action_prompt:
                response.action_prompt = "Would you like to choose one of these roles and open its application/source page?"
            if not response.actionable_steps:
                response.actionable_steps = [
                    "Review the role requirements and location constraints.",
                    "Choose the listing that best matches your profile.",
                    "Open the supplied application/source page and complete the employer's application process.",
                ]
        elif intent == "products" and response.products:
            response.actionable = True
            response.action_type = "buy"
            if not response.action_prompt:
                response.action_prompt = "Would you like to compare the shortlisted products before deciding?"
        elif intent == "events" and response.events:
            response.actionable = True
            response.action_type = "register"
            if not response.action_prompt:
                response.action_prompt = "Would you like to choose an event and open its registration/details page?"
        elif intent == "services":
            response.actionable = True
            response.action_type = "contact"
            if not response.action_prompt:
                response.action_prompt = "Would you like to compare the providers and choose one to contact?"
        return response

    @staticmethod
    def fallback_synthesize(query: str, intent: str, ranked_pages: List[dict]) -> AnswerResponse:
        usable = [p for p in ranked_pages if p.get("url") and p.get("content")]
        if not usable:
            return AnswerResponse(
                main_answer=f"I could not retrieve usable live sources for '{query}'. I won't invent a current answer. Please retry the search.",
                key_points=["No usable live sources were retrieved."],
                actionable=False,
                action_type="none",
                action_prompt="",
                follow_up_questions=["Would you like me to retry the live search?"]
            )

        lines = [f"I found the following source-backed information for '{query}':"]
        for idx, page in enumerate(usable[:5], start=1):
            content = " ".join(page.get("content", "").split())
            lines.append(f"[{idx}] {page.get('title', 'Source')}: {content[:900]}")

        if intent == "jobs":
            action_type, action_prompt, steps = "apply", "Would you like to choose a role and open its application/source page?", [
                "Review the listed role requirements.",
                "Choose the best matching opening.",
                "Open the supplied source/application page to continue.",
            ]
        elif intent == "products":
            action_type, action_prompt, steps = "buy", "Would you like to compare the shortlisted products before deciding?", [
                "Compare the relevant specifications and prices shown in the sources.",
                "Check compatibility and warranty before purchasing.",
            ]
        elif intent == "events":
            action_type, action_prompt, steps = "register", "Would you like to choose an event and open its details page?", [
                "Review the event date and location.",
                "Open the supplied event page to check registration details.",
            ]
        elif intent == "services":
            action_type, action_prompt, steps = "contact", "Would you like to compare the providers and choose one to contact?", [
                "Compare the available providers and their relevant details.",
                "Use the supplied source information to contact your preferred provider.",
            ]
        else:
            action_type, action_prompt, steps = "none", "", []

        return AnswerResponse(
            main_answer="\n\n".join(lines),
            key_points=[p.get("title", "Source") for p in usable[:5]],
            actionable=bool(action_prompt),
            action_type=action_type,
            action_prompt=action_prompt,
            actionable_steps=steps,
            follow_up_questions=AnswerAgentService._fallback_followups(intent),
        )

    @staticmethod
    def _fallback_followups(intent: str) -> List[str]:
        return {
            "jobs": ["Which of these roles best matches my experience?", "Can you filter these jobs by location or experience level?", "Can you show only the roles with salary information?"],
            "products": ["Which option offers the best value for money?", "Can you compare the top three options?", "Which one is best for my specific requirements?"],
            "events": ["Which event is most relevant to my interests?", "Which events are online or available in my location?", "Can you compare the dates and registration details?"],
            "services": ["Which provider looks best for my requirements?", "Can you compare these providers?", "What should I check before contacting one?"],
            "general": ["Can you explain this in more detail?", "Can you compare the main options or approaches?", "What should I do next based on this information?"],
        }.get(intent, [])
