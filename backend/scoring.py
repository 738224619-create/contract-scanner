DIMENSIONS = {
    "违约金": ["违约金", "罚金", "逾期"],
    "免责条款": ["免责", "概不负责", "概不承担"],
    "解除权": ["解除", "终止", "单方"],
    "押金定金": ["押金", "定金", "扣除", "扣款"],
    "权利义务": ["不得有异议", "放弃", "最终解释权", "甲方有权", "乙方不得"],
}

def calculate(risks: list[dict]) -> dict:
    score = 100.0
    dim_scores = {d: 100.0 for d in DIMENSIONS}

    for risk in risks:
        level = risk.get("risk_level", "medium")
        confidence = risk.get("confidence", 50) / 100.0
        clause = risk.get("clause", "")

        # Base deduction by risk level, scaled by confidence
        base = {"high": 30, "medium": 12, "low": 3}.get(level, 8)
        deduction = base * confidence
        score = max(5, score - deduction)

        for dim, keywords in DIMENSIONS.items():
            if any(k in clause for k in keywords):
                dim_scores[dim] = max(5, dim_scores[dim] - deduction)

    risk_counts = {"high": 0, "medium": 0, "low": 0}
    for r in risks:
        risk_counts[r.get("risk_level", "medium")] += 1

    total = round(score)
    return {
        "total_score": total,
        "dimensions": [{"name": d, "score": round(s)} for d, s in dim_scores.items()],
        "risk_counts": risk_counts,
        "verdict": (
            "建议修改后再签" if total < 50 else
            "存在重大风险" if total < 65 else
            "存在风险，需谨慎" if total < 80 else
            "整体相对安全"
        ),
    }
