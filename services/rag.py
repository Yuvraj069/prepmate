"""Azure AI Search retrieval for grounded PrepMate coaching."""
import os


class InterviewKnowledgeBase:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index = os.getenv("AZURE_SEARCH_INDEX")

    @property
    def configured(self):
        return bool(self.endpoint and self.key and self.index)

    def retrieve(self, query, limit=3):
        """Return compact passages from an Azure AI Search index.

        The index should expose `content` and optionally `title` fields. An empty
        list keeps coaching available when retrieval is not configured.
        """
        if not self.configured:
            return []
        try:
            import requests
            url = f"{self.endpoint}/indexes/{self.index}/docs/search?api-version=2024-07-01"
            body = {"search": query, "top": limit, "select": "title,content"}
            response = requests.post(url, headers={"api-key": self.key, "Content-Type": "application/json"}, json=body, timeout=8)
            response.raise_for_status()
            items = response.json().get("value", [])
            return [f"{item.get('title', 'PrepMate knowledge')}: {item.get('content', '')}"[:1800] for item in items if item.get("content")]
        except Exception:
            return []
