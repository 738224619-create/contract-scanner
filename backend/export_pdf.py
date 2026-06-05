import os, difflib, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import red, HexColor
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Register CJK font for Chinese support
try:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    CN_FONT = 'STSong-Light'
except:
    CN_FONT = 'Helvetica'

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LEVEL_LABELS = {"high": "高风险", "medium": "中风险", "low": "低风险"}
LEVEL_ICONS = {"high": "●", "medium": "●", "low": "●"}

cn = ParagraphStyle("cn", fontName=CN_FONT, fontSize=11, leading=20)
cn_red = ParagraphStyle("cn_red", parent=cn, textColor=red)
title_s = ParagraphStyle("t", fontName=CN_FONT, fontSize=22, leading=28)
h2_s = ParagraphStyle("h2", fontName=CN_FONT, fontSize=15, leading=22)
note_s = ParagraphStyle("note", fontName=CN_FONT, fontSize=9, textColor=HexColor("#999"))


def generate(record: dict) -> str:
    aid = record["id"]
    path = os.path.join(OUTPUT_DIR, f"report_{aid}.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    elements = []

    elements.append(Paragraph("AI 合同风险扫描报告", title_s))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(f"文件: {record['filename']}<br/>日期: {record['created_at']}", cn))
    elements.append(Spacer(1, 8*mm))

    elements.append(Paragraph("整体评估", h2_s))
    elements.append(Paragraph(record["summary"], cn))
    elements.append(Spacer(1, 8*mm))

    risks = record["risks"]
    high_c = sum(1 for r in risks if r["risk_level"] == "high")
    med_c = sum(1 for r in risks if r["risk_level"] == "medium")
    low_c = sum(1 for r in risks if r["risk_level"] == "low")
    elements.append(Paragraph(f"共 {len(risks)} 个风险（{high_c}高 {med_c}中 {low_c}低）", cn))
    elements.append(Spacer(1, 6*mm))

    for i, risk in enumerate(risks, 1):
        label = LEVEL_LABELS.get(risk["risk_level"], risk["risk_level"])
        elements.append(Paragraph(f"风险 {i}: {label}", h2_s))
        elements.append(Paragraph(f"条款: {risk['clause']}", cn))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(f"解释: {risk['explanation']}", cn))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(f"建议: {risk['suggestion']}", cn))
        elements.append(Spacer(1, 6*mm))

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("本报告由 AI 生成，仅供参考，不构成法律意见", note_s))
    doc.build(elements)
    return path


def generate_optimized(record: dict) -> str:
    aid = record["id"]
    path = os.path.join(OUTPUT_DIR, f"optimized_{aid}.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    elements = []

    elements.append(Paragraph("合同优化版（修改处以红色标注）", title_s))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(f"原文件: {record['filename']}<br/>日期: {record['created_at']}", cn))
    elements.append(Spacer(1, 8*mm))

    original = record.get("content_text", "")
    optimized = record.get("optimized_text", "")

    orig_words = re.findall(r"\S+|\s+", original)
    opt_words = re.findall(r"\S+|\s+", optimized)

    matcher = difflib.SequenceMatcher(None, orig_words, opt_words)
    result_parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result_parts.append(Paragraph(_escape("".join(opt_words[j1:j2])), cn))
        elif tag in ("replace", "insert"):
            result_parts.append(Paragraph(f'<font color="red">{_escape("".join(opt_words[j1:j2]))}</font>', cn_red))
        # delete: skip

    elements.extend(result_parts)
    elements.append(Spacer(1, 12*mm))
    elements.append(Paragraph("红色文字为 AI 优化修改，仅供参考", note_s))
    doc.build(elements)
    return path


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
