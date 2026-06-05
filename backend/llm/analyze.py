import json, re, hashlib
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from models import AnalysisResult, RiskItem, RiskLevel

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
MODEL = "deepseek-chat"

# --- Rule Engine ---

RULE_PATTERNS = [
    # (pattern, risk_level, explanation, base_confidence)
    (r"概不负责|概不承担|不负任何", "high", "可能构成无效免责条款，违反民法典第506条", 80),
    (r"任何损[坏毁害]", "high", "'任何'表述过宽，可能包含正常磨损", 70),
    (r"随时解除|任意解除|无需.*理由.*解除", "high", "单方任意解除权显失公平", 75),
    (r"不得有异议|不得.*异议|放弃.*权利", "high", "排除对方申辩权，违反公平原则", 75),
    (r"(每[日天]|每日).*?(\d{2,})%.*?(违约金|罚金)", "high", "违约金比例过高，超实际损失30%可被法院调减", 75),
    (r"全额.*扣[除押]", "high", "全额扣除条件过于严苛", 70),
    (r"提前\d{1,2}[日天].*通知.*解除", "medium", "通知期过短，建议至少提前30日", 60),
    (r"无息.*退还", "low", "押金无息退还属于常见做法", 60),
    (r"最终解释权", "high", "最终解释权条款侵犯消费者权益", 80),
    (r"保密.*永久|永久.*保密", "medium", "永久保密期限过严，建议设定期限", 55),
    (r"转让.*不得|不得.*转让", "medium", "限制转让权可能影响正常经营", 50),
    (r"自动续[期约]", "medium", "自动续约条款需注意是否有退出机制", 50),
]

KEYWORD_LAWS = {
    "格式条款": ("民法典第496条", "格式条款提供方应遵循公平原则"),
    "违约金": ("民法典第585条", "违约金过高法院可调减"),
    "免责": ("民法典第506条", "人身伤害/故意重大过失免责无效"),
    "押金": ("民法典第713条", "维修费出租人负担"),
    "解除合同": ("民法典第563条", "不可抗力/违约/迟延履行可解除"),
    "违约责任": ("民法典第577条", "违约须承担继续履行、补救或赔偿"),
    "定金": ("民法典第587条", "定金不超过标的额20%"),
    "保证": ("民法典第686条", "保证方式不明按一般保证"),
    "赔偿损失": ("民法典第584条", "损失赔偿含可得利益"),
    "劳动合同": ("劳动合同法第82条", "未签书面合同应付双倍工资"),
    "试用期": ("劳动合同法第19条", "试用期最长不超过6个月"),
    "竞业限制": ("劳动合同法第23条", "竞业限制须支付经济补偿"),
}

def rule_scan(text: str) -> list[dict]:
    """Run all rules, return findings with confidence"""
    findings = []
    for pattern, level, note, conf in RULE_PATTERNS:
        for m in re.finditer(pattern, text):
            findings.append({
                "clause": m.group(0) if len(m.group(0)) < 80 else m.group(0)[:80] + "...",
                "risk_level": level,
                "note": note,
                "confidence": conf,
                "position": m.start(),
            })
    return findings

def keyword_lookup(text: str) -> list[str]:
    refs, seen = [], set()
    for kw, (article, desc) in KEYWORD_LAWS.items():
        if kw in text and kw not in seen:
            refs.append(f"{article}：{desc}")
            seen.add(kw)
    return refs

def split_clauses(text: str) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return []
    clauses, current = [], lines[0]
    for line in lines[1:]:
        if re.match(r"^(第[一二三四五六七八九十百]+[条章节]|[\(（]*[一二三四五六七八九十]|\d+[\.\、\)）])", line):
            clauses.append(current)
            current = line
        else:
            current += "\n" + line
    if current:
        clauses.append(current)
    if len(clauses) <= 1:
        return [text[i:i+800] for i in range(0, len(text), 800)]
    return clauses


# --- LLM Prompt ---

SYSTEM_PROMPT = """你是中国合同风险审查专家。仔细审查以下合同条款，输出 JSON。

对每个风险输出：
- clause: 原文（精确摘录，不超过150字）
- risk_level: "low"|"medium"|"high"
- explanation: 通俗解释，引用民法典具体条款
- suggestion: 明确具体的修改建议
- confidence: 你对此判断的确信度 0-100

判断标准：
- high: 违反法律强制性规定（如民法典第506条人身伤害免责无效）→ confidence 80-95
- medium: 不合理但可协商（如通知期过短）→ confidence 60-80
- low: 微小瑕疵 → confidence 50-70
- 若无风险则返回空 risks 数组

输出格式：{"risks":[...],"summary":"整体概述"}
只输出 JSON，不要其他内容。"""


def analyze_with_llm(clauses: list[str], laws: list[str], filename: str) -> dict:
    law_text = "\n".join(f"- {r}" for r in laws) if laws else "无"
    clauses_text = "\n\n---\n".join(f"[条款{i+1}] {c}" for i, c in enumerate(clauses[:20]))

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"文件名: {filename}\n\n相关法条:\n{law_text}\n\n合同内容:\n{clauses_text}"},
        ],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content.strip()
    # Parse
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        raw = raw.rstrip("```").strip()
    for _ in range(3):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                raw = raw[start:end+1]
            else:
                raw = raw.replace("\n", "\\n").replace("\r", "\\r")
    raise ValueError("LLM 返回格式异常")


# --- Cross-validation ---


def cross_validate(llm_risks: list[dict], rule_findings: list[dict]) -> list[dict]:
    """Merge rule findings into LLM risks if clause overlaps."""
    result = []

    HEDGING = ['可能', '或许', '也许', '有可能', '不一定', '视情况', '取决于']
    # Boost confidence for LLM risks that match rules
    for lr in llm_risks:
        lc = lr.get("clause", "")
        expl = lr.get("explanation", "")
        base = lr.get("confidence", 60)

        # Penalize hedging language: each hedge word reduces confidence
        hedge_count = sum(1 for h in HEDGING if h in expl)
        if hedge_count:
            base = max(30, base - hedge_count * 10)

        rule_conf = 0
        for rf in rule_findings:
            if rf["clause"] in lc or lc in rf["clause"]:
                rule_conf = max(rule_conf, rf["confidence"])
        if rule_conf:
            # Average LLM and rule confidence, not just max
            lr["confidence"] = min(90, int((base + rule_conf) / 2) + 5)
        else:
            lr["confidence"] = min(base, 65)
        result.append(lr)

    # Add unmatched rules
    for rf in rule_findings:
        rc = rf["clause"]
        matched = any(rc in lr.get("clause", "") or lr.get("clause", "") in rc for lr in llm_risks)
        if not matched:
            result.append({
                "clause": rc,
                "risk_level": rf["risk_level"],
                "explanation": rf["note"],
                "suggestion": "请人工核实",
                "confidence": max(40, rf["confidence"] - 15),
            })
    return result

def analyze_contract(text: str, filename: str, on_progress=None):
    def emit(step, detail):
        if on_progress:
            on_progress(step, detail)

    emit("split", "拆分条款...")
    clauses = split_clauses(text)
    emit("split", f"{len(clauses)} 个条款")

    emit("rules", "规则扫描...")
    rule_findings = rule_scan(text)
    emit("rules", f"命中 {len(rule_findings)} 条")

    emit("laws", "法条匹配...")
    laws = keyword_lookup(text)
    emit("laws", f"匹配 {len(laws)} 条")

    emit("ai", "AI 深度分析...")
    llm_result = analyze_with_llm(clauses, laws, filename)

    emit("merge", "交叉验证...")
    merged = cross_validate(llm_result.get("risks", []), rule_findings)
    emit("done", f"完成 {len(merged)} 个风险")

    risks = [
        RiskItem(
            clause=r["clause"][:200],
            risk_level=RiskLevel(r.get("risk_level", "medium")),
            explanation=r.get("explanation", ""),
            suggestion=r.get("suggestion", ""),
            confidence=r.get("confidence", 50),
        )
        for r in merged
    ]
    return AnalysisResult(filename=filename, risks=risks, summary=llm_result.get("summary", ""))
