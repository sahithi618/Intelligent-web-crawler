import math
import re
from typing import List, Dict, Any
from pydantic import BaseModel

class RankedResult(BaseModel):
    url: str
    title: str
    snippet: str
    domain: str
    relevance_score: float  # TF-IDF similarity (0-100)
    authority_score: float  # Domain reputation (0-100)
    combined_score: float   # Weighted combination (0-100)
    rank: int

class SearchRanker:
    # Pre-defined authority domains for various intents
    AUTHORITY_DOMAINS = {
        # General / Tech
        "wikipedia.org": 95,
        "github.com": 90,
        "stackoverflow.com": 90,
        "w3schools.com": 80,
        "medium.com": 75,
        # Jobs
        "linkedin.com": 95,
        "indeed.com": 90,
        "monster.com": 85,
        "glassdoor.com": 85,
        "simplyhired.com": 80,
        "builtin.com": 85,
        # Products
        "wirecutter.com": 95,
        "nytimes.com": 90,
        "techradar.com": 90,
        "cnet.com": 85,
        "rtings.com": 85,
        "tomsguide.com": 85,
        "amazon.com": 80,
        # Events
        "meetup.com": 90,
        "eventbrite.com": 90,
        "luma.com": 80,
    }

    @staticmethod
    def get_domain(url: str) -> str:
        """Extract domain name from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            return netloc[4:]
        return netloc

    @staticmethod
    def clean_text(text: str) -> List[str]:
        """Convert text to list of cleaned words."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return words

    @classmethod
    def calculate_tfidf(cls, documents: List[str], query_keywords: List[str]) -> List[float]:
        """Compute cosine similarity of query keywords across documents using TF-IDF."""
        if not documents or not query_keywords:
            return [0.0] * len(documents)
        
        # Clean doc tokens
        doc_words = [cls.clean_text(doc) for doc in documents]
        query_words = [k.lower() for k in query_keywords]
        
        # Calculate DF (Document Frequency) for each keyword
        df = {}
        for qw in query_words:
            df[qw] = sum(1 for doc in doc_words if qw in doc)
        
        num_docs = len(documents)
        
        # Calculate IDF
        idf = {}
        for qw in query_words:
            # Add-one smoothing to avoid division by zero
            idf[qw] = math.log((num_docs + 1) / (df[qw] + 1)) + 1
            
        # Calculate TF-IDF vectors for documents
        scores = []
        for doc in doc_words:
            doc_tf_idf = 0.0
            doc_len = len(doc)
            if doc_len == 0:
                scores.append(0.0)
                continue
                
            for qw in query_words:
                tf = doc.count(qw) / doc_len
                doc_tf_idf += tf * idf[qw]
            scores.append(doc_tf_idf)
            
        # Normalize scores to 0-100 range
        max_score = max(scores) if scores else 0
        if max_score > 0:
            scores = [(s / max_score) * 100 for s in scores]
        return scores

    @classmethod
    def rank_results(cls, crawled_pages: List[Any], query: str, keywords: List[str]) -> List[RankedResult]:
        """Rank crawled pages using TF-IDF and domain authority."""
        if not crawled_pages:
            return []
            
        documents = [page.content for page in crawled_pages]
        relevance_scores = cls.calculate_tfidf(documents, keywords)
        
        ranked_list = []
        for idx, page in enumerate(crawled_pages):
            domain = cls.get_domain(page.url)
            
            # Find domain authority
            auth_score = 50.0  # default baseline
            for auth_domain, score in cls.AUTHORITY_DOMAINS.items():
                if auth_domain in domain:
                    auth_score = score
                    break
                    
            rel_score = relevance_scores[idx]
            
            # Combined score = 60% TF-IDF relevance + 40% Domain Authority
            combined_score = (0.6 * rel_score) + (0.4 * auth_score)
            
            # Create snippet (take first 200 characters of text if snippet is missing)
            snippet = page.content[:200].replace("\n", " ") + "..." if len(page.content) > 200 else page.content.replace("\n", " ")
            
            ranked_list.append({
                "url": page.url,
                "title": page.title or domain,
                "snippet": snippet,
                "domain": domain,
                "relevance_score": round(rel_score, 2),
                "authority_score": round(auth_score, 2),
                "combined_score": round(combined_score, 2)
            })
            
        # Sort by combined score descending
        ranked_list.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Add rank index and convert to RankedResult
        results = []
        for rank, item in enumerate(ranked_list, start=1):
            results.append(RankedResult(
                url=item["url"],
                title=item["title"],
                snippet=item["snippet"],
                domain=item["domain"],
                relevance_score=item["relevance_score"],
                authority_score=item["authority_score"],
                combined_score=item["combined_score"],
                rank=rank
            ))
            
        return results
