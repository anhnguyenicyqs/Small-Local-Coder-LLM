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
    Trạm 4: Ghi file đệ quy, chạy pytest, trả về kết quả.
    """
    logger.info("=" * 50)
    logger.info("COMPILER bắt đầu")

    WORKSPACE.mkdir(exist_ok=True)

    # Dọn dẹp các file cũ trong workspace để tránh các tệp mồ côi từ phiên chạy/vòng lặp trước
    import shutil
    for item in WORKSPACE.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            logger.warning(f"Không thể dọn dẹp {item} trong compiler: {e}")

    # 1. Parse và ghi source code
    src_files = _parse_and_write_files(state["source_code"], WORKSPACE)
    if not src_files:
        # Fallback ghi phẳng
        default_path = WORKSPACE / "solution.py"
        default_path.write_text(state["source_code"], encoding="utf-8")
        src_files = ["solution.py"]
        logger.info(f"Fallback ghi source code vào {default_path}")
    else:
        logger.info(f"Đã ghi các file nguồn: {', '.join(src_files)}")

    # 2. Parse và ghi test code
    test_files = _parse_and_write_files(state["test_code"], WORKSPACE)
    if not test_files:
        # Fallback ghi phẳng
        default_path = WORKSPACE / "test_solution.py"
        default_path.write_text(state["test_code"], encoding="utf-8")
        test_files = ["test_solution.py"]
        logger.info(f"Fallback ghi test code vào {default_path}")
    else:
        logger.info(f"Đã ghi các file test: {', '.join(test_files)}")

    # 3. Tự động sinh requirements.txt từ architecture
    _generate_requirements(state.get("architecture", ""), WORKSPACE)

    # 4. Chạy pytest
    logger.info("Chạy pytest...")

    # Chạy pytest đệ quy từ workspace/ để tự động phát hiện mọi file test
    # Chúng ta cũng thêm PYTHONPATH trỏ về workspace để các relative import thành công
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(WORKSPACE.resolve()) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "-v",                    # Verbose để thấy từng test
            "--tb=short",            # Stack trace ngắn
            "--no-header",
            "-p", "no:cacheprovider",
            "--timeout=30",          # Mỗi test max 30s
        ],
        capture_output=True,
        text=True,
        cwd=WORKSPACE,
        env=env,
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


def _parse_and_write_files(content: str, base_dir: pathlib.Path) -> list[str]:
    import re
    pattern = r'<file\s+path=["\']([^"\']+)["\']\s*>(.*?)</file>'
    matches = re.findall(pattern, content, re.DOTALL)
    
    written_files = []
    for rel_path, file_content in matches:
        file_content = file_content.strip()
        full_path = base_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(file_content, encoding="utf-8")
        written_files.append(rel_path)
    return written_files


def _generate_requirements(architecture: str, base_dir: pathlib.Path) -> None:
    import re
    # Trích xuất tên các thư viện từ lệnh 'pip install'
    matches = re.findall(r"pip install\s+([\w\-\s>=<]+)", architecture, re.IGNORECASE)
    libs = []
    for match in matches:
        for lib in match.split():
            lib = lib.strip()
            # Bỏ qua các cờ option của pip
            if lib and not lib.startswith("-"):
                libs.append(lib)
    if libs:
        req_path = base_dir / "requirements.txt"
        req_path.write_text("\n".join(sorted(set(libs))), encoding="utf-8")
        logger.info(f"Đã tạo requirements.txt với các thư viện: {list(set(libs))}")


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
            "E   ", "ERRORS", "raises", "workspace\\", "workspace/",
            "tests\\", "tests/", "src\\", "src/", "in <module>"
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
