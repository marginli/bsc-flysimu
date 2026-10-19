#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""做完影片之後的兩道驗證——做的人聽不到，所以用算的。

   1. 影音同步：每張投影片的交界時間點（由 out/video_meta.json 的 segment_seconds ＋ pad 算出）
      要落在成品音軌 silencedetect 偵測到的靜音段裡。
   2. 辨識回填：把每一段旁白的合成音丟回本機的語音辨識（faster-whisper，CPU），
      與旁白稿比對字元層級的相似度，把低於門檻的段落與差異印出來，給人判斷是唸錯還是辨識錯。
      要用辨識那個環境的 python：~/.venvs/asr/bin/python scripts/video_verify.py
   報告寫到 _video/verify.txt（不進 repo）。
"""
import glob
import difflib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from video_slides import SLIDES, SAY_FIX   # noqa: E402
from make_video import zh_num             # noqa: E402

WORK = os.path.join(ROOT, "_video")
meta = json.load(open(os.path.join(ROOT, "out", "video_meta.json")))
mp4 = os.path.join(ROOT, meta["file"])
out = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.append(s)


# ── 1. 同步 ──
r = subprocess.run(["ffmpeg", "-i", mp4, "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
sil = list(zip(starts, ends))
t, ok, bounds = 0.0, 0, []
for d in meta["segment_seconds"][:-1]:
    t += d + meta["pad"]
    bounds.append(t)
    if any(a - 0.05 <= t <= b + 0.05 for a, b in sil):
        ok += 1
say(f"同步：{len(bounds)} 個投影片交界，{ok} 個落在靜音段裡" + ("" if ok == len(bounds) else "　← 有交界不在靜音裡，要查"))

# ── 2. 辨識回填 ──
from faster_whisper import WhisperModel   # noqa: E402
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=12)
import opencc                            # noqa: E402
_cc = opencc.OpenCC("s2t")


def plain(s):
    return re.sub(r"[\s，。、：；！？「」（）《》,.;:!?\-—…·]", "", s)


low = 0
for i, s in enumerate(SLIDES):
    # 合成音以「編號_旁白雜湊」命名（make_video.py），取同編號最新的那一個
    cands = sorted(glob.glob(f"{WORK}/aud/a{i:02d}_*.wav") + glob.glob(f"{WORK}/aud/a{i:02d}_*.mp3") +
                   glob.glob(f"{WORK}/aud/a{i:02d}.wav") + glob.glob(f"{WORK}/aud/a{i:02d}.mp3"), key=os.path.getmtime)
    a = cands[-1]
    segs, _ = m.transcribe(a, language="zh", beam_size=5, initial_prompt="繁體中文，果蠅神經科學課程。")
    heard = "".join(x.text for x in segs)
    # 辨識常吐簡體字與阿拉伯數字：先轉成繁體（opencc），再把數字轉成國字，才跟稿子同一種寫法
    heard = zh_num(_cc.convert(heard))
    # 比對前把稿子轉成「唸出來的樣子」（數字轉國字、名字照 SAY_FIX 換），否則 138,639 對「十三萬八千六百三十九」會被算成不同
    said = zh_num(s["say"])
    ratio = difflib.SequenceMatcher(None, plain(said), plain(heard)).ratio()
    flag = "" if ratio >= 0.85 else "　← 低"
    low += ratio < 0.85
    say(f"投影片 {i + 1:>2}　相似度 {ratio:.2f}{flag}")
    if ratio < 0.85:
        for tag, x1, x2, y1, y2 in difflib.SequenceMatcher(None, plain(said), plain(heard)).get_opcodes():
            if tag != "equal":
                say(f"      稿「{plain(said)[x1:x2]}」→ 聽「{plain(heard)[y1:y2]}」")
say(f"辨識回填：{len(SLIDES)} 段，{low} 段相似度低於 0.85")
io.open(os.path.join(WORK, "verify.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
