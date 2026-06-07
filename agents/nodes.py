"""
Ba agent chính: Architect, Tester, Developer.
Mỗi agent = 1 lần gọi Ollama stateless + optional web search trước khi gọi.
"""
from loguru import logger
from state import AgentState
from ollama_client import call_ollama, extract_code_block
from prompts import ARCHITECT_PROMPTS, TESTER_PROMPTS, DEVELOPER_PROMPTS
from tools.web_search import web_search, should_search


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_searches(queries: list[str], cache: dict, label: str) -> tuple[str, dict, str]:
    """
    Chạy nhiều search queries, trả về:
    - context text để nhét vào prompt
    - cache đã cập nhật
    - log string để lưu vào state
    """
    if not queries:
        return "", cache, ""

    sections = []
    log_lines = []

    for q in queries:
        result, cache = web_search(q, cache)
        sections.append(f"[Search: {q}]\n{result}")
        log_lines.append(f"✓ {q}")
        logger.info(f"[{label}] Searched: {q}")

    context = "\n\n".join(sections)
    log = "\n".join(log_lines)
    return context, cache, log


def _build_search_section(context: str) -> str:
    if not context:
        return ""
    return f"\n\n--- Thông tin tra cứu từ internet ---\n{context}\n---\n"


# ── Agent 1: Architect ────────────────────────────────────────────────────────

def architect_node(state: AgentState) -> dict:
    """
    Trạm 1: Đọc task → (search nếu cần) → sinh architecture.md
    Context bị xóa hoàn toàn sau khi trả về dict.
    """
    logger.info("=" * 55)
    logger.info("ARCHITECT bắt đầu")

    task = state["task"]
    ptype = state["project_type"]
    cache = state.get("search_cache") or {}

    # ── Bước 1: Quyết định có cần search không ──
    # Luôn search để cập nhật thông tin thư viện mới nhất
    base_queries = [f"Python {ptype} best practices 2025"]

    # Thêm query từ nội dung task
    task_queries = should_search(task)

    # Thêm query theo project type
    type_queries = {
        "fastapi":   ["FastAPI latest version features 2025"],
        "flask":     ["Flask modern patterns 2025"],
        "pipeline":  ["Python pandas ETL pipeline best practices"],
        "scraping":  ["Python web scraping playwright beautifulsoup 2025"],
        "ml":        ["scikit-learn latest version usage"],
        "algorithm": [],
    }

    all_queries = list(dict.fromkeys(
        base_queries + task_queries + type_queries.get(ptype, [])
    ))[:4]  # Max 4 queries để không tốn quá nhiều thời gian

    # ── Bước 2: Chạy search ──
    search_context, cache, search_log = _run_searches(
        all_queries, cache, "Architect"
    )
    search_section = _build_search_section(search_context)

    if search_log:
        logger.info(f"Architect search log:\n{search_log}")

    # ── Bước 3: Gọi Ollama ──
    system = ARCHITECT_PROMPTS.get(ptype, ARCHITECT_PROMPTS["algorithm"])

    user_msg = (
        f"Yêu cầu của người dùng:\n{task}"
        f"{search_section}"
        f"\nHãy tạo tài liệu kiến trúc chi tiết cho project này."
    )

    architecture = call_ollama(system, user_msg, label="Architect")

    logger.success(f"ARCHITECT xong — {len(architecture)} ký tự")
    logger.info("Context Architect bị xóa. Chỉ giữ architecture.md")

    return {
        "architecture":          architecture,
        "search_cache":          cache,
        "architect_search_log":  search_log,
        "latest_error":          "",
        "test_code":             "",
        "source_code":           "",
    }


# ── Agent 2: Tester ───────────────────────────────────────────────────────────

def tester_node(state: AgentState) -> dict:
    """
    Trạm 2: Đọc architecture → sinh test file.
    Tester KHÔNG search — đủ thông tin từ architecture.md Architect đã tra cứu.
    Context bị xóa sau khi trả về dict.
    """
    logger.info("=" * 55)
    logger.info("TESTER bắt đầu (không cần search — dùng architecture đã đủ)")

    ptype = state["project_type"]
    system = TESTER_PROMPTS.get(ptype, TESTER_PROMPTS["algorithm"])

    user_msg = (
        f"Tài liệu kiến trúc:\n{state['architecture']}\n\n"
        f"Yêu cầu gốc:\n{state['task']}\n\n"
        f"Viết file test đầy đủ theo kiến trúc trên."
    )

    raw = call_ollama(system, user_msg, label="Tester")
    test_code = extract_code_block(raw, "python")

    logger.success(f"TESTER xong — {len(test_code)} ký tự")
    logger.info("Context Tester bị xóa.")

    return {"test_code": test_code}


# ── Agent 3: Developer ────────────────────────────────────────────────────────

def developer_node(state: AgentState) -> dict:
    """
    Trạm 3: Đọc architecture + test + error → viết/sửa source code.
    Search khi gặp lỗi lạ hoặc cần biết API cụ thể để fix.
    Context bị xóa sau khi trả về dict.
    """
    attempt = state["dev_retries"] + 1
    logger.info("=" * 55)
    logger.info(f"DEVELOPER bắt đầu — lần thử {attempt}/3")

    cache = state.get("search_cache") or {}
    latest_error = state.get("latest_error", "")
    dev_search_log = state.get("developer_search_log", "")

    # ── Bước 1: Search nếu có lỗi cần tra cứu ──
    search_section = ""
    new_search_log = ""

    if latest_error:
        # Trích tên exception / lỗi từ error log để search
        error_queries = _extract_error_queries(latest_error, state["task"])

        if error_queries:
            search_context, cache, new_search_log = _run_searches(
                error_queries, cache, f"Developer-{attempt}"
            )
            search_section = _build_search_section(search_context)
            logger.info(f"Developer search log:\n{new_search_log}")
        else:
            logger.debug("Developer: không cần search cho lỗi này")

    # ── Bước 2: Xây dựng prompt ──
    ptype = state["project_type"]
    system = DEVELOPER_PROMPTS.get(ptype, DEVELOPER_PROMPTS["algorithm"])

    error_section = ""
    if latest_error:
        error_section = (
            f"\n\n⚠️ LỖI LẦN TRƯỚC (phải sửa):\n{latest_error}"
            f"\nPhân tích lỗi và sửa ĐÚNG chỗ đó."
        )

    user_msg = (
        f"Tài liệu kiến trúc:\n{state['architecture']}\n\n"
        f"File test cần pass:\n```python\n{state['test_code']}\n```"
        f"{error_section}"
        f"{search_section}"
        f"\nViết code hoàn chỉnh để pass toàn bộ test trên."
    )

    raw = call_ollama(system, user_msg, label=f"Developer-{attempt}")
    source_code = extract_code_block(raw, "python")

    logger.success(f"DEVELOPER xong — {len(source_code)} ký tự")
    logger.info("Context Developer bị xóa.")

    # Cộng dồn search log (để debug sau này)
    combined_log = "\n".join(filter(None, [dev_search_log, new_search_log]))

    return {
        "source_code":          source_code,
        "dev_retries":          state["dev_retries"] + 1,
        "search_cache":         cache,
        "developer_search_log": combined_log,
    }


# ── Helpers nội bộ ────────────────────────────────────────────────────────────

def _extract_error_queries(error_log: str, task: str) -> list[str]:
    """
    Phân tích error log, sinh query tìm kiếm phù hợp.
    Ưu tiên: ImportError > specific Exception > generic error.
    """
    import re
    queries = []
    error_lower = error_log.lower()

    # ImportError / ModuleNotFoundError → search thư viện
    import_match = re.search(
        r"(?:importerror|modulenotfounderror)[^\n]*'([^']+)'",
        error_lower
    )
    if import_match:
        lib = import_match.group(1).split(".")[0]
        queries.append(f"Python {lib} install usage example")
        return queries  # Import error rõ ràng, không cần thêm

    # AttributeError → search API đúng
    attr_match = re.search(
        r"attributeerror[^\n]*'([^']+)' object has no attribute '([^']+)'",
        error_lower
    )
    if attr_match:
        obj, attr = attr_match.groups()
        queries.append(f"Python {obj} {attr} correct usage")

    # Specific exceptions cần biết cách xử lý
    known_exceptions = [
        "validationerror", "jsondecodeerror", "connectionerror",
        "timeouterror", "keyerror", "valueerror", "typeerror",
    ]
    for exc in known_exceptions:
        if exc in error_lower:
            # Lấy thêm context từ task để search thêm chính xác
            task_words = " ".join(task.lower().split()[:5])
            queries.append(f"Python {exc} fix {task_words}")
            break

    # Lỗi liên quan đến thư viện cụ thể trong stack trace
    lib_in_trace = re.search(
        r'file ".*?site-packages[/\\]([\w\-]+)',
        error_log.lower()
    )
    if lib_in_trace:
        lib = lib_in_trace.group(1)
        queries.append(f"{lib} python error fix stackoverflow")

    return list(dict.fromkeys(queries))[:3]  # Max 3 queries
