import requests
from urllib.parse import quote

THUNDER_BASE = "https://thunder.api.overdrive.com/v2"
LIBBY_SEARCH_BASE = "https://libbyapp.com/library/{library_key}/search/query-{query}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def check_availability(library_key: str, title: str, author: str) -> dict | None:
    """
    Search the OverDrive Thunder API for a book.

    Returns a dict with keys:
        title, isAvailable, estimatedWaitDays, copiesOwned, libby_url
    or None if not found in the catalog.
    """
    query = f"{title} {author}".strip()
    url = f"{THUNDER_BASE}/libraries/{library_key}/search"
    params = {
        "query": query,
        "format": "ebook,audiobook-mp3",
        "perPage": 3,
    }

    response = requests.get(url, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    items = data.get("items", [])
    if not items:
        return None

    # Take the first result
    item = items[0]
    availability = item.get("availability", {})

    libby_query = quote(title, safe="")
    libby_url = LIBBY_SEARCH_BASE.format(
        library_key=library_key, query=libby_query
    )

    return {
        "title": item.get("title", title),
        "isAvailable": availability.get("isAvailable", False),
        "estimatedWaitDays": availability.get("estimatedWaitDays"),
        "copiesOwned": availability.get("copiesOwned", 0),
        "libby_url": libby_url,
    }
