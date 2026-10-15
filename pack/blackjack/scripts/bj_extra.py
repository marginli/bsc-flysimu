"""計畫第 4 節：作者沒做、本輪加做的四項檢查。在 repo/ 目錄下以 PYTHONPATH=. 執行。
不改作者程式碼；需要不同電路時另存 npz 到 ../results/circuits/，再把 experiment 模組裡的
MushroomBody 換成指向該檔的版本。
  X1 種子數：12 → 50，報告平均、SD、95% CI
  X2 洗牌 DAN→MBON（把每顆 DAN 連到的 MBON 欄位隨機置換），10 組置換
  X3 KC 子集：作者用 1,200 顆「依排名等距取樣」；改成 5 組隨機 1,200 顆 + 全部在路徑上的 KC
  X4 MBON 價值：作者依主要多巴胺輸入標 +1/−1；與 Aso 2014 的傳導物質規則
     （麩胺酸 MBON 活化 → 迴避；乙醯膽鹼 / GABA → 趨近）交叉比對
"""
import json, functools
from pathlib import Path
from collections import Counter
import numpy as np
import scipy.sparse as sp

from flybrain.mb import experiment as ex
from flybrain.mb.model import MushroomBody
from flybrain.mb.extract import extract

OUT = Path("../results"); (OUT / "circuits").mkdir(parents=True, exist_ok=True)
res = {}


def stats(v):
    v = np.asarray(v); se = v.std(ddof=1) / np.sqrt(len(v))
    return dict(n=len(v), mean=float(v.mean()), sd=float(v.std(ddof=1)),
                ci95=[float(v.mean() - 1.96 * se), float(v.mean() + 1.96 * se)])


def use_circuit(path=None, post=None):
    """讓 experiment.build() 用指定的 npz，並可在建好後對 model 動手腳（post）。"""
    def make(**kw):
        mb = MushroomBody(path=path or "data/mb_circuit.npz", **kw)
        if post: post(mb, kw.get("seed", 0))
        return mb
    ex.MushroomBody = make


# ---------------- X1
use_circuit()
x1 = {c: ex.pooled(control=c, seeds=50).tolist() for c in ["none", "shuffled"]}
res["X1_50_seeds"] = {c: stats(v) for c, v in x1.items()}
res["X1_50_seeds"]["none_first12"] = stats(x1["none"][:12])
print("X1", json.dumps(res["X1_50_seeds"]), flush=True)

# ---------------- X2
x2 = []
for k in range(10):
    def perm_dan(mb, seed, k=k):
        rng = np.random.default_rng(1000 + k)
        mb.W_dan_mbon = mb.W_dan_mbon[:, rng.permutation(mb.n_mbon)]
    use_circuit(post=perm_dan)
    v = ex.pooled(seeds=12)
    x2.append(stats(v)); print("X2 perm", k, x2[-1]["mean"], flush=True)
res["X2_dan_mbon_shuffled"] = dict(per_permutation=x2, mean_of_means=float(np.mean([s["mean"] for s in x2])))

# ---------------- X3
blocks, info = extract(kenyon=None)          # 全部在路徑上的 KC
n_live = blocks["pn_kc"].shape[1]


def save_npz(path, bl, info):
    arrays = {}
    for name, b in bl.items():
        coo = sp.coo_matrix(b)
        arrays[f"{name}_row"] = coo.row.astype(np.int32); arrays[f"{name}_col"] = coo.col.astype(np.int32)
        arrays[f"{name}_val"] = coo.data.astype(np.float32); arrays[f"{name}_shape"] = np.array(b.shape, np.int32)
    arrays["mbon_valence"] = np.array(info["mbon_valence"], np.int8)
    arrays["dan_is_punishment"] = np.array(info["dan_is_punishment"], np.int8)
    np.savez_compressed(path, **arrays)


x3 = {}
variants = {"all_live_kc": np.arange(n_live)}
for k in range(5):
    variants[f"random1200_{k}"] = np.sort(np.random.default_rng(500 + k).choice(n_live, 1200, replace=False))
for name, idx in variants.items():
    bl = dict(blocks); bl["pn_kc"] = blocks["pn_kc"][:, idx]; bl["kc_mbon"] = blocks["kc_mbon"][idx, :]
    p = OUT / "circuits" / f"mb_{name}.npz"; save_npz(p, bl, info)
    use_circuit(path=str(p))
    x3[name] = dict(n_kc=len(idx), full=stats(ex.pooled(seeds=12)), dopamine_cut=stats(ex.pooled("dopamine-cut", seeds=12)))
    print("X3", name, x3[name]["full"]["mean"], x3[name]["dopamine_cut"]["mean"], flush=True)
res["X3_kc_subsets"] = dict(n_live_kc=int(n_live), variants=x3)

# ---------------- X4
cells = json.loads(Path("data/mb_cells.json").read_text())
types, nts, val = cells["types"]["mbon"], cells["nt"]["mbon"], cells["mbon_valence"]
lit = {"glutamate": -1, "acetylcholine": 1, "gaba": 1}
rows, tab = [], Counter()
for t, nt, v in zip(types, nts, val):
    exp = lit.get(nt.lower())
    tab[(nt, v)] += 1
    rows.append(dict(type=t, nt=nt, author=v, nt_rule=exp, agree=(exp == v) if exp is not None and v != 0 else None))
judged = [r for r in rows if r["agree"] is not None]
res["X4_mbon_valence"] = dict(
    rule="Aso et al. 2014 eLife：麩胺酸 MBON 活化促迴避（−1），乙醯膽鹼／GABA 促趨近（+1）；簡化規則，有已知例外",
    crosstab={f"{nt}|{v:+d}": n for (nt, v), n in sorted(tab.items())},
    judged=len(judged), agree=sum(r["agree"] for r in judged),
    disagree=[r for r in judged if not r["agree"]], cells=rows)
print("X4", res["X4_mbon_valence"]["crosstab"], res["X4_mbon_valence"]["agree"], "/", len(judged), flush=True)

(OUT / "bj_extra.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("wrote ../results/bj_extra.json")
