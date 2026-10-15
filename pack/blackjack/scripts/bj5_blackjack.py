"""BJ5：21 點。blackjack.py 沒有命令列入口，依其檔尾 RESULT 註解的設定重跑：
3 種子 × 30,000 手，四個條件，對照組先跑。在 repo/ 目錄下以 PYTHONPATH=. 執行。
用法：python bj5_blackjack.py [hands] [seeds...]"""
import json, sys, time
import numpy as np
from flybrain.mb.blackjack import FlyPlayer, session, reference_winrates, chart_cells, basic_strategy, HIT, STAND, DOUBLE

HANDS = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
SEEDS = [int(s) for s in sys.argv[2:]] or [0, 1, 2]
CONDS = [  # 註解中的順序：對照組先跑
    ("untrained greedy", dict(learn=False, explore=0.0, explore_floor=0.0)),
    ("no learning + exploration decay", dict(learn=False)),
    ("dopamine cut + exploration decay", dict(dopamine=False)),
    ("connectome + dopamine", dict()),
]


def spot_counts(fly):
    """訓練後 greedy 在 260 格的選擇：hit / stand / double 各幾格。"""
    c = {HIT: 0, STAND: 0, DOUBLE: 0}
    for (t, soft, up) in chart_cells():
        c[fly.greedy(t, soft, up, True, [HIT, STAND, DOUBLE])] += 1
    out = {"hit": c[HIT], "stand": c[STAND], "double": c[DOUBLE]}
    # 依基本策略分類：圖表說該 hit／stand／double 的格子裡，蒼蠅選對幾格（作者稱 double 0/39）
    for want_a, nm in [(HIT, "hit"), (STAND, "stand"), (DOUBLE, "double")]:
        cells = [(t, s, u) for (t, s, u) in chart_cells() if basic_strategy(t, s, u, True) == want_a]
        out[f"chart_{nm}_cells"] = len(cells)
        out[f"chart_{nm}_matched"] = sum(fly.greedy(t, s, u, True, [HIT, STAND, DOUBLE]) == want_a for (t, s, u) in cells)
    return out


out = {"hands": HANDS, "seeds": SEEDS, "conditions": {}}
for name, kw in CONDS:
    runs = []
    for s in SEEDS:
        t0 = time.time()
        fly = FlyPlayer(seed=s, **kw)
        nets, blocks, agree = session(fly, hands=HANDS, seed=s)
        runs.append(dict(seed=s, first_block=blocks[0], last_block=blocks[-1], agree_first=agree[0],
                         agree_last=agree[-1], blocks=blocks, agree=agree, spots=spot_counts(fly)))
        print(f"{name:34s} seed {s}  winrate {blocks[0]:+.3f} -> {blocks[-1]:+.3f}  "
              f"agree {agree[0]:.3f} -> {agree[-1]:.3f}  spots {runs[-1]['spots']}  ({time.time() - t0:.0f}s)", flush=True)
    out["conditions"][name] = dict(runs=runs, mean_last=float(np.mean([r["last_block"] for r in runs])),
                                   mean_agree_last=float(np.mean([r["agree_last"] for r in runs])))
out["reference"] = {k: float(v) for k, v in reference_winrates(np.random.default_rng(0)).items()}
print("reference", out["reference"])
json.dump(out, open(f"../results/bj5_blackjack_{HANDS}.json", "w"), indent=1)
