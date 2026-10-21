#!/usr/bin/env python3
"""PART 1 第 2 節附註「權重的精確定義」的數字來源：直接讀作者的連線表與子圖檔。

   讀 Shiu 等人的 Connectivity_783.parquet（作者 extract.py 用的同一份）與
   作者切好的 circuit/edges.bin、meta.json，存 out/weight_def.json。
   用法：python3 scripts/weight_def_probe.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

R = Path.home() / "claude_bscai/fly_play_game/fruitfly_lab/repo"
OUT = Path(__file__).resolve().parent.parent / "out/weight_def.json"

con = pd.read_parquet(R / "Drosophila_brain_model/Connectivity_783.parquet",
                      columns=["Presynaptic_ID", "Connectivity", "Excitatory", "Excitatory x Connectivity"])
ratio = con["Excitatory x Connectivity"] / con.Connectivity
# 正負號是不是每顆上游神經元固定一個（Dale 定律）
per_pre = con.groupby("Presynaptic_ID").Excitatory.nunique()
sign = con.drop_duplicates("Presynaptic_ID").set_index("Presynaptic_ID").Excitatory
ann = pd.read_csv(R / "data/flywire_annotations_783.tsv", sep="\t", usecols=["root_id", "top_nt"],
                  low_memory=False).set_index("root_id")
j = ann.join(sign, how="inner")
ct = pd.crosstab(j.top_nt.fillna("NA"), j.Excitatory)

meta = json.loads((R / "circuit/meta.json").read_text())
n, m = meta["n_neurons"], meta["n_edges"]
raw = (R / "circuit/edges.bin").read_bytes()
o = 4 * (n + 1)
offsets = np.frombuffer(raw, np.uint32, n + 1, 0).astype(np.int64)
post = np.frombuffer(raw, np.uint16, m, o).astype(np.int64)
w = np.frombuffer(raw, np.int16, m, o + 2 * m).astype(np.int64)
pre = np.repeat(np.arange(n), np.diff(offsets))
g = meta["groups"]
ex = {}
for a, b in [("LC10a_L", "AOTU019_L"), ("LC10a_R", "AOTU019_R")]:
    msk = np.isin(pre, g[a]) & np.isin(post, g[b])
    s = int(w[msk].sum())
    ex[f"{a}->{b}"] = {"edges": int(msk.sum()), "signed_synapses": s,
                       "w_mv": round(s * meta["w_syn_mv"], 3)}

res = {
    "_note": "權重定義的實測（作者 extract.py 第 109 行、lif.py 第 33 行；Shiu 等人 model.py 第 183 行 syn.w = Excitatory x Connectivity × w_syn）",
    "shiu_table": {"rows": len(con), "connectivity_min": int(con.Connectivity.min()),
                   "connectivity_max": int(con.Connectivity.max()),
                   "excitatory_values": sorted(int(v) for v in con.Excitatory.unique()),
                   "product_equals_sign_times_count": bool((ratio.abs() == 1).all()),
                   "presyn_neurons": int(len(per_pre)),
                   "presyn_with_one_sign": int((per_pre == 1).sum())},
    "sign_vs_flywire_top_nt": {nt: {"minus": int(r.get(-1, 0)), "plus": int(r.get(1, 0)),
                                   "total": int(r.get(-1, 0) + r.get(1, 0))} for nt, r in ct.iterrows()},
    "subgraph": {"n": n, "m": m, "w_syn_mv": meta["w_syn_mv"],
                 "signed_synapses_min": int(w.min()), "signed_synapses_max": int(w.max()),
                 "abs_min": int(np.abs(w).min()), "negative_edges": int((w < 0).sum()),
                 "clipped_int16": int((np.abs(w) >= 32767).sum()),
                 "w_mv_min": round(float(w.min()) * meta["w_syn_mv"], 3),
                 "w_mv_max": round(float(w.max()) * meta["w_syn_mv"], 3),
                 "w_mv_min_abs": round(float(-w.min()) * meta["w_syn_mv"], 3)},
    "group_sum_examples": ex,
}
# 論文原文另外手存在 shiu2024_methods（重跑時保留）
if OUT.exists():
    res["shiu2024_methods"] = json.loads(OUT.read_text()).get("shiu2024_methods")
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False, indent=1))
