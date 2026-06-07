from typing import TypedDict, Literal

ProjectType = Literal["fastapi", "flask", "pipeline", "scraping", "ml", "algorithm"]
OutputFormat = Literal["multi", "ipynb", "both"]

class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────
    task: str
    project_type: ProjectType
    output_format: OutputFormat

    # ── Artifacts ──────────────────────────────────────────
    architecture: str
    test_code: str
    source_code: str

    # ── Error pruning ──────────────────────────────────────
    latest_error: str

    # ── Web search ─────────────────────────────────────────
    search_cache: dict         # {query: result} tránh search trùng
    architect_search_log: str  # Ghi lại Architect đã search gì
    developer_search_log: str  # Ghi lại Developer đã search gì

    # ── Circuit breaker ────────────────────────────────────
    dev_retries: int
    arch_retries: int

    # ── Runtime info ───────────────────────────────────────
    final_output: str
