"""Search Ultimate Guitar for tabs using headless browser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlencode

from playwright.async_api import async_playwright

SEARCH_URL = "https://www.ultimate-guitar.com/search.php"


@dataclass
class TabResult:
    """A single tab search result."""

    title: str
    artist: str
    url: str
    rating: float  # 0-5 stars
    votes: int
    type: str  # "Chords", "Text Tab", "Guitar Pro", etc.
    is_official: bool

    @property
    def display_votes(self) -> str:
        """Human-friendly vote count."""
        if self.votes >= 1000:
            return f"{self.votes / 1000:.1f}K"
        return str(self.votes)


def _parse_votes(text: str) -> int:
    """Parse vote count string like '4,225' or '21.1K' to int."""
    text = text.strip().replace(",", "")
    if not text or text == "0":
        return 0
    if text.upper().endswith("K"):
        return int(float(text[:-1]) * 1000)
    try:
        return int(text)
    except ValueError:
        return 0


def _artist_from_url(url: str) -> str:
    """Extract artist name from UG tab URL (e.g. /tab/nirvana/... -> Nirvana)."""
    match = re.search(r"/tab/([^/]+)/", url)
    if not match:
        return "Unknown"
    raw = match.group(1)
    # Convert slug to title case: "led-zeppelin" -> "Led Zeppelin"
    return raw.replace("-", " ").title()


async def search(query: str, *, tab_type: str = "") -> list[TabResult]:
    """
    Search Ultimate Guitar for tabs matching the query.

    Uses headless Chromium to render the page and extract results from DOM.

    Args:
        query: Free-text search (e.g. "teen spirit nirvana")
        tab_type: Optional filter: "Chords", "Tab", etc.

    Returns:
        List of TabResult sorted by votes descending.
    """
    params = urlencode({"search_type": "title", "value": query})
    url = f"{SEARCH_URL}?{params}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # Extract results from the rendered DOM
        raw_results = await page.evaluate("""() => {
            const rows = document.querySelectorAll('.oRSaY');
            const data = [];
            for (const row of rows) {
                const link = row.querySelector("a[href*='/tab/']");
                if (!link) continue;

                const href = link.getAttribute('href');
                const title = link.innerText.trim();

                // Vote count
                const voteEl = row.querySelector('[data-exclude-page-guardian]');
                const votes = voteEl ? voteEl.innerText.trim() : '0';

                // Tab type (last column)
                const typeEl = row.querySelector('.okCUx');
                const type = typeEl ? typeEl.innerText.trim() : '';

                // Star rating: count filled vs total
                const allStars = row.querySelectorAll('span._7OgtD');
                const emptyStars = row.querySelectorAll('span._7OgtD._5FNKh');
                const filled = allStars.length - emptyStars.length;

                // Artist name from the group header (badge column)
                const badgeSpan = row.querySelector('.nGwD6 a[href*="/artist/"]');
                const artist = badgeSpan ? badgeSpan.innerText.trim() : '';

                data.push({
                    href: href || '',
                    title,
                    votes,
                    type,
                    stars: allStars.length > 0 ? filled : 0,
                    totalStars: allStars.length || 5,
                    artist
                });
            }
            return data;
        }""")

        await browser.close()

    # Parse into TabResult objects
    results: list[TabResult] = []
    current_artist = ""
    for item in raw_results:
        item_type = item.get("type", "")
        if not item_type:
            continue

        # Track the current artist (UG groups results by artist)
        if item.get("artist"):
            current_artist = item["artist"]

        # Filter by type if specified
        if tab_type and tab_type.lower() not in item_type.lower():
            continue

        url = item.get("href", "")
        if not url:
            continue

        # Detect official/pro tabs (pay-to-view)
        is_official = item_type.lower() in ("official", "pro", "power")

        total_stars = item.get("totalStars", 5) or 5
        rating = (item.get("stars", 0) / total_stars) * 5.0

        artist = current_artist or _artist_from_url(url)

        results.append(
            TabResult(
                title=item.get("title", "Unknown"),
                artist=artist,
                url=url,
                rating=round(rating, 1),
                votes=_parse_votes(item.get("votes", "0")),
                type=item_type,
                is_official=is_official,
            )
        )

    # Sort by votes descending
    results.sort(key=lambda r: r.votes, reverse=True)
    return results
