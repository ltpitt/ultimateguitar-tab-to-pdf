"""Select the best tab version from search results."""

from __future__ import annotations

from .search import TabResult


def pick_best(results: list[TabResult]) -> TabResult | None:
    """
    Pick the best tab version from search results.

    Strategy:
        1. Exclude official/verified tabs (they're pay-to-view)
        2. Prefer tabs with highest vote count (community validation)
        3. Among tied votes, prefer higher rating

    Returns:
        The best TabResult, or None if no suitable version found.
    """
    # Filter out official tabs
    candidates = [r for r in results if not r.is_official]

    if not candidates:
        return None

    # Sort by votes (desc), then rating (desc)
    candidates.sort(key=lambda r: (r.votes, r.rating), reverse=True)
    return candidates[0]
