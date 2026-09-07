import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from datetime import datetime
import asyncio
from typing import List, Optional
import urllib.parse

class CrawledContent(BaseModel):
    url: str
    title: str
    content: str
    links: List[str]
    fetch_time: datetime
    status_code: int

class WebCrawler:
    def __init__(self, timeout: float = 10.0, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.headers = {"User-Agent": self.user_agent}

    async def crawl(self, url: str) -> Optional[CrawledContent]:
        """Crawl a single URL asynchronously and extract title, content, and outbound links."""
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return CrawledContent(
                        url=url,
                        title="",
                        content="",
                        links=[],
                        fetch_time=datetime.utcnow(),
                        status_code=response.status_code
                    )
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Strip out script, style, navigation, footer and noscript tags
                for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    script.extract()
                
                title = soup.title.string.strip() if soup.title else ""
                
                # Gather links
                links = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    # Resolve relative URLs to absolute links
                    full_url = urllib.parse.urljoin(url, href)
                    if full_url.startswith("http"):
                        links.append(full_url)
                
                # Extract and clean text
                text = soup.get_text(separator=" ")
                # Split lines, strip spaces, drop empty lines
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                cleaned_text = "\n".join(chunk for chunk in chunks if chunk)
                
                return CrawledContent(
                    url=url,
                    title=title,
                    content=cleaned_text,
                    links=list(set(links))[:30],  # limit outbound link collection to 30
                    fetch_time=datetime.utcnow(),
                    status_code=response.status_code
                )
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return CrawledContent(
                url=url,
                title="",
                content="",
                links=[],
                fetch_time=datetime.utcnow(),
                status_code=500
            )

    async def crawl_multiple(self, urls: List[str]) -> List[CrawledContent]:
        """Crawl multiple URLs concurrently."""
        tasks = [self.crawl(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
