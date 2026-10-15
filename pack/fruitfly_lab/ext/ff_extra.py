"""計畫第 5 節：作者沒做、本輪加做的檢查（E1–E3）。不改作者程式碼：匯入 doom/fly_doom.py，
把 RESULTS 指到 ../results/ext_vizdoom<版本>/，需要的新條件在這裡另外定義。
在 repo/ 目錄下執行：ffl_doom 環境  python ../ext/ff_extra.py [E1|E2|E3 ...]

  E1 加大樣本：fly / lesion025 / scrambled_cal / random 各 50 局（種子 0–49），重算配對置換 p
  E2 打亂對照逐一校準：作者 scrambled_cal 的閾值只在打亂種子 100 上校準，卻套用到每局不同的打亂；
     這裡 10 組打亂各自校準，各跑 5 局
  E3 拆開 lesion：作者的開火條件讀 AOTU019，靜音 AOTU019 就必然 0 殺。改用與 AOTU019 無關的讀出
     （轉向 = DNa02 右減左；開火 = 兩側 DNa02 較小者 > 閾值，閾值同作者方法在 0° 校準），
     比較 fly_alt（完整迴路）與 lesion019_alt（靜音 AOTU019 左右），各 50 局
"""
import json, sys, shutil
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent / "repo"
sys.path.insert(0, str(ROOT / "doom")); sys.path.insert(0, str(ROOT / "flycircuit"))
import fly_doom as fd                                         # noqa: E402
from lif import Circuit                                        # noqa: E402

import vizdoom                                                 # noqa: E402
EXT = ROOT.parent / "results" / f"ext_vizdoom{vizdoom.__version__}"; EXT.mkdir(parents=True, exist_ok=True)
for f in ["calibration_fly.json", "calibration_scrambled.json"]:
    shutil.copy(ROOT / "doom" / "results" / f, EXT / f)
fd.RESULTS = EXT
rng = np.random.default_rng(0)


def perm_p(a, b, n=20000):
    d = np.asarray(a, float) - np.asarray(b, float)
    flips = rng.choice([-1, 1], size=(n, d.size))
    return float(((np.abs((flips * d).mean(axis=1)) >= abs(d.mean()) - 1e-12).sum() + 1) / (n + 1))


def kills(out):
    return [e["kills"] for e in out["episodes"]]


def summary(k):
    k = np.asarray(k, float); se = k.std(ddof=1) / np.sqrt(len(k))
    return dict(n=len(k), mean=round(float(k.mean()), 2), sd=round(float(k.std(ddof=1)), 2),
                ci95=[round(float(k.mean() - 1.96 * se), 2), round(float(k.mean() + 1.96 * se), 2)])


def play_with(policy_fn, tag, episodes, seed=0):
    """借用 fd.play 的遊戲迴圈，只換 make_policy。"""
    orig = fd.make_policy
    fd.make_policy = lambda name, circuit, s: policy_fn(circuit, s)
    try:
        return fd.play(tag, episodes, seed)
    finally:
        fd.make_policy = orig


def e1():
    res = {}
    for p in ["fly", "lesion025", "scrambled_cal", "random"]:
        res[p] = kills(fd.play(p, 50, 0))
    out = {p: summary(k) for p, k in res.items()}
    for p in res:
        if p != "fly":
            out[p]["p_vs_fly"] = perm_p(res["fly"], res[p])
    out["fly_first10_vs_lesion025_first10_p"] = perm_p(res["fly"][:10], res["lesion025"][:10])
    return dict(kills=res, summary=out)


def calibrate_circuit(c, steer=fd.steer_signal, fire_keys=("AOTU019_L", "AOTU019_R"), silenced=(), seed=0):
    """逐行照抄 fd.calibrate 的方法（每個方位先跑 10 tic 暖機，再取 20 tic 平均；轉向閾值取 |steer| 在 0° 與 ±10° 較小者的中點；
    開火閾值取 0° 時 fire_keys 較小者的一半，下限 1），但可換電路、換讀出、可靜音，且不寫檔。"""
    by = {}
    for az in fd.CAL_AZ:
        brain = fd.FlyBrain(c, seed=seed, silenced=silenced)
        for _ in range(10):
            brain.step([(float(az), 1.0)])
        acc = {k: 0.0 for k in fd.PANEL}
        for _ in range(20):
            r = brain.step([(float(az), 1.0)])
            for k in fd.PANEL:
                acc[k] += r[k] / 20
        by[az] = acc
    s0 = abs(steer(by[0])); s_off = min(abs(steer(by[-10])), abs(steer(by[10])))
    turn_th = (s0 + s_off) / 2 if s_off > s0 else max(1.1 * s0, 1.0)
    fire_th = max(0.5 * min(by[0][fire_keys[0]], by[0][fire_keys[1]]), 1.0)
    return dict(turn_th=turn_th, fire_th=fire_th, quiet_th=5.0), by


def e2():
    base = Circuit(); res = []
    for k in range(10):
        c = base.scrambled(seed=100 + k)
        cal, _ = calibrate_circuit(c)

        def pol(circuit, s, c=c, cal=cal):
            brain = fd.FlyBrain(c, seed=s)

            def act(targets):
                r = brain.step(targets); st = fd.steer_signal(r)
                left, right = int(st < -cal["turn_th"]), int(st > cal["turn_th"])
                fire = int(min(r["AOTU019_L"], r["AOTU019_R"]) > cal["fire_th"])
                if not targets and sum(r.values()) < cal["quiet_th"]:
                    left, right = 0, 1
                return [left, right, fire], dict(r)
            return act, brain
        out = play_with(pol, f"scrambled_selfcal_{k}", 5, seed=1000 + 5 * k)
        res.append(dict(scramble_seed=100 + k, cal={a: round(float(b), 2) for a, b in cal.items()}, kills=kills(out)))
    allk = [x for r in res for x in r["kills"]]
    return dict(per_scramble=res, summary=summary(allk))


def alt_readout(silence):
    """與 AOTU019 無關的讀出：轉向 = DNa02 右減左；開火 = 兩側 DNa02 較小者 > 閾值。閾值在完整迴路上以作者同法校準。"""
    st = lambda r: r["DNa02_R"] - r["DNa02_L"]
    cal, by = calibrate_circuit(Circuit(), steer=st, fire_keys=("DNa02_L", "DNa02_R"))

    def pol(circuit, s):
        sil = [i for k in silence for i in circuit.groups[k]]
        brain = fd.FlyBrain(circuit, seed=s, silenced=sil)

        def act(targets):
            r = brain.step(targets); d = st(r)
            left, right = int(d < -cal["turn_th"]), int(d > cal["turn_th"])
            fire = int(min(r["DNa02_L"], r["DNa02_R"]) > cal["fire_th"])
            if not targets and sum(r.values()) < cal["quiet_th"]:
                left, right = 0, 1
            return [left, right, fire], dict(r)
        return act, brain
    return pol, cal, {a: by[a] for a in (-10, 0, 10)}


def e3():
    pol_f, cal, rows = alt_readout([])
    pol_l, _, _ = alt_readout(["AOTU019_L", "AOTU019_R"])
    kf = kills(play_with(pol_f, "fly_alt", 50))
    kl = kills(play_with(pol_l, "lesion019_alt", 50))
    return dict(cal={a: round(float(b), 2) for a, b in cal.items()}, cal_rows={str(a): {k: round(v, 1) for k, v in r.items()} for a, r in rows.items()},
                fly_alt=summary(kf), lesion019_alt=summary(kl), p=perm_p(kf, kl), kills=dict(fly_alt=kf, lesion019_alt=kl))


if __name__ == "__main__":
    todo = sys.argv[1:] or ["E1", "E2", "E3"]
    for name in todo:
        r = {"E1": e1, "E2": e2, "E3": e3}[name]()
        (EXT / f"{name}.json").write_text(json.dumps(r, indent=1))
        print(name, json.dumps({k: v for k, v in r.items() if k not in ("kills", "per_scramble", "cal_rows")}), flush=True)
