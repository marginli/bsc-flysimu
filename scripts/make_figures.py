"""產生本專題的真實資料圖，數字全部讀 out/（由 collect_out.py 從實跑產出收來）。
圖內一律英文，說明寫在 HTML 的 figcaption。用法：~/anaconda3/bin/python scripts/make_figures.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(D, "out")
A = os.path.join(D, "assets")
J = lambda p: json.load(open(os.path.join(O, p)))
INK, SOFT, FAINT = "#1b2733", "#5a6b7b", "#c9d1da"
BLUE, AMBER, GREEN, RED = "#2563eb", "#d97706", "#16a34a", "#dc2626"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": SOFT, "axes.labelcolor": INK, "xtick.color": SOFT,
                     "ytick.color": SOFT, "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight"})
meta = {}


def save(fig, name):
    fig.savefig(os.path.join(A, name))
    plt.close(fig)
    print("寫出", name)


def fly_episodes():
    """作者／本機 1.3.0／本機 1.3.2，fly 條件 10 局逐局擊殺數。"""
    src = [("author (ViZDoom 1.3.0)", "fruitfly/author_doom/fly.json", INK, "o", 9),
           ("ours, ViZDoom 1.3.0", "fruitfly/local_doom_vizdoom130/fly.json", BLUE, "x", 9),
           ("ours, ViZDoom 1.3.2", "fruitfly/local_doom_vizdoom132/fly.json", AMBER, "s", 6)]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for lab, f, c, m, ms in src:
        k = [e["kills"] for e in J(f)["episodes"]]
        ax.plot(range(10), k, m + "-", color=c, ms=ms, lw=1.2, label=f"{lab}: mean {np.mean(k):.1f}",
                mfc="none" if m == "o" else c, alpha=.95)
        meta.setdefault("fly_episodes", {})[lab] = k
    ax.set_xticks(range(10)); ax.set_xlabel("episode (seed 0, episodes 0-9)"); ax.set_ylabel("kills")
    ax.legend(frameon=False, fontsize=9.5, ncol=3, loc="lower center", bbox_to_anchor=(.5, 1.0)); ax.set_ylim(0, 19)
    save(fig, "p3-fly-episodes.png")






def n50():
    e = J("fruitfly/ext_vizdoom1.3.0/E1.json")
    order = [("fly", "fly", GREEN), ("lesion025", "lesion025", AMBER), ("scrambled_cal", "scrambled_cal", SOFT),
             ("random", "random", SOFT)]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    rng = np.random.default_rng(0)
    for i, (k, lab, c) in enumerate(order):
        v = np.array(e["kills"][k]); s = e["summary"][k]
        ax.scatter(i + rng.uniform(-.18, .18, len(v)), v, s=14, color=c, alpha=.6, lw=0)
        ax.plot([i + .28, i + .28], s["ci95"], color=INK, lw=3.5)
        ax.plot([i + .2, i + .36], [s["mean"]] * 2, color=INK, lw=2)
        ax.text(i + .4, s["mean"], f"{s['mean']:.2f}", va="center", fontsize=9, color=INK)
    ax.set_xticks(range(4), [l for _, l, _ in order]); ax.set_ylabel("kills per episode")
    ax.set_xlim(-.5, 3.8); ax.set_ylim(-0.5, 21)
    save(fig, "p5-n50.png")


def tuning():
    rows = J("fruitfly/local_doom_vizdoom130/calibration_fly.json")["rows"]
    az = [r["az"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.axvspan(-30, 30, color="#eef1f5", lw=0)
    for k, c, ls in [("AOTU019_L", BLUE, "-"), ("AOTU019_R", AMBER, "-"), ("DNa02_L", BLUE, "--"), ("DNa02_R", AMBER, "--")]:
        ax.plot(az, [r[k] for r in rows], ls, color=c, lw=2, marker="o" if ls == "-" else None, ms=3.5, label=k)
    ax.text(-20, 100, "within ±30°:\nDNa02 ≤ 4 Hz", ha="center", fontsize=8.5, color=SOFT)
    ax.set_xticks([-90, -60, -30, 0, 30, 60, 90]); ax.set_xlabel("enemy azimuth in the fly's visual field (deg)")
    ax.set_ylabel("firing rate (Hz)"); ax.set_ylim(0, 265)
    ax.legend(frameon=False, fontsize=9, ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.13))
    save(fig, "p5-tuning.png")
    meta["tuning_dna02_max_within_30"] = max(max(r["DNa02_L"], r["DNa02_R"]) for r in rows if abs(r["az"]) <= 30)




for f in (fly_episodes, n50, tuning):
    f()
json.dump(meta, open(os.path.join(O, "figures.json"), "w"), indent=1)
