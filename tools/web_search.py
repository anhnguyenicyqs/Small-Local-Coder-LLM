"""
Web Search Tool — 3 tầng tìm kiếm:
  1. DuckDuckGo Instant Answer (nhanh, không cần key)
  2. DuckDuckGo HTML scrape (fallback khi Instant trả về rỗng)
  3. PyPI JSON API (cho query liên quan đến thư viện Python)

Cache kết quả trong AgentState để tránh search lặp.
"""
import requests
import re
import json
from urllib.parse import quote_plus
from loguru import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AgentSearchBot/1.0)"
}
TIMEOUT = 12


# ── Tầng 1: DuckDuckGo Instant Answer ────────────────────────────────────────

def _ddg_instant(query: str) -> str:
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query, "format": "json",
            "no_html": 1, "skip_disambig": 1,
            "no_redirect": 1,
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        data = r.json()

        parts = []
        if data.get("Abstract"):
            parts.append(data["Abstract"][:500])
        if data.get("Answer"):
            parts.append(f"Answer: {data['Answer']}")
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                parts.append(f"- {topic['Text'][:200]}")

        return "\n".join(parts) if parts else ""
    except Exception as e:
        logger.debug(f"DDG instant failed: {e}")
        return ""


# ── Tầng 2: DuckDuckGo HTML scrape ───────────────────────────────────────────

def _ddg_html(query: str) -> str:
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</a>',
            r.text, re.DOTALL
        )
        cleaned = []
        for s in snippets[:4]:
            text = re.sub(r"<[^>]+>", "", s).strip()
            if text and len(text) > 30:
                cleaned.append(text[:250])
        return "\n".join(cleaned) if cleaned else ""
    except Exception as e:
        logger.debug(f"DDG html failed: {e}")
        return ""


# ── Tầng 3: PyPI API (cho thư viện Python) ───────────────────────────────────

def _pypi_info(lib_name: str) -> str:
    try:
        r = requests.get(
            f"https://pypi.org/pypi/{lib_name}/json",
            headers=HEADERS, timeout=TIMEOUT
        )
        if r.status_code != 200:
            return ""
        data = r.json()
        info = data.get("info", {})
        version = info.get("version", "")
        summary = info.get("summary", "")
        home = info.get("home_page") or info.get("project_url") or ""
        requires = ", ".join((info.get("requires_dist") or [])[:5])
        return (
            f"PyPI: {lib_name} v{version}\n"
            f"Summary: {summary}\n"
            f"Home: {home}\n"
            f"Requires: {requires}"
        ).strip()
    except Exception as e:
        logger.debug(f"PyPI failed for {lib_name}: {e}")
        return ""


# ── Public API ────────────────────────────────────────────────────────────────

def web_search(query: str, cache: dict | None = None) -> tuple[str, dict]:
    """
    Tìm kiếm web với 3-tầng fallback.

    Returns:
        (result_text, updated_cache)
    """
    cache = cache or {}

    # Cache hit
    if query in cache:
        logger.debug(f"Search cache hit: {query}")
        return cache[query], cache

    logger.info(f"Searching: {query}")

    result = _ddg_instant(query)

    # Fallback tầng 2
    if not result or len(result) < 50:
        result = _ddg_html(query)

    # Nếu query có tên thư viện Python → bổ sung PyPI
    lib_match = re.search(
        r"\b(fastapi|flask|pandas|numpy|scikit.learn|playwright|"
        r"beautifulsoup4|bs4|requests|httpx|sqlalchemy|pydantic|"
        r"langchain|langgraph|ollama|pytest|celery|redis|aiohttp)\b",
        query.lower()
    )
    if lib_match:
        lib = lib_match.group(1).replace("scikit.learn", "scikit-learn")
        pypi = _pypi_info(lib)
        if pypi:
            result = f"{result}\n\n{pypi}".strip() if result else pypi

    if not result:
        result = "Không tìm thấy kết quả phù hợp."

    # Giới hạn kích thước để không ăn context
    result = result[:1200]

    cache[query] = result
    logger.success(f"Search xong: {len(result)} ký tự")
    return result, cache


def should_search(text: str) -> list[str]:
    """
    Phân tích text, trả về list query nên search.
    Architect và Developer gọi hàm này để tự quyết định.
    """
    queries = []
    text_lower = text.lower()

    # Thư viện/framework cụ thể kèm version
    version_pattern = re.findall(
        r'([\w\-]+)\s*(?:v|version)?\s*(\d+\.\d+[\w\.]*)',
        text_lower
    )
    for lib, ver in version_pattern:
        if len(lib) > 2:
            queries.append(f"{lib} {ver} python usage example")

    # Từ khóa cần tra cứu
    lookup_triggers = [
        (r'\bhow to\b', lambda m, t: t[max(0,m.start()-10):m.end()+60].strip()),
        (r'\blatest\b', lambda m, t: re.sub(r'\blatest\b', '', t[max(0,m.start()-20):m.end()+50]).strip() + " python latest"),
        (r'\bnew api\b', lambda m, t: t[max(0,m.start()-20):m.end()+60].strip()),
        (r'\bcách dùng\b', lambda m, t: t[max(0,m.start()):m.end()+60].strip() + " python example"),
    ]

    for pattern, fn in lookup_triggers:
        for m in re.finditer(pattern, text_lower):
            q = fn(m, text_lower)
            if q and len(q) > 10:
                queries.append(q[:120])

    # Thư viện chưa quen (không có trong training data cũ)
    unknown_libs = re.findall(
        r'\bpip install\s+([\w\-]+)', text_lower
    )
    for lib in unknown_libs:
        queries.append(f"{lib} python library documentation")

    return list(dict.fromkeys(queries))[:4]  # Max 4 queries, dedup
