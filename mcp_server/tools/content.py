"""URL content extraction using httpx and BeautifulSoup."""

import httpx
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 30.0
MAX_CONTENT_LENGTH = 500_000


def extract_content(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Fetch a URL and extract its main text content.

    Strips scripts, styles, and navigation; prefers <article> or <main> tags.
    """
    if not url or not url.strip():
        raise ValueError("url must be a non-empty string")

    normalized_url = url.strip()
    if not normalized_url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")

    try:
        response = httpx.get(
            normalized_url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "SageResearchBot/1.0"},
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Request timed out for {normalized_url}") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"HTTP {exc.response.status_code} for {normalized_url}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Failed to fetch {normalized_url}: {exc}") from exc

    if len(response.text) > MAX_CONTENT_LENGTH:
        raise ValueError(f"Response too large from {normalized_url}")

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    main = soup.find("article") or soup.find("main") or soup.body
    if main is None:
        raise RuntimeError(f"No extractable content found at {normalized_url}")

    text = main.get_text(separator="\n", strip=True)
    if not text:
        raise RuntimeError(f"Page contained no readable text at {normalized_url}")

    return text
