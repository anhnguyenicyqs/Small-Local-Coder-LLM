"""
MCP Compiler Tool: ghi file → chạy pytest → prune lỗi
Đây là Trạm 4 trong graph.
"""
import subprocess
import pathlib
import tempfile
import re
import sys
from loguru import logger
from state import AgentState

WORKSPACE = pathlib.Path("workspace")
MAX_ERROR_LINES = 60       # Hard cap tổng số dòng lỗi
HEAD_LINES = 40            # Lấy 40 dòng đầu
TAIL_LINES = 20            # Lấy 20 dòng cuối


def compiler_node(state: AgentState) -> dict:
    """
    Trạm 4: Ghi file, chạy pytest, trả về kết quả.
    """
    logger.info("=" * 50)
    logger.info("COMPILER bắt đầu")

    WORKSPACE.mkdir(exist_ok=True)

    # Ghi source code
    src_path = WORKSPACE / "solution.py"
    src_path.write_text(state["source_code"], encoding="utf-8")

    # Ghi test code
    test_path = WORKSPACE / "test_solution.py"
    test_path.write_text(state["test_code"], encoding="utf-8")

    logger.info(f"Đã ghi: {src_path}, {test_path}")
    logger.info("Chạy pytest...")

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            test_path.name,
            "-v",                    # Verbose để thấy từng test
            "--tb=short",            # Stack trace ngắn
            "--no-header",
            "-p", "no:cacheprovider",
            "--timeout=30",          # Mỗi test max 30s (cần pytest-timeout)
        ],
        capture_output=True,
        text=True,
        cwd=WORKSPACE,
        timeout=120,                 # Toàn bộ test suite max 2 phút
    )

    output = result.stdout + result.stderr

    if result.returncode == 0:
        logger.success("COMPILER: Tất cả test PASS!")
        _log_summary(output)
        return {
            "latest_error": "",
            "final_output": output,
        }

    # Test fail → prune lỗi
    pruned = _prune_error(output)
    logger.warning(f"COMPILER: Test FAIL\n{pruned[:500]}...")

    return {"latest_error": pruned}


def _prune_error(raw: str) -> str:
    """
    Giữ lại phần thông tin nhất của pytest output.
    Loại bỏ noise, giữ trong MAX_ERROR_LINES dòng.
    """
    lines = raw.splitlines()

    # Ưu tiên dòng có thông tin lỗi thực sự
    priority_lines = []
    normal_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Dòng có giá trị cao
        if any(k in line for k in [
            "FAILED", "ERROR", "assert", "AssertionError",
            "Exception", "Error:", "def test_", "short test summary",
            "E   ", "ERRORS", "raises"
        ]):
            priority_lines.append(line)
        else:
            normal_lines.append(line)

    # Lấy head + tail từ tất cả lines
    all_lines = lines
    if len(all_lines) > MAX_ERROR_LINES:
        head = all_lines[:HEAD_LINES]
        tail = all_lines[-TAIL_LINES:]
        all_lines = head + ["... [pruned] ..."] + tail

    # Nếu có priority lines, đặt lên đầu
    if priority_lines:
        result = priority_lines[:20] + ["---"] + all_lines
        return "\n".join(result[:MAX_ERROR_LINES])

    return "\n".join(all_lines)


def _log_summary(output: str) -> None:
    """Log dòng summary của pytest (passed/failed count)."""
    for line in reversed(output.splitlines()):
        if "passed" in line or "failed" in line or "error" in line:
            logger.info(f"pytest summary: {line.strip()}")
            break
