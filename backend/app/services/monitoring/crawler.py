"""Web crawler for regulatory sources."""

import hashlib
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.regulation import RegulatorySource


class CrawlerResult:
    """Result from crawling a regulatory source."""

    def __init__(
        self,
        source: RegulatorySource,
        content: str,
        content_hash: str,
        etag: str | None = None,
        last_modified: str | None = None,
        links: list[str] | None = None,
        metadata: dict | None = None,
    ):
        self.source = source
        self.content = content
        self.content_hash = content_hash
        self.etag = etag
        self.last_modified = last_modified
        self.links = links or []
        self.metadata = metadata or {}
        self.crawled_at = datetime.now(UTC)

    @property
    def has_changed(self) -> bool:
        """Check if content has changed since last crawl."""
        if not self.source.last_content_hash:
            return True
        return self.content_hash != self.source.last_content_hash


class RegulatoryCrawler:
    """Crawler for regulatory websites."""

    def __init__(self):
        self.browser: Browser | None = None
        self.http_client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Initialize browser and HTTP client."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "ComplianceAgent/1.0 (Regulatory Monitoring Bot)",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources."""
        if self.browser:
            await self.browser.close()
        if self.http_client:
            await self.http_client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def crawl(self, source: RegulatorySource) -> CrawlerResult:
        """Crawl a regulatory source."""
        if source.parser_config.get("requires_javascript", False):
            return await self._crawl_with_browser(source)
        return await self._crawl_with_http(source)

    async def _crawl_with_http(self, source: RegulatorySource) -> CrawlerResult:
        """Crawl using simple HTTP requests."""
        headers = {}
        if source.last_etag:
            headers["If-None-Match"] = source.last_etag

        response = await self.http_client.get(source.url, headers=headers)

        if response.status_code == 304:
            # Not modified
            return CrawlerResult(
                source=source,
                content="",
                content_hash=source.last_content_hash or "",
                etag=source.last_etag,
            )

        response.raise_for_status()
        content = response.text
        content_hash = self._compute_hash(content)

        # Parse HTML
        soup = BeautifulSoup(content, "lxml")
        links = self._extract_links(soup, source.url)

        return CrawlerResult(
            source=source,
            content=content,
            content_hash=content_hash,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
            links=links,
            metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
            },
        )

    async def _crawl_with_browser(self, source: RegulatorySource) -> CrawlerResult:
        """Crawl using headless browser for JavaScript-heavy sites."""
        page: Page = await self.browser.new_page()
        try:
            await page.goto(source.url, wait_until="networkidle")

            # Wait for specific selector if configured
            if selector := source.parser_config.get("wait_for_selector"):
                await page.wait_for_selector(selector, timeout=10000)

            content = await page.content()
            content_hash = self._compute_hash(content)

            # Parse HTML
            soup = BeautifulSoup(content, "lxml")
            links = self._extract_links(soup, source.url)

            return CrawlerResult(
                source=source,
                content=content,
                content_hash=content_hash,
                links=links,
                metadata={
                    "rendered_with": "playwright",
                },
            )
        finally:
            await page.close()

    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        # Normalize whitespace for more stable hashing
        normalized = " ".join(content.split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract relevant links from the page."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Convert relative to absolute
            absolute_url = urljoin(base_url, href)
            # Filter for relevant links (PDFs, legal documents)
            if any(ext in absolute_url.lower() for ext in [".pdf", "/legal/", "/regulation/", "/directive/"]):
                links.append(absolute_url)
        return list(set(links))


class ChangeDetector:
    """Detect changes in regulatory content."""

    def __init__(self):
        pass

    def detect_changes(
        self,
        old_content: str,
        new_content: str,
        parser_type: str = "html",
    ) -> dict[str, Any]:
        """Detect and categorize changes between old and new content."""
        if parser_type == "html":
            return self._detect_html_changes(old_content, new_content)
        return self._detect_text_changes(old_content, new_content)

    def _detect_html_changes(self, old_content: str, new_content: str) -> dict[str, Any]:
        """Detect changes in HTML content."""
        old_soup = BeautifulSoup(old_content, "lxml") if old_content else None
        new_soup = BeautifulSoup(new_content, "lxml")

        old_text = old_soup.get_text(separator="\n") if old_soup else ""
        new_text = new_soup.get_text(separator="\n")

        # Simple diff
        old_lines = set(old_text.split("\n"))
        new_lines = set(new_text.split("\n"))

        added = new_lines - old_lines
        removed = old_lines - new_lines

        return {
            "has_changes": bool(added or removed),
            "added_count": len(added),
            "removed_count": len(removed),
            "added_sample": list(added)[:10],
            "removed_sample": list(removed)[:10],
        }

    def _detect_text_changes(self, old_content: str, new_content: str) -> dict[str, Any]:
        """Detect changes in plain text content."""
        old_lines = set(old_content.split("\n")) if old_content else set()
        new_lines = set(new_content.split("\n"))

        added = new_lines - old_lines
        removed = old_lines - new_lines

        return {
            "has_changes": bool(added or removed),
            "added_count": len(added),
            "removed_count": len(removed),
        }
