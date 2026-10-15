"""BJ4b：README 指令（seconds 預設 40）訓練出的策略不會覓食；作者附的 forage.json 記錄 seconds=45。
用 seconds=45、其他照 README（generations=32），看能否接近作者的 validation 2942。在 repo/ 下以 PYTHONPATH=. 執行。"""
import json, numpy as np
from flybrain.mb.embodied import train, evaluate
train(generations=32, seconds=45.0, quiet=False, out="../results/bj4b_forage_s45.json")
th = np.array(json.load(open("../results/bj4b_forage_s45.json"))["theta"])
res = {}
for label, kw in [("learning", {}), ("dopamine cut", dict(dopamine=False)), ("plasticity off", dict(plasticity=False))]:
    thirds, food = evaluate(th, seeds=40, seconds=90.0, **kw)
    res[label] = dict(shocks=float(thirds.sum(axis=1).mean()), food=float(food.mean()))
    print("s45", label, "shocks %.2f  food %.2f" % (res[label]["shocks"], res[label]["food"]), flush=True)
res["validation"] = json.load(open("../results/bj4b_forage_s45.json"))["validation"]
json.dump(res, open("../results/bj4b_forage_s45_eval.json", "w"), indent=1)
