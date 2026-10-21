"""PART 1 第 2 節〈漏電整合發放〉示意圖（圖 0）的資料：作者 lif.py 的參數與單顆神經元在幾個示範情境下的結果。
參數從作者 circuit/meta.json 讀；更新順序逐字確認 lif.py 還是這樣寫（改了就報錯）。
單顆神經元照 lif.py 的 _kernel 一步一步算（每步 0.1 ms）：先收到期的輸入 → 不反應期外才積分與衰減 → 倒數 → 外部刺激 → 過閾值就放電。
瀏覽器裡的圖（scripts/make_lif_anim.py）用同一套更新，頁面上的數字對這裡。
用法：python3 scripts/lif_fig_data.py   （輸出 out/lif_fig.json）"""
import json
import math
from decimal import ROUND_HALF_UP, Decimal
import os

import numpy as np

REPO = os.path.expanduser("~/claude_bscai/fly_play_game/fruitfly_lab/repo")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(REPO, "flycircuit/lif.py"), encoding="utf-8").read()
for s in ["g[i] += buf[slot, i]", "if rfc[i] <= 0:", "v[i] += a_v * (v0 - v[i] + g[i])", "g[i] *= decay_g", "rfc[i] -= 1",
          "if p_spk[i] > 0.0 and np.random.random() < p_spk[i]:", "v[i] += kick", "if v[i] > vth:", "v[i] = vr",
          "g[i] = 0.0", "rfc[i] = rfc_steps", "buf[dst, post[k]] += w[k]", "dst = (t + dly) % rows",
          "self.a_v = dt * 1e3 / p[\"t_mbr_ms\"]", "self.decay_g = float(np.exp(-dt * 1e3 / p[\"tau_ms\"]))",
          "self.rfc_steps = int(round(p[\"t_rfc_ms\"] * 1e-3 / dt))", "self.dly = int(round(p[\"t_dly_ms\"] * 1e-3 / dt))",
          "p_spk = np.asarray(rates_hz, dtype=np.float64) * self.dt"]:
    assert s in src, s
meta = json.load(open(os.path.join(REPO, "circuit/meta.json")))
P = meta["params"]
DT_MS = 0.1
W_SYN = meta["w_syn_mv"]
A_V = DT_MS / P["t_mbr_ms"]
DECAY_G = math.exp(-DT_MS / P["tau_ms"])
RFC = int(round(P["t_rfc_ms"] / DT_MS))
DLY = int(round(P["t_dly_ms"] / DT_MS))
SYN = 11                                   # 示範用一次輸入的突觸數：11 × 0.275 ≈ 3 mV，第 3 節圖 1「一顆 LC10a 平均約 3 mV」
W = SYN * W_SYN


def run(n_steps, sends=(), v_init=None, rate_hz=0.0, seed=0):
    """sends：[(送出的步, 權重 mV)]，上游在那一步放電，DLY 步後加進 g。rate_hz：外部刺激（LC10a 那種）的設定放電率。
    回傳每步的 V、g 與放電的步。"""
    rng = np.random.default_rng(seed)
    v = P["v0"] if v_init is None else v_init
    g, rfc = 0.0, 0
    arrive = {}
    for t, w in sends:
        arrive[t + DLY] = arrive.get(t + DLY, 0.0) + w
    V, G, spk = [], [], []
    p = rate_hz * DT_MS / 1000
    for t in range(n_steps):
        g += arrive.get(t, 0.0)
        if rfc <= 0:
            v += A_V * (P["v0"] - v + g)
            g *= DECAY_G
        rfc -= 1
        if p > 0 and rng.random() < p:
            v += P["poisson_kick_mv"]
        if v > P["v_th"]:
            v, g, rfc = P["v_rst"], 0.0, RFC
            spk.append(t)
        V.append(v)
        G.append(g)
    return np.array(V), np.array(G), spk


out = {"_note": "PART 1 第 2 節圖 0（漏電整合發放）的資料；scripts/lif_fig_data.py 產生，照作者 flycircuit/lif.py 的單顆神經元更新逐步算",
       "params": dict(P, w_syn_mv=W_SYN, dt_ms=DT_MS, rfc_steps=RFC, dly_steps=DLY, a_v=A_V, decay_g=DECAY_G),
       "demo_syn": SYN, "demo_w_mv": round(W, 3)}

# ① 漏電：從 −47 mV 放著不管
V, _, _ = run(1000, v_init=-47.0)
gap0 = -47.0 - P["v0"]
out["leak"] = {"v_init": -47.0, "gap0": gap0, "gap_at_tau_m": round(V[int(P["t_mbr_ms"] / DT_MS) - 1] - P["v0"], 3),
               "frac_at_tau_m": round((V[int(P["t_mbr_ms"] / DT_MS) - 1] - P["v0"]) / gap0, 3),
               "v_at_tau_m": round(V[int(P["t_mbr_ms"] / DT_MS) - 1], 2), "e_inv": round(math.exp(-1), 3)}

# ② 一次輸入（3 mV）：水位最多升多少、何時到頂
V, G, _ = run(800, sends=[(0, W)])
k = int(np.argmax(V))
out["single"] = {"w": round(W, 3), "peak_dv": round(V[k] - P["v0"], 3), "peak_ms_after_arrival": round((k - DLY) * DT_MS, 1),
                 "peak_frac_of_w": round((V[k] - P["v0"]) / W, 3), "g_after_tau_syn": round(G[DLY + int(P["tau_ms"] / DT_MS) - 1], 3),
                 "theory_peak_frac": round((P["tau_ms"] / (P["t_mbr_ms"] - P["tau_ms"])) *
                                           (math.exp(-math.log(P["t_mbr_ms"] / P["tau_ms"]) * P["tau_ms"] / (P["t_mbr_ms"] - P["tau_ms"]))
                                            - math.exp(-math.log(P["t_mbr_ms"] / P["tau_ms"]) * P["t_mbr_ms"] / (P["t_mbr_ms"] - P["tau_ms"]))), 3)}

# ③ 整合：同一步送 N 個，最少幾個會放電；同樣 N 個分散送（每 5 ms 一個）
n_min = next(n for n in range(1, 100) if run(600, sends=[(0, W)] * n)[2])
SPREAD_EVERY = 5.0
spread = [(int(i * SPREAD_EVERY / DT_MS), W) for i in range(n_min)]
V, _, s = run(1200, sends=spread)
out["integrate"] = {"n_min_same_step": n_min, "thresh_gap": P["v_th"] - P["v0"], "spread_every_ms": SPREAD_EVERY,
                    "spread_spikes": len(s), "spread_steady_dv": round(W * P["tau_ms"] / SPREAD_EVERY, 3)}
V, _, s = run(600, sends=[(i, W) for i in range(n_min)])            # 每 0.1 ms 一個
out["integrate"].update(burst_within_ms=round((n_min - 1) * DT_MS, 1), burst_spikes=len(s))
V, _, s = run(600, sends=[(0, W)] * (n_min - 1))
out["integrate"]["peak_v_one_less"] = round(V.max(), 2)

# 圖上逐步播放的劇本：sends 是 [送出的 ms, 權重 mV, 個數]。瀏覽器照這裡播，結果應與下面算的一樣
first_spike = run(400, sends=[(int(10 / DT_MS), W)] * 30)[2][0]
SCEN = {
    "1": {"window_ms": 60, "v_init": -47.0, "sends": []},
    "2": {"window_ms": 45, "sends": [[5.0, W, 1]]},
    "3": {"window_ms": 170, "sends": [[5.0 + i * SPREAD_EVERY, W, 1] for i in range(n_min)] + [[120.0, W, n_min]]},
    # ④ 放電後 1 ms 讓第二批到達（落在不反應期裡）
    "4": {"window_ms": 30, "sends": [[10.0, W, 30], [round((first_spike + int(1.0 / DT_MS) - DLY) * DT_MS, 1), W, 20]]},
    "5": {"window_ms": 110, "sends": [[10.0, W, 20], [60.0, W, 20], [60.0, -W, 10]]},
}
for k, sc in SCEN.items():
    sends = [(int(round(ms / DT_MS)), w) for ms, w, n in sc["sends"] for _ in range(n)]
    V, G, s = run(int(sc["window_ms"] / DT_MS), sends=sends, v_init=sc.get("v_init"))
    sc["spike_ms"] = [round(t * DT_MS, 1) for t in s]
    sc["max_v"], sc["max_v_ms"] = round(V.max(), 2), round(int(np.argmax(V)) * DT_MS, 1)
    sc["min_v"], sc["max_g"], sc["min_g"] = round(V.min(), 2), round(G.max(), 2), round(G.min(), 2)
    if k == "3":
        a = int(120 / DT_MS)
        sc["max_v_spread"], sc["max_v_spread_ms"] = round(V[:a].max(), 2), round(int(np.argmax(V[:a])) * DT_MS, 1)
    if k == "4":
        sc["arrive2_ms"] = round(sc["sends"][1][0] + P["t_dly_ms"], 1)
        sc["g_stored"] = round(20 * W, 2)
        sc["rfc_end_ms"] = round(sc["spike_ms"][0] + P["t_rfc_ms"], 1)
    if k == "5":
        b = int(60 / DT_MS)
        sc["max_v_inh"], sc["max_v_inh_ms"] = round(V[b:].max(), 2), round((b + int(np.argmax(V[b:]))) * DT_MS, 1)
        sc["g_net_at_60"] = round(10 * W, 2)
out["scen"] = SCEN

# ⑥ 持續輸入：上游總共每秒送 R 個 3 mV 輸入（隨機時刻），輸出放電率
rng = np.random.default_rng(1)
SEC = 20
f_in = {}
for R in [500, 1000, 1500, 2000, 3000, 4000]:
    n = int(SEC * 1000 / DT_MS)
    hits = np.flatnonzero(rng.random(n) < R * DT_MS / 1000)
    _, _, s = run(n, sends=[(int(t), W) for t in hits])
    f_in[R] = round(len(s) / SEC, 1)
out["drive"] = {"seconds": SEC, "in_rate_to_out_hz": f_in,
                "mean_g_at": {R: round(R * W * P["tau_ms"] / 1000, 2) for R in f_in}}

# ⑦ 外部刺激（LC10a）：每 0.1 ms 抽籤，抽中 V 加 68.75 mV
kick = {}
for r in [10, 50, 100, 150]:
    _, _, s = run(int(SEC * 1000 / DT_MS), rate_hz=r, seed=2)
    kick[r] = round(len(s) / SEC, 1)
out["kick"] = {"kick_mv": P["poisson_kick_mv"], "seconds": SEC, "rate_to_out_hz": kick, "p_per_step_at_150": 150 * DT_MS / 1000,
               "max_rate_hz": round(1000 / P["t_rfc_ms"], 1)}

# 頁面上寫的形式：水位寫成「−49.01 mV」，number_audit 只比對絕對值；1.835 依四捨五入寫成 1.84
out["shown"] = {"gap_at_tau_m": float(Decimal(repr(out["leak"]["gap_at_tau_m"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "v_abs": sorted({abs(x) for x in [out["leak"]["v_at_tau_m"], out["integrate"]["peak_v_one_less"], SCEN["2"]["max_v"],
                                                    SCEN["3"]["max_v_spread"], SCEN["5"]["max_v_inh"]]})}
json.dump(out, open(os.path.join(D, "out/lif_fig.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
