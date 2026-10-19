"""把重現實跑的產出收進 out/，頁面上每個數字都要對得回這裡（scripts/number_audit.py 會掃）。

來源是本機的實跑資料夾 ~/claude_bscai/fly_play_game/（fruitfly_lab/run_all.sh 跑出來的 logs/ 與 results/）。
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
]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    n = 0
    for src, dst, pats in PLAN:
        for pat in pats:
            for f in sorted(glob.glob(os.path.join(SRC, src, pat))):
                rel = os.path.relpath(f, os.path.join(SRC, src))
                if rel.endswith("_trace.json"):
                    continue                                   # 逐格軌跡留給 PART 5 的 demo_data.json
                t = os.path.join(OUT, dst, rel)
                os.makedirs(os.path.dirname(t), exist_ok=True)
                shutil.copy2(f, t)
                n += 1
    shutil.copy2(os.path.join(SRC, "demo/site/data.json"), os.path.join(OUT, "demo_data.json"))
    n += 1
    # fruitfly-lab 沒有授權檔，不收整份 README；只摘它宣稱結果的那幾行表格（作者自己的數字），標明出處行號
    rd = open(os.path.join(SRC, "fruitfly_lab/repo/README.md"), encoding="utf-8").read().splitlines()
    claims = [{"line": i + 1, "text": t} for i, t in enumerate(rd) if t.startswith("|") and any(ch.isdigit() for ch in t)
              or "10.2 kills" in t or "Thresholds come from" in t or "central field" in t or "periphery 40" in t or "DNa02 has no baseline" in t or "AOTU025-only lesion" in t]
    json.dump({"source": "webergithub/fruitfly-lab README.md @ 8c27fe8", "claims": claims},
              open(os.path.join(OUT, "upstream/fruitfly_README_claims.json"), "w"), indent=1, ensure_ascii=False)
    # ViZDoom 執行時自動產生的設定檔，第一行記著產生它的版本：PART 3 第 8 節的依據
    with open(os.path.join(SRC, "fruitfly_lab/repo/_vizdoom.ini")) as f:
        open(os.path.join(OUT, "upstream/fruitfly_vizdoom_ini_line1.txt"), "w").write(f.readline())
    n += 2
    meta = {"source": "~/claude_bscai/fly_play_game", "files": n,
            "fruitfly_commit": "8c27fe8e70903e09b1d87bae6989051d09161e92"}
    json.dump(meta, open(os.path.join(OUT, "_manifest.json"), "w"), indent=1)
    print(f"收進 out/：{n} 個檔案")


main()
