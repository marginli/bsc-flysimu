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



exp = {"fruitfly": fruitfly()}
json.dump(exp, open(os.path.join(D, "pack/expected.json"), "w"), indent=1, ensure_ascii=False)
print({k: len(v) for k, v in exp.items()})
