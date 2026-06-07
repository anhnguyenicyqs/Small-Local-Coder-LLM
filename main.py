#!/usr/bin/env python3
"""
Entry point — chạy từ terminal:
    python main.py "Viết FastAPI CRUD cho User model"
    python main.py "Implement quicksort" --type algorithm
    python main.py  (interactive mode)
"""
import sys
import argparse
import pathlib
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO", colorize=True,
)
logger.add(
    "logs/run_{time:YYYY-MM-DD_HH-mm-ss}.log",
    format="{time} | {level} | {message}",
    level="DEBUG", rotation="10 MB",
)

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from graph import run, detect_project_type

PROJECT_TYPES = ["fastapi", "flask", "pipeline", "scraping", "ml", "algorithm"]

EXAMPLES = {
    "fastapi":   "Viết FastAPI CRUD API cho User model với id, name, email, created_at",
    "flask":     "Viết Flask app có endpoint /health và /echo nhận POST body",
    "pipeline":  "Đọc CSV có cột: name, age, salary. Lọc age>18, fill NaN, xuất CSV mới",
    "scraping":  "Scrape tiêu đề và giá sản phẩm từ trang HTML tĩnh, trả về list dict",
    "ml":        "Train RandomForest phân loại Iris dataset, lưu model, load và predict",
    "algorithm": "Implement Dijkstra tìm đường đi ngắn nhất trên đồ thị có trọng số",
}


def interactive_mode():
    print("\n=== 3-Agent Python Code Generator (với Web Search) ===")
    print("Powered by Qwen 2.5 Coder 14B + LangGraph\n")
    print("Chọn loại project (Enter để auto-detect):")
    for i, pt in enumerate(PROJECT_TYPES, 1):
        print(f"  {i}. {pt:12} — {EXAMPLES[pt][:55]}...")

    choice = input("\nLoại project (1-6 hoặc Enter): ").strip()
    project_type = None
    if choice.isdigit() and 1 <= int(choice) <= 6:
        project_type = PROJECT_TYPES[int(choice) - 1]

    task = input("\nNhập yêu cầu của bạn:\n> ").strip()
    if not task:
        print("Không có yêu cầu. Thoát.")
        sys.exit(1)
    return task, project_type


def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="3-Agent Python Code Generator")
    parser.add_argument("task", nargs="?", help="Mô tả yêu cầu")
    parser.add_argument("--type", choices=PROJECT_TYPES, help="Override auto-detect")
    parser.add_argument("--no-search", action="store_true",
                        help="Tắt web search (chạy offline hoàn toàn)")
    args = parser.parse_args()

    # Tắt search nếu yêu cầu
    if args.no_search:
        import tools.web_search as ws
        ws.web_search = lambda q, cache=None: ("(search disabled)", cache or {})
        logger.info("Web search: TẮT")

    if args.task:
        task, project_type = args.task, args.type
    else:
        task, project_type = interactive_mode()

    # Auto-detect để hiển thị
    detected = project_type or detect_project_type(task)
    print(f"\n{'='*55}")
    print(f"Task    : {task}")
    print(f"Type    : {detected}{' (manual)' if project_type else ' (auto-detected)'}")
    print(f"Search  : {'OFF' if args.no_search else 'ON — Architect + Developer sẽ tra cứu khi cần'}")
    print(f"{'='*55}\n")

    final = run(task, project_type)

    print(f"\n{'='*55}")
    if final.get("final_output"):
        print("THÀNH CÔNG")
        print(f"Type    : {final.get('project_type')}")

        # Hiển thị search log
        arch_log = final.get("architect_search_log", "")
        dev_log  = final.get("developer_search_log", "")
        if arch_log:
            print(f"\nArchitect đã search:\n{arch_log}")
        if dev_log:
            print(f"\nDeveloper đã search:\n{dev_log}")

        print(f"\nOutput  : workspace/solution.py")
        print(f"Test    : workspace/test_solution.py")

        src = final.get("source_code", "")
        if src:
            lines = src.splitlines()
            print(f"\n--- Preview ({min(20, len(lines))} dòng đầu) ---")
            print("\n".join(lines[:20]))
            if len(lines) > 20:
                print(f"... ({len(lines)-20} dòng nữa)")
    else:
        print("THẤT BẠI — Hard stop sau khi vượt quá số lần retry")
        print("Kiểm tra logs/ để xem chi tiết")
        if final.get("latest_error"):
            print(f"\nLỗi cuối:\n{final['latest_error'][:400]}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
