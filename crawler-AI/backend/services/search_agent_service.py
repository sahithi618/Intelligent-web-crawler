import asyncio
from datetime import datetime
from typing import List, Dict, Any
from duckduckgo_search import DDGS

from services.intent_classifier import IntentClassifier, IntentResult
from services.ranking_service import SearchRanker, RankedResult
from fact_checker.answer_agent import AnswerAgentService, AnswerResponse

class SearchAgentService:
    @staticmethod
    async def run_pipeline(query: str) -> Dict[str, Any]:
        """Runs a simplified search pipeline utilizing DuckDuckGo search snippets directly."""
        # Step 1: Classify user intent
        print(f"[Pipeline] Classifying intent for query: '{query}'")
        intent_result: IntentResult = await IntentClassifier.classify(query)
        print(f"[Pipeline] Intent: {intent_result.intent} (Confidence: {intent_result.confidence})")
        print(f"[Pipeline] Keywords: {intent_result.keywords}")
        print(f"[Pipeline] Suggested queries: {intent_result.suggested_queries}")
        
        # Step 2: Search web using DuckDuckGo with diverse queries
        search_queries = intent_result.suggested_queries
        if not search_queries:
            search_queries = [query]
            
        # Extract time limit code for DuckDuckGo
        time_filter_str = IntentClassifier._extract_time_filter(query.lower())
        timelimit = None
        if time_filter_str:
            time_filter_str = time_filter_str.lower()
            if any(w in time_filter_str for w in ["today", "yesterday", "day"]):
                timelimit = "d"
            elif any(w in time_filter_str for w in ["week", "7 days", "posted"]):
                timelimit = "w"
            elif any(w in time_filter_str for w in ["month", "recent", "latest"]):
                timelimit = "m"
        
        # Clean suggested queries (remove time filters from DDG queries to prevent noise and empty results)
        import re
        cleaned_queries = []
        for s_query in search_queries:
            clean_q = IntentClassifier._remove_time_filter(s_query)
            clean_q = re.sub(r'\s+', ' ', clean_q).strip()
            if clean_q:
                cleaned_queries.append(clean_q)
        
        cleaned_queries = list(dict.fromkeys(cleaned_queries))
        if not cleaned_queries:
            cleaned_queries = [query]
            
        print(f"[Pipeline] Timelimit code extracted: {timelimit}")
        print(f"[Pipeline] Cleaned search queries: {cleaned_queries}")

        search_results = []
        
        # Define the synchronous run function that reuses a single DDGS session
        def run_ddg_queries(queries_to_run, limit):
            results = []
            with DDGS() as ddgs:
                for q in queries_to_run:
                    print(f"[Pipeline] Searching DuckDuckGo for: '{q}' (timelimit: {limit})")
                    try:
                        res = ddgs.text(q, timelimit=limit, backend='api', max_results=5)
                        if res:
                            results.extend(res)
                            print(f"[Pipeline] Got {len(res)} results for '{q}'")
                        else:
                            # Fallback without timelimit if timelimit returned nothing
                            if limit:
                                print(f"[Pipeline] No results with timelimit. Retrying '{q}' without timelimit...")
                                res_fallback = ddgs.text(q, backend='api', max_results=5)
                                if res_fallback:
                                    results.extend(res_fallback)
                                    print(f"[Pipeline] Got {len(res_fallback)} results without timelimit for '{q}'")
                    except Exception as e:
                        print(f"[Pipeline] Search error for query '{q}': {e}")
            return results

        # Run DuckDuckGo searches in a thread pool using the single session helper
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, run_ddg_queries, cleaned_queries[:3], timelimit)
            if results:
                search_results.extend(results)
        except Exception as e:
            print(f"[Pipeline] Executor execution failed: {e}")
                
        # Deduplicate results by URL
        seen_urls = set()
        unique_search_results = []
        for r in search_results:
            url = r.get("href")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_search_results.append(r)
        
        print(f"[Pipeline] Total unique results after deduplication: {len(unique_search_results)}")
        
        # Map unique search results to RankedResult directly
        ranked_results = []
        for rank, r in enumerate(unique_search_results[:8], start=1):
            url = r.get("href", "")
            domain = SearchRanker.get_domain(url)
            
            # Find domain authority
            auth_score = 50.0  # default baseline
            for auth_domain, score in SearchRanker.AUTHORITY_DOMAINS.items():
                if auth_domain in domain:
                    auth_score = score
                    break
                    
            ranked_results.append(RankedResult(
                url=url,
                title=r.get("title", "") or domain,
                snippet=r.get("body", "") or "No details available.",
                domain=domain,
                relevance_score=float(round(100.0 - (rank * 5), 2)),
                authority_score=float(auth_score),
                combined_score=float(round(100.0 - (rank * 5), 2)),
                rank=rank
            ))
            
        if not ranked_results:
            print("[Pipeline] No search results returned. Setting fallback source.")
            ranked_results = [
                RankedResult(
                    url="https://google.com",
                    title="Web Search",
                    snippet="No live search results could be retrieved. Synthesizing answer directly.",
                    domain="google.com",
                    relevance_score=0.0,
                    authority_score=50.0,
                    combined_score=0.0,
                    rank=1
                )
            ]
            
        # Format pages dump for AnswerAgentService
        ranked_pages_dump = []
        for r in ranked_results:
            d = r.model_dump()
            if r.url == "https://google.com" and len(unique_search_results) == 0:
                d["content"] = "No search results returned from search engine. Please answer the query directly using your own extensive knowledge."
            else:
                d["content"] = r.snippet
            ranked_pages_dump.append(d)
            
        print("[Pipeline] Synthesizing final answer...")
        answer_result: AnswerResponse = await AnswerAgentService.synthesize(
            query, intent_result.intent, ranked_pages_dump
        )
        
        confidence_level = "high" if intent_result.confidence >= 0.85 else "medium" if intent_result.confidence >= 0.6 else "low"
        
        return {
            "intent": intent_result.intent,
            "confidence_score": f"{int(intent_result.confidence * 100)}%",
            "confidence_level": confidence_level,
            "summary": answer_result.main_answer,
            "recommendation": answer_result.action_prompt,
            "key_claim": query,
            "key_claim_verdict": intent_result.intent.upper(),
            "key_claim_reason": f"Analyzed query with intent: {intent_result.intent}",
            "note": "SearchShield AI Intelligent Search Assistant",
            "synthesized_answer": answer_result.main_answer,
            "key_points": answer_result.key_points,
            "action_prompt": answer_result.action_prompt,
            "jobs": [j.model_dump() for j in answer_result.jobs] if hasattr(answer_result, 'jobs') else [],
            "products": [p.model_dump() for p in answer_result.products] if hasattr(answer_result, 'products') else [],
            "events": [e.model_dump() for e in answer_result.events] if hasattr(answer_result, 'events') else [],
            "sources": [s.model_dump() for s in ranked_results]
        }

