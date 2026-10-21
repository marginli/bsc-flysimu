"""PART 1 第 4 節〈讀出規則〉示意圖（圖 5）的資料：讀出規則的常數、校準表 17 個方位，與 PART 5 那一局（fly）的逐格紀錄。
常數從作者 fly_doom.py 抓（逐字確認讀出那幾行還是這樣寫）；閾值讀 calibration_fly.json；逐格紀錄讀 out/demo_data.json。
另外用讀出規則把逐格紀錄的放電率重算一遍，確認每一格按的鍵都和紀錄相同，圖上才能說「照規則算出來的就是當時按的」。
用法：python3 scripts/readout_fig_data.py   （輸出 out/readout_fig.json）"""
import json
import math
import os
import re
from collections import Counter

REPO = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(REPO, "doom/fly_doom.py"), encoding="utf-8").read()
for s in ['return (r["DNa02_R"] - r["DNa02_L"]) + (r["AOTU019_R"] - r["AOTU019_L"])',
          'left, right = int(s < -cal["turn_th"]), int(s > cal["turn_th"])',
          'fire = int(min(r["AOTU019_L"], r["AOTU019_R"]) > cal["fire_th"])',
          'if not targets and sum(r.values()) < cal["quiet_th"]:', "left, right = 0, 1",
          "self.alpha = np.exp(-(1 / 35) / TAU_S)",
          "self.rate[k] = self.alpha * self.rate[k] + (1 - self.alpha) * float(hz[ids].mean())",
          "hz = cnt / (STEPS_PER_TIC * DT)"]:
    assert s in src, s
TAU_S = float(re.search(r"^TAU_S = ([\d.]+)", src, re.M).group(1))
STEPS = round(1 / 35 / 1e-4)
ALPHA = math.exp(-(1 / 35) / TAU_S)
P = ["LC10a_L", "LC10a_R", "AOTU019_L", "AOTU019_R", "AOTU025_L", "AOTU025_R", "DNa02_L", "DNa02_R"]

calf = json.load(open(os.path.join(D, "out/fruitfly/local_doom_vizdoom130/calibration_fly.json")))
cal, rows = calf["cal"], calf["rows"]
ep = json.load(open(os.path.join(D, "out/demo_data.json")))["episodes"]["fly"]
n = ep["n"]


def readout(r, has_enemy):
    s = (r["DNa02_R"] - r["DNa02_L"]) + (r["AOTU019_R"] - r["AOTU019_L"])
    left, right = int(s < -cal["turn_th"]), int(s > cal["turn_th"])
    fire = int(min(r["AOTU019_L"], r["AOTU019_R"]) > cal["fire_th"])
    quiet = (not has_enemy) and sum(r.values()) < cal["quiet_th"]
    if quiet:
        left, right = 0, 1
    return f"{left}{right}{fire}", s, quiet


mism, quiet_tics, steer = [], [], []
for i in range(n):
    r = {k: ep[k][i] for k in P}
    a, s, q = readout(r, bool(ep["e"][i]))
    steer.append(round(s, 1))
    if q:
        quiet_tics.append(i)
    if a != ep["a"][i]:
        mism.append(i)
assert not mism, mism

# 第 ⑥ 步的片段：第一次「沒有敵人而且安靜」之前，敵人剛消失、迴路還有活動的那幾格
q0 = quiet_tics[0]
gone = max(i for i in range(q0) if ep["e"][i]) + 1           # 敵人消失的第一格
seg6 = [gone - 3, q0 + 4]
# 第 ① 步的片段：開局，放電率從 0 經平滑慢慢升上去
seg1 = [0, 24]
# 由平滑後的值反推「這一格單算」的放電率：hz = (r_t − α r_{t−1}) ÷ (1 − α)（紀錄取到 0.1，反推約有 ±0.4 的誤差）
raw = {k: [round(max(0.0, (ep[k][i] - ALPHA * (ep[k][i - 1] if i else 0.0)) / (1 - ALPHA)), 1) for i in range(n)] for k in P}

sizes = json.load(open(os.path.join(D, "out/demo_data.json")))["circuit"]["sizes"]
act = Counter(ep["a"])
out = {
    "_note": "PART 1 第 4 節圖 5（讀出規則）的資料；scripts/readout_fig_data.py 產生",
    "const": {"tau_s": TAU_S, "steps_per_tic": STEPS, "tic_ms": round(1000 / 35, 1), "alpha": round(ALPHA, 4),
              "alpha_2dp": round(ALPHA, 2), "one_minus_alpha_2dp": round(1 - ALPHA, 2), "tics_per_s": 35,
              "hz_per_spike": round(35.0, 2), "tau_s_ms": TAU_S * 1000},
    "sizes": {k: sizes[k] for k in P},
    "cal": {k: cal[k] for k in ("turn_th", "fire_th", "quiet_th")},
    "cal_rule": {"s0": abs(next(r for r in rows if r["az"] == 0)["steer"]),
                 "s_off": min(abs(next(r for r in rows if r["az"] == a)["steer"]) for a in (-10, 10)),
                 "aotu019_min_at_0": min(next(r for r in rows if r["az"] == 0)[k] for k in ("AOTU019_L", "AOTU019_R"))},
    "rows": rows,
    "fire_az": [r["az"] for r in rows if min(r["AOTU019_L"], r["AOTU019_R"]) > cal["fire_th"]],
    "turn_az": [r["az"] for r in rows if abs(r["steer"]) > cal["turn_th"]],
    "episode": {"n": n, "kills": ep["kills"], "seconds": round(n / 35, 1), "mismatch": len(mism),
                "actions": {k: act.get(k, 0) for k in ("000", "010", "100", "001", "011", "101")},
                "no_enemy_tics": sum(1 for e in ep["e"] if not e), "quiet_tics": len(quiet_tics),
                "seg1": seg1, "seg6": seg6, "gone_tic": gone, "first_quiet_tic": q0,
                "sum_at_gone": round(sum(ep[k][gone] for k in P), 1), "sum_at_q0": round(sum(ep[k][q0] for k in P), 1),
                "sum_before_q0": round(sum(ep[k][q0 - 1] for k in P), 1), "search_delay_tics": q0 - gone,
                "search_delay_ms": round((q0 - gone) * 1000 / 35)},
    "trace": {"e": ep["e"], "a": ep["a"], "k": ep["k"], "steer": steer, **{k: ep[k] for k in P}},
    "raw": raw,
}
json.dump(out, open(os.path.join(D, "out/readout_fig.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps({k: v for k, v in out.items() if k not in ("trace", "raw", "rows")}, ensure_ascii=False, indent=1))
