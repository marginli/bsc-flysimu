"""驗收：把 run_all.sh 跑出來的數字跟 expected.json（本課實跑的結果）逐項比對。
用法：python check.py fruitfly   或   python check.py blackjack   （在 pack 根目錄或子資料夾都可以）
判定有五種：exact（逐位相同）、rel（相對誤差在容許範圍內，用在沒有固定亂數種子的全腦模型）、
same（兩個檔案內容相同）、contains（終端輸出裡出現預期的那幾行）、md5_twice（同一支程式跑兩次的 md5 相同且等於預期）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUB = {"fruitfly": "fruitfly_lab", "blackjack": "blackjack"}


def get(path, keys, pluck=None, mean=False):
    with open(path) as f:
        d = json.load(f) if path.endswith(".json") else f.read()
    for k in keys:
        d = d[k]
    if pluck:                      # 一串 dict 裡取同一個欄位，例如每一局的 kills
        d = [x[pluck] for x in d]
    if mean:
        d = round(sum(d) / len(d), 6)
    return d


def main(which):
    exp = json.load(open(os.path.join(ROOT, "expected.json")))[which]
    base = os.path.join(ROOT, SUB[which])
    ok = bad = known = 0
    for c in exp:
        try:
            got = get(os.path.join(base, c["file"]), c.get("keys", []), c.get("pluck"), c.get("mean", False))
            if c["kind"] == "exact":
                good = got == c["value"]
            elif c["kind"] == "rel":
                v = c["value"]
                good = abs(got - v) <= c["tol"] * max(abs(v), 1e-9)
            elif c["kind"] == "same":
                other = get(os.path.join(base, c["other"]), [])
                good = got == other
            elif c["kind"] == "contains":
                good = all(v in got for v in c["value"])
            elif c["kind"] == "md5_twice":     # 同一支程式跑兩次，兩行 md5 相同且等於預期
                h = got.split()[0::2]
                good = len(h) == 2 and h[0] == h[1] == c["value"]
            else:
                good = False
        except (OSError, KeyError, IndexError, ValueError) as e:
            got, good = f"讀不到（{type(e).__name__}）", False
        if not good and c.get("known"):         # 本課實跑時就不符、頁面上已說明的項目
            known += 1
            print(f"△ {c['step']:6s} {c['what']}　本次 {got!r}；已知：{c['known']}")
            continue
        ok += good
        bad += not good
        mark = "✓" if good else "✗"
        print(f"{mark} {c['step']:6s} {c['what']}" + ("" if good else f"　本次 {got!r}，預期 {c.get('value', c.get('other'))!r}"))
    tail = f"，{known} 項已知不符（△，本課實跑時也一樣）" if known else ""
    print(f"\n{which}：{ok} 項通過，{bad} 項不符{tail}（共 {ok + bad + known} 項）")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
