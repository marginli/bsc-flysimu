#!/usr/bin/env python3
"""PART 6「讀程式」的程式區塊產生器。

頁面（part6-code.html）裡用標記指定要放哪個檔案的哪幾行：

    <!-- code: fly_doom.py 58-67 hl=62,65 lab=62:①,65:② -->
    （中間由本程式填入）
    <!-- /code -->

本程式把標記之間換成帶行號的 <pre class="code">，hl 的行加底色，lab 在行號旁放一個標記。
行號與原檔一致。我們自己寫的檔案（pack/）全文可放；作者的檔案（fruitfly-lab，無授權檔）只放片段，
圖說寫明 commit 與行號，請學員對照自己 clone 的檔案。

用法
  python3 scripts/make_code.py            重新產生所有區塊，並寫 out/code_meta.json（行數、sha256）
  python3 scripts/make_code.py --check    只比對：頁面上的區塊和原檔現在的內容是否一致（規範第 10 節第 7 條）
"""
import hashlib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE)
PAGE = os.path.join(D, "part6-code.html")
AUTHOR = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
COMMIT = "8c27fe8"

SOURCES = {
    # 我們自己寫的（下載包裡有）
    "setup_envs.sh":      ("ours",   os.path.join(D, "pack/setup_envs.sh"),                      "setup_envs.sh"),
    "run_all.sh":         ("ours",   os.path.join(D, "pack/fruitfly_lab/run_all.sh"),             "fruitfly_lab/run_all.sh"),
    "check.py":           ("ours",   os.path.join(D, "pack/check.py"),                            "check.py"),
    "ff1_compare_conn.py":("ours",   os.path.join(D, "pack/fruitfly_lab/ext/ff1_compare_conn.py"),"fruitfly_lab/ext/ff1_compare_conn.py"),
    "ff_extra.py":        ("ours",   os.path.join(D, "pack/fruitfly_lab/ext/ff_extra.py"),        "fruitfly_lab/ext/ff_extra.py"),
    "e4_asymmetry.py":    ("ours",   os.path.join(D, "pack/fruitfly_lab/ext/e4_asymmetry.py"),    "fruitfly_lab/ext/e4_asymmetry.py"),
    # 作者的（fruitfly-lab @ 8c27fe8，沒有授權檔：只放片段）
    "extract.py":         ("author", os.path.join(AUTHOR, "flycircuit/extract.py"),  "flycircuit/extract.py"),
    "validate.py":        ("author", os.path.join(AUTHOR, "flycircuit/validate.py"), "flycircuit/validate.py"),
    "lif.py":             ("author", os.path.join(AUTHOR, "flycircuit/lif.py"),      "flycircuit/lif.py"),
    "fly_doom.py":        ("author", os.path.join(AUTHOR, "doom/fly_doom.py"),       "doom/fly_doom.py"),
    "analyze.py":         ("author", os.path.join(AUTHOR, "doom/analyze.py"),        "doom/analyze.py"),
}

MARK = re.compile(r'<!-- code: (\S+) (\d+)-(\d+)((?: \w+=\S+)*) -->\n(.*?)<!-- /code -->', re.S)


def read(name):
    kind, path, shown = SOURCES[name]
    with open(path, encoding="utf-8") as f:
        return kind, shown, f.read().split("\n")


def colour(line):
    """註解上色：shell 與 python 都用 #。字串裡的 # 這些檔案沒有，不另外處理。"""
    e = html.escape(line)
    m = re.search(r'(^|\s)(#.*)$', e)
    if m and not e.lstrip().startswith("#!"):
        return e[:m.start(2)] + '<span class="cm">' + e[m.start(2):] + '</span>'
    if e.lstrip().startswith("#"):
        return '<span class="cm">' + e + '</span>'
    return e


def block(name, a, b, opts):
    kind, shown, lines = read(name)
    assert 1 <= a <= b <= len(lines), (name, a, b, len(lines))
    hl = set()
    for part in opts.get("hl", "").split(","):
        if not part:
            continue
        if "-" in part:
            x, y = part.split("-"); hl.update(range(int(x), int(y) + 1))
        else:
            hl.add(int(part))
    lab = dict(p.split(":") for p in opts.get("lab", "").split(",") if p)
    out = []
    for n in range(a, b + 1):
        ln = f'<span class="ln">{n:>3}</span>'
        tag = lab.get(str(n))
        mk = f'<span class="mk">{tag}</span>' if tag else '<span class="mk"> </span>'
        body = colour(lines[n - 1])
        row = f"{ln}{mk}{body}"
        # 標記行是 display:block 的 span，本身就會換行；後面不能再接 \n，否則多一個空行
        out.append(f'<span class="hl">{row}</span>' if n in hl else row + "\n")
    code = "".join(out).rstrip("\n")
    if kind == "ours":
        cap = f'下載包的 <code>{shown}</code> 第 {a}–{b} 行'
    else:
        cap = (f'fruitfly-lab 的 <code>{shown}</code> 第 {a}–{b} 行（commit <code>{COMMIT}</code>；'
               f'repo 沒有授權檔，本頁只引片段，請對照你自己 clone 下來的檔案）')
    return (f'<figure class="code"><pre class="code">{code}</pre>'
            f'<figcaption class="figsrc">{cap}</figcaption></figure>\n')


def render(src):
    def sub(m):
        name, a, b, optstr, _ = m.groups()
        opts = dict(kv.split("=", 1) for kv in optstr.split())
        head = f'<!-- code: {name} {a}-{b}{optstr} -->\n'
        return head + block(name, int(a), int(b), opts) + '<!-- /code -->'
    return MARK.sub(sub, src)


def meta():
    files = {}
    for name, (kind, path, shown) in SOURCES.items():
        raw = open(path, "rb").read()
        files[name] = {"kind": kind, "path": shown, "lines": raw.decode("utf-8").count("\n") + (0 if raw.endswith(b"\n") else 1),
                       "sha256_8": hashlib.sha256(raw).hexdigest()[:8]}
    # 頁面上會以文字引用的常數，直接從原始碼抓，讓 number_audit 對得到
    fd = open(SOURCES["fly_doom.py"][1], encoding="utf-8").read()
    consts = {k: float(v) for k, v in re.findall(r'^([A-Z_]+) = ([\d.]+)', fd, flags=re.M)}
    consts["DT"] = 1e-4                     # 原始碼寫 1e-4，上面的 regex 只抓到 1
    consts["STEPS_PER_TIC"] = round(1 / 35 / 1e-4)
    consts["POISSON_KICK_MV"] = 0.275 * 250   # lif.py 說明字串的 68.75 mV ＝ 每個突觸 0.275 mV × 250
    ex = open(SOURCES["extract.py"][1], encoding="utf-8").read()
    m = re.search(r'^THR, DEPTH = (\d+), (\d+)', ex, flags=re.M)
    consts["THR"], consts["DEPTH"] = int(m.group(1)), int(m.group(2))
    va = open(SOURCES["validate.py"][1], encoding="utf-8").read()
    m = re.search(r'^RATE, N_RUN, STEPS = ([\d.]+), (\d+), ([\d_]+)', va, flags=re.M)
    consts["RATE"], consts["N_RUN"], consts["STEPS"] = float(m.group(1)), int(m.group(2)), int(m.group(3).replace("_", ""))
    return {"author_commit": COMMIT, "files": files, "constants": consts,
            "ours_total_lines": sum(v["lines"] for v in files.values() if v["kind"] == "ours"),
            "author_total_lines": sum(v["lines"] for v in files.values() if v["kind"] == "author")}


def main():
    src = open(PAGE, encoding="utf-8").read()
    new = render(src)
    if "--check" in sys.argv:
        if new != src:
            print("[程式區塊] 頁面上的區塊與原檔不一致，重跑 scripts/make_code.py"); return 1
        print(f"=== 程式區塊對回原檔：{len(MARK.findall(src))} 個區塊全部一致"); return 0
    open(PAGE, "w", encoding="utf-8").write(new)
    os.makedirs(os.path.join(D, "out"), exist_ok=True)
    json.dump(meta(), open(os.path.join(D, "out/code_meta.json"), "w"), indent=1, ensure_ascii=False)
    print(f"產生 {len(MARK.findall(new))} 個區塊；out/code_meta.json 已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
