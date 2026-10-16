#!/usr/bin/env python3
"""產生首頁那支約 10 分鐘的說明影片（沿用 VFB／LPU 的管線）。

   內容在 video_slides.py（COURSE 設定 ＋ 投影片要點 ＋ 旁白稿），這支只負責產出：
     1. 每張投影片用 headless Chrome 截成 1920×1080 的 PNG
     2. 每段旁白合成（看 _voice/ 在不在決定走哪一條，見下）
     3. 依各段長度把 PNG 排成影像軌，與音軌一起用 ffmpeg 合成 MP4（本機沒有 libx264，用 libopenh264）
     4. 依各段長度切出 WebVTT 字幕；量成品的秒數寫進 out/video_meta.json

   改了投影片或旁白就重跑：  python3 scripts/make_video.py
   產出：assets/<COURSE["out"]>.mp4、.vtt、assets/poster.jpg、out/video_meta.json

   **旁白有兩種來源，看 _voice/ 在不在：**
     · `_voice/ref.wav` ＋ `_voice/ref.txt` 存在 → 用本機的 F5-TTS 合成，全程在這台機器的 GPU 上跑，稿子不送出去：
           ~/.venvs/tts/bin/python scripts/make_video.py
     · 不存在 → 退回 edge-tts（微軟的語音服務，會把旁白文字送出去）。
   `_voice/` 不進版控（.gitignore）：那是本機合成要用的參考音檔與它的逐字稿，屬於這台機器的設定。

   **本機合成的實測教訓**（VFB 2026-09-15 三條，加上本課 2026-10-16 的驗證）：
     1. 參考音檔的頭尾都要落在停頓處，否則它最後幾個字會漏進合成音。
     2. 合成語速跟著參考音檔走，要用照稿唸的那一種。
     3. 阿拉伯數字要先轉國字（zh_num），負號「−」要轉成「負」、正號「+」轉成「正」（直接送會被唸成別的字）。
     4. 縮寫逐一驗過（辨識回填）：不拆字母才對的有 KC、PAM、CEM、Dino、Doom、GitHub、conda、md5、
        FF1–FF6／E1–E4／BJ1–BJ5／X1–X4 這類「兩個字母＋數字」；要拆或改寫的在 video_slides.py 的 SAY_FIX 表裡
        （旁白稿寫原名，送進 TTS 前照表換成唸得對的寫法；字幕與 video_check 用的都還是原名）。
   每一段旁白各自補 PAD 秒靜音再串起來（不是整段串完補一次），否則每張投影片聲音提前 PAD 秒、一路累積。
"""
import io, os, re, json, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from video_slides import SLIDES, COURSE, SAY_FIX          # noqa: E402

ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "_video")      # 中間檔，不進 repo（.gitignore）
OUT = os.path.join(ROOT, "assets")
VOICE, RATE, PAD = "zh-TW-HsiaoChenNeural", "-8%", 0.6
REF_WAV = os.path.join(ROOT, "_voice", "ref.wav")
REF_TXT = os.path.join(ROOT, "_voice", "ref.txt")
LOCAL = os.path.exists(REF_WAV) and os.path.exists(REF_TXT)
BASE = COURSE["out"]

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1920px;height:1080px;background:#fbfcfd;font:400 17px/1.7 "Noto Sans CJK TC","Noto Sans TC",sans-serif;color:#1b2733;overflow:hidden}
.bar{height:10px;background:linear-gradient(90deg,#2563eb 0%,#7c3aed 55%,#d97706 100%)}
.wrap{padding:56px 84px 0;height:1070px;display:flex;flex-direction:column}
.eyebrow{color:#2563eb;font-weight:700;font-size:24px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px}
h1{font-size:58px;line-height:1.28;font-weight:700;letter-spacing:-.01em}
h1 b{color:#2563eb}
.body{display:flex;gap:60px;margin-top:40px;flex:1;min-height:0}
.col{flex:1;min-width:0}
ul{list-style:none}
li{position:relative;padding-left:40px;margin-bottom:26px;font-size:31px;line-height:1.62;color:#2b3a48}
li:before{content:"";position:absolute;left:0;top:18px;width:20px;height:5px;border-radius:3px;background:#2563eb}
li b{color:#0f1b26;font-weight:700}
.fig{flex:0 0 720px;display:flex;flex-direction:column;justify-content:center}
.fig img{width:100%;max-height:700px;object-fit:contain;border:1px solid #e4e8ee;border-radius:14px;background:#fff}
.cap{font-size:19px;color:#7a8794;margin-top:14px;line-height:1.6}
.full li{font-size:34px}
.foot{display:flex;justify-content:space-between;align-items:center;padding:22px 0 26px;color:#9aa7b4;font-size:19px;border-top:1px solid #e8ecf1;margin-top:auto}
.pg{font-variant-numeric:tabular-nums}
"""


def slide_html(s, i, n):
    fig = (f'<div class="fig"><img src="file://{s["img"]}">'
           f'<div class="cap">{s["imgcap"]}</div></div>') if s["img"] else ""
    return (f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
            f'<style>{CSS}</style></head><body><div class="bar"></div><div class="wrap">'
            f'<div class="eyebrow">{s["eyebrow"]}</div><h1>{s["title"]}</h1>'
            f'<div class="body"><div class="{"col" if s["img"] else "col full"}">'
            f'<ul>{"".join(f"<li>{b}</li>" for b in s["bullets"])}</ul></div>{fig}</div>'
            f'<div class="foot"><div>BSC 腦空間體研究中心 · 專題課程 {COURSE["short"]}　｜　{COURSE["url"]}</div>'
            f'<div class="pg">{i + 1} / {n}</div></div></div></body></html>')


# ── 數字轉國字（只在送進本機 TTS 前做一次；稿子、字幕、video_check 都還是阿拉伯數字）──
_D = "零一二三四五六七八九"
_U = ["", "十", "百", "千"]


def _card(n: int) -> str:
    if n == 0:
        return "零"
    if n >= 10 ** 8:
        return "".join(_D[int(c)] for c in str(n))
    out = ""
    for unit, name in ((10 ** 4, "萬"),):
        if n >= unit:
            out += _card(n // unit) + name
            n %= unit
            if n == 0:
                return out
            if n < unit // 10:
                out += "零"
    s4 = str(n)
    for i, c in enumerate(s4):
        d, u = int(c), _U[len(s4) - 1 - i]
        if d == 0:
            if not out.endswith("零") and i != len(s4) - 1:
                out += "零"
        else:
            out += _D[d] + u
    out = out.rstrip("零") or "零"
    return out[1:] if out.startswith("一十") else out


def zh_num(t: str) -> str:
    """阿拉伯數字 → 國字；負號 → 「負」；年份逐字唸。"""
    t = re.sub(r"[−-](?=\s*\d)", "負", t)
    t = re.sub(r"\+(?=\s*\d)", "正", t)      # 「+0.03」直接送會掉字或唸成別的
    t = re.sub(r"(\d{4})\s*年", lambda m: "".join(_D[int(c)] for c in m.group(1)) + "年", t)
    t = re.sub(r"(\d[\d,]*)(?:\.(\d+))?\s*%",
               lambda m: "百分之" + _card(int(m.group(1).replace(",", "")))
               + ("點" + "".join(_D[int(c)] for c in m.group(2)) if m.group(2) else ""), t)
    t = re.sub(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])",
               lambda m: "點".join("".join(_D[int(c)] for c in g) for g in m.groups()), t)
    t = re.sub(r"(?<![\d.])(\d[\d,]*)\.(\d+)(?![\d.])",
               lambda m: _card(int(m.group(1).replace(",", ""))) + "點" + "".join(_D[int(c)] for c in m.group(2)), t)
    t = re.sub(r"(?<![\d.])(\d[\d,]*)(?![\d.])", lambda m: _card(int(m.group(0).replace(",", ""))), t)
    return t


def for_tts(t: str) -> str:
    """送進本機 TTS 前的最後一步：先把唸不對的名字換成唸得對的寫法（SAY_FIX），再把數字轉國字。"""
    for a, b in SAY_FIX:
        t = t.replace(a, b)
    return zh_num(t)


def ts(t):
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"


def main():
    os.makedirs(f"{WORK}/png", exist_ok=True)
    os.makedirs(f"{WORK}/aud", exist_ok=True)
    tts = None
    if LOCAL:
        from f5_tts.api import F5TTS
        tts = F5TTS(model="F5TTS_v1_Base")
    ref_text = io.open(REF_TXT, encoding="utf-8").read().strip() if LOCAL else ""
    print(f"旁白來源：{'本機合成' if LOCAL else 'edge-tts'}")
    durs = []
    for i, s in enumerate(SLIDES):
        p = f"{WORK}/s{i:02d}.html"
        io.open(p, "w", encoding="utf-8").write(slide_html(s, i, len(SLIDES)))
        subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--hide-scrollbars", "--window-size=1920,1080", "--virtual-time-budget=3000",
                        f"--screenshot={WORK}/png/s{i:02d}.png", f"file://{p}"], capture_output=True)
        a = f"{WORK}/aud/a{i:02d}." + ("wav" if LOCAL else "mp3")
        if not os.path.exists(a):
            if LOCAL:
                tts.infer(ref_file=REF_WAV, ref_text=ref_text, gen_text=for_tts(s["say"]), file_wave=a, remove_silence=False)
            else:
                subprocess.run(["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", s["say"], "--write-media", a],
                               capture_output=True, timeout=300)
        durs.append(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a],
                                         capture_output=True, text=True).stdout.strip()))
        print(f"   投影片 {i + 1}/{len(SLIDES)}　旁白 {durs[-1]:.1f} 秒")

    ext = "wav" if LOCAL else "mp3"
    for i in range(len(durs)):      # 每一段各自補 PAD 秒靜音
        subprocess.run(["ffmpeg", "-y", "-i", f"{WORK}/aud/a{i:02d}.{ext}", "-af", f"apad=pad_dur={PAD}",
                        "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", f"{WORK}/aud/p{i:02d}.wav"], capture_output=True)
    with io.open(f"{WORK}/ca.txt", "w") as f:
        for i in range(len(durs)):
            f.write(f"file 'aud/p{i:02d}.wav'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/ca.txt", "-c:a", "aac", "-b:a", "128k",
                    f"{WORK}/voice.m4a"], capture_output=True, cwd=WORK)
    with io.open(f"{WORK}/cv.txt", "w") as f:
        for i, d in enumerate(durs):
            f.write(f"file 'png/s{i:02d}.png'\nduration {d + PAD:.3f}\n")
        f.write(f"file 'png/s{len(durs) - 1:02d}.png'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/cv.txt", "-i", f"{WORK}/voice.m4a",
                    "-c:v", "libopenh264", "-b:v", "900k", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "24",
                    "-c:a", "copy", "-shortest", "-movflags", "+faststart", f"{OUT}/{BASE}.mp4"], capture_output=True, cwd=WORK)

    vtt, t = ["WEBVTT", ""], 0.0
    for s, d in zip(SLIDES, durs):
        sents = [x for x in re.split(r"(?<=[。！？])", s["say"]) if x.strip()]
        tot, cur = sum(len(x) for x in sents), t
        for x in sents:
            dur = d * len(x) / tot
            vtt += [f"{ts(cur)} --> {ts(cur + dur)}", x.strip(), ""]
            cur += dur
        t += d + PAD
    io.open(f"{OUT}/{BASE}.vtt", "w", encoding="utf-8").write("\n".join(vtt))
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  f"{OUT}/{BASE}.mp4"], capture_output=True, text=True).stdout.strip())
    json.dump({"file": f"assets/{BASE}.mp4", "slides": len(SLIDES), "seconds": round(total, 1),
               "mm": int(total // 60), "ss": round(total % 60), "width": 1920, "height": 1080, "resolution": "1080p",
               "fps": 24, "say_chars": sum(len(s["say"]) for s in SLIDES), "pad": PAD,
               "segment_seconds": [round(d, 2) for d in durs],
               "mb": round(os.path.getsize(f"{OUT}/{BASE}.mp4") / 2**20, 1)},
              io.open(os.path.join(ROOT, "out", "video_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from PIL import Image
    Image.open(f"{WORK}/png/s00.png").convert("RGB").save(f"{OUT}/poster.jpg", quality=86, optimize=True)
    print(f"\n完成：{total:.0f} 秒，{os.path.getsize(f'{OUT}/{BASE}.mp4') / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
