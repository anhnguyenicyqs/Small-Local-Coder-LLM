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


def backup_workspace():
    import shutil
    import datetime
    workspace_path = pathlib.Path("workspace")
    if workspace_path.exists() and any(workspace_path.iterdir()):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        target_parent = pathlib.Path("backup")
        # Nếu đang đứng ở thư mục agent_system, backup nằm ở thư mục cha
        if not target_parent.exists() and pathlib.Path("../backup").exists():
            target_parent = pathlib.Path("../backup")
        if not target_parent.exists():
            target_parent = pathlib.Path("backup")
            target_parent.mkdir(exist_ok=True)
        
        backup_dir = target_parent / f"workspace_backup_{timestamp}"
        shutil.copytree(workspace_path, backup_dir)
        logger.info(f"Đã sao lưu workspace cũ sang: {backup_dir}")

        # Dọn dẹp toàn bộ file/thư mục cũ trong workspace để bắt đầu phiên chạy sạch
        for item in workspace_path.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                logger.warning(f"Không thể xóa {item}: {e}")
        logger.info("Đã làm sạch thư mục workspace.")


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

    print("\nChọn định dạng đầu ra mong muốn:")
    print("  1. Nhiều file Python (.py) [Multi-file]")
    print("  2. Jupyter Notebook (.ipynb)")
    print("  3. Cả hai (.py và .ipynb) [Mặc định]")
    fmt_choice = input("Định dạng (1-3 hoặc Enter): ").strip()
    output_format = "both"
    if fmt_choice == "1":
        output_format = "multi"
    elif fmt_choice == "2":
        output_format = "ipynb"

    task = input("\nNhập yêu cầu của bạn:\n> ").strip()
    if not task:
        print("Không có yêu cầu. Thoát.")
        sys.exit(1)
    return task, project_type, output_format


def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="3-Agent Python Code Generator")
    parser.add_argument("task", nargs="?", help="Mô tả yêu cầu")
    parser.add_argument("--type", choices=PROJECT_TYPES, help="Override auto-detect")
    parser.add_argument("--format", choices=["multi", "ipynb", "both"], default="both",
                        help="Định dạng đầu ra mong muốn: 'multi' (nhiều file .py), 'ipynb' (Jupyter Notebook), hoặc 'both' (cả hai)")
    parser.add_argument("--no-search", action="store_true",
                        help="Tắt web search (chạy offline hoàn toàn)")
    args = parser.parse_args()

    # Tắt search nếu yêu cầu
    if args.no_search:
        import tools.web_search as ws
        ws.web_search = lambda q, cache=None: ("(search disabled)", cache or {})
        logger.info("Web search: TẮT")

    if args.task:
        task, project_type, output_format = args.task, args.type, args.format
    else:
        task, project_type, output_format = interactive_mode()

    # Tự động sao lưu workspace cũ
    backup_workspace()

    # Auto-detect để hiển thị
    detected = project_type or detect_project_type(task)
    print(f"\n{'='*55}")
    print(f"Task    : {task}")
    print(f"Type    : {detected}{' (manual)' if project_type else ' (auto-detected)'}")
    print(f"Format  : {output_format}")
    print(f"Search  : {'OFF' if args.no_search else 'ON — Architect + Developer sẽ tra cứu khi cần'}")
    print(f"{'='*55}\n")

    final = run(task, project_type, output_format)

    # Xử lý convert Notebook và dọn dẹp định dạng sau khi chạy xong
    workspace_path = pathlib.Path("workspace")
    if final.get("final_output") and workspace_path.exists():
        py_files = list(workspace_path.glob("**/*.py"))
        source_py_files = [f for f in py_files if "test_" not in f.name]
        
        target_py = None
        if source_py_files:
            # Ưu tiên file có chứa cell marker "# %%"
            for f in source_py_files:
                if "# %%" in f.read_text(encoding="utf-8"):
                    target_py = f
                    break
            # Phục hồi: Lấy main.py hoặc solution.py hoặc file đầu tiên
            if not target_py:
                for name in ["main.py", "solution.py"]:
                    for f in source_py_files:
                        if f.name == name:
                            target_py = f
                            break
                    if target_py:
                        break
            if not target_py:
                target_py = source_py_files[0]
                
        # Convert sang notebook nếu người dùng yêu cầu ipynb hoặc both
        if target_py and output_format in ["ipynb", "both"]:
            try:
                from tools.notebook_converter import convert_py_to_ipynb
                ipynb_path = workspace_path / "solution.ipynb"
                convert_py_to_ipynb(target_py.read_text(encoding="utf-8"), str(ipynb_path))
                logger.info(f"Đã chuyển đổi {target_py.relative_to(workspace_path)} thành Jupyter Notebook tại: workspace/solution.ipynb")
            except Exception as e:
                logger.error(f"Lỗi khi xuất notebook: {e}")
                
        # Dọn dẹp nếu chỉ muốn lưu ipynb
        if output_format == "ipynb":
            for f in py_files:
                try:
                    f.unlink()
                except Exception:
                    pass
            logger.info("Đã dọn dẹp các tệp Python (.py) khỏi workspace theo cấu hình 'ipynb'")

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

        if output_format in ["multi", "both"]:
            print(f"\nOutput  : workspace/ (Đa file)")
        if output_format in ["ipynb", "both"]:
            print(f"Notebook: workspace/solution.ipynb")
    else:
        print("THẤT BẠI — Hard stop sau khi vượt quá số lần retry")
        print("Kiểm tra logs/ để xem chi tiết")
        if final.get("latest_error"):
            print(f"\nLỗi cuối:\n{final['latest_error'][:400]}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
