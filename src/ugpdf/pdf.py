"""Generate PDF from a tab page using UG's print endpoint."""

from __future__ import annotations

import re
from pathlib import Path

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


def _slugify(text: str) -> str:
    """Convert text to a filesystem-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _extract_tab_id(url: str) -> str:
    """Extract tab ID from Ultimate Guitar tab URL."""
    # Tab URLs look like: /tab/artist/song-title-chords-TABID
    # The ID is the last numeric part after the last hyphen
    parts = url.split("-")
    for part in reversed(parts):
        if part.isdigit():
            return part
    raise ValueError(f"Could not extract tab ID from URL: {url}")


async def generate_pdf(
    url: str,
    *,
    artist: str = "",
    title: str = "",
    output_dir: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """
    Generate PDF from a UG tab by clicking the Download PDF button.

    Navigates to the tab page, dismisses the privacy modal, clicks the
    Download PDF button to trigger the print view, then generates the PDF.

    Args:
        url: Full URL to the tab page.
        artist: Artist name (for filename).
        title: Song title (for filename).
        output_dir: Directory to save the PDF (defaults to cwd).
        output_path: Explicit output path (overrides auto-naming).

    Returns:
        Path to the generated PDF file.
    """
    if output_dir is None:
        output_dir = Path.cwd()

    if output_path is None:
        filename = _slugify(f"{artist} {title}") if artist and title else "tab"
        output_path = output_dir / f"{filename}.pdf"

    stealth = Stealth()
    async with stealth.use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1200, "height": 900},
        )
        page = await context.new_page()

        # Load the tab page
        await page.goto(url, wait_until="load", timeout=30000)

        # Dismiss privacy/consent modal if present
        try:
            await page.locator("#accept-btn").click(timeout=5000)
        except Exception:
            pass

        # Click "Download PDF" — opens the print view in a new tab
        async with context.expect_page() as new_page_info:
            await page.get_by_text("Download PDF", exact=True).click(timeout=5000)

        print_page = await new_page_info.value
        await print_page.wait_for_load_state("load")

        # Avoid fixed sleeps; only wait if the challenge is still visible.
        try:
            await print_page.wait_for_function(
                """() => {
                    const body = document.body;
                    if (!body) return false;
                    return !body.innerText.toLowerCase().includes('security verification');
                }""",
                timeout=10000,
            )
        except Exception:
            pass

        # Verify the print page loaded (not stuck on Cloudflare)
        body = await print_page.inner_text("body")
        if "security verification" in body.lower():
            await browser.close()
            raise RuntimeError(
                "Cloudflare blocked the print page. "
                "Try again in a moment, or check your network."
            )

        # Generate PDF from the print view
        await print_page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
            print_background=True,
        )

        await browser.close()

    return output_path
