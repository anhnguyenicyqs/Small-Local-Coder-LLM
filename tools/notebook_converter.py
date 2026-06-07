import json
import pathlib

def convert_py_to_ipynb(py_content: str, ipynb_output_path: str):
    """
    Chuyển đổi nội dung mã nguồn Python (.py) thành Jupyter Notebook (.ipynb).
    Hỗ trợ chia ô bằng cách phát hiện các đánh dấu cell marker '# %%'.
    Nếu có thêm tag '[markdown]' (ví dụ '# %% [markdown]'), ô đó sẽ được chuyển thành Markdown cell.
    """
    lines = py_content.splitlines()
    cells = []
    current_cell_type = "code"
    current_cell_lines = []

    def flush_cell():
        if not current_cell_lines:
            return
        
        # Xóa dòng trống thừa ở đầu và cuối cell
        cell_content = "\n".join(current_cell_lines).strip("\n")
        if not cell_content.strip():
            return
            
        # Thêm newline vào cuối mỗi dòng cho đúng chuẩn jupyter
        formatted_source = [line + "\n" for line in cell_content.splitlines()]
        # Dòng cuối cùng không cần dấu xuống dòng thừa
        if formatted_source:
            formatted_source[-1] = formatted_source[-1].rstrip("\n")

        if current_cell_type == "markdown":
            # Loại bỏ ký tự comment '#' ở đầu mỗi dòng đối với Markdown cell
            clean_source = []
            for line in cell_content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    # Bỏ dấu # và 1 khoảng trắng nếu có
                    clean_source.append(line.replace("#", "", 1).strip() + "\n")
                else:
                    clean_source.append(line + "\n")
            if clean_source:
                clean_source[-1] = clean_source[-1].rstrip("\n")
            
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": clean_source
            })
        else:
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": formatted_source
            })

    for line in lines:
        stripped = line.strip()
        # Phát hiện cell marker
        if stripped.startswith("# %%"):
            flush_cell()
            current_cell_lines = []
            if "markdown" in stripped or "[markdown]" in stripped:
                current_cell_type = "markdown"
            else:
                current_cell_type = "code"
        else:
            current_cell_lines.append(line)
            
    # Xử lý phần còn lại cuối cùng
    flush_cell()

    # Nếu không tìm thấy cell marker nào, gộp toàn bộ file thành 1 code cell duy nhất
    if not cells and py_content.strip():
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in py_content.splitlines()]
        })

    # Cấu trúc JSON tiêu chuẩn của Jupyter Notebook
    notebook_json = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    # Ghi file notebook
    output_file = pathlib.Path(ipynb_output_path)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(notebook_json, f, indent=1, ensure_ascii=False)
