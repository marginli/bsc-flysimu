"""從 out/（本課實跑的結果）產生下載包的驗收表 pack/expected.json，check.py 拿它逐項比對。
預期值一律讀實跑產出，不手打；作者宣稱的值讀作者附的結果檔。用法：python3 scripts/make_expected.py"""
import json
import os
import re

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(D, "out")
J = lambda p: json.load(open(os.path.join(O, p)))
POL = ["fly", "scrambled", "scrambled_cal", "lesion", "lesion025", "random", "oracle"]


def fruitfly():
    c = []
    log = open(os.path.join(O, "fruitfly/logs/ff1_conn.log")).read()
    ff1 = json.loads(log[log.index("{"):])
    for k, w in [("shiu_neurons", "神經元數"), ("shiu_edges", "連結數"), ("shiu_synapses", "突觸總數")]:
        c.append(dict(step="FF1", what=f"Shiu 連線表的{w} = {ff1[k]:,}", file="results/ff1_conn.json", keys=[k], kind="exact", value=ff1[k]))
    c.append(dict(step="FF2", what="重新抽出的子圖與作者附的檔案逐位相同（md5）", file="logs/ff2_md5_rerun.txt",
                  kind="same", other="logs/ff2_md5_committed.txt"))
    au = J("fruitfly/validation_author.json")
    for stim in ("LC10a_L", "LC10a_R"):
        for model in ("subgraph", "scrambled", "full_brain"):
            for n in ("DNa02_L", "DNa02_R", "AOTU019_L", "AOTU019_R"):
                v = au[f"{stim}/{model}"][n]
                if v > 10:      # 計畫訂的判準：大於 10 Hz 的項目在作者值的 ±20% 內
                    lo = J("fruitfly/validation_local.json")[f"{stim}/{model}"][n]
                    item = dict(step="FF3", what=f"刺激 {stim}、{model}：{n} 在作者 {v} Hz 的 ±20% 內",
                                file="results/validation_local.json", keys=[f"{stim}/{model}", n], kind="rel", tol=0.2, value=v)
                    if abs(lo - v) > 0.2 * v:   # 本課實跑也不符的那一項：標成已知，不算失敗（PART 3 第 5 節）
                        item["known"] = f"本課實跑也不符（{lo} Hz），見 PART 3 第 5 節"
                    c.append(item)
    for w, f in [("fly", "calibration_fly.json"), ("scrambled", "calibration_scrambled.json")]:
        cal = J(f"fruitfly/author_doom/{f}")["cal"]
        for k in ("turn_th", "fire_th"):
            c.append(dict(step="FF4", what=f"{w} 的{'轉向' if k == 'turn_th' else '開火'}閾值 = 作者的 {cal[k]}",
                          file=f"results/local_doom_vizdoom130/{f}", keys=["cal", k], kind="exact", value=cal[k]))
    for p in POL:
        k = [e["kills"] for e in J(f"fruitfly/author_doom/{p}.json")["episodes"]]
        c.append(dict(step="FF5", what=f"ViZDoom 1.3.0、{p}：10 局逐局擊殺 = 作者 {k}",
                      file=f"results/local_doom_vizdoom130/{p}.json", keys=["episodes"], pluck="kills", kind="exact", value=k))
    for p in POL:
        k = [e["kills"] for e in J(f"fruitfly/local_doom_vizdoom132/{p}.json")["episodes"]]
        c.append(dict(step="FF5", what=f"ViZDoom 1.3.2、{p}：10 局逐局擊殺 = 本課 {k}",
                      file=f"results/local_doom_vizdoom132/{p}.json", keys=["episodes"], pluck="kills", kind="exact", value=k))
    for v in ("1.3.0", "1.3.2"):
        e1 = J(f"fruitfly/ext_vizdoom{v}/E1.json")["summary"]
        for p in ("fly", "lesion025", "scrambled_cal", "random"):
            c.append(dict(step="E1", what=f"ViZDoom {v}、{p}：50 局平均擊殺 {e1[p]['mean']}",
                          file=f"results/ext_vizdoom{v}/E1.json", keys=["summary", p, "mean"], kind="exact", value=e1[p]["mean"]))
    e2 = J("fruitfly/ext_vizdoom1.3.0/E2.json")["summary"]["mean"]
    c.append(dict(step="E2", what=f"打亂接線各自校準：50 局平均 {e2}", file="results/ext_vizdoom1.3.0/E2.json",
                  keys=["summary", "mean"], kind="exact", value=e2))
    e3 = J("fruitfly/ext_vizdoom1.3.0/E3.json")
    for k in ("fly_alt", "lesion019_alt"):
        c.append(dict(step="E3", what=f"只讀 DNa02、{k}：50 局平均 {e3[k]['mean']}", file="results/ext_vizdoom1.3.0/E3.json",
                      keys=[k, "mean"], kind="exact", value=e3[k]["mean"]))
    c.append(dict(step="E4", what="E4 的分析結果檔存在且含右眼刺激的比較", file="results/E4_asymmetry.json",
                  keys=["LC10a_R"], kind="contains", value=[]))
    return c


def blackjack():
    c = []
    log = open(os.path.join(O, "blackjack/logs/bj1_train.log")).read()
    rows = [l for l in log.splitlines() if re.match(r"^(connectome|SAME|untrained|uniform)", l)]
    c.append(dict(step="BJ1", what="Dino 四列結果與 README 相同（45／0／0／0 完成）", file="logs/bj1_train.log", kind="contains", value=rows))
    h = open(os.path.join(O, "blackjack/logs/bj2_md5.txt")).read().split()[0]
    c.append(dict(step="BJ2", what=f"切出蕈狀體跑兩次，md5 相同且 = {h}", file="logs/bj2_md5.txt", kind="md5_twice", value=h))
    r = J("blackjack/mb_results.json")["acquisition"]
    for k in ("connectome + plasticity", "KC->MBON shuffled", "dopamine disconnected"):
        m = round(sum(r[k]) / len(r[k]), 6)
        c.append(dict(step="BJ3", what=f"{k}：12 種子平均學習指數 {m:.3f}", file="results/mb_results.json",
                      keys=["acquisition", k], mean=True, kind="exact", value=m))
    f4 = J("blackjack/bj4_forage.json")
    for g in ("author_policy", "retrained"):
        for k in ("learning", "dopamine cut"):
            v = f4[g][k]["shocks"]
            c.append(dict(step="BJ4", what=f"{g}、{k}：每 90 秒電擊 {v}", file="results/bj4_forage.json", keys=[g, k, "shocks"], kind="exact", value=v))
    s45 = J("blackjack/bj4b_forage_s45_eval.json")
    for k in ("learning", "dopamine cut"):
        c.append(dict(step="BJ4b", what=f"seconds=45 重新訓練、{k}：電擊 {s45[k]['shocks']}", file="results/bj4b_forage_s45_eval.json",
                      keys=[k, "shocks"], kind="exact", value=s45[k]["shocks"]))
    c.append(dict(step="BJ4b", what=f"seconds=45 重新訓練的驗證分數 = 作者策略檔記錄的 {s45['validation']:.1f}",
                  file="results/bj4b_forage_s45_eval.json", keys=["validation"], kind="exact", value=s45["validation"]))
    b5 = J("blackjack/bj5_blackjack_30000.json")["conditions"]
    for k, v in b5.items():
        c.append(dict(step="BJ5", what=f"{k}：最後 2,000 手平均每手 {v['mean_last']:.4f}", file="results/bj5_blackjack_30000.json",
                      keys=["conditions", k, "mean_last"], kind="exact", value=v["mean_last"]))
    x = J("blackjack/bj_extra.json")
    c.append(dict(step="X1", what=f"50 種子學習指數 {x['X1_50_seeds']['none']['mean']:.3f}", file="results/bj_extra.json",
                  keys=["X1_50_seeds", "none", "mean"], kind="exact", value=x["X1_50_seeds"]["none"]["mean"]))
    c.append(dict(step="X2", what=f"DAN→MBON 打亂 10 組平均 {x['X2_dan_mbon_shuffled']['mean_of_means']:.3f}", file="results/bj_extra.json",
                  keys=["X2_dan_mbon_shuffled", "mean_of_means"], kind="exact", value=x["X2_dan_mbon_shuffled"]["mean_of_means"]))
    c.append(dict(step="X4", what=f"MBON 標記與文獻規則一致 {x['X4_mbon_valence']['agree']}/{x['X4_mbon_valence']['judged']}",
                  file="results/bj_extra.json", keys=["X4_mbon_valence", "agree"], kind="exact", value=x["X4_mbon_valence"]["agree"]))
    return c


exp = {"fruitfly": fruitfly(), "blackjack": blackjack()}
json.dump(exp, open(os.path.join(D, "pack/expected.json"), "w"), indent=1, ensure_ascii=False)
print({k: len(v) for k, v in exp.items()})
