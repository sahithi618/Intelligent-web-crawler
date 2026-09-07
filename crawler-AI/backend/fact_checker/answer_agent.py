import sys
import json
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import List, Optional

# Setup path to import build_model from fact_checker subdirectory
fact_checker_path = Path(__file__).parent.parent / "fact_checker"
if str(fact_checker_path) not in sys.path:
    sys.path.insert(0, str(fact_checker_path))

from llm import build_model, run_agent_with_retry, parse_json_robust

class JobListing(BaseModel):
    title: str = Field(description="Job title/role name")
    company: str = Field(description="Name of the hiring company")
    location: str = Field(description="Location of the job (e.g. Remote, NYC, San Francisco)")
    salary_range: Optional[str] = Field(description="Salary range if listed, or 'Not specified'")
    apply_url: str = Field(description="Target application link or original source URL")
    match_score: int = Field(description="Simulated compatibility score out of 100 based on the query match")

class ProductInfo(BaseModel):
    name: str = Field(description="Product name")
    price: str = Field(default="Not specified", description="Price or price range")
    rating: str = Field(default="Not specified", description="Rating/review score")
    description: str = Field(description="Brief product description or specs")
    source_url: str = Field(description="Source URL or link to view/buy")

class EventInfo(BaseModel):
    name: str = Field(description="Event name")
    date: str = Field(default="Not specified", description="Event date/time")
    location: str = Field(default="Not specified", description="Event location (city, venue, or Online)")
    description: str = Field(description="Brief event description")
    url: str = Field(description="Event registration or info URL")

class AnswerResponse(BaseModel):
    main_answer: str = Field(description="The synthesized, cohesive response summarizing the crawled findings.")
    key_points: List[str] = Field(default=[], description="Key bullet points summarizing main insights or recommendations.")
    action_prompt: str = Field(default="Would you like to search for more details?", description="An action-oriented prompt guiding the user to the next step (e.g. 'Would you like me to open the application page for the Senior Python role at Acme?')")
    jobs: List[JobListing] = Field(default=[], description="List of structured job openings extracted, empty if intent is not job search.")
    products: List[ProductInfo] = Field(default=[], description="List of structured products extracted, empty if intent is not product research.")
    events: List[EventInfo] = Field(default=[], description="List of structured events/hackathons extracted, empty if intent is not event finder.")

answer_prompt = """
You are an expert Answer Synthesis Agent. Your goal is to provide a complete, well-summarized response based on crawled web results.
You are given:
1. The user's query
2. The user's classified intent
3. A list of ranked crawled pages (with title, url, snippet, content)

Synthesize a comprehensive answer (main_answer) incorporating relevant findings. Use cited references [1], [2], etc., linking to the numbered sources if available.
If the crawled sources list is empty, contains no relevant information, or search fails, you MUST answer the user's query directly using your own extensive internal knowledge. Provide a helpful, detailed response matching the domain (e.g. products, movies, events, general Q&A, etc.).

Extract key bullet points (key_points).
Formulate an action-oriented prompt (action_prompt) guiding the user on the next step.

Even if you are answering from your own internal knowledge (due to empty search results), you MUST extract and populate the structured `jobs`, `products`, or `events` lists with the respective items you mention in your answer:
- If the intent is 'jobs', extract up to 5 structured job listings (jobs), specifying company, title, location, salary, original url, and compatibility match score (0-100).
- If the intent is 'products', extract up to 5 structured product listings (products), specifying name, price, rating, description, and source url.
- If the intent is 'events', extract up to 5 structured event/hackathon listings (events), specifying name, date, location, description, and registration url.

Return ONLY a valid JSON object matching this schema:
{
  "main_answer": "string containing synthesized answer",
  "key_points": ["bullet 1", "bullet 2", ...],
  "action_prompt": "action-oriented prompt string",
  "jobs": [
    {
      "title": "string",
      "company": "string",
      "location": "string",
      "salary_range": "string",
      "apply_url": "string",
      "match_score": integer
    }
  ],
  "products": [
    {
      "name": "string",
      "price": "string",
      "rating": "string",
      "description": "string",
      "source_url": "string"
    }
  ],
  "events": [
    {
      "name": "string",
      "date": "string",
      "location": "string",
      "description": "string",
      "url": "string"
    }
  ]
}
Do not include any other text or explanation. Just return raw JSON.
"""

answer_agent = Agent(
    name="AnswerAgent",
    model=build_model(),
    system_prompt=answer_prompt,
    retries=3
)

class AnswerAgentService:
    @staticmethod
    async def synthesize(query: str, intent: str, ranked_pages: List[dict]) -> AnswerResponse:
        import os
        if not os.getenv("GROQ_API_KEY"):
            print("[AnswerAgentService] GROQ_API_KEY not found. Running fallback synthesizer.")
            return AnswerAgentService.fallback_synthesize(query, intent, ranked_pages)
        try:
            from datetime import datetime
            current_date = datetime.now().strftime("%B %Y")
            
            # Format inputs
            sources_summary = ""
            for idx, r in enumerate(ranked_pages, start=1):
                sources_summary += f"\nSource [{idx}]:\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}\nContent: {r['content'][:1500]}\n"
            
            input_text = f"Current Date: {current_date}\nUser Query: {query}\nIntent: {intent}\n\nCrawled Sources:\n{sources_summary}"
            
            result = await run_agent_with_retry(answer_agent, input_text)
            output = result.output
            if isinstance(output, AnswerResponse):
                return output
            elif isinstance(output, dict):
                return AnswerResponse(**output)
            elif isinstance(output, str):
                parsed = parse_json_robust(output)
                return AnswerResponse(**parsed)
            raise ValueError("Invalid answer output format")
        except Exception as e:
            print(f"AnswerAgent synthesis failed: {e}. Executing fallback synthesizer.")
            return AnswerAgentService.fallback_synthesize(query, intent, ranked_pages)

    @staticmethod
    def fallback_synthesize(query: str, intent: str, ranked_pages: List[dict]) -> AnswerResponse:
        """Simple baseline fallback synthesizer that does not use complex extractors."""
        sources_text = ", ".join([f"[{i}] {r['title']}" for i, r in enumerate(ranked_pages[:3], start=1)])
        main_answer = f"Based on our search snippets, here is the information for '{query}':\n\n"
        for idx, page in enumerate(ranked_pages[:3], start=1):
            main_answer += f"[{idx}] {page.get('title', 'Source')}: {page.get('snippet', '')}\n\n"
            
        return AnswerResponse(
            main_answer=main_answer,
            key_points=[page.get('title', 'Source') for page in ranked_pages[:3]],
            action_prompt="Would you like to search for more details?",
            jobs=[]
        )

