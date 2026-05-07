from typing import List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


class WebSearchTool:
    def execute(self, query: str, limit: int = 5) -> List[dict]:
        # Deterministic fallback strategy without requiring extra search APIs.
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            titles = [a.get_text(strip=True) for a in soup.select("a.result__a")[:limit]]
            return [{"title": t} for t in titles]
        except Exception:
            return [{"title": f"search-unavailable:{query}"}]
