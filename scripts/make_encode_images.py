"""PART 1 圖 3（輸入編碼）的投影片用圖與離線包。
用無頭 Chrome 開單獨頁 encode.html?s=…&cx=…&h=…&clean=1，逐一存下每個畫面：
  downloads/encode/p1enc-*.png   高解析點陣圖（寬 3,200 像素），直接插進 PowerPoint
  downloads/encode/p1enc-*.svg   向量圖（PowerPoint 365 可插入、放大不糊）
  downloads/encode/flydoom-encode.zip   圖 ＋ 單獨頁 ＋ 使用說明
單獨頁由 make_encode_anim.py 產生；改了它就重跑本檔。第 6 步的放電是隨機的，用固定種子（seed）讓每次產出一樣。
用法：python3 scripts/make_encode_images.py"""
import pathlib
import zipfile

from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).resolve().parent.parent
OUT = D / "downloads/encode"
STATES = [  # (網址參數, 檔名, 說明)
    ("s=1&cx=232&h=26", "s1", "第 1 步　遊戲回報方框"),
    ("s=2&cx=232&h=26", "s2", "第 2 步　換成方位角"),
    ("s=3&cx=232&h=26", "s3", "第 3 步　哪一眼（敵人在右，只刺激右眼）"),
    ("s=3&cx=165&h=26", "s3-front", "第 3 步　敵人在正前方 ±6° 內，兩眼都刺激"),
    ("s=4&cx=232&h=26", "s4", "第 4 步　哪幾顆（鐘形曲線的形狀）"),
    ("s=5&cx=232&h=12", "s5-far", "第 5 步　多強：敵人遠、方框小"),
    ("s=5&cx=232&h=45", "s5-near", "第 5 步　多強：敵人近、方框大（滿格）"),
    ("s=6&cx=232&h=26&seed=7", "s6", "第 6 步　隨機放電（黑點是這一刻放電的 LC10a）"),
    ("s=6&cx=232&h=26&two=1&seed=7", "s6-two", "第 6 步　兩個敵人，刺激疊加"),
]

OUT.mkdir(parents=True, exist_ok=True)
errs, files = [], []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--disable-gpu"])
    pg = b.new_page(viewport={"width": 1600, "height": 1107}, device_scale_factor=2)   # 900:622 的圖剛好填滿
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    for q, tag, _ in STATES:
        pg.goto(f"{(D / 'encode.html').as_uri()}?{q}&clean=1")
        pg.wait_for_timeout(700)
        el = pg.locator(".enc-svg")
        stem = f"p1enc-{tag}"
        el.screenshot(path=str(OUT / f"{stem}.png"))
        svg = el.evaluate("""e => { const c = e.cloneNode(true); c.removeAttribute('class');
            const vb = c.viewBox.baseVal; c.setAttribute('width', vb.width); c.setAttribute('height', vb.height);
            c.querySelectorAll('[visibility=hidden]').forEach(n => n.remove());
            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('width', '100%'); bg.setAttribute('height', '100%'); bg.setAttribute('fill', '#fff');
            c.insertBefore(bg, c.firstChild);
            return '<?xml version="1.0" encoding="UTF-8"?>\\n' + c.outerHTML; }""")
        (OUT / f"{stem}.svg").write_text(svg, encoding="utf-8")
        files += [f"{stem}.png", f"{stem}.svg"]
    b.close()
assert not errs, errs

readme = ("果蠅玩 Doom：輸入編碼（PART 1 圖 3）投影片用圖\n\n"
          f"{len(STATES)} 個畫面，每個都有 PNG（點陣，寬 3,200 像素）與 SVG（向量）兩種，挑一種插進 PowerPoint 即可：\n"
          + "".join(f"  p1enc-{tag}　{zh}\n" for _, tag, zh in STATES)
          + "\n例子是敵人在畫面中心 232 像素（方位角 +40.5°）、方框高 26 像素；第二個敵人固定在 70 像素、高 14 像素。"
          "每一步的說明在 PART 1 第 4 節圖 3。\n\n"
          "要現場操作：用瀏覽器打開 encode.html（單一檔案、不需網路）。\n"
          "  ← → 或 PageUp／PageDown：上一步、下一步；1–6：跳到第幾步；Home／End：第一步／最後一步；\n"
          "  W：讓敵人走動／停住；T：加／拿掉第二個敵人；D：顯示／隱藏這一步的說明；F：全螢幕。\n"
          "  滑桿可拖敵人位置與大小。網址後面加 ?s=6&cx=165&two=1 這類參數可以指定一開始的畫面（s 第幾步、cx 位置 0–320、h 大小、two 第二個敵人、walk=1 走動）。\n\n"
          "線上版：https://marginli.github.io/bsc-flysimu/encode.html\n"
          "說明：https://marginli.github.io/bsc-flysimu/part1-what.html#s4\n")
z = OUT / "flydoom-encode.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    root = z.stem + "/"
    zf.write(D / "encode.html", root + "encode.html")
    zf.writestr(root + "使用說明.txt", readme)
    for f in files:
        zf.write(OUT / f, root + f)
print(len(files), "個圖檔；", z.name, z.stat().st_size // 1024, "KB")
