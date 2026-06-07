"""
LangGraph orchestrator với web search tích hợp.

Graph flow:
  detect_type → architect → tester → developer → compiler → router
      ↑ (search)     ↑ (search nếu error)
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent / "agents"))
sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))

from langgraph.graph import StateGraph, END
from loguru import logger

from state import AgentState
from agents.nodes import architect_node, tester_node, developer_node
from tools.compiler import compiler_node


# ── Auto-detect project type ──────────────────────────────────────────────────

TYPE_KEYWORDS = {
    "fastapi":   ["fastapi", "rest api", "endpoint", "openapi", "swagger", "pydantic"],
    "flask":     ["flask", "blueprint", "jinja", "render_template"],
    "pipeline":  ["etl", "pipeline", "csv", "dataframe", "pandas",
                  "transform", "json xử lý", "data pipeline"],
    "scraping":  ["scraping", "crawl", "beautifulsoup", "playwright",
                  "selenium", "web scrape", "scrape", "lấy dữ liệu web",
                  "thu thập web", "crawl web"],
    "ml":        ["machine learning", "model", "train", "sklearn",
                  "tensorflow", "pytorch", "neural", "classification",
                  "regression", "predict", "huấn luyện"],
    "algorithm": ["thuật toán", "algorithm", "sort", "search", "tree",
                  "graph", "dp", "dynamic programming", "data structure"],
}

def detect_project_type(task: str) -> str:
    task_lower = task.lower()
    scores = {pt: 0 for pt in TYPE_KEYWORDS}
    for pt, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in task_lower:
                scores[pt] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "algorithm"


# ── Node wrappers ─────────────────────────────────────────────────────────────

def detect_type_node(state: AgentState) -> dict:
    ptype = state["project_type"] or detect_project_type(state["task"])
    logger.info(f"Project type: {ptype}")
    return {"project_type": ptype}


def router_node(state: AgentState) -> dict:
    retries = state["dev_retries"]
    arch_retries = state["arch_retries"]

    if retries >= 3:
        if arch_retries < 2:
            logger.error(f"dev_retries={retries} >= 3 → ESCALATE về Architect (arch #{arch_retries+1})")
            return {"dev_retries": 0, "arch_retries": arch_retries + 1}
        else:
            logger.critical("arch_retries >= 2 → HARD STOP")
    else:
        logger.warning(f"dev_retries={retries} < 3 → retry Developer")
    return {}


# ── Conditional edges ─────────────────────────────────────────────────────────

def after_compiler(state: AgentState) -> str:
    return "success" if not state.get("latest_error") else "fail"

def after_router(state: AgentState) -> str:
    if state["dev_retries"] == 0 and state["arch_retries"] > 0:
        return "hard_stop" if state["arch_retries"] >= 2 else "re_architect"
    return "retry_dev" if state["dev_retries"] < 3 else "hard_stop"


# ── Build & run ───────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("detect_type", detect_type_node)
    g.add_node("architect",   architect_node)
    g.add_node("tester",      tester_node)
    g.add_node("developer",   developer_node)
    g.add_node("compiler",    compiler_node)
    g.add_node("router",      router_node)

    g.set_entry_point("detect_type")
    g.add_edge("detect_type", "architect")
    g.add_edge("architect",   "tester")
    g.add_edge("tester",      "developer")
    g.add_edge("developer",   "compiler")

    g.add_conditional_edges("compiler", after_compiler, {
        "success": END,
        "fail":    "router",
    })
    g.add_conditional_edges("router", after_router, {
        "retry_dev":    "developer",
        "re_architect": "architect",
        "hard_stop":    END,
    })
    return g.compile()


def run(task: str, project_type: str = None) -> AgentState:
    app = build_graph()
    initial: AgentState = {
        "task":                  task,
        "project_type":          project_type or "",
        "architecture":          "",
        "test_code":             "",
        "source_code":           "",
        "latest_error":          "",
        "search_cache":          {},
        "architect_search_log":  "",
        "developer_search_log":  "",
        "dev_retries":           0,
        "arch_retries":          0,
        "final_output":          "",
    }
    logger.info(f"Pipeline bắt đầu: {task[:80]}...")
    final = app.invoke(initial)
    if final.get("final_output"):
        logger.success("Pipeline THÀNH CÔNG")
    else:
        logger.error("Pipeline kết thúc — hard stop hoặc timeout")
    return final
