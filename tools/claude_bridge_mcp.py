"""讓 Claude（桌面版的 Chat 分頁）把工作交給 Lumina：MCP 伺服器，透過 Lumina 的介面伺服器（http://127.0.0.1:8765）
請 Gemini 做事，例如看很長的影片、讀大量檔案，只把整理好的結果交回給 Claude。

用法（Claude 桌面版的 claude_desktop_config.json）：
    "lumina": {"command": "<python.exe>", "args": ["<Lumina 資料夾>/tools/claude_bridge_mcp.py"]}

設計：
- 長工作不能讓 Claude 一直卡在一次工具呼叫裡，所以分兩步：lumina_ask 交出去（馬上回傳工作編號），
  lumina_result 之後再來拿結果（可以等一段時間）。
- 工作的結果存在 data/claude_jobs/，Claude 桌面版重開也拿得到；交出去的對話也會出現在 Lumina 的對話清單，使用者看得到。
- 交給 Lumina 的檔案：不在 Lumina 能讀的資料夾裡時，在 uploads 建一個硬連結（同一顆硬碟不佔空間、不用複製），
  不同硬碟才複製。
- 不給 work_dir：一般對話模式，只能讀檔、查資料；需要授權的操作自動拒絕。
- 給 work_dir：Lumina Code 模式，可以在那個資料夾執行指令（例如 ffmpeg 切影片、抽影格）、讀寫檔案、用其他 MCP 工具。
  Lumina 設定開了「自動模式」就不會詢問；沒開時，需要授權的操作會停下來，由 lumina_result 回報給 Claude，
  Claude 問使用者後用 lumina_approve 回答。
"""

import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://127.0.0.1:8765"
HDR = {"Content-Type": "application/json", "Origin": API}
JOBS = ROOT / "data" / "claude_jobs"
LINKS = ROOT / "data" / "workspace" / "uploads" / "claude"
DEFAULT_MODEL = "gemini-3.8-flash-high"
GUIDE = ("\n\n---\n[交辦說明] 這件工作是 Claude 交給你的，結果會交回給 Claude 整理後給使用者。"
         "附件請用 view_file 直接讀（影片、音訊、圖片、PDF 都可以直接看）。"
         "回答要具體、有根據：提到影片內容時寫出時間點（mm:ss），引用說話內容時盡量用原話；"
         "看不清楚、聽不清楚或不確定的地方直接說，不要猜。不需要客套話。")

TOOLS = [
    {"name": "lumina_ask", "description":
        "把一件工作交給 Lumina（使用者電腦上的 Gemini，用 Antigravity 的額度，不用 Claude 的額度）。"
        "適合：很長的影片或錄音（Gemini 可以直接看影片、聽聲音）、很大的 PDF 或大量檔案、需要先讀很多內容再摘要的工作。"
        "會馬上回傳工作編號（job_id），之後用 lumina_result 拿結果。"
        "prompt 要寫清楚要什麼（例如「列出影片中每個段落的主題和時間點」）；files 放本機檔案的完整路徑。"
        "要接著同一段內容追問時，帶上 lumina_result 回傳的 conversation_id，Lumina 會記得前面看過的東西，不用重看。",
     "inputSchema": {"type": "object", "properties": {
         "prompt": {"type": "string", "description": "要 Lumina 做什麼"},
         "files": {"type": "array", "items": {"type": "string"}, "description": "本機檔案的完整路徑（影片、音訊、圖片、PDF、文字檔）"},
         "conversation_id": {"type": "string", "description": "接著之前的對話追問時填（lumina_result 會給）"},
         "model": {"type": "string", "description": "模型 ID，預設 gemini-3.8-flash-high；可用的模型見 lumina_models"},
         "work_dir": {"type": "string", "description":
             "要讓 Lumina 能執行指令、存檔時填一個資料夾的完整路徑（Lumina Code 模式）。例如影片超過 100 MB 要先用 ffmpeg 切段、"
             "要抽影格、要把報告存到使用者指定的地方。不填就是只能讀的一般模式。"}},
         "required": ["prompt"]}},
    {"name": "lumina_result", "description":
        "拿 lumina_ask 交出去的工作結果。還沒做完時最多等 wait_seconds 秒（預設 50），"
        "時間到還沒好就回報進度（已經跑多久、用了哪些工具），再呼叫一次就好。長影片可能要好幾分鐘。",
     "inputSchema": {"type": "object", "properties": {
         "job_id": {"type": "string"},
         "wait_seconds": {"type": "integer", "description": "最多等幾秒（0～55），預設 50"}},
         "required": ["job_id"]}},
    {"name": "lumina_approve", "description":
        "回答 Lumina 的授權詢問（只有 Code 模式、而且 Lumina 沒開自動模式時才會有）。lumina_result 回報「等待授權」時，"
        "把要執行的內容告訴使用者，使用者同意才用 allow；不確定、有風險、使用者沒明確同意就用 deny。不要自己替使用者決定。",
     "inputSchema": {"type": "object", "properties": {
         "job_id": {"type": "string"},
         "decision": {"type": "string", "enum": ["allow", "allow_all", "deny"],
                      "description": "allow 允許這一次；allow_all 這段工作裡同一個程式都允許；deny 拒絕"},
         "reason": {"type": "string", "description": "拒絕的原因（會告訴模型）"}},
         "required": ["job_id", "decision"]}},
    {"name": "lumina_models", "description": "列出 Lumina 現在可以用的模型 ID。",
     "inputSchema": {"type": "object", "properties": {}}},
]


class ToolError(Exception):
    pass


def post(path, data, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(API + path, json.dumps(data).encode("utf-8"), HDR), timeout=timeout)


def get(path, timeout=30):
    return json.loads(urllib.request.urlopen(urllib.request.Request(API + path, headers=HDR), timeout=timeout).read())


def alive():
    try:
        get("/api/version", timeout=3)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def job_file(jid):
    return JOBS / f"{jid}.json"


LIVE = {}                 # 這個程式交出去的工作：背景執行緒和工具呼叫共用同一份（不從檔案讀回來，免得互相覆蓋）
LIVE_LOCK = threading.RLock()


def save(job):
    LIVE[job["id"]] = job
    JOBS.mkdir(parents=True, exist_ok=True)
    tmp = job_file(job["id"]).with_suffix(".tmp")
    tmp.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(job_file(job["id"]))


def load(jid):
    if jid in LIVE:
        return LIVE[jid]
    try:
        return json.loads(job_file(jid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stage(path):
    """讓 Lumina 讀得到這個檔案：放一個硬連結到 uploads（同一顆硬碟不佔空間），不行才複製。"""
    src = Path(path).expanduser()
    if not src.is_file():
        raise ToolError(f"找不到檔案：{path}（要用完整的本機路徑）")
    LINKS.mkdir(parents=True, exist_ok=True)
    dst = LINKS / f"{uuid.uuid4().hex[:6]}_{src.name}"
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    return str(dst)


def wait_decision(job, e):
    """Code 模式的授權詢問：記進工作檔，等 Claude 用 lumina_approve 回答（最多等到 Lumina 那邊的期限）。"""
    job.update(status="waiting", pending={"command": e.get("command"), "cwd": e.get("cwd"), "level": e.get("level"),
                                          "warnings": e.get("warnings"), "can_conv": e.get("can_conv")})
    save(job)
    end = time.time() + (e.get("wait") or 600) - 20
    choice, reason = "deny", "沒有在時間內得到使用者同意"
    while time.time() < end:
        time.sleep(0.3)
        with LIVE_LOCK:
            d = job.get("decision")
        if d:
            choice = {"allow": "once", "allow_all": "conv" if e.get("can_conv") else "once"}.get(d["decision"], "deny")
            reason = d.get("reason") or ("使用者拒絕" if choice == "deny" else "")
            break
    post("/api/permission/answer", {"id": e["id"], "nonce": e["nonce"], "choice": choice, "reason": reason}).read()
    with LIVE_LOCK:
        job.update(status="running", pending=None, decision=None)
    job.setdefault("asked", []).append({"command": e.get("command"), "choice": choice})
    save(job)


def run_job(job):
    """在背景執行：把工作送給 Lumina，讀串流直到結束，結果存進工作檔。"""
    body = {"text": job["prompt"] + GUIDE, "files": job["staged"], "model": job["model"]}
    if job.get("ws"):
        body["code"] = job["ws"]
    if job.get("conversation_id"):
        body["conversation_id"] = job["conversation_id"]
    reply, err = "", None
    try:
        for line in post("/api/chat", body, timeout=6 * 3600):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            ev = e.get("event")
            su = e.get("step_update") or {}
            if su.get("step_type") == "tool" and su.get("state") == "ACTIVE":
                job["tools"].append(su.get("tool_name") or "?")
                save(job)
            if su.get("step_type") == "agent_response" and su.get("text_delta"):
                reply += su["text_delta"]
            if ev == "permission":
                if job.get("ws"):         # Code 模式：交給 Claude 問使用者
                    wait_decision(job, e)
                else:                     # 一般模式沒有要執行的東西：一律拒絕，模型會改用其他方法
                    post("/api/permission/answer", {"id": e["id"], "nonce": e["nonce"], "choice": "deny",
                                                    "reason": "這是 Claude 交辦的唯讀工作，不能使用需要授權的操作"}).read()
            if ev in ("pdf", "images") and e.get("reply"):
                reply = e["reply"]
            if ev == "result":
                r = e.get("result") or {}
                reply = r.get("response") or reply
                job["tokens"] = (r.get("usage") or {}).get("turn_tokens") or (r.get("usage") or {}).get("total_tokens")
                job["conversation_id"] = r.get("conversation_id") or job.get("conversation_id")
            if ev in ("conv_created", "done") and e.get("conversation_id"):
                job["conversation_id"] = e["conversation_id"]
            if ev == "done":
                err = e.get("error")
    except Exception as e:
        err = f"和 Lumina 的連線中斷：{type(e).__name__}: {e}"
    job.update(status="error" if err and not reply.strip() else "done", answer=reply.strip(), error=err,
               finished=time.time())
    save(job)


def t_ask(a):
    prompt = str(a.get("prompt") or "").strip()
    if not prompt:
        raise ToolError("prompt 不能是空的。")
    if not alive():
        raise ToolError("Lumina 沒有開著（http://127.0.0.1:8765 連不到）。請使用者雙擊 Lumina 的「啟動.vbs」或桌面捷徑後再試。")
    files = [str(f) for f in (a.get("files") or []) if str(f).strip()]
    wd, ws = str(a.get("work_dir") or "").strip(), None
    if wd:
        if not Path(wd).is_dir():
            raise ToolError(f"找不到資料夾：{wd}（要用完整的本機路徑）")
        r = json.loads(post("/api/code/create", {"work_dir": wd}).read())
        if not r.get("ok"):
            raise ToolError("Lumina 不能用這個資料夾：" + str(r.get("message")))
        ws = r["id"]
    inside = lambda f: wd and Path(f).resolve().is_relative_to(Path(wd).resolve())   # 工作資料夾裡的檔案直接讀
    job = {"id": uuid.uuid4().hex[:10], "prompt": prompt, "files": files, "ws": ws, "work_dir": wd or None,
           "staged": [f if inside(f) else stage(f) for f in files],
           "model": a.get("model") or DEFAULT_MODEL, "conversation_id": a.get("conversation_id"),
           "status": "running", "started": time.time(), "pid": os.getpid(), "tools": [], "answer": "", "error": None, "tokens": None}
    save(job)
    threading.Thread(target=run_job, args=(job,), daemon=True).start()
    return (f"已交給 Lumina，工作編號：{job['id']}（模型 {job['model']}，附件 {len(files)} 個，"
            f"{'Code 模式，工作資料夾 ' + wd if wd else '一般模式（唯讀）'}）。"
            f"用 lumina_result 拿結果；長影片可能要好幾分鐘。")


def t_result(a):
    jid = str(a.get("job_id") or "")
    wait = max(0, min(55, int(a.get("wait_seconds") or 50)))
    end = time.time() + wait
    job = load(jid)
    if job is None:
        raise ToolError(f"找不到工作 {jid}。")
    while job["status"] == "running" and time.time() < end:
        time.sleep(1)
        job = load(jid) or job
    if job["status"] == "waiting":
        pd = job.get("pending") or {}
        warn = "；".join(pd.get("warnings") or [])
        return (f"等待授權：Lumina 想執行\n{pd.get('command')}\n（位置：{pd.get('cwd')}"
                + (f"；注意：{warn}" if warn else "") + "）\n"
                "請先問使用者，再用 lumina_approve（job_id=" + jid + "）回答 allow／allow_all／deny。"
                "不要自己替使用者決定。")
    if job["status"] == "running":
        if job.get("pid") != os.getpid():     # 交出去之後 Claude 桌面版重開過：這邊已經收不到結果了
            return ("這件工作是在 Claude 重開之前交出去的，這邊已經收不到它的結果。"
                    "Lumina 那邊可能已經做完：請使用者到 Lumina 的對話清單看，或重新用 lumina_ask 交一次。")
        mins = (time.time() - job["started"]) / 60
        used = "、".join(job["tools"][-8:]) or "（還在讀內容）"
        return (f"還在處理（已經 {mins:.1f} 分鐘）。用過的工具：{used}。"
                f"請再呼叫 lumina_result（job_id={jid}）繼續等。")
    head = f"conversation_id：{job.get('conversation_id')}（要追問同一份內容時帶上它）\n" \
           f"花了 {(job.get('finished', time.time()) - job['started']) / 60:.1f} 分鐘" + \
           (f"，{job['tokens']:,} tokens" if job.get("tokens") else "") + "\n\n"
    if job["status"] == "error":
        raise ToolError(head + "Lumina 做這件工作時出錯：" + str(job.get("error"))[:1500])
    return head + (job["answer"] or "（Lumina 沒有回覆內容）") + \
        (f"\n\n（附註：Lumina 回報 {job['error'][:300]}）" if job.get("error") else "")


def t_models(a):
    if not alive():
        raise ToolError("Lumina 沒有開著（http://127.0.0.1:8765 連不到）。")
    models = get("/api/models?cached=1").get("models") or []
    return "\n".join(f"{m['id']}　{m['name']}" for m in models) or "（取不到模型清單）"


def t_approve(a):
    jid = str(a.get("job_id") or "")
    job = load(jid)
    if job is None:
        raise ToolError(f"找不到工作 {jid}。")
    if job["status"] != "waiting":
        raise ToolError("這件工作現在沒有在等授權。")
    dec = a.get("decision")
    if dec not in ("allow", "allow_all", "deny"):
        raise ToolError("decision 要是 allow、allow_all 或 deny。")
    with LIVE_LOCK:
        if job["status"] != "waiting" or job.get("decision"):
            raise ToolError("這件工作現在沒有在等授權（可能已經回答過了）。")
        job["decision"] = {"decision": dec, "reason": str(a.get("reason") or "")}
    end = time.time() + 10               # 等背景把答案送出去、狀態變回執行中，下一次 lumina_result 才不會又看到同一個詢問
    while job["status"] == "waiting" and time.time() < end:
        time.sleep(0.2)
    return f"已回答：{dec}。用 lumina_result 繼續拿結果。"


CALLS = {"lumina_ask": t_ask, "lumina_result": t_result, "lumina_approve": t_approve, "lumina_models": t_models}
OUT_LOCK = threading.Lock()


def send(msg):
    with OUT_LOCK:
        sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def handle(msg):
    mid, p = msg.get("id"), msg.get("params") or {}
    try:
        fn = CALLS.get(p.get("name", ""))
        if fn is None:
            raise ToolError(f"沒有這個工具：{p.get('name')}")
        text, err = fn(p.get("arguments") or {}), False
    except ToolError as e:
        text, err = str(e), True
    except Exception as e:
        text, err = f"工具執行失敗：{type(e).__name__}: {e}", True
    send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": err}})


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": (msg.get("params") or {}).get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}}, "serverInfo": {"name": "lumina", "version": "1.0"},
                "instructions": "Lumina 是使用者電腦上的 Gemini（用 Antigravity 的額度，不用你的額度），可以直接看影片、聽聲音。"
                                "很長的影片、錄音、大 PDF、大量檔案交給它看，你只拿整理好的結果，省下你的上下文和額度；"
                                "長影片不要用 Naiz Studio 的 video-look（畫面和逐字稿會全部塞進你的對話）。"
                                "用法：lumina_ask（prompt 寫具體要什麼、files 給完整路徑）→ lumina_result 拿結果（沒好就再呼叫）；"
                                "追問同一份內容時帶 conversation_id，不用重看。拿到結果後由你整理、判斷、回答使用者。"
                                "Lumina 一個檔案最多讀 100 MB：影片太大時給 work_dir（Code 模式），讓它用 ffmpeg 切段或抽影格後再看；"
                                "Code 模式需要授權時 lumina_result 會回報，先問使用者再用 lumina_approve 回答。"
                                "完整說明在 Lumina 資料夾的 README.md「給 AI 協作：Claude（桌面版對話）」一節。"}})
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":          # 每個呼叫各自一條執行緒：等結果時不會擋住其他呼叫
            threading.Thread(target=handle, args=(msg,), daemon=True).start()
        elif mid is not None:
            send({"jsonrpc": "2.0", "id": mid, "result": {}})


if __name__ == "__main__":
    main()
