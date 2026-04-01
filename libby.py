import requests
from urllib.parse import quote

THUNDER_BASE = "https://thunder.api.overdrive.com/v2"
LIBBY_SEARCH_BASE = "https://libbyapp.com/library/{library_key}/search/query-{query}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/14.0.2 Safari/605.1.15"
    ),
    "Referer": "https://libbyapp.com/",
    "Origin": "https://libbyapp.com",
}


def check_availability(library_key: str, title: str, author: str) -> dict | None:
    """
    Search the OverDrive Thunder API for a book.

    Returns a dict with keys:
        title, isAvailable, estimatedWaitDays, copiesOwned, libby_url
    or None if not found in the catalog.
    """
    query = f"{title} {author}".strip()
    url = f"{THUNDER_BASE}/libraries/{library_key}/media"
    params = {
        "query": query,
        "mediaType": "ebook",
        "perPage": 3,
        "x-client-id": "dewey",
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
