"""PART 1 圖 5（讀出規則）的投影片用圖與離線包。
用無頭 Chrome 開單獨頁 readout.html?s=…&az=…|tic=…&clean=1（停在那個方位或那一格），逐一存下每個畫面：
  downloads/readout/p1ro-*.png   高解析點陣圖（寬 3,200 像素），直接插進 PowerPoint
  downloads/readout/p1ro-*.svg   向量圖（PowerPoint 365 可插入、放大不糊）
  downloads/readout/flydoom-readout.zip   圖 ＋ 單獨頁 ＋ 使用說明
單獨頁由 make_readout_anim.py 產生；改了它就重跑本檔。圖上沒有隨機的部分，每次產出一樣。
用法：python3 scripts/make_readout_images.py"""
import json
import pathlib
import zipfile

from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).resolve().parent.parent
OUT = D / "downloads/readout"
R = json.load(open(D / "out/readout_fig.json", encoding="utf-8"))
EP, CAL = R["episode"], R["cal"]
TT, FT, QT = (str(CAL[k]) for k in ("turn_th", "fire_th", "quiet_th"))
STATES = [  # (網址參數, 檔名, 說明)
    ("s=1&tic=12", "s1", "第 1 步　讀哪些數：八群的放電率，單算一格的值與平滑後的值（PART 5 那一局第 12 格）"),
    ("s=2&az=10", "s2", "第 2 步　轉向訊號：四個數加減（校準表，敵人在 +10°）"),
    ("s=3&az=0", "s3-0", f"第 3 步　轉向門檻 ±{TT}：敵人在 0°，訊號在中間，不轉"),
    ("s=3&az=-10", "s3-m10", f"第 3 步　轉向門檻 ±{TT}：敵人在 −10°，超過門檻，按左轉"),
    ("s=4&az=0", "s4-0", f"第 4 步　開火：敵人在 0°，兩側 AOTU019 都超過 {FT}，按開火"),
    ("s=4&az=10", "s4-10", "第 4 步　開火：敵人在 +10°，只有一側亮，不開火"),
    ("s=5&az=0", "s5", "第 5 步　門檻怎麼定：校準曲線（17 個方位）"),
    ("s=6&tic=30", "s6-30", f"第 6 步　沒有敵人：第 30 格，敵人第 {EP['gone_tic']} 格離開，放電率還沒降完，什麼都不按"),
    ("s=6&tic=41", "s6-41", f"第 6 步　沒有敵人：第 41 格，八群加總低於安靜門檻 {QT} Hz，固定按右轉"),
    ("s=7&tic=160", "s7", f"第 7 步　真實的一局：第 160 格（共 {EP['n']} 格），照規則算的和遊戲當時按的相同"),
]

OUT.mkdir(parents=True, exist_ok=True)
errs, files = [], []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--disable-gpu"])
    pg = b.new_page(viewport={"width": 1600, "height": 1102}, device_scale_factor=2)   # 900:620 的圖剛好填滿
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    for q, tag, _ in STATES:
        pg.goto(f"{(D / 'readout.html').as_uri()}?{q}&clean=1")
        pg.wait_for_timeout(800)   # 等淡入淡出（opacity .3 s）跑完
        el = pg.locator(".ro-svg")
        stem = f"p1ro-{tag}"
        el.screenshot(path=str(OUT / f"{stem}.png"))
        svg = el.evaluate("""e => { const c = e.cloneNode(true); c.removeAttribute('class');
            const vb = c.viewBox.baseVal; c.setAttribute('width', vb.width); c.setAttribute('height', vb.height);
            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('width', '100%'); bg.setAttribute('height', '100%'); bg.setAttribute('fill', '#fff');
            c.insertBefore(bg, c.firstChild);
            return '<?xml version="1.0" encoding="UTF-8"?>\\n' + c.outerHTML; }""")
        (OUT / f"{stem}.svg").write_text(svg, encoding="utf-8")
        files += [f"{stem}.png", f"{stem}.svg"]
    b.close()
assert not errs, errs

readme = ("果蠅玩 Doom：讀出規則（PART 1 圖 5）投影片用圖\n\n"
          f"{len(STATES)} 個畫面，每個都有 PNG（點陣，寬 3,200 像素）與 SVG（向量）兩種，挑一種插進 PowerPoint 即可：\n"
          + "".join(f"  p1ro-{tag}　{zh}\n" for _, tag, zh in STATES)
          + "\n第 2–5 步用校準表的數字（假想敵人、20 格平均）；第 1、6、7 步是 PART 5 影片那一局的逐格紀錄。"
          "每一步的說明在 PART 1 第 4 節圖 5。\n\n"
          "要現場操作：用瀏覽器打開 readout.html（單一檔案、不需網路）。\n"
          "  ← → 或 PageUp／PageDown：上一步、下一步；1–7：跳到第幾步；Home／End：第一步／最後一步；\n"
          "  ↑ ↓：第 2–5 步換敵人方位、第 1、6、7 步換一格（Shift 一次 10 格）；\n"
          "  空白鍵或 P：暫停／播放；S：換速度；D：顯示／隱藏這一步的說明；F：全螢幕。\n"
          "  網址後面加 ?s=3&az=-10 或 ?s=7&tic=160 這類參數可以指定一開始的畫面"
          "（s 第幾步、az 敵人方位、tic 第幾格、speed 0 慢／1 中／2 實際速度、play=0 停住）。\n\n"
          "線上版：https://marginli.github.io/bsc-flysimu/readout.html\n"
          "說明：https://marginli.github.io/bsc-flysimu/part1-what.html#s4\n")
z = OUT / "flydoom-readout.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    root = z.stem + "/"
    zf.write(D / "readout.html", root + "readout.html")
    zf.writestr(root + "使用說明.txt", readme)
    for f in files:
        zf.write(OUT / f, root + f)
print(len(files), "個圖檔；", z.name, z.stat().st_size // 1024, "KB")
