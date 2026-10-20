"""PART 1 第 3 節的細胞體位置圖（圖 2）：切出來的 3,963 顆神經元的細胞體在腦裡的位置，
底圖是 FlyWire 標註表裡全部有細胞體座標的神經元（果蠅的細胞體都在腦表面，點一多腦的輪廓就出來）。
只畫細胞體，不畫神經元的形狀：本機只有標註表（細胞體座標）與連結表，沒有骨架。
需要作者 repo（~/claude_bscai/fly_play_game/fruitfly_lab/repo）：data/flywire_annotations_783.tsv（Schlegel 等人 2024 的標註，
作者的 extract.py 也是從這裡拿座標）與 circuit/meta.json（切出來的 3,963 顆，座標已換成 μm）。
用法：python3 scripts/make_soma_fig.py   （寫 assets/p1-soma-front.png、assets/p1-soma-top.png、out/soma_fig.json）

座標軸（用已知方位的細胞群算出來，數字存進 json 的 axis_check；FlyWire 體素 4×4×40 nm 換成 μm）：
  x 往果蠅的右側增加（side=left 平均 x 318、right 731）；y 往腹側增加（KC 在背側 132、下行神經元 287）；
  z 往後側增加（觸角葉投射神經元 49、KC 193、T4/T5 244）。
  A 前視：站在果蠅正前方看，背側朝上，果蠅的左邊在圖的右邊（x 反轉、y 反轉）。
  B 上視：從背側往下看，前側朝上，果蠅的左邊在圖的左邊（x 照原、z 反轉）。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(D, "assets")
OUT = os.path.join(D, "out/soma_fig.json")
REPO = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
SPAN = 400                      # 兩個面板縱向都畫 400 μm（腦高約 350、前後厚約 300），PNG 同尺寸、圖說才對得齊

ann = pd.read_csv(os.path.join(REPO, "data/flywire_annotations_783.tsv"), sep="\t", low_memory=False,
                  usecols=["root_id", "soma_x", "soma_y", "soma_z", "cell_class", "cell_type", "super_class", "side"])
has = ann.soma_x.notna() & ann.soma_y.notna() & ann.soma_z.notna()
B = np.stack([ann.soma_x[has] * 4e-3, ann.soma_y[has] * 4e-3, ann.soma_z[has] * 40e-3], axis=1)   # 底圖：有細胞體座標的全部
meta = json.load(open(os.path.join(REPO, "circuit/meta.json")))
N = meta["neurons"]
P = np.array([[n["x"], n["y"], n["z"]] for n in N])
soma_ids = set(ann.root_id[has].astype(str))
no_soma = [n["type"] for n in N if n["id"] not in soma_ids]     # 座標是作者用 pos 補的（標註表沒有細胞體座標）

def sel(t):
    return np.array([i for i, n in enumerate(N) if n["type"] == t])

groups = [  # (名字, index, 顏色, 點大小, 圖例)
    ("other", np.array([i for i, n in enumerate(N) if n["type"] not in ("LC10a", "AOTU019", "AOTU025", "DNa02")]), "#6b7280", 3, "other circuit neurons"),
    ("LC10a", sel("LC10a"), "#2563eb", 6, "LC10a"),
    ("AOTU025", sel("AOTU025"), "#16a34a", 40, "AOTU025"),
    ("AOTU019", sel("AOTU019"), "#9333ea", 40, "AOTU019"),
    ("DNa02", sel("DNa02"), "#dc2626", 40, "DNa02"),
]
counts = {name: int(len(idx)) for name, idx, *_ in groups}
counts["LC10a_L"] = len(meta["groups"]["LC10a_L"]); counts["LC10a_R"] = len(meta["groups"]["LC10a_R"])

cc = ann.cell_class.fillna(""); ct = ann.cell_type.fillna(""); sc = ann.super_class.fillna("")
def mean(mask):
    m = (mask & has).to_numpy()
    return np.stack([ann.soma_x[m] * 4e-3, ann.soma_y[m] * 4e-3, ann.soma_z[m] * 40e-3], axis=1).mean(axis=0).round(0).tolist()
axis_check = {"side_left_mean_xyz_um": mean(ann.side == "left"), "side_right_mean_xyz_um": mean(ann.side == "right"),
              "KC_mean_xyz_um": mean(cc == "Kenyon_Cell"), "ALPN_mean_xyz_um": mean(cc == "ALPN"),
              "T4T5_mean_xyz_um": mean(ct.str.match(r"^T4|^T5")), "descending_mean_xyz_um": mean(sc == "descending")}


def panel(fname, ix, iy, flipx, flipy, label):
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    sx = -1 if flipx else 1
    sy = -1 if flipy else 1
    xs = sx * B[:, ix]; ys = sy * B[:, iy]
    ax.scatter(xs, ys, s=0.25, c="#e3e7ec", lw=0, rasterized=True)
    for name, idx, col, sz, leg in groups:
        Q = P[idx]
        ax.scatter(sx * Q[:, ix], sy * Q[:, iy], s=sz, c=col, lw=0.4 if sz >= 40 else 0, edgecolors="#fff" if sz >= 40 else "none",
                   label=f"{leg} ({len(Q):,})", zorder=3 if sz >= 40 else 2)
    ax.set_xlim(xs.min() - 10, xs.max() + 10)
    yc = (ys.min() + ys.max()) / 2
    ax.set_ylim(yc - SPAN / 2, yc + SPAN / 2)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(label, fontsize=11, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3, fontsize=9, markerscale=1.6, frameon=False)
    fig.savefig(os.path.join(A, fname), dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("寫出", fname)


panel("p1-soma-front.png", 0, 1, True, True, "A  front view (viewer in front of the fly, dorsal up; fly's left on the right)")
panel("p1-soma-top.png", 0, 2, False, True, "B  top view (viewer above the fly, anterior up; fly's left on the left)")

no_soma_rows = ~has
model_ids = set(pd.read_csv(os.path.join(REPO, "Drosophila_brain_model/Completeness_783.csv")).iloc[:, 0].astype(int))
ann_ids = set(ann.root_id.astype(int))
res = {"model_neurons": len(model_ids), "annotation_minus_model": int(len(ann_ids) - len(model_ids)), "annotation_not_in_model": len(ann_ids - model_ids), "model_not_in_annotation": len(model_ids - ann_ids),"background_somas_drawn": int(has.sum()), "annotation_rows": int(len(ann)),
       "annotation_without_soma": {"n": int(no_soma_rows.sum()),
                                   "by_super_class": {k: int(v) for k, v in ann.super_class[no_soma_rows].value_counts().head(6).items()}},
       "circuit_neurons": int(len(N)), "counts": counts,
       "circuit_without_soma_coord": {"n": len(no_soma), "types": sorted(set(no_soma))},
       "group_mean_xyz_um": {name: P[idx].mean(axis=0).round(0).tolist() for name, idx, *_ in groups},
       "axis_check": axis_check}
json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k != "axis_check"}, ensure_ascii=False, indent=1))
