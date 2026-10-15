"""BJ4：覓食。先用作者附的 policies/forage.json 評估，再用 README 指令自己訓練一次（存到 results/）並評估。
在 repo/ 目錄下執行。"""
import json, sys, numpy as np
from flybrain.mb.embodied import train, evaluate

def ev(theta, tag):
    out = {}
    for label, kw in [("learning", {}), ("dopamine cut", dict(dopamine=False)), ("plasticity off", dict(plasticity=False))]:
        thirds, food = evaluate(theta, seeds=40, seconds=90.0, **kw)
        out[label] = dict(shocks=float(thirds.sum(axis=1).mean()), shocks_sd=float(thirds.sum(axis=1).std()), food=float(food.mean()))
        print(tag, label, "shocks %.2f  food %.2f" % (out[label]["shocks"], out[label]["food"]), flush=True)
    return out

res = {"author_policy": ev(np.array(json.load(open("policies/forage.json"))["theta"]), "author")}
train(generations=32, quiet=False, out="../results/bj4_forage_retrained.json")
res["retrained"] = ev(np.array(json.load(open("../results/bj4_forage_retrained.json"))["theta"]), "retrained")
json.dump(res, open("../results/bj4_forage.json", "w"), indent=1)
