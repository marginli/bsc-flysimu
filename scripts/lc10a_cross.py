"""PART 1 第 4 節的補充數字：LC10a 到同側／對側 AOTU019、AOTU025 的連結，在作者切出的子圖裡各有幾條、權重加總多少。
圖 2 只畫加總絕對值 30 以上的連結，讀者會問「跨側的線是沒有，還是太小沒畫」，這支程式直接數。
需要作者 repo（~/claude_bscai/fly_play_game/fruitfly_lab/repo）的 circuit/edges.bin 與 flycircuit/lif.py。
用法：python3 scripts/lc10a_cross.py   （輸出 out/lc10a_cross.json）"""
import json
import os
import sys

import numpy as np

REPO = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
sys.path.insert(0, os.path.join(REPO, "flycircuit"))
os.chdir(REPO)
from lif import Circuit  # noqa: E402

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = Circuit()
g = c.groups
pre = np.repeat(np.arange(c.n), np.diff(c.offsets))          # CSR：offsets 展開成每條邊的起點
res = {}
for a in ("LC10a_L", "LC10a_R"):
    for b in ("AOTU019_L", "AOTU019_R", "AOTU025_L", "AOTU025_R"):
        m = np.isin(pre, g[a]) & np.isin(c.post, g[b])
        res[f"{a}->{b}"] = {"edges": int(m.sum()), "w_mv_sum": round(float(c.w[m].sum()), 1)}
json.dump(res, open(os.path.join(D, "out/lc10a_cross.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
