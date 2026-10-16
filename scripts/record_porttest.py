"""把下載包的可攜測試結果存成 out/porttest.json（PART 2 的執行時間、硬碟用量、驗收輸出都對回這裡）。

可攜測試的做法（~/claude_bscai/porttest2/run_porttests.sh）：把 downloads/*.zip 解到空資料夾；先把 setup_envs.sh 裡的環境名加上
zt_ 前綴從零建一次並計時（本機已有同名環境時 setup_envs.sh 會跳過建立），用 du -sm 量環境大小後刪掉 zt_ 環境；再用既有環境跑
run_all.sh 並計時；兩門課依序跑，不同時跑。計時用 /usr/bin/time，輸出存在 envtest/setup.out 與 run.out。
最後用目前版本的 check.py 對同一批輸出再驗收一次。
用法：python3 scripts/record_porttest.py <可攜測試資料夾> <blackjack|fruitfly>"""
import json
import os
import re
import subprocess
import sys

T, COURSE = sys.argv[1], sys.argv[2]
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = {"blackjack": "BLACKJACK", "fruitfly": "FRUITFLY"}[COURSE]
SUB = {"blackjack": "blackjack", "fruitfly": "fruitfly_lab"}[COURSE]


def secs(path, tag):
    return float(re.search(rf"^{tag} ([\d.]+) s", open(path).read(), re.M).group(1))


def du_mb(path):
    return round(int(subprocess.run(["du", "-sb", path], capture_output=True, text=True).stdout.split()[0]) / 1e6)


env_mb = {m.group(2): int(m.group(1)) for m in re.finditer(r"^(\d+)\s+\S+/envs/zt_(\S+)$", open(os.path.join(T, "envtest/env_du.txt")).read(), re.M)}
res = {
    "course": COURSE,
    "setup_fresh_seconds": secs(os.path.join(T, "envtest/setup.out"), "SETUP"),
    "run_seconds": secs(os.path.join(T, "run.out"), TAG),
    "parallel": False,
    "data_mb": {f"{SUB}/repo": du_mb(os.path.join(T, SUB, "repo"))},
    "env_mb": env_mb,
    "check_last": subprocess.run([sys.executable, os.path.join(T, "check.py"), COURSE], capture_output=True, text=True).stdout.strip().splitlines()[-1],
    "python_versions": {m.group(1): m.group(2) for m in re.finditer(r"^zt_(\S+) ([\d.]+) OK$", open(os.path.join(T, "envtest/setup.out")).read(), re.M)},
    "machine": "Linux, 12-core CPU, no GPU",
}
res["data_mb_total"] = sum(res["data_mb"].values())
res["env_mb_total"] = sum(env_mb.values())
json.dump(res, open(os.path.join(D, "out/porttest.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
