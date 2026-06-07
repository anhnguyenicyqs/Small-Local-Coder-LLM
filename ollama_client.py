import requests
import json
from loguru import logger

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:14b"
NUM_CTX = 16384

def call_ollama(system_prompt: str, user_message: str, label: str = "agent") -> str:
    """
    Gọi Ollama hoàn toàn stateless.
    Mỗi lần gọi = session mới, không reuse context.
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "options": {
            "num_ctx": NUM_CTX,
            "num_gpu_layers": 99,   # Toàn bộ lên VRAM RTX 5060 Ti
            "temperature": 0.2,     # Thấp để code ổn định
        },
        "stream": False,
    }

    logger.info(f"[{label}] Gọi Ollama — model={MODEL}, ctx={NUM_CTX}")
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        r.raise_for_status()
        content = r.json()["message"]["content"]
        logger.info(f"[{label}] Nhận response — {len(content)} ký tự")
        return content
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Không kết nối được Ollama. Chạy: ollama serve")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def extract_code_block(text: str, lang: str = "python") -> str:
    """
    Trích code từ markdown code block.
    Nếu không có block, trả về toàn bộ text.
    """
    import re
    pattern = rf"```{lang}\s*(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    # Fallback: thử ```  không có ngôn ngữ
    matches = re.findall(r"```\s*(.*?)```", text, re.DOTALL)
    if matches:
        return matches[0].strip()
    return text.strip()
