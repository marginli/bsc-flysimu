"""從 PART 6 的三段錄影（assets/demo/*.mp4，record_demo.py 錄的原始遊戲畫面，640×480、35 fps）
抽出幾格當 PART 3 的實況截圖。格號與 assets/demo/data.json 的逐格資料對齊（第 n 格 = 影片第 n 幀）。
用法：python3 scripts/make_shots.py   （需要 ~/anaconda3/bin/ffmpeg）
"""
import os, subprocess
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = os.path.expanduser("~/anaconda3/bin/ffmpeg")
SHOTS = [("fly", 21), ("fly", 60)]
for pol, n in SHOTS:
    src = os.path.join(D, "assets", "demo", f"{pol}.mp4")
    dst = os.path.join(D, "assets", f"p3-shot-{pol}-{n:03d}.png")
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf", f"select=eq(n\\,{n})", "-vframes", "1", dst], check=True)
    print("寫出", os.path.relpath(dst, D))
