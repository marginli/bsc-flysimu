"""BJ5b：作者附的 30,000 手大腦（data/brain_seed.json，標記為 python 30k-hand session, seed 0）
載入 Python 模型後重新評分，與作者自述（stand 約 227、double 0/39、一致率 53.1%）及本機 BJ5 比較。
gain 只存 18,183 條 KC→MBON 連結，順序依 site/mb.json 的 w_kc_mbon (r, c)。在 repo/ 下以 PYTHONPATH=. 執行。"""
import json, base64
import numpy as np
from flybrain.mb.blackjack import FlyPlayer, chart_cells, basic_strategy, HIT, STAND, DOUBLE

b = json.load(open("data/brain_seed.json"))
w = json.load(open("site/mb.json"))["w_kc_mbon"]
g = np.frombuffer(base64.b64decode(b["gain"]), np.uint8) / 255.0
fly = FlyPlayer(seed=0)
assert fly.mb.gain.shape == tuple(w["shape"]) and len(g) == b["n"] == len(w["r"])
# 先確認 site/mb.json 的連結位置與本機切出的電路相同
raw = fly.mb.W_kc_mbon_raw
same_edges = bool(np.all(raw[w["r"], w["c"]] > 0) and (raw > 0).sum() == len(w["r"]))
gain = np.ones_like(fly.mb.gain); gain[w["r"], w["c"]] = g
fly.mb.gain = gain
out = dict(stored_agreement=b["agreement"], stored_units_per_hand=b["units"] / b["hands"], same_edges=same_edges,
           python_agreement=fly.agreement())
c = {HIT: 0, STAND: 0, DOUBLE: 0}
for (t, s, u) in chart_cells():
    c[fly.greedy(t, s, u, True, [HIT, STAND, DOUBLE])] += 1
out["spots"] = {"hit": c[HIT], "stand": c[STAND], "double": c[DOUBLE]}
for a, nm in [(HIT, "hit"), (STAND, "stand"), (DOUBLE, "double")]:
    cells = [(t, s, u) for (t, s, u) in chart_cells() if basic_strategy(t, s, u, True) == a]
    out["spots"][f"chart_{nm}_matched"] = f"{sum(fly.greedy(t, s, u, True, [HIT, STAND, DOUBLE]) == a for (t, s, u) in cells)}/{len(cells)}"
print(json.dumps(out, indent=1))
json.dump(out, open("../results/bj5b_author_brain.json", "w"), indent=1)
