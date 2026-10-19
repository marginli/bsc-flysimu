#!/usr/bin/env python3
"""從 out/demo_data.json（PART 5 的逐格紀錄）算 PART 5 內文引用的幾個彙總數字，寫成 out/demo_stats.json，
讓 number_audit 對得到。只做加總與平均，不做任何模型計算。
  lc10a_mean_hz[cond]：該局有敵人的每一格，取左右 LC10a 較大者，再平均
  steer[cond][frame]：該格的轉向訊號 (DNa02_R − DNa02_L) + (AOTU019_R − AOTU019_L) 與四個分量
用法：python3 scripts/demo_stats.py
"""
import json, os, statistics
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(D, "out/demo_data.json")))["episodes"]
out = {"lc10a_mean_hz": {}, "steer": {}}
for cond, e in d.items():
    idx = [i for i in range(e["n"]) if e["e"][i]]
    out["lc10a_mean_hz"][cond] = round(statistics.mean(max(e["LC10a_L"][i], e["LC10a_R"][i]) for i in idx), 1)
for cond, frames in {"scrambled_cal": [49], "fly": [146, 148, 149]}.items():
    e = d[cond]; out["steer"][cond] = {}
    for i in frames:
        comp = {k: e[k][i] for k in ("DNa02_R", "DNa02_L", "AOTU019_R", "AOTU019_L")}
        out["steer"][cond][str(i)] = {**comp, "steer": round((comp["DNa02_R"] - comp["DNa02_L"]) + (comp["AOTU019_R"] - comp["AOTU019_L"]), 1), "action": e["a"][i]}
json.dump(out, open(os.path.join(D, "out/demo_stats.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False, indent=1))
