"""把下載包的可攜測試結果存成 out/porttest.json（PART 2 的執行時間、硬碟用量、驗收輸出都對回這裡）。
可攜測試的做法：把 downloads/flysimu-code.zip 解到空資料夾，依序跑 setup_envs.sh、兩個 run_all.sh（兩個同時跑），
每一步用 /usr/bin/time 計時，輸出存在 setup.out、ff.out、bj.out；最後用目前版本的 check.py 對同一批輸出再驗收一次。
建環境另外用暫時改名的環境實測（本機已有同名環境時 setup_envs.sh 會跳過建立），結果存在 envtest/setup.out，四個環境的 du -sh 存在 envtest/env_du.txt。
用法：python3 scripts/record_porttest.py <可攜測試資料夾> <建環境測試資料夾>"""
import json
import os
import re
import subprocess
import sys

T, E = sys.argv[1], sys.argv[2]
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def secs(path, tag):
    return float(re.search(rf"{tag} ([\d.]+) s", open(path).read()).group(1))


def du_mb(path):
    return round(int(subprocess.run(["du", "-sb", path], capture_output=True, text=True).stdout.split()[0]) / 1e6)


env_mb = {m.group(2): int(m.group(1)) for m in re.finditer(r"^(\d+)M\s+\S+/envs/zt_(\S+)$", open(os.path.join(E, "env_du.txt")).read(), re.M)}
res = {
    "setup_fresh_seconds": secs(os.path.join(E, "setup.out"), "SETUP"),
    "fruitfly_seconds": secs(os.path.join(T, "ff.out"), "FRUITFLY"),
    "blackjack_seconds": secs(os.path.join(T, "bj.out"), "BLACKJACK"),
    "parallel": True,
    "data_mb": {"fruitfly_lab/repo": du_mb(os.path.join(T, "fruitfly_lab/repo")),
                "blackjack/repo": du_mb(os.path.join(T, "blackjack/repo"))},
    "env_mb": env_mb,
    "check_fruitfly_last": subprocess.run([sys.executable, os.path.join(T, "check.py"), "fruitfly"], capture_output=True, text=True).stdout.strip().splitlines()[-1],
    "check_blackjack_last": subprocess.run([sys.executable, os.path.join(T, "check.py"), "blackjack"], capture_output=True, text=True).stdout.strip().splitlines()[-1],
    "python_versions": {m.group(1): m.group(2) for m in re.finditer(r"^zt_(\S+) ([\d.]+) OK$", open(os.path.join(E, "setup.out")).read(), re.M)},
    "machine": "Linux, 12-core CPU, no GPU",
}
res["data_mb_total"] = sum(res["data_mb"].values())
res["env_mb_total"] = sum(env_mb.values())
json.dump(res, open(os.path.join(D, "out/porttest.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
