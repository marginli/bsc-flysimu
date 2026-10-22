"""PART 1 第 3 節〈子圖裡有哪些神經元〉那張表的數字：作者切出的 3,963 顆，依細胞種類分組數顆數與傳導物質。
有指定作用的種類（刺激、讀出、損毀、切子圖的端點）逐一列；其餘的依 FlyWire 標註表的 super_class 欄分大類。
需要作者 repo（~/claude_bscai/fly_play_game/fruitfly_lab/repo）的 circuit/meta.json。
用法：python3 scripts/subgraph_types.py   （輸出 out/subgraph_types.json）"""
import collections
import json
import os

import numpy as np

REPO = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = ["LC10a", "AOTU019", "AOTU025", "DNa02", "DNa01", "DNa03", "DNa04", "DNa11", "LC10d"]   # 作者 meta.json 的 groups 有分組的種類

meta = json.load(open(os.path.join(REPO, "circuit/meta.json")))
n = meta["neurons"]


def summary(cells):
    return {"n": len(cells),
            "side": dict(collections.Counter(x["side"] for x in cells)),
            "nt": dict(collections.Counter(x["nt"] for x in cells).most_common())}


res = {"n_neurons": len(n), "types": {t: summary([x for x in n if x["type"] == t]) for t in NAMED}}
rest = [x for x in n if x["type"] not in NAMED]
res["other"] = summary(rest)
res["other"]["n_types"] = len({x["type"] for x in rest})
res["other"]["cls"] = dict(collections.Counter(x["cls"] for x in rest).most_common())
res["other"]["nt_minor"] = sum(v for k, v in res["other"]["nt"].items() if k not in ("acetylcholine", "glutamate", "gaba"))
res["other_incl_unread"] = len(n) - sum(res["types"][t]["n"] for t in ("LC10a", "AOTU019", "AOTU025", "DNa02"))   # 圖 2 沒畫的
res["dn_other4"] = sum(res["types"][t]["n"] for t in ("DNa01", "DNa03", "DNa04", "DNa11"))

# 圖 2 沒畫的 3,723 顆裡的視覺神經元（FlyWire super_class 為視覺投射、視葉、視覺離心），以及哪些直接收 LC10a 的連結
# edges.bin 是 CSR：offsets u32 | post u16 | weight i16（weight ＝ 正負號 × 突觸數，作者 flycircuit/extract.py）
raw = open(os.path.join(REPO, "circuit/edges.bin"), "rb").read()
N = len(n)
off = np.frombuffer(raw, np.uint32, N + 1, 0).astype(np.int64)
m = int(off[-1])
post = np.frombuffer(raw, np.uint16, m, 4 * (N + 1)).astype(np.int64)
pre = np.repeat(np.arange(N), np.diff(off))
is_lc = np.array([x["type"] == "LC10a" for x in n])
from_lc = np.zeros(N, bool)
from_lc[post[is_lc[pre]]] = True
VIS = ("visual_projection", "optic", "visual_centrifugal")
unread = [i for i, x in enumerate(n) if x["type"] not in ("LC10a", "AOTU019", "AOTU025", "DNa02")]
vis = [i for i in unread if n[i]["cls"] in VIS]
res["unread_visual"] = {"n": len(vis),
                        "cls": dict(collections.Counter(n[i]["cls"] for i in vis).most_common()),
                        "n_types": len({n[i]["type"] for i in vis}),
                        "top_types": collections.Counter(n[i]["type"] for i in vis).most_common(8),
                        "direct_from_lc10a": int(from_lc[vis].sum())}
res["unread_direct_from_lc10a"] = int(from_lc[unread].sum())
# 圖 2 的主幹在全部接線裡占多少：以突觸數算（|weight|，不管正負號）
syn = np.abs(np.frombuffer(raw, np.int16, m, 4 * (N + 1) + 2 * m).astype(np.int64))
T = np.array([x["type"] for x in n])


def share(sel, other_end):
    """sel 選出的連結，依另一端的種類加總突觸數，回傳總數與各種類的百分比（一位小數）。"""
    c = collections.Counter()
    for t, k in zip(T[other_end[sel]], syn[sel]):
        c[t] += int(k)
    tot = sum(c.values())
    return {"n_partners": int(len(set(other_end[sel]))), "syn": tot,
            "pct": {t: round(100 * k / tot, 1) for t, k in c.most_common(12)},
            "pct_named": {t: round(100 * c[t] / tot, 1) for t in ("LC10a", "AOTU019", "AOTU025", "DNa02")}}


res["backbone_share"] = {
    "lc10a_out": share(T[pre] == "LC10a", post),
    "dna02_in": share(T[post] == "DNa02", pre),
    "aotu019_out": share(T[pre] == "AOTU019", post),
    "aotu025_out": share(T[pre] == "AOTU025", post),
}
# 圖 2 八個數字的拆解：兩群之間的連結數、突觸數、正負各多少、加總 × 0.275 mV
w_signed = np.frombuffer(raw, np.int16, m, 4 * (N + 1) + 2 * m).astype(np.int64)
g = meta["groups"]
res["fig2_edges"] = []
for a, b in [("LC10a_L", "AOTU019_L"), ("LC10a_R", "AOTU019_R"), ("LC10a_L", "AOTU025_L"), ("LC10a_R", "AOTU025_R"),
             ("AOTU025_L", "DNa02_L"), ("AOTU025_R", "DNa02_R"), ("AOTU019_L", "DNa02_R"), ("AOTU019_R", "DNa02_L")]:
    sel = np.isin(pre, g[a]) & np.isin(post, g[b])
    ws = w_signed[sel]
    neg_pre = sorted({n[i]["nt"] for i in pre[sel][ws < 0]})
    res["fig2_edges"].append({"pre": a, "post": b, "n_edges": int(sel.sum()), "n_pre": len(g[a]), "syn": int(np.abs(ws).sum()),
                              "pos": int(ws[ws > 0].sum()), "neg": int(-ws[ws < 0].sum()), "n_neg_pre": int((ws < 0).sum()),
                              "neg_pre_nt": neg_pre, "signed": int(ws.sum()), "mv": round(float(ws.sum()) * meta["w_syn_mv"], 3),
                              "mv_abs": round(abs(float(ws.sum())) * meta["w_syn_mv"], 3),
                              # 每條連結的突觸數分布（一條連結 ＝ 一對神經元）
                              "syn_per_edge": {"min": int(np.abs(ws).min()), "median": float(np.median(np.abs(ws))),
                                               "max": int(np.abs(ws).max()), "lt5": int((np.abs(ws) < 5).sum()),
                                               "eq1": int((np.abs(ws) == 1).sum()),
                                               "max_mv": round(int(np.abs(ws).max()) * meta["w_syn_mv"], 3),
                                               "min_mv": round(int(np.abs(ws).min()) * meta["w_syn_mv"], 3)}})
res["lc10a_glutamate_side"] = [n[i]["side"] for i in range(N) if n[i]["type"] == "LC10a" and n[i]["nt"] == "glutamate"]
side = np.array([x["side"] for x in n])
# 兩顆麩胺酸 LC10a 各自連到哪一顆 AOTU（圖 2 左側兩列的負號突觸出自哪一顆）
res["lc10a_glutamate_to_aotu"] = [
    {"side": n[i]["side"], "to": {f"{T[q]}_{side[q]}": int(x) for q, x in zip(post[pre == i], w_signed[pre == i])
                                  if T[q] in ("AOTU019", "AOTU025")}}
    for i in range(N) if T[i] == "LC10a" and n[i]["nt"] == "glutamate"]
# AOTU019／AOTU025 → DNa02，分同側、對側
res["aotu_to_dna02_by_side"] = {
    f"{k}_{sd}": {("same" if side[q] == sd else "contra"): int(x)
                  for q, x in zip(post[(T[pre] == k) & (side[pre] == sd) & (T[post] == "DNa02")],
                                  w_signed[(T[pre] == k) & (side[pre] == sd) & (T[post] == "DNa02")])}
    for k in ("AOTU019", "AOTU025") for sd in ("left", "right")}
res["unread_rest"] = res["other_incl_unread"] - res["dn_other4"] - len(vis)   # 其餘 3,723 顆扣掉另外四種下行神經元與視覺神經元
assert sum(v["n"] for v in res["types"].values()) + len(rest) == len(n)
json.dump(res, open(os.path.join(D, "out/subgraph_types.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
