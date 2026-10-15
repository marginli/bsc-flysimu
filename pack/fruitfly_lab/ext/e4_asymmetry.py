"""E4：右眼刺激時子圖 DNa02_R 只有約 4 Hz、全腦約 60 Hz，找出子圖少掉的輸入。
做法：讀 FF3 全腦 Brian2 的放電結果（Drosophila_brain_model/results/validate/LC10a_{L,R}.parquet），
對 DNa02_L / DNa02_R 的每個突觸前神經元算「全腦放電率 × 帶正負號的突觸數」= 驅動量，
分成在子圖內／不在子圖內，列出不在子圖內、驅動最大的神經元與其細胞型態、以及它們沒被選進子圖的原因。
在 repo/ 目錄下以 ffl_brian 環境執行。"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent / "repo"
OUT = ROOT.parent / "results" / "E4_asymmetry.json"
meta = json.loads((ROOT / "circuit/meta.json").read_text())
sub_ids = {int(n["id"]) for n in meta["neurons"]}
groups = {k: [int(meta["neurons"][i]["id"]) for i in v] for k, v in meta["groups"].items()}
ann = pd.read_csv(ROOT / "data/flywire_annotations_783.tsv", sep="\t", low_memory=False,
                  usecols=["root_id", "cell_type", "hemibrain_type", "side"]).set_index("root_id")
con = pd.read_parquet(ROOT / "Drosophila_brain_model/Connectivity_783.parquet",
                      columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory x Connectivity"])
THR = 5
strong = con[con.Connectivity >= THR]
lc = {s: set(groups[f"LC10a_{s}"]) for s in "LR"}


def name(i):
    if i not in ann.index:
        return "?"
    r = ann.loc[i]
    t = r.cell_type if isinstance(r.cell_type, str) else (r.hemibrain_type if isinstance(r.hemibrain_type, str) else "unknown")
    return f"{t}_{r.side[0].upper() if isinstance(r.side, str) else 'C'}"


def hops_from_lc(i, side, depth=4):
    """在 ≥THR 的強連結上，從該側 LC10a 走到 i 最少要幾步（>depth 回傳 None）。"""
    seen, front = set(lc[side]), set(lc[side])
    for d in range(1, depth + 1):
        front = set(strong.Postsynaptic_ID[strong.Presynaptic_ID.isin(front)]) - seen
        if i in front:
            return d
        seen |= front
    return None


def rates(stim):
    df = pd.read_parquet(ROOT / f"Drosophila_brain_model/results/validate/{stim}.parquet")
    n_run, t_run = df.trial.nunique() if "trial" in df else 5, 1.0
    return (df.groupby("flywire_id").size() / (5 * t_run)).to_dict()


res = {}
for stim in ["LC10a_L", "LC10a_R"]:
    r = rates(stim)
    side = stim[-1]
    res[stim] = {}
    for dn in ["DNa02_L", "DNa02_R"]:
        tgt = groups[dn][0]
        inp = con[con.Postsynaptic_ID == tgt].copy()
        inp["rate"] = inp.Presynaptic_ID.map(r).fillna(0.0)
        inp["drive"] = inp.rate * inp["Excitatory x Connectivity"]
        inp["in_sub"] = inp.Presynaptic_ID.isin(sub_ids)
        tot = inp.groupby("in_sub").drive.sum().to_dict()
        miss = inp[~inp.in_sub & (inp.drive != 0)].sort_values("drive", key=np.abs, ascending=False).head(12)
        rows = []
        for i, (_, m) in zip(miss.Presynaptic_ID.tolist(), miss.iterrows()):   # ID 取自整數欄，iterrows 會轉成 float 失去精度
            rows.append(dict(id=str(i), type=name(i), syn=int(m["Excitatory x Connectivity"]), rate_hz=round(m.rate, 1),
                             drive=round(m.drive, 1), weak_edge_to_dn=bool(m.Connectivity < THR),
                             strong_hops_from_lc=hops_from_lc(i, side)))
        res[stim][dn] = dict(rate_full=round(r.get(tgt, 0.0), 1),
                             drive_in_subgraph=round(tot.get(True, 0.0), 1), drive_outside=round(tot.get(False, 0.0), 1),
                             top_missing=rows)
        print(stim, dn, res[stim][dn]["rate_full"], "in", res[stim][dn]["drive_in_subgraph"],
              "out", res[stim][dn]["drive_outside"], flush=True)
        for x in rows[:6]:
            print("   ", x)
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("wrote", OUT)

# ---------- 第二步：DNa02 的輸入幾乎都來自子圖內，所以比較子圖內各突觸前神經元在「子圖模擬」與「全腦模擬」的放電率
import sys
sys.path.insert(0, str(ROOT / "flycircuit"))
from lif import LIF, Circuit
circ = Circuit()
ids = np.array([int(n["id"]) for n in circ.meta["neurons"]])
step2 = {}
for stim in ["LC10a_L", "LC10a_R"]:
    rr = np.zeros(circ.n); rates_in = np.zeros(circ.n); rates_in[circ.groups[stim]] = 100.0
    for k in range(5):
        rr += LIF(circ, seed=k).run(10_000, rates_in) / 5.0           # 每秒放電次數
    sub_rate = dict(zip(ids.tolist(), rr.tolist()))
    full = rates(stim)
    dn = "DNa02_" + stim[-1]
    tgt = groups[dn][0]
    inp = con[(con.Postsynaptic_ID == tgt) & con.Presynaptic_ID.isin(sub_ids)].copy()
    inp["full_hz"] = inp.Presynaptic_ID.map(full).fillna(0.0)
    inp["sub_hz"] = inp.Presynaptic_ID.map(sub_rate).fillna(0.0)
    inp["d_drive"] = (inp.full_hz - inp.sub_hz) * inp["Excitatory x Connectivity"]
    top = inp.sort_values("d_drive", key=np.abs, ascending=False).head(10)
    rows = []
    for i, (_, m) in zip(top.Presynaptic_ID.tolist(), top.iterrows()):
        # 這顆神經元在全腦中來自子圖外的輸入（全腦放電率 × 帶號突觸數）
        up = con[con.Postsynaptic_ID == i].copy(); up["hz"] = up.Presynaptic_ID.map(full).fillna(0.0)
        up["drive"] = up.hz * up["Excitatory x Connectivity"]; up["in_sub"] = up.Presynaptic_ID.isin(sub_ids)
        outside = up[~up.in_sub].sort_values("drive", key=np.abs, ascending=False).head(3)
        rows.append(dict(id=str(i), type=name(i), syn=int(m["Excitatory x Connectivity"]), full_hz=round(m.full_hz, 1),
                         sub_hz=round(m.sub_hz, 1), d_drive=round(m.d_drive, 1),
                         its_drive_in_sub=round(float(up[up.in_sub].drive.sum()), 1),
                         its_drive_outside=round(float(up[~up.in_sub].drive.sum()), 1),
                         its_top_outside=[f"{name(j)} {o.hz:.0f}Hz×{int(o['Excitatory x Connectivity'])}" for j, (_, o) in zip(outside.Presynaptic_ID.tolist(), outside.iterrows())]))
    step2[stim] = dict(dn=dn, dn_sub_hz=round(sub_rate[tgt], 1), dn_full_hz=round(full.get(tgt, 0.0), 1),
                       sum_d_drive=round(float(inp.d_drive.sum()), 1), top=rows)
    print("\nSTEP2", stim, dn, "sub", step2[stim]["dn_sub_hz"], "full", step2[stim]["dn_full_hz"], "Σ(full−sub) drive", step2[stim]["sum_d_drive"])
    for x in rows[:8]:
        print("   ", x)
res["step2_sub_vs_full"] = step2
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("wrote", OUT)

# ---------- 第三步：子圖內哪些神經元在全腦裡收到最多「子圖外」的輸入（真正被切掉的驅動）
step3 = {}
for stim in ["LC10a_L", "LC10a_R"]:
    full = rates(stim)
    rr = np.zeros(circ.n); rates_in = np.zeros(circ.n); rates_in[circ.groups[stim]] = 100.0
    for k in range(5):
        rr += LIF(circ, seed=k).run(10_000, rates_in) / 5.0
    sub_rate = dict(zip(ids.tolist(), rr.tolist()))
    e = con[con.Postsynaptic_ID.isin(sub_ids) & ~con.Presynaptic_ID.isin(sub_ids)].copy()
    e["drive"] = e.Presynaptic_ID.map(full).fillna(0.0) * e["Excitatory x Connectivity"]
    per = e.groupby("Postsynaptic_ID").drive.sum().sort_values(key=np.abs, ascending=False)
    rows = []
    for i, d in per.head(12).items():
        src = e[e.Postsynaptic_ID == i].sort_values("drive", key=np.abs, ascending=False).head(3)
        rows.append(dict(id=str(i), type=name(int(i)), outside_drive=round(float(d), 1),
                         full_hz=round(full.get(int(i), 0.0), 1), sub_hz=round(sub_rate.get(int(i), 0.0), 1),
                         from_=[f"{name(j)} {r:.0f}Hz×{int(w)}" for j, r, w in
                                zip(src.Presynaptic_ID.tolist(), src.Presynaptic_ID.map(full).fillna(0).tolist(), src["Excitatory x Connectivity"].tolist())]))
    step3[stim] = dict(total_outside_drive=round(float(per.sum()), 1), top=rows)
    print("\nSTEP3", stim, "total outside drive into subgraph", step3[stim]["total_outside_drive"])
    for x in rows[:10]:
        print("   ", x)
res["step3_outside_drive"] = step3
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("wrote", OUT)
