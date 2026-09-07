import asyncio
import re
from types import SimpleNamespace
from typing import Any, Dict, List

from ddgs import DDGS

from fact_checker.answer_agent import AnswerAgentService, AnswerResponse
from services.intent_classifier import IntentClassifier, IntentResult
from services.ranking_service import SearchRanker
from services.web_crawler import WebCrawler


class SearchAgentService:
    @staticmethod
    def _timelimit_from_query(query: str) -> str | None:
        value = IntentClassifier._extract_time_filter(query.lower())
        if not value:
            return None
        value = value.lower()
        if any(x in value for x in ("today", "yesterday", "day")):
            return "d"
        if any(x in value for x in ("week", "7 days", "posted")):
            return "w"
        if any(x in value for x in ("month", "recent", "latest")):
            return "m"
        return None

    @staticmethod
    def _clean_queries(queries: List[str]) -> List[str]:
        cleaned = []
        for q in queries:
            q = IntentClassifier._remove_time_filter(q)
            q = re.sub(r"\s+", " ", q).strip()
            if q:
                cleaned.append(q)
        return list(dict.fromkeys(cleaned))

    @staticmethod
    def _search_sync(queries: List[str], timelimit: str | None, per_query: int = 6):
        results = []
        with DDGS() as ddgs:
            for q in queries:
                try:
                    kwargs = {"max_results": per_query}
                    if timelimit:
                        kwargs["timelimit"] = timelimit
                    current = list(ddgs.text(q, **kwargs) or [])
                    if not current and timelimit:
                        current = list(ddgs.text(q, max_results=per_query) or [])
                    results.extend(current)
                except Exception as exc:
                    print(f"[Pipeline] Search failed for '{q}': {exc}")
        return results

    @staticmethod
    async def _crawl_results(search_results: List[Dict[str, Any]], max_pages: int = 8):
        urls, seen = [], set()
        for item in search_results:
            url = (item.get("href") or "").strip()
            if not url or url in seen or not url.startswith(("http://", "https://")):
                continue
            seen.add(url)
            urls.append(url)
            if len(urls) >= max_pages:
                break
        if not urls:
            return []
        pages = await WebCrawler(timeout=12.0).crawl_multiple(urls)
        return [p for p in pages if p.status_code == 200 and len((p.content or "").strip()) >= 80]

    @staticmethod
    def _rank(search_results, crawled_pages, keywords):
        crawled = {p.url: p for p in crawled_pages}
        candidates, seen = [], set()
        for item in search_results:
            url = (item.get("href") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            page = crawled.get(url)
            candidates.append(page or SimpleNamespace(
                url=url,
                title=item.get("title", ""),
                content=item.get("body", "") or "",
            ))
        return SearchRanker.rank_results(candidates, " ".join(keywords), keywords)[:8]

    @staticmethod
    async def run_pipeline(query: str) -> Dict[str, Any]:
        query = (query or "").strip()
        if not query:
            raise ValueError("Query cannot be empty")

        intent_result: IntentResult = await IntentClassifier.classify(query)
        intent = intent_result.intent.value
        queries = SearchAgentService._clean_queries(
            [query] + (intent_result.suggested_queries or [])
        )[:5]
        timelimit = SearchAgentService._timelimit_from_query(query)

        loop = asyncio.get_running_loop()
        search_results = await loop.run_in_executor(
            None, SearchAgentService._search_sync, queries, timelimit, 6
        )

        unique, seen = [], set()
        for item in search_results:
            url = (item.get("href") or "").strip()
            if url and url not in seen:
                seen.add(url)
                unique.append(item)

        crawled_pages = await SearchAgentService._crawl_results(unique[:12], max_pages=8)
        ranked_results = SearchAgentService._rank(unique, crawled_pages, intent_result.keywords)

        crawled = {p.url: p for p in crawled_pages}
        ranked_pages_dump = []
        for r in ranked_results:
            page = crawled.get(r.url)
            ranked_pages_dump.append({
                **r.model_dump(),
                "content": (page.content if page else r.snippet)[:8000],
            })

        if not ranked_pages_dump:
            ranked_pages_dump = [{
                "url": "", "title": "No sources retrieved", "snippet": "",
                "domain": "", "relevance_score": 0, "authority_score": 0,
                "combined_score": 0, "rank": 1,
                "content": "No live search results were retrieved. Do not invent current facts.",
            }]

        answer_result: AnswerResponse = await AnswerAgentService.synthesize(
            query, intent, ranked_pages_dump
        )
        confidence_level = (
            "high" if intent_result.confidence >= 0.85
            else "medium" if intent_result.confidence >= 0.60 else "low"
        )

        return {
            "intent": intent,
            "confidence_score": f"{int(intent_result.confidence * 100)}%",
            "confidence_level": confidence_level,
            "summary": answer_result.main_answer,
            "recommendation": answer_result.action_prompt,
            "key_claim": query,
            "key_claim_verdict": intent.upper(),
            "key_claim_reason": "Answer generated from classified intent and retrieved/crawled sources.",
            "note": "SearchShield AI Intelligent Search Assistant",
            "synthesized_answer": answer_result.main_answer,
            "key_points": answer_result.key_points,
            "actionable": answer_result.actionable,
            "action_type": answer_result.action_type,
            "action_prompt": answer_result.action_prompt,
            "actionable_steps": answer_result.actionable_steps,
            "follow_up_questions": answer_result.follow_up_questions,
            "jobs": [j.model_dump() for j in answer_result.jobs],
            "products": [p.model_dump() for p in answer_result.products],
            "events": [e.model_dump() for e in answer_result.events],
            "sources": [s.model_dump() for s in ranked_results],
        }
