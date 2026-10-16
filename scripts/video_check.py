#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查說明影片的旁白有沒有講到投影片上寫的每一點（沿用 VFB）。

   投影片是給眼睛看的摘要，旁白是給耳朵聽的完整句子；上面寫了、下面沒講，觀眾一定抓得到。
   查兩件事：
     1. 要點裡的每一個數字，旁白有沒有出現（旁白一律寫阿拉伯數字，所以能精確比對）
     2. 要點裡用 <b> 標出來的英數專有名詞，旁白有沒有出現
   旁白稿寫的是原名（DNa02、MBON…），唸法的替換在 make_video.py 送 TTS 前才做，所以這裡直接比。
   用法：python3 scripts/video_check.py
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video_slides import SLIDES                      # noqa: E402


def plain(t):
    return re.sub(r"[\s，。、：；！？「」（）《》%．·—…]", "", re.sub(r"<[^>]+>", "", t))


def main():
    total = miss = 0
    for i, s in enumerate(SLIDES, 1):
        say, bad_n, bad_w = plain(s["say"]), [], []
        for b in s["bullets"]:
            for num in re.findall(r"\d[\d,]*(?:\.\d+)?%?", re.sub(r"<[^>]+>", "", b)):
                total += 1
                if num.replace(",", "") not in s["say"].replace(",", "").replace(" ", ""):
                    bad_n.append(num)
            for w in re.findall(r"<b>(.*?)</b>", b):
                w = plain(w)
                if re.fullmatch(r"[A-Za-z0-9_\-\.％%]{3,}", w) and w not in say:
                    bad_w.append(w)
        if bad_n or bad_w:
            miss += len(bad_n) + len(bad_w)
            print(f"投影片 {i:>2}　{plain(s['title'])[:24]}")
            if bad_n:
                print(f"     旁白沒講的數字：{'、'.join(sorted(set(bad_n)))}")
            if bad_w:
                print(f"     旁白沒講的名詞：{'、'.join(sorted(set(bad_w)))}")
    chars = sum(len(s["say"]) for s in SLIDES)
    print(f"\n{len(SLIDES)} 張投影片，要點裡 {total} 個數字，漏講 {miss} 項；旁白共 {chars:,} 字"
          f"（以 4.4 字/秒估約 {chars / 4.4 / 60:.1f} 分鐘）")
    return miss


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
