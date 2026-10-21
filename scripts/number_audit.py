#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""稽核：頁面上的每一個數字都要對得回 out/（實跑的 JSON 與 log）。

   這一型專題的硬條件是「頁面上每個數字都有一支存下來的 API 輸出可以對回去」
   （types/tool.md〈查證〉）。這支程式把那句話變成可執行的檢查，分兩道：

     A. 逐一比對　每個數字都要在 out/ 的探針輸出裡找得到
        （含 out/ui/——那是 browser_probe.py 用真的瀏覽器拍回來的畫面）。
        允許三種變形，因為頁面上的寫法跟 JSON 裡存的常常不同單位或精度：
          · 四捨五入   206.51 → 206.5
          · 比例↔百分比 0.816 → 81.6%
          · 千分位逗號 16127 → 16,127
        三種都對不上的，必須列進本檔的 EXEMPT，**而且要寫理由**。
        （計畫書第 6 節說「對不到的人工逐條交代」——EXEMPT 就是那份交代。）

        **這一道的天花板**：它查的是「這個數字在探針輸出裡出現過沒有」，
        不是「這個數字出現在對的地方」。把 46 改成 47 它抓不到，
        因為 47 剛好是另一支探針的回傳筆數。真正的把關仍然是人——
        `--where` 會印出每個數字是在哪幾支探針裡對上的，
        **改完數字之後用它掃一眼，看看對上的地方是不是該對上的那個**。

     B. 出處行　含有「有辨識度的數字」的每一節，都要有一行 class="figsrc"
        指向 out/*.json 或產生器。
        會有這一道，是因為出處行是手寫的，改寫內容時會被順手刪掉而沒人發現
        （_notes 第 21 條：第 7 節就這樣掉過一次）。
        「有辨識度」＝ 10 以上或帶小數點。個位數幾乎都是節次、步驟、
        「三張圖」這類修辭，拿來要求出處只會製造雜訊。

   用法：python3 scripts/number_audit.py              （掃專題根目錄所有 *.html）
         python3 scripts/number_audit.py part1-templates.html
         python3 scripts/number_audit.py --where part1-templates.html
                                                （印出每個數字對到哪幾支探針）
   換一個專題時只要改 D 這一行。
"""
import io, re, os, sys, glob, json, html

D = "/home/wanjuli/claude_linux/BSC_plan/specific_topics/fly_doom"

# ── 對不回 out/ 但確定沒問題的數字：一筆一個理由，沒有理由就不要加 ────────
EXEMPT = {
    "0.0001": "「p < 0.0001」是上界寫法：E1 的 p 值都是 4.99975e-05（out/fruitfly/ext_vizdoom1.3.0/E1.json），"
              "也就是配對置換檢定 20,000 次能給出的最小值，比 0.0001 小。",
    "20,001": "1／20,001 是配對置換檢定 20,000 次的最小 p（(0+1)/(20000+1)），E1.json 的 4.99975e-05 就是它；20000 是 doom/analyze.py 的常數。",
    "240": "115 + 119 + 6 ＝ 240（圖 2 八群的顆數加總；sizes 在 out/demo_data.json 的 circuit.sizes）。",
    "3,723": "3,963 − 240 ＝ 3,723（子圖神經元數減掉圖 2 八群的顆數）。3,963 在 out/demo_data.json 的 circuit.n。",
    "1,024": "2 的 10 次方＝1,024：10 局配對置換的翻號組合數，PART 3 第 7 節用它解釋 p 的下限 2／1,024 ≈ 0.002（analysis.json 裡三個條件的 p 都是 0.0023）。",
    "1.96": "95% 信賴區間的常數（常態分布的 97.5 百分位）；PART 4 E1 用它解釋 ci95 怎麼算，不是資料。拆課前它碰巧對到 out/blackjack 的某個數。",
    "28.59": "完整接線 0° 的轉向訊號在 calibration_fly.json 的 rows 裡是 −28.59（負號＝偏左），PART 3 第 6 節寫的是它的絕對值；校準規則取絕對值。",
}

# ── 不是資料的數字：節次、日期、授權版本、文獻出處 ──────────────────────
SKIP_CONTEXT = [
    (r'第\s*$',            "第 N 節／第 N 步"),
    (r'PART\s*$',          "PART 編號"),
    (r'id="s$',            "章節錨點"),
    (r'CC-BY[-A-Z]*[_ ]$', "授權版本號"),
    (r'20\d\d[-年]\s*$',   "日期的月"),
    (r'20\d\d[-年]\s*\d+\s*[-月]\s*$', "日期的日"),
    (r'(Neuron|Cell|Nature|Science)\s*$', "期刊卷號"),
    (r'\d:$',              "頁碼"),
    (r'doi:\s*$',          "DOI"),
    (r'doi:10\.$',         "DOI 的後半"),
    (r'[–-]$',             "頁碼範圍的後半"),
]
SKIP_TOKEN = {
    "2010", "2014", "2018", "2020", "2023", "2024", "2025", "2026",   # 文獻與抓取年份（2024 = Shiu 等人的全腦模型；拆課前它碰巧對到 out/blackjack 的某個數）
    "4.0", "3.0",                                             # 授權版本
}

# 千分位逗號要吃進來（16,127），但句末的逗號不能算數字的一部分（「2014,」）
# 第一個分支要求「至少有一組千分位逗號」，否則 2026 會被切成 202 ＋ 6。
NUM = re.compile(r'(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])\d+(?:\.\d+)?')


# 這些欄位裡的數字不是「資料」，是網址、雜湊、計時、位元組數、編號。
# 留著只會讓任何數字都碰巧對得上，把稽核稀釋成橡皮圖章。
JUNK_KEYS = {"url", "urls", "sha256", "seconds", "bytes", "fetched_at", "run_at",
             "id", "iri", "source_iri", "link", "thumbnail", "thumbnail_transparent",
             "short_form", "accession", "report_url", "base"}


def haystack():
    """out/ 底下探針輸出裡出現過的數字 → 出自哪幾支探針。"""
    got = {}

    def add(v, src):
        got.setdefault(repr(float(v)), set()).add(src)

    def walk(o, src):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in JUNK_KEYS or str(k).endswith("_url"):
                    continue
                walk(k, src); walk(v, src)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v, src)
        elif isinstance(o, bool):
            pass
        elif isinstance(o, (int, float)):
            add(o, src)
        elif isinstance(o, str):
            if o.startswith(("http://", "https://")):
                return
            for m in NUM.findall(o):
                add(m.replace(",", ""), src)

    # 這個專題的「原文」是兩個 run_all.sh 的實跑產出：results/ 的 JSON 與 logs/ 的終端輸出，
    # 由 scripts/collect_out.py 收進 out/。JSON 逐欄走；log 與文字檔整份抽數字。
    for f in sorted(glob.glob(os.path.join(D, "out", "**", "*"), recursive=True)):
        if not os.path.isfile(f):
            continue
        tag = os.path.relpath(f, os.path.join(D, "out"))
        if f.endswith(".json"):
            walk(json.load(io.open(f, encoding="utf-8")), tag)
        else:
            for m in NUM.findall(io.open(f, encoding="utf-8", errors="replace").read()):
                add(m.replace(",", ""), tag)
    return got


def found(page_num, hay):
    """頁面上的數字對得回 out/ 嗎？回傳 (對上的方式, 出自哪幾支探針)，對不上回 None。"""
    v = float(page_num.replace(",", ""))
    if repr(v) in hay:
        return "直接", hay[repr(v)]
    for h in hay:
        f = float(h)
        # 四捨五入：JSON 裡存的精度比頁面上寫的高
        for nd in (0, 1, 2, 3):
            if round(f, nd) == v and f != v:
                return f"四捨五入自 {h.rstrip('0').rstrip('.')}", hay[h]
        # 比例↔百分比
        if f and abs(f * 100 - v) < 1e-9:
            return f"百分比，來自比例 {h.rstrip('0').rstrip('.')}", hay[h]
        if f and abs(f / 100 - v) < 1e-12:
            return f"比例，來自百分比 {h.rstrip('0').rstrip('.')}", hay[h]
    return None


def text_of(fragment):
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', fragment, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', t))


def sections(src):
    # 目錄是索引不是內文——它會把各節的小標（連同小標裡的數字）再列一次，
    # 於是「前言」那一段永遠缺出處行。整段拿掉。
    src = re.sub(r'<nav class="toc">.*?</nav>', " ", src, flags=re.S)
    """切成 (錨點, 標題, 原始 HTML) 的清單；h2 之前的算作「(前言)」。"""
    # 最後一節的範圍會一路吃到頁尾，而頁尾有日期也有出處字樣——
    # 不切掉的話，最後一節等於自動通過所有「這一節有沒有…」的檢查（實測過）。
    cut = src.find('<div class="pager"')
    if cut > 0:
        src = src[:cut]
    parts = re.split(r'(<h2\b[^>]*id="s\d+"[^>]*>.*?</h2>)', src, flags=re.S)
    out = [("(前言)", "(前言)", parts[0])]
    for k in range(1, len(parts), 2):
        sid = re.search(r'id="(s\d+)"', parts[k]).group(1)
        title = re.sub(r'\s+', ' ', text_of(parts[k])).strip()
        out.append((sid, title, parts[k] + parts[k + 1]))
    return out


def audit(path, hay, where=False):
    b = os.path.basename(path)
    src = io.open(path, encoding="utf-8").read()
    src = re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=re.S)
    # PART 6 的程式區塊（<pre class="code">）是原始碼的照抄，數字由 scripts/make_code.py --check 逐行對回原檔
    src = re.sub(r'<pre class="code">.*?</pre>', ' ', src, flags=re.S)
    bad = 0
    print(f"══════ {b}")

    # ── A. 每個數字都要對得回 out/ ──
    txt = text_of(src)
    unmatched, checked, seen = {}, 0, {}
    for m in NUM.finditer(txt):
        tok = m.group(0)
        before = txt[max(0, m.start() - 24):m.start()]
        if tok in SKIP_TOKEN or any(re.search(p, before) for p, _ in SKIP_CONTEXT):
            continue
        checked += 1
        # **out/ 要先查，EXEMPT 是最後手段。**
        # 反過來寫的話，一筆為某一頁寫的 EXEMPT 會把別頁同一個數字一起蓋掉：
        # PART 3 的「481 倍」列了 EXEMPT，於是 PART 6 那個真的存在於
        # out/three_layers.json 的 481（cells_only 的筆數）也被吞掉，
        # --where 只印得出「EXEMPT」，看不出它其實有來源。（第 78 條同一型。）
        hit = found(tok, hay)
        if hit:
            seen.setdefault(tok, hit)
            continue
        if tok in EXEMPT:
            seen.setdefault(tok, ("EXEMPT", {"（見 EXEMPT 的理由）"}))
            continue
        ctx = re.sub(r'\s+', ' ', txt[max(0, m.start() - 30):m.end() + 20])
        unmatched.setdefault(tok, ctx)
    for tok, ctx in sorted(unmatched.items()):
        print(f"  [對不回] {tok}　…{ctx}…")
        bad += 1
    print(f"  A　查了 {checked} 個數字，對不回的 {len(unmatched)} 個"
          f"（另有 {len(EXEMPT)} 個列在 EXEMPT，各有理由）")
    if where:
        print("  ── 每個數字對到哪裡（請人眼確認「對上的是不是該對上的那個」）──")
        # 只列有辨識度的：個位數在每一支探針裡都找得到，列出來全是雜訊
        picked = [t for t in seen
                  if float(t.replace(",", "")) >= 10 or "." in t]
        for tok in sorted(picked, key=lambda x: float(x.replace(",", ""))):
            how, srcs = seen[tok]
            print(f"     {tok:>9}　{how:<26}{'、'.join(sorted(srcs))}")

    # ── B. 有辨識度的數字所在的那一節，要有出處行 ──
    for sid, title, body in sections(src):
        t = text_of(body)
        hits = []
        for m in NUM.finditer(t):
            tok = m.group(0)
            before = t[max(0, m.start() - 24):m.start()]
            if tok in SKIP_TOKEN or any(re.search(p, before) for p, _ in SKIP_CONTEXT):
                continue
            v = float(tok.replace(",", ""))
            if v >= 10 or "." in tok:          # 有辨識度
                hits.append(tok)
        if hits and 'class="figsrc"' not in body:
            print(f"  [缺出處] {sid} {title[:26]} 有 {len(hits)} 個數字"
                  f"（{'、'.join(sorted(set(hits))[:5])}…）卻沒有 figsrc")
            bad += 1
    return bad


def main():
    args = [a for a in sys.argv[1:] if a != "--where"]
    where = "--where" in sys.argv[1:]
    files = ([os.path.join(D, a) if not os.path.isabs(a) else a for a in args]
             or sorted(glob.glob(os.path.join(D, "*.html"))))
    hay = haystack()
    print(f"out/ 裡可以對回去的數字：{len(hay)} 個"
          f"（已排除網址、雜湊、計時、位元組數與編號）\n")
    bad = sum(audit(f, hay, where) for f in files)
    print("\n=== 稽核：數字對回 out/ ===",
          "全部通過" if bad == 0 else f"{bad} 個問題")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
