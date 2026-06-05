import os, uuid, json, hashlib, asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from parser import parse
from llm import analyze_contract
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
import db
from scoring import calculate as calc_score
from export_pdf import generate as generate_pdf, generate_optimized

app = FastAPI(title="AI 合同风险扫描")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
llm = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

STATIC_DIR = os.environ.get("STATIC_DIR", os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "未提供文件")
    ext = os.path.splitext(file.filename)[1].lower()
    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件过大，请上传小于 10MB 的文件")
    with open(filepath, "wb") as f:
        f.write(content)
    text = parse(filepath)
    if not text.strip():
        raise HTTPException(400, "无法提取文本，请确认不是扫描件或安装 PaddleOCR")
    content_hash = hashlib.md5(text.encode()).hexdigest()[:12]

    async def event_stream():
        events = []
        def on_progress(step, detail):
            events.append({"step": step, "detail": detail})
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: analyze_contract(text, file.filename, on_progress))
        for evt in events:
            yield f"data: {json.dumps({'type': 'progress', **evt}, ensure_ascii=False)}\n\n"
        risks_dict = [r.model_dump() for r in result.risks]
        scoring = calc_score(risks_dict)
        aid = db.save(file.filename, result.risks, result.summary, content_hash, text)
        data = result.model_dump()
        data["id"] = aid
        data["scoring"] = scoring
        yield f"data: {json.dumps({'type': 'result', 'data': data}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/optimize/{aid}")
def optimize(aid: int):
    record = db.get_one(aid)
    if not record:
        raise HTTPException(404, "记录不存在")
    if not record.get("content_text"):
        raise HTTPException(400, "该记录无合同原文，无法优化")
    risks_text = "\n".join(
        f"- {r['clause'][:60]}... → {r['risk_level']}: {r['suggestion']}" for r in record["risks"]
    )
    resp = llm.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是合同修订专家。根据风险分析直接输出修改后的完整合同，保持结构，只改有问题条款。不输出解释。"},
            {"role": "user", "content": f"原合同:\n{record['content_text']}\n\n风险:\n{risks_text}\n\n输出优化后合同："},
        ],
        temperature=0.2,
    )
    optimized = resp.choices[0].message.content.strip()
    db.save_optimized(aid, optimized)
    return {"id": aid, "optimized": optimized}


@app.post("/api/chat/{aid}")
def chat(aid: int, question: str = Body(..., embed=True)):
    record = db.get_one(aid)
    if not record:
        raise HTTPException(404, "记录不存在")
    context = f"合同: {record['filename']}\n分析: {record['summary']}\n风险: {json.dumps(record['risks'], ensure_ascii=False)[:2000]}"
    resp = llm.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"你正在帮用户理解一份合同分析结果。参考以下上下文回答用户问题，通俗易懂，不要法言法语。\n\n{context}"},
            {"role": "user", "content": question},
        ],
        temperature=0.5,
    )
    return {"answer": resp.choices[0].message.content}


@app.post("/api/share/{aid}")
def share(aid: int):
    record = db.get_one(aid)
    if not record:
        raise HTTPException(404, "记录不存在")
    share_id = db.create_share(aid)
    return {"url": f"/share/{share_id}"}


@app.get("/api/shared/{share_id}")
def get_shared(share_id: str):
    record = db.get_shared(share_id)
    if not record:
        raise HTTPException(404, "分享不存在或已过期")
    from scoring import calculate
    record["scoring"] = calculate(record["risks"])
    return record


@app.get("/api/export/{aid}")
def export(aid: int, type: str = Query("report")):
    record = db.get_one(aid)
    if not record:
        raise HTTPException(404, "记录不存在")
    if type == "optimized" and record.get("optimized_text"):
        path = generate_optimized(record)
        return FileResponse(path, filename=f"合同优化版_{aid}.pdf", media_type="application/pdf")
    path = generate_pdf(record)
    return FileResponse(path, filename=f"合同风险报告_{aid}.pdf", media_type="application/pdf")


@app.get("/api/history")
def history():
    return db.list_all()

@app.get("/api/history/{aid}")
def history_detail(aid: int):
    record = db.get_one(aid)
    if not record:
        raise HTTPException(404, "记录不存在")
    return record

@app.get("/api/compare")
def compare(id1: int = Query(...), id2: int = Query(...)):
    r1 = db.get_one(id1); r2 = db.get_one(id2)
    if not r1 or not r2:
        raise HTTPException(404, "记录不存在")
    risks1 = {r["clause"][:80]: r for r in r1["risks"]}
    risks2 = {r["clause"][:80]: r for r in r2["risks"]}
    diff = []
    for key in set(risks1) | set(risks2):
        a, b = risks1.get(key), risks2.get(key)
        if a and b:
            diff.append({"type": "changed" if a["risk_level"] != b["risk_level"] else "same", "clause": key, "risk1": a, "risk2": b})
        elif a:
            diff.append({"type": "removed", "clause": key, "risk1": a, "risk2": None})
        else:
            diff.append({"type": "added", "clause": key, "risk1": None, "risk2": b})
    return {"id1": id1, "filename1": r1["filename"], "id2": id2, "filename2": r2["filename"], "diff": diff}

@app.get("/api/health")
def health():
    return {"status": "ok"}

# === 合同模板 ===

TEMPLATE_TYPES = {
    "rental": "房屋租赁合同",
    "labor": "劳动合同",
    "sales": "买卖合同",
    "service": "服务合同",
}

@app.get("/api/templates")
def list_templates():
    return [
        {"key": k, "name": v}
        for k, v in TEMPLATE_TYPES.items()
    ]


@app.post("/api/templates/generate")
def generate_template(type: str = Body(..., embed=True)):
    if type not in TEMPLATE_TYPES:
        raise HTTPException(400, f"不支持的模板类型: {type}")

    name = TEMPLATE_TYPES[type]
    resp = llm.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": f"你是中国合同起草专家。请生成一份公平、合法的{name}模板。必须遵循民法典规定，双方权利义务对等，不得包含任何霸王条款。使用标准合同格式，包含必要条款（当事人、标的、数量、质量、价款、履行期限、违约责任、争议解决）。用中文输出完整合同正文，不要额外解释。",
            },
            {
                "role": "user",
                "content": f"请生成一份标准{name}模板：",
            },
        ],
        temperature=0.3,
    )
    template = resp.choices[0].message.content.strip()
    return {"type": type, "name": name, "template": template}


# === 静态文件（生产环境） ===
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    import os as _os
    file_path = _os.path.join(STATIC_DIR, full_path)
    if full_path and _os.path.isfile(file_path):
        return FileResponse(file_path)
    index_path = _os.path.join(STATIC_DIR, "index.html")
    if _os.path.isfile(index_path):
        return HTMLResponse(open(index_path).read())
    return {"message": "Frontend not built. Run: cd frontend && npm run build"}
