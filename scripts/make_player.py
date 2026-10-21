"""播放台單獨版（player.html）的資料與離線包。
  assets/demo/data.js                     data.json 裡播放台用到的三塊（episodes、cal、circuit）包成 window.FD_DATA（file:// 開網頁時 fetch 讀不到 JSON，<script> 可以）
  downloads/player/flydoom-player.zip     player.html ＋ assets/demo/（data.js、三支影片）＋ 使用說明，解壓後直接用瀏覽器開
data.json 或影片改了（build_data.py 之後）就重跑。player.html 的播放邏輯照抄 part5-demo.html，改那邊要一起改。
用法：python3 scripts/make_player.py"""
import json
import os
import zipfile

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(D, "assets/demo")
VIDEOS = ["fly.mp4", "lesion025.mp4", "scrambled_cal.mp4"]
README = """果蠅玩 Doom：播放台離線版

用法：解壓縮後，用瀏覽器（Chrome、Edge、Safari、Firefox）打開 player.html。
不需要網路，也不用裝任何東西。player.html 旁邊的 assets 資料夾要一起留著。

簡報時：在投影片上插入超連結，連到這個 player.html，點了就開瀏覽器；按「全螢幕」放大整頁。
指定一開始的大腦與時間：在網址後面加 ?b=lesion025&t=3.5
  b：fly（完整接線）、lesion025（損毀 AOTU025）、scrambled_cal（打亂接線，各自校準）
  t：從第幾秒開始
鍵盤：空白鍵 播放／暫停、← → 一格（1/35 秒）、Shift＋← → 一秒、1 2 3 換大腦

線上版：https://marginli.github.io/bsc-flysimu/player.html
說明：https://marginli.github.io/bsc-flysimu/part5-demo.html
"""

data = json.load(open(os.path.join(DEMO, "data.json"), encoding="utf-8"))
sub = {k: data[k] for k in ["episodes", "cal", "circuit"]}
js = "window.FD_DATA=" + json.dumps(sub, ensure_ascii=False, separators=(",", ":")) + ";\n"
open(os.path.join(DEMO, "data.js"), "w", encoding="utf-8").write(js)

out = os.path.join(D, "downloads/player/flydoom-player.zip")
os.makedirs(os.path.dirname(out), exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    root = "flydoom-player/"
    z.write(os.path.join(D, "player.html"), root + "player.html")
    z.writestr(root + "使用說明.txt", README)
    z.write(os.path.join(DEMO, "data.js"), root + "assets/demo/data.js")
    for v in VIDEOS:
        z.write(os.path.join(DEMO, v), root + "assets/demo/" + v, compress_type=zipfile.ZIP_STORED)
print("data.js", len(js) // 1024, "KB;", out, os.path.getsize(out) // 1024, "KB")
