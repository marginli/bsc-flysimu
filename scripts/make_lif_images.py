"""PART 1 圖 1（漏電整合發放）的投影片用圖與離線包。
用無頭 Chrome 開單獨頁 lif.html?s=…&at=…&clean=1（直接算到那一刻並暫停），逐一存下每個畫面：
  downloads/lif/p1lif-*.png   高解析點陣圖（寬 3,200 像素），直接插進 PowerPoint
  downloads/lif/p1lif-*.svg   向量圖（PowerPoint 365 可插入、放大不糊）
  downloads/lif/flydoom-lif.zip   圖 ＋ 單獨頁 ＋ 使用說明
單獨頁由 make_lif_anim.py 產生；改了它就重跑本檔。第 6、7 步的輸入是隨機的，用固定種子（seed）讓每次產出一樣。
用法：python3 scripts/make_lif_images.py"""
import pathlib
import zipfile

from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).resolve().parent.parent
OUT = D / "downloads/lif"
STATES = [  # (網址參數, 檔名, 說明)
    ("s=1&at=60", "s1", "第 1 步　漏電：水位往 V_rest 回落，20 ms 後差距剩約 37%"),
    ("s=2&at=45", "s2", "第 2 步　一次輸入：g 跳高約 3 mV，水位只升 0.48 mV"),
    ("s=3&at=170", "s3", "第 3 步　整合：同樣 15 個輸入，分散送不放電、同一刻送就放電"),
    ("s=4&at=15", "s4-mid", "第 4 步　放電後的不反應期（15 ms 那一刻：水位停在 V_rest，第二批輸入先存在 g）"),
    ("s=4&at=30", "s4", "第 4 步　放電與不反應期：不反應期結束後再放電一次"),
    ("s=5&at=110", "s5", "第 5 步　抑制：同樣 20 個興奮，加上 10 個抑制就不放電"),
    ("s=6&nup=50&seed=7&at=1000", "s6-50", "第 6 步　持續輸入：上游 50 顆（每顆每秒 20 次），跑 1 秒"),
    ("s=6&nup=150&seed=7&at=1000", "s6-150", "第 6 步　持續輸入：上游 150 顆，放電率更高"),
    ("s=7&rate=100&seed=7&at=1000", "s7", "第 7 步　LC10a 的外部刺激：r ＝ 100 Hz，抽中直接加 68.75 mV"),
]

OUT.mkdir(parents=True, exist_ok=True)
errs, files = [], []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--disable-gpu"])
    pg = b.new_page(viewport={"width": 1600, "height": 942}, device_scale_factor=2)   # 900:530 的圖剛好填滿
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    for q, tag, _ in STATES:
        pg.goto(f"{(D / 'lif.html').as_uri()}?{q}&clean=1")
        pg.wait_for_timeout(700)
        el = pg.locator(".lif-svg")
        stem = f"p1lif-{tag}"
        el.screenshot(path=str(OUT / f"{stem}.png"))
        svg = el.evaluate("""e => { const c = e.cloneNode(true); c.removeAttribute('class');
            const vb = c.viewBox.baseVal; c.setAttribute('width', vb.width); c.setAttribute('height', vb.height);
            c.querySelectorAll('[opacity="0"]').forEach(n => n.remove());
            c.querySelectorAll('.lif-now').forEach(n => n.remove());
            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('width', '100%'); bg.setAttribute('height', '100%'); bg.setAttribute('fill', '#fff');
            c.insertBefore(bg, c.firstChild);
            return '<?xml version="1.0" encoding="UTF-8"?>\\n' + c.outerHTML; }""")
        (OUT / f"{stem}.svg").write_text(svg, encoding="utf-8")
        files += [f"{stem}.png", f"{stem}.svg"]
    b.close()
assert not errs, errs

readme = ("果蠅玩 Doom：漏電整合發放（PART 1 圖 1）投影片用圖\n\n"
          f"{len(STATES)} 個畫面，每個都有 PNG（點陣，寬 3,200 像素）與 SVG（向量）兩種，挑一種插進 PowerPoint 即可：\n"
          + "".join(f"  p1lif-{tag}　{zh}\n" for _, tag, zh in STATES)
          + "\n每個輸入是 11 個突觸 × 0.275 mV ≈ 3 mV；第 6、7 步的隨機輸入用固定種子，每次產出一樣。"
          "每一步的說明在 PART 1 第 2 節圖 1。\n\n"
          "要現場操作：用瀏覽器打開 lif.html（單一檔案、不需網路）。\n"
          "  ← → 或 PageUp／PageDown：上一步、下一步；1–7：跳到第幾步；Home／End：第一步／最後一步；\n"
          "  空白鍵或 P：暫停／播放；R：重播這一步；S：換速度；\n"
          "  E：送 1 個興奮輸入；I：送 1 個抑制輸入；B：同一刻送 15 個興奮輸入；D：顯示／隱藏這一步的說明；F：全螢幕。\n"
          "  網址後面加 ?s=4&speed=0 這類參數可以指定一開始的畫面（s 第幾步、speed 0 很慢／1 慢／2 快、nup 第 6 步上游顆數、rate 第 7 步的 r）。\n\n"
          "線上版：https://marginli.github.io/bsc-flysimu/lif.html\n"
          "說明：https://marginli.github.io/bsc-flysimu/part1-what.html#s2\n")
z = OUT / "flydoom-lif.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    root = z.stem + "/"
    zf.write(D / "lif.html", root + "lif.html")
    zf.writestr(root + "使用說明.txt", readme)
    for f in files:
        zf.write(OUT / f, root + f)
print(len(files), "個圖檔；", z.name, z.stat().st_size // 1024, "KB")
