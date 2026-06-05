def extract_ocr(filepath: str) -> str:
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang="ch")
        result = ocr.ocr(filepath, cls=True)
        if not result or not result[0]:
            return ""
        lines = [line[1][0] for line in result[0] if line]
        return "\n".join(lines)
    except ImportError:
        raise RuntimeError("PaddleOCR 未安装, 无法处理扫描件")
