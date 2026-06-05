from pathlib import Path
from .text import extract_text
from .ocr import extract_ocr

SUPPORTED = {".pdf", ".docx", ".txt"}

def parse(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"不支持的文件格式: {ext}，支持 PDF / DOCX / TXT")

    try:
        text = extract_text(filepath)
    except Exception as e:
        raise ValueError(f"文档解析失败: {e}")

    if text.strip():
        return text
    return extract_ocr(filepath)
