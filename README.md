# 3-Agent Python Code Generator

Hệ thống tự động viết và test code Python dùng Qwen 2.5 Coder 14B + LangGraph.

## Yêu cầu phần cứng
- RTX 5060 Ti 16GB (hoặc GPU >= 12GB VRAM)
- RAM >= 16GB
- Python 3.10+

## Cài đặt

```bash
# 1. Cài Ollama và pull model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder:14b

# 2. Tạo virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Tạo thư mục cần thiết
mkdir -p workspace logs
```

## Chạy

```bash
# Interactive mode
python main.py

# Truyền task trực tiếp
python main.py "Viết FastAPI CRUD cho User model với id, name, email"

# Chỉ định loại project
python main.py "Implement merge sort" --type algorithm

# FastAPI
python main.py "REST API quản lý todo list với CRUD đầy đủ" --type fastapi

# Data pipeline
python main.py "Đọc CSV sales, tính tổng doanh thu theo tháng, xuất báo cáo" --type pipeline

# ML
python main.py "Train model phân loại spam email dùng Naive Bayes" --type ml

# Web scraping
python main.py "Scrape tên và giá sản phẩm từ trang HTML, lưu JSON" --type scraping
```

## Cấu trúc project

```
agent_system/
├── main.py              ← Entry point
├── graph.py             ← LangGraph orchestrator + circuit breaker
├── state.py             ← AgentState TypedDict
├── prompts.py           ← System prompts cho từng agent × project type
├── ollama_client.py     ← Ollama API caller (stateless)
├── agents/
│   └── nodes.py         ← Architect, Tester, Developer nodes
├── tools/
│   └── compiler.py      ← MCP Compiler (pytest runner + error pruner)
├── workspace/           ← File output: solution.py, test_solution.py
├── logs/                ← Log file mỗi lần chạy
└── requirements.txt
```

## Luồng hoạt động

```
Task → detect_type → Architect → Tester → Developer → Compiler
                          ↑            ↑         ↓
                          |            └─ retry ─┤ (< 3 lần)
                          └──── re-design ───────┘ (>= 3 lần, < 2 arch)
                                                  → HARD STOP (>= 2 arch)
```

## Tuỳ chỉnh

### Đổi model
Trong `ollama_client.py`:
```python
MODEL = "qwen2.5-coder:7b"   # Nhẹ hơn nếu VRAM < 12GB
MODEL = "codellama:13b"       # Thay thế khác
```

### Đổi context window
```python
NUM_CTX = 8192    # Giảm nếu bị OOM
NUM_CTX = 32768   # Tăng nếu còn dư VRAM
```

### Thêm project type mới
Trong `prompts.py`: thêm key vào `ARCHITECT_PROMPTS`, `TESTER_PROMPTS`, `DEVELOPER_PROMPTS`.
Trong `graph.py`: thêm keywords vào `TYPE_KEYWORDS`.
