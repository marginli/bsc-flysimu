"""把錄影的逐格資料、校準曲線、50 局統計、21 點學習曲線整理成 assets/demo/data.json，並複製影片（PART 6 用）。
用法：PYTHONNOUSERSITE=1 ~/anaconda3/envs/ffl_doom130/bin/python scripts/build_data.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

WORK = Path.home() / "claude_bscai" / "fly_play_game"     # 本機的重現實跑資料夾
HERE = WORK / "demo"
FF = WORK / "fruitfly_lab"
BJ = WORK / "blackjack"
SITE = Path(__file__).resolve().parent.parent / "assets" / "demo"   # PART 6 讀這裡
sys.path.insert(0, str(FF / "repo" / "flycircuit"))
from lif import Circuit  # noqa: E402

PANEL = ["LC10a_L", "LC10a_R", "AOTU019_L", "AOTU019_R", "AOTU025_L", "AOTU025_R", "DNa02_L", "DNa02_R"]
J = lambda p: json.loads(Path(p).read_text())


def episode(p):
    d = J(HERE / "rec" / f"{p}.json")
    t = d["tics"]
    out = {"kills": d["kills"], "n": len(t), "k": [x["k"] for x in t], "a": ["".join(map(str, x["a"])) for x in t],
           "e": [x["e"] for x in t]}
    for k in PANEL:
        out[k] = [x["r"][k] if x["r"] else 0 for x in t]
    return out


def group_edges():
    c = Circuit()
    gid = np.full(c.n, -1)
    for i, k in enumerate(PANEL):
        gid[c.groups[k]] = i
    src = np.repeat(np.arange(c.n), np.diff(c.offsets))
    a, b = gid[src], gid[c.post]
    keep = (a >= 0) & (b >= 0) & (a != b)
    tot = {}
    for x, y, w in zip(a[keep], b[keep], c.w[keep]):
        tot[(x, y)] = tot.get((x, y), 0.0) + w
    sizes = {k: int(len(c.groups[k])) for k in PANEL}
    edges = [{"from": PANEL[x], "to": PANEL[y], "w_mv": round(w, 1)} for (x, y), w in tot.items() if abs(w) > 0]
    return sizes, sorted(edges, key=lambda e: -abs(e["w_mv"])), {"n": int(c.n), "m": int(c.m)}


def main():
    SITE.mkdir(exist_ok=True)
    for p in ("fly", "lesion025", "scrambled_cal"):
        shutil.copy(HERE / "rec" / f"{p}.mp4", SITE / f"{p}.mp4")
    r = FF / "results"
    cal = {w: J(r / "local_doom_vizdoom130" / f"calibration_{w}.json") for w in ("fly", "scrambled")}
    e1 = J(r / "ext_vizdoom1.3.0" / "E1.json")
    e2 = J(r / "ext_vizdoom1.3.0" / "E2.json")
    e3 = J(r / "ext_vizdoom1.3.0" / "E3.json")
    a10 = J(r / "local_doom_vizdoom130" / "analysis.json")["conditions"]
    sizes, edges, cn = group_edges()
    bj = J(BJ / "results" / "bj5_blackjack_30000.json")
    curves = {}
    for name, c in bj["conditions"].items():
        blocks = np.array([run["blocks"] for run in c["runs"]])
        curves[name] = {"mean": [round(x, 4) for x in blocks.mean(0)], "runs": blocks.round(4).tolist()}
    data = {
        "episodes": {p: episode(p) for p in ("fly", "lesion025", "scrambled_cal")},
        "cal": {w: {"rows": v["rows"], "cal": {k: v["cal"][k] for k in ("turn_th", "fire_th", "quiet_th")}} for w, v in cal.items()},
        "stats50": {k: {**e1["summary"][k], "kills": e1["kills"][k]} for k in ("fly", "lesion025", "scrambled_cal", "random")},
        "selfcal": e2["summary"], "dna02_only": e3["fly_alt"], "lesion019_alt": e3["lesion019_alt"],
        "stats10": {k: {"kills": v["kills"], "kills_list": v["kills_list"], "p_vs_fly": v.get("p_vs_fly")} for k, v in a10.items()},
        "circuit": {"sizes": sizes, "edges": edges, **cn},
        "blackjack": {"hands": bj["hands"], "block": bj["hands"] // len(next(iter(curves.values()))["mean"]),
                      "curves": curves, "reference": bj["reference"]},
    }
    (SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print("sizes", sizes)
    for e in edges[:20]:
        print(e)
    print("data.json", (SITE / "data.json").stat().st_size)


main()
