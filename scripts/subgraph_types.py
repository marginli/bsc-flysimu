"""PART 1 第 3 節〈子圖裡有哪些神經元〉那張表的數字：作者切出的 3,963 顆，依細胞種類分組數顆數與傳導物質。
有指定作用的種類（刺激、讀出、損毀、切子圖的端點）逐一列；其餘的依 FlyWire 標註表的 super_class 欄分大類。
需要作者 repo（~/claude_bscai/fly_play_game/fruitfly_lab/repo）的 circuit/meta.json。
用法：python3 scripts/subgraph_types.py   （輸出 out/subgraph_types.json）"""
import collections
import json
import os

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
assert sum(v["n"] for v in res["types"].values()) + len(rest) == len(n)
json.dump(res, open(os.path.join(D, "out/subgraph_types.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
