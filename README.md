# Lumina（for Antigravity）

在瀏覽器裡使用 Google Antigravity CLI（`agy`）：可以切換模型、附加圖片／PDF／檔案、建立專案（多份 PDF + 共享記憶）、看用量、開關聯網搜尋。
每則訊息都是呼叫官方 `agy -p`，登入的是你自己的帳號。

## 下載
到 [Releases](https://github.com/NaizOuO/Lumina/releases/latest) 下載最新的 `Antigravity-UI-v*.zip`，解壓縮到任何地方。

## 需要先準備
1. 安裝 [Python 3](https://www.python.org/downloads/)（安裝時勾選 "Add python.exe to PATH"）。
2. 安裝 Antigravity CLI（`agy`），並在終端機執行一次 `agy` 完成登入。

## 使用
- 雙擊 `啟動.vbs`：在背景啟動，並自動打開 http://127.0.0.1:8765
- 雙擊 `關閉.bat`：關掉背景伺服器
- **桌面捷徑**：第一次開啟時會詢問要不要在桌面建立「Lumina」捷徑（之後也能從左下角「建立桌面捷徑」建立）。
  資料夾搬家後，按「重新建立捷徑」即可
- 左上角顯示目前版本；有新版本時會變成橘色，點一下就能更新
- **輸出檔案**：請 AI「輸出成 md 檔」之類的，檔案會存在主目錄的 `output` 資料夾；右上角「📂 輸出」可以直接打開
- **⚙ 設定**：送出鍵、新對話預設模型、文字大小、對話寬度、背景（5 張內建背景隨機輪播，也可以放自己的圖到 `setting\images`）、
  回答完成提醒、點公式複製 LaTeX、額度提醒、匯出／備份／匯入、元件、更新
- **輸出 PDF**：說「輸出成 PDF」，AI 會照內建模板（講義、報告、簡報、信件）寫好，介面自動排版成 PDF。
  第一次使用時會在對話裡詢問是否下載排版工具 Typst（下載約 21 MB）
- **生圖**：概念插畫會自動用 Gemini 的生圖（Nano Banana），圖片存到 output 並直接顯示
- **預測回覆**：回答完輸入框會出現灰色的建議，按 Tab 採用
- **用量小工具**：右上角顯示 5 小時／每週額度的已用比例與重置倒數
- **側欄**：拖曳右邊緣調整寬度（雙擊恢復預設），按「«」收起、「☰」展開
- 右上角「常駐指示」：設定每個新對話開頭自動附上的指示（例如你的科系、回答語言）
- **重新回答 / 編輯**：最後一則回答下方有「↻ 重新回答」（回答失敗或不滿意時用）；
  滑鼠移到自己的訊息上會出現「✎ 編輯」，改完送出後，那則之後的對話會被新的回答取代
- **自動標題**：新對話第一輪回答完後，會用 Gemini Flash 在背景取一個簡短標題（手動改過名稱的不會被覆蓋）
- 左側「專案」：
  - 上傳多份 PDF／講義，提問時模型會自己挑需要的檔案讀，並註明出處
  - **專案記憶**：每次在專案裡對話後，會在背景整理重點（使用者背景、結論、數值、待辦），
    這個專案的每個新對話開頭都會帶上。可以在專案設定裡查看、修改、關閉自動更新，或「從所有對話重建」。
    整理記憶用 Gemini Flash，額度消耗很少。
    記憶最多 3000 字：超過時會自動請模型壓縮，壓不下來才截斷；手動編輯超過上限時無法儲存。
  - **搜尋過去的專案對話**：專案裡每段對話都會另存一份紀錄到專案資料夾。
    記憶裡沒有的細節（例如「之前說過的退火溫度」），模型需要時會自己挑相關的對話來讀，用不到時不花額度。

## 更新
開啟介面時會自動檢查有沒有新版本，有的話上方會出現「⬆ 有新版本」，按「更新」就會自動下載、換好並重新啟動。
左下角也可以手動「檢查更新」。

**更新只會換掉程式檔案，`data/` 資料夾（對話紀錄、專案、上傳的檔案、設定）永遠不會被動到。**
更新途中失敗會自動還原成舊版。

## 打不開時
- **跳出「無法啟動介面伺服器」或「系統找不到指定的檔案」**：通常是沒有安裝 Python。到 python.org 下載安裝，
  第一個畫面勾選「Add python.exe to PATH」，裝完再雙擊 `啟動.vbs`。
- **網頁開了但上方出現紅色提示「找不到 Antigravity CLI」**：還沒安裝 agy，或還沒登入。安裝後在終端機執行一次 `agy` 登入，
  再雙擊 `關閉.bat`、`啟動.vbs` 重新啟動。
- **其他錯誤**：查看 `data/server.log`。

## 資料存放
所有個人資料都放在 `data/`，第一次啟動時會自動建立：
- `data/history/`：對話紀錄
- `data/projects/`：專案（檔案、指示、記憶）
- `data/workspace/uploads/`：對話中上傳的附件
- `data/settings.json`：常駐指示

另外兩個個人資料夾：
- `output/`：AI 產生的檔案
- `setting/`：設定（`config.json`，包含常駐指示與背景設定）與背景圖片（`images/`）

- `components/`：使用者同意後才下載的元件（例如 Typst）

`data/`、`output/`、`setting/`、`components/` 都不會進版本控制、不會被打包，也不會被更新覆蓋。

## 給 AI 協作：Claude Code 派工給 Lumina Code

> **給 AI 模型**：使用者要你「交給 Lumina 做」「跟 Lumina 分工」時讀這一節。
> Lumina Code 用的是 Antigravity 的額度（跟 Claude Code 分開），適合接手大量實作；判斷、規劃、驗收留給你自己。

### 1. Lumina Code 能做什麼

Lumina Code 是 agy（Gemini 等模型）在一個工作資料夾裡寫程式、執行指令的環境。除了一般的讀寫檔、終端機，還有這些工具（說明都寫在工具裡）：

| 工具 | 用途 |
|---|---|
| `todo_write` | 任務清單；標成完成時必須寫出怎麼驗證的 |
| `acceptance_set` | 登記驗收指令；每次回答結束，介面會自己重跑，沒過就交回去修。測試檔在核准後被改過就不會自動執行 |
| `design_review` | 依程式類型（遊戲、工具、網頁、命令列）給檢查清單：開工前展開規格、完成前審查缺漏 |
| `run_capture` | 在隱藏桌面執行程式並截圖；`actions` 可以按鍵、等待、截圖，實際「玩」遊戲或操作視窗程式（不出聲、不佔使用者螢幕） |
| `venv_create`、`venv_install` | Python 虛擬環境 |
| `pdf_*` | 讀 PDF |

### 2. 怎麼派工

介面伺服器要開著（`啟動.vbs`，http://127.0.0.1:8765）。用 `dev/delegate.py`：

```
python dev/delegate.py "<工作資料夾>" --task "要做什麼" [--task-file 規格.md] \
    [--test "python acceptance_test.py ."] [--keep "不能改的介面或檔案"] [--model gemini-3.8-flash-high] [--rounds 2]
```

- 會自動在工作資料夾建立 Lumina Code 工作區，送出任務，權限詢問自動回答（「這段對話都允許」或「允許一次」）。
- 做完後 **delegate.py 自己重跑 `--test`**（不採信模型說的）；沒過就把失敗輸出交回同一段對話再修，最多 `--rounds` 輪。
- 最後印出 JSON 報告：`passed`、`changed`／`added`／`deleted`（實際比對檔案，不是模型說的）、`final_reply`、時間、tokens、詢問次數、`conversation`。
- `final_reply` 固定四段：①改了哪些檔案 ②怎麼驗證的 ③還沒解決的地方 ④**建議（尚未執行）**——Lumina 對設計的意見，給你參考，由你和使用者決定要不要做。
- 想自己寫程式呼叫：`POST /api/code/create {"work_dir": ...}` 建立工作區，`POST /api/chat {"text", "model", "code": 工作區 id, "conversation_id"?}`
  回傳一行一個 JSON 事件；`permission` 事件要用 `POST /api/permission/answer {"id", "nonce", "choice"}` 回答（`once`／`conv`／`deny`）。
  請求都要帶 `Origin: http://127.0.0.1:8765`。

### 3. 怎麼分工（實驗得到的結論）

同一個 Gemini Flash，自己規劃的 Pac-Man 自動評分 12/18；拿到 Claude 寫的規格書和驗收測試後是 21/21。
**差別在「需求想得夠不夠周全」，不在寫程式的能力**，所以：

| 你（Claude Code） | Lumina |
|---|---|
| 判斷使用者真正要什麼、寫規格書（含使用者沒說但該有的東西） | 照規格實作、反覆修到測試通過 |
| 寫驗收測試（含「不應該發生」的情況、實際跑一段流程） | 用 `run_capture` 的 `actions` 實際操作確認 |
| 最後驗收：自己重跑測試、看截圖、讀「建議」 | 回報做了什麼、怎麼驗證、還缺什麼 |

- **直接自己做比較好的情況**：小而關鍵、需要判斷力的修改（例如修 Lumina 本身）；寫規格加驗收測試的力氣超過直接做的一半時。
- **派工比較划算的情況**：實作量遠大於規格（完整的遊戲、大量重複修改、要跑很多測試）。
- 派工不保證省 Claude 的用量：品質不夠時，讀程式、找 bug、重新說明反而更花。
- **界線**：只讓 Lumina 做被要求或明顯必要的事；建立 repo、上傳、發布、刪檔、安裝大型軟體一律不派、不自動允許，先問使用者。

### 4. 額度

`GET /api/usage` 回傳 Antigravity 的兩個額度池（`remaining_fraction` 是剩下的比例、`reset_time` 重置時間）：

| 額度池 | 模型 | 注意 |
|---|---|---|
| Gemini Models | `gemini-3.8-flash-high` 等 | 預設用這個。一個中型遊戲大約 20～50 萬 tokens |
| Claude and GPT models | `claude-sonnet-4-6`、`claude-opus-4-6-thinking` | 額度很少、燒得很快（一題 Pac-Man 沒做完就用完 5 小時額度）；使用者同意才用，用前先查剩多少 |

派工前先查額度；剩不到 20% 時告訴使用者，不要硬跑到被鎖。

## 給 AI 協作：Claude（桌面版對話）把長影片、大檔案交給 Lumina

> **給 AI 模型**：你是 Claude 桌面版 Chat 分頁裡的 Claude，而且看得到 `lumina_ask` 工具時讀這一節。

### 什麼時候交給 Lumina

Lumina 是使用者電腦上的 Gemini，用 Antigravity 的額度（跟你的額度分開）。Gemini 可以**直接看影片、聽聲音**，不用先拆成圖片和逐字稿。

| 交給 Lumina | 自己做 |
|---|---|
| 很長的影片、錄音（例如超過幾分鐘的課程、會議、遊戲實況） | 很短的片段、使用者只問一個小細節 |
| 很大的 PDF、一次很多檔案，需要先讀完再摘要 | 需要你自己判斷、整理、跟使用者討論的部分 |
| 使用者說「交給 Lumina」「讓 Gemini 看」 | |

**不要**用 Naiz Studio 的 `video-look` 看長影片：拆出來的畫面和逐字稿會全部進到你的對話裡，很吃上下文和額度。長影片一律交給 Lumina。

### 怎麼用

1. `lumina_ask`：交出工作，馬上回傳 `job_id`。
   - `prompt`：寫清楚要什麼，越具體越好。例如「列出每個段落的主題和開始時間」「找出講者提到 X 的所有時間點，附原話」，不要只寫「看一下這個影片」。
   - `files`：本機檔案的**完整路徑**（影片、音訊、圖片、PDF、文字檔都可以）。
   - `conversation_id`：追問同一份內容時帶上（`lumina_result` 會給），Lumina 記得看過的東西，不用重看，又快又省。
   - `model`：預設 `gemini-3.8-flash-high`，通常不用改；`lumina_models` 可以列出能用的模型。
2. `lumina_result`：拿結果。還沒好會回報進度（每次最多等約 50 秒），再呼叫一次就好。長影片可能要好幾分鐘，等的時候可以先跟使用者說正在處理。
3. 拿到結果後，由你整理、判斷、回答使用者。Lumina 的回答會附時間點，有疑問就用 `conversation_id` 追問，不要自己猜影片內容。

### 檔案超過 100 MB、要執行指令、要存檔：Code 模式

Lumina（agy）**一個檔案最多讀 100 MB**，這是 Google 那邊的限制，調不了。很長的影片通常超過，這時 `lumina_ask` 帶 `work_dir`（一個資料夾的完整路徑，通常就是影片所在的資料夾）：

- Lumina 會在那個資料夾工作，可以執行指令（例如用 ffmpeg 把影片切成 100 MB 以內的段落、依換頁抽投影片影格）、讀寫檔案、用其他 MCP 工具，再看處理後的結果。
- prompt 裡寫清楚怎麼處理，例如「影片太大，先用 ffmpeg 切成每段 10 分鐘、720p，再逐段看」，以及結果要存到哪裡。
- **授權**：使用者在 Lumina「設定 → 一般」開了「自動模式」就不會詢問。沒開時，`lumina_result` 會回「等待授權：Lumina 想執行 …」，這時**先問使用者**，再用 `lumina_approve` 回答 `allow`（這一次）、`allow_all`（這段工作同一個程式都允許）或 `deny`。不要自己替使用者決定。
- 沒有 `work_dir` 時是唯讀的一般模式：不能執行指令，需要授權的操作會被自動拒絕。

**誠實要求**：要求看畫面時，在 prompt 裡要求 Lumina 每一項標出來源（【畫面】或【字幕】），而且「看不到畫面就停下來回報，不要用字幕推測」。曾經發生過影片讀不到、模型只讀字幕卻寫出「逐頁整理」的情況。

### 注意

- Lumina 要開著（http://127.0.0.1:8765）。連不到時工具會說，請使用者打開 Lumina（雙擊「啟動.vbs」或桌面捷徑）。
- 沒給 `work_dir` 時 Lumina 只能讀檔、上網查資料，**不能執行指令或改檔案**；需要授權的操作會自動拒絕。
- 交出去的對話會出現在 Lumina 的對話清單，使用者可以在 Lumina 裡看到完整過程。
- 實測：7 秒的影片約 45 秒拿到結果（含畫面和說話內容、附時間點）；追問約 12 秒。

### 安裝（使用者或開發者做一次）

在 Claude 桌面版的 `claude_desktop_config.json` 的 `mcpServers` 加入（路徑換成自己的），再重開 Claude 桌面版：

```json
"lumina": {
  "command": "C:\\...\\python.exe",
  "args": ["C:\\...\\Lumina\\tools\\claude_bridge_mcp.py"],
  "env": {"PYTHONUTF8": "1"}
}
```

設定檔位置：Microsoft Store 版在 `%LOCALAPPDATA%\Claude-Data\claude_<一串字>\claude_desktop_config.json`；一般安裝版在 `%APPDATA%\Claude\claude_desktop_config.json`。

## 發布新版（開發者）
```
python release.py 1.1.0 "更新內容第一行" "第二行"
```
會改 `version.py`、產生 `manifest.json` 與 `dist/Antigravity-UI-v1.1.0.zip`，然後 commit、tag、push 並建立 GitHub Release。
大家的介面下次開啟時就會看到更新通知。
