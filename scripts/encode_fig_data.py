"""PART 1 第 4 節〈輸入編碼〉示意圖（圖 3）的資料：作者 fly_doom.py 裡輸入編碼用到的常數，與 234 顆 LC10a 的偏好位置。
常數從作者原始碼直接抓（抓不到就報錯），所以作者改了數字這裡會跟著變；偏好位置 ＝ 1 − central（meta.json，作者 extract.py 算的占比）。
另外算三個示範敵人的結果，頁面文字裡的數字對這裡。
需要作者 repo（~/claude_bscai/fly_play_game/fruitfly_lab/repo）與 ViZDoom 1.3.0 環境的 defend_the_center.cfg。
用法：python3 scripts/encode_fig_data.py   （輸出 out/encode_fig.json）"""
import glob
import json
import math
import os
import re
import sys

import numpy as np

REPO = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(REPO, "doom/fly_doom.py"), encoding="utf-8").read()


def const(name):
    return float(re.search(rf"^{name} = ([\d.]+)", src, re.M).group(1))


# enemies() 裡的寫死數字：逐字確認原始碼還是這樣寫
for s in ["lb.height < 4", "lb.width > lb.height * 1.3", "az = (cx - 160) / 160 * HALF_FOV_DOOM * FLY_SCALE",
          "min(1.0, 0.35 + lb.height / 60)", "ecc = min(abs(az) / 90.0, 1.0)",
          "sides = [\"L\", \"R\"] if abs(az) < BINO", "tune = np.exp(-((self.pref_ecc[ids] - ecc) ** 2) / (2 * SIGMA ** 2))",
          "rates[ids] = np.minimum(MAX_RATE, rates[ids] + MAX_RATE * strength * tune)", "DT = 1e-4"]:
    assert s in src, s
cfg = glob.glob(os.path.expanduser("~/anaconda3/envs/ffl_doom130/lib/python3.12/site-packages/vizdoom/scenarios/defend_the_center.cfg"))[0]
w, h = map(int, re.search(r"screen_resolution = RES_(\d+)X(\d+)", open(cfg).read()).groups())

C = {k: const(k) for k in ("HALF_FOV_DOOM", "FLY_SCALE", "BINO", "MAX_RATE", "SIGMA")}
C.update(screen_w=w, screen_h=h, screen_center=w // 2, min_height=4, corpse_ratio=1.3, strength_base=0.35, strength_div=60, dt_ms=0.1)
assert C["screen_center"] == 160

meta = json.load(open(os.path.join(REPO, "circuit/meta.json")))
sys.path.insert(0, os.path.join(REPO, "flycircuit"))
os.chdir(REPO)
from lif import Circuit  # noqa: E402
c = Circuit()
pre = np.repeat(np.arange(c.n), np.diff(c.offsets))
no_aotu = {}   # 同側 AOTU019、AOTU025 一條連結都沒有的 LC10a：extract.py 給它預設 central ＝ 0.5
for s in "LR":
    tgt = np.concatenate([c.groups[f"AOTU019_{s}"], c.groups[f"AOTU025_{s}"]])
    no_aotu[s] = int(sum(not np.isin(c.post[pre == i], tgt).any() for i in c.groups[f"LC10a_{s}"]))
pref = {s: [round(1 - meta["neurons"][i].get("central", 0.5), 3) for i in meta["groups"][f"LC10a_{s}"]] for s in "LR"}


def encode(cx, height):
    az = max(-90, min(90, (cx - 160) / 160 * C["HALF_FOV_DOOM"] * C["FLY_SCALE"]))
    st = min(1.0, C["strength_base"] + height / C["strength_div"])
    ecc = min(abs(az) / 90, 1)
    sides = ["L", "R"] if abs(az) < C["BINO"] else (["R"] if az > 0 else ["L"])
    rates = {s: [C["MAX_RATE"] * st * math.exp(-(p - ecc) ** 2 / (2 * C["SIGMA"] ** 2)) if s in sides else 0 for p in pref[s]] for s in "LR"}
    allr = rates["L"] + rates["R"]
    return {"cx": cx, "height": height, "az": round(az, 2), "ecc": round(ecc, 3), "strength": round(st, 3), "sides": sides,
            "max_hz": round(max(allr), 1), "n_over_half": sum(r > C["MAX_RATE"] * st / 2 for r in allr),
            "total_hz": round(sum(allr)), "p_max_per_step": round(max(allr) * C["dt_ms"] / 1000, 4)}


res = {"const": C, "pref_ecc": pref,
       "pref_summary": {s: {"n": len(v), "min": min(v), "max": max(v), "no_aotu": no_aotu[s], "at_0": v.count(0.0), "at_1": v.count(1.0)} for s, v in pref.items()},
       "no_aotu_total": sum(no_aotu.values()),
       "height_full": round((1 - C["strength_base"]) * C["strength_div"]),   # 高這麼多像素以上強度就是 1
       "display": {"slow": 20, "frame_ms": 50, "model_ms_per_frame": 2.5},   # 圖 3 隨機放電放慢播放的倍數
       "tune_table": {f"{d:g}": round(math.exp(-d ** 2 / (2 * C["SIGMA"] ** 2)), 3) for d in (0, 0.3, 0.5, 0.9)},   # 差 → 接近程度
       "examples": [encode(240, 20), encode(240, 45), encode(165, 30)]}
json.dump(res, open(os.path.join(D, "out/encode_fig.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k != "pref_ecc"}, indent=1, ensure_ascii=False))
