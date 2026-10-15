"""把重現實跑的產出收進 out/，頁面上每個數字都要對得回這裡（scripts/number_audit.py 會掃）。

來源是本機的實跑資料夾 ~/claude_bscai/fly_play_game/（兩個 run_all.sh 跑出來的 logs/ 與 results/）。
只收數字（JSON、log 文字），不收作者的程式碼。fruitfly-lab 沒有授權檔，所以它的 README 不收；
作者原本的結果檔（results/author_doom/、validation_author.json）是作者附在 repo 裡的輸出，照收以便逐局對照。
用法：~/anaconda3/bin/python scripts/collect_out.py（需要 numpy）
"""
import glob
import json
import os
import shutil

SRC = os.path.expanduser("~/claude_bscai/fly_play_game")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

PLAN = [
    ("fruitfly_lab/results", "fruitfly", ("*.json", "*/*.json", "*/*.log")),
    ("fruitfly_lab/logs", "fruitfly/logs", ("*.log", "*.txt")),
    ("fruitfly_lab", "fruitfly", ("env*.txt", "runall_test.out")),
    ("fruitfly_lab/patches", "fruitfly", ("env_notes.txt",)),
    ("blackjack/results", "blackjack", ("*.json",)),
    ("blackjack/logs", "blackjack/logs", ("*.log", "*.txt")),
    ("blackjack", "blackjack", ("env.txt", "runall_test.out")),
    ("blackjack/repo", "upstream", ("README.md",)),          # MIT 授權，作者宣稱的數字以這份為準
    ("blackjack/repo/data", "blackjack", ("mb_results.json", "mb_tmaze.json")),   # BJ3 的輸出寫在 repo/data/
]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    n = 0
    for src, dst, pats in PLAN:
        for pat in pats:
            for f in sorted(glob.glob(os.path.join(SRC, src, pat))):
                rel = os.path.relpath(f, os.path.join(SRC, src))
                if dst == "upstream":
                    rel = "blackjack_README.md"
                if rel.endswith("_trace.json"):
                    continue                                   # 逐格軌跡留給 PART 6 的 demo_data.json
                t = os.path.join(OUT, dst, rel)
                os.makedirs(os.path.dirname(t), exist_ok=True)
                shutil.copy2(f, t)
                n += 1
    shutil.copy2(os.path.join(SRC, "demo/site/data.json"), os.path.join(OUT, "demo_data.json"))
    n += 1
    # 作者策略檔的訓練設定（不收 theta 本身）：seconds=45 這件事的出處
    pol = json.load(open(os.path.join(SRC, "blackjack/repo/policies/forage.json")))
    json.dump({k: v for k, v in pol.items() if k != "theta"}, open(os.path.join(OUT, "upstream/blackjack_forage_policy_meta.json"), "w"), indent=1)
    # fruitfly-lab 沒有授權檔，不收整份 README；只摘它宣稱結果的那幾行表格（作者自己的數字），標明出處行號
    rd = open(os.path.join(SRC, "fruitfly_lab/repo/README.md"), encoding="utf-8").read().splitlines()
    claims = [{"line": i + 1, "text": t} for i, t in enumerate(rd) if t.startswith("|") and any(ch.isdigit() for ch in t)
              or "10.2 kills" in t or "Thresholds come from" in t]
    json.dump({"source": "webergithub/fruitfly-lab README.md @ 8c27fe8", "claims": claims},
              open(os.path.join(OUT, "upstream/fruitfly_README_claims.json"), "w"), indent=1, ensure_ascii=False)
    # ViZDoom 執行時自動產生的設定檔，第一行記著產生它的版本：PART 3 第 8 節的依據
    with open(os.path.join(SRC, "fruitfly_lab/repo/_vizdoom.ini")) as f:
        open(os.path.join(OUT, "upstream/fruitfly_vizdoom_ini_line1.txt"), "w").write(f.readline())
    # fly-blackjack（MIT）：作者 commit 進 repo 的蕈狀體 manifest，以及 blackjack.py 檔尾的 RESULT 註解
    import subprocess
    man = subprocess.run(["git", "-C", os.path.join(SRC, "blackjack/repo"), "show", "HEAD:data/mb_manifest.json"],
                         capture_output=True, text=True, check=True).stdout
    open(os.path.join(OUT, "upstream/blackjack_mb_manifest_committed.json"), "w").write(man)
    src = open(os.path.join(SRC, "blackjack/repo/flybrain/mb/blackjack.py"), encoding="utf-8").read().splitlines()
    i = next(k for k, t in enumerate(src) if t.startswith("# RESULT"))
    open(os.path.join(OUT, "upstream/blackjack_py_RESULT_comment.txt"), "w").write(
        f"# flybrain/mb/blackjack.py lines {i + 1}-{i + 24} @ 004b2e3\n" + "\n".join(src[i:i + 24]) + "\n")
    # BJ2：README 的連結數對不上 1,200 顆 KC 的電路；量一下用全部 KC 切出的電路（加做檢查 X3 存下的）有幾條
    import numpy as np
    cnt = {}
    for tag, f in [("kc1200_committed_circuit", "blackjack/repo/data/mb_circuit.npz"),
                   ("all_live_kc_circuit", "blackjack/results/circuits/mb_all_live_kc.npz")]:
        z = np.load(os.path.join(SRC, f))
        cnt[tag] = {k: int(z[k + "_val"].size) for k in ("pn_kc", "kc_mbon", "dan_mbon")}
    json.dump(cnt, open(os.path.join(OUT, "blackjack/bj2_edge_counts.json"), "w"), indent=1)
    n += 6
    meta = {"source": "~/claude_bscai/fly_play_game", "files": n,
            "fruitfly_commit": "8c27fe8e70903e09b1d87bae6989051d09161e92",
            "blackjack_commit": "004b2e3e9ccb742f83c5bdc2717c97f5a64b420f"}
    json.dump(meta, open(os.path.join(OUT, "_manifest.json"), "w"), indent=1)
    print(f"收進 out/：{n} 個檔案")


main()
