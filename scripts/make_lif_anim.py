"""PART 1 第 2 節〈漏電整合發放〉的圖 1：左邊水桶（水位＝膜電位 V、水龍頭開度＝g、桶底的洞＝漏電），右邊 V 與 g 隨時間的軌跡，七步可逐步看。
數字全部讀 out/lif_fig.json（scripts/lif_fig_data.py 從作者 meta.json 讀參數、照 lif.py 逐步算的結果）；
瀏覽器裡的更新照抄作者 flycircuit/lif.py 的 _kernel（單顆神經元）：先收到期的輸入 → 不反應期外才積分與衰減 → 倒數 → 外部刺激 → 過閾值就放電。
產出：part1-what.html 裡 <!-- lif:start --> … <!-- lif:end --> 之間的片段，與簡報用的單獨頁 lif.html。圖的文字要改在這裡，不要直接改頁面。
用法：python3 scripts/make_lif_anim.py"""
import json
import os
import re
from decimal import ROUND_HALF_UP, Decimal

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(os.path.join(D, "out/lif_fig.json")))
P, S = L["params"], L["scen"]
PAGE = os.path.join(D, "part1-what.html")


def n(x, d=2):
    """數字照 out/ 的精度印，負號用全形減號。"""
    if isinstance(x, float):
        s = str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
        s = s.rstrip("0").rstrip(".") if "." in s else s
    else:
        s = str(x)
    return s.replace("-", "−")


W = L["demo_w_mv"]
lk, sg, it, dr, kk = L["leak"], L["single"], L["integrate"], L["drive"], L["kick"]
s3, s4, s5 = S["3"], S["4"], S["5"]

# ── 每一步：說明文字、畫面上的註記（ms 到了才出現）、g 軸範圍、預設速度 ─────────
# 註記：row 是 up（上游那一排）、g、V；v 是該列的值；dx、dy 是文字相對位置（像素）
STEPS = [
    dict(k=1, title="漏電", g=[-1, 4], speed=1, text=(
        f"水位比 V<sub>rest</sub> 高 {n(lk['gap0'], 0)} mV，沒有任何輸入。桶底的洞讓水位往 V<sub>rest</sub> 回落，離得愈遠落得愈快，"
        f"愈接近落得愈慢。過 {P['t_mbr_ms']} ms（τ<sub>m</sub>）差距從 {n(lk['gap0'], 0)} mV 剩 {n(L['shown']['gap_at_tau_m'])} mV，"
        f"約 {round(lk['frac_at_tau_m'] * 100)}%。"),
         notes=[dict(ms=0, row="V", v=-47.0, dx=8, dy=-10, t=f"起點：比 V_rest 高 {n(lk['gap0'], 0)} mV"),
                dict(ms=P["t_mbr_ms"], row="V", v=lk["v_at_tau_m"], dx=8, dy=-12, vline=1,
                     t=f"{P['t_mbr_ms']} ms 後：差距剩 {n(L['shown']['gap_at_tau_m'])} mV（約 {round(lk['frac_at_tau_m'] * 100)}%）")]),
    dict(k=2, title="一次輸入", g=[-1, 4], speed=0, text=(
        f"一顆上游神經元放電一次（假設兩顆之間有 {L['demo_syn']} 個突觸：{L['demo_syn']} × {P['w_syn_mv']} ≈ {n(W)} mV，"
        f"和第 3 節圖 2 裡一顆 LC10a 的平均差不多）。{P['t_dly_ms']} ms 後訊號到達，g 跳高 {n(W)} mV，接著每 {P['tau_ms']} ms 剩 37%。"
        f"水位跟著 g 慢慢升，到達後約 {sg['peak_ms_after_arrival']} ms 到頂，只升 {n(sg['peak_dv'])} mV，"
        f"離刻度還差 {it['thresh_gap']} mV 的一大截。"),
         notes=[dict(ms=5.0, row="up", dx=6, dy=0, t="上游放電"),
                dict(ms=5.0 + P["t_dly_ms"], row="g", v=W, dx=8, dy=4, t=f"{P['t_dly_ms']} ms 後到達：g 跳高 {n(W)} mV"),
                dict(ms=5.0 + P["t_dly_ms"] + P["tau_ms"], row="g", v=sg["g_after_tau_syn"], dx=8, dy=-6,
                     t=f"再過 {P['tau_ms']} ms：剩 {n(sg['g_after_tau_syn'])} mV（37%）"),
                dict(ms=S["2"]["max_v_ms"], row="V", v=S["2"]["max_v"], dx=8, dy=-12, t=f"水位到頂：只升 {n(sg['peak_dv'])} mV")]),
    dict(k=3, title="整合", g=[-3, 50], speed=1, text=(
        f"同樣是 {it['n_min_same_step']} 個輸入，送法不同。前面每 {n(it['spread_every_ms'], 0)} ms 送一個：每一個留下的水還沒漏完下一個就來，"
        f"水位疊到 {n(s3['max_v_spread'])} mV 左右就上不去（進來的和漏掉的打平），沒到刻度。{120} ms 時 {it['n_min_same_step']} 個同時送："
        f"水位在 {s3['spike_ms'][0]} ms 過刻度、放電。{it['n_min_same_step']} 個是同一刻送最少要的個數，少一個水位只到 {n(it['peak_v_one_less'])} mV。"
        f"這就是「整合」：神經元把短時間內的輸入加起來，加得夠多才放電。"),
         notes=[dict(ms=5.0, row="up", dx=6, dy=0, t=f"每 {n(it['spread_every_ms'], 0)} ms 送 1 個"),
                dict(ms=s3["max_v_spread_ms"], row="V", v=s3["max_v_spread"], dx=-4, dy=-12, anchor="end",
                     t=f"最高 {n(s3['max_v_spread'])} mV，沒到刻度"),
                dict(ms=120.0, row="up", dx=6, dy=0, t=f"同一刻 {it['n_min_same_step']} 個"),
                dict(ms=s3["spike_ms"][0], row="V", v=-45, dx=-6, dy=-16, anchor="end", t=f"{s3['spike_ms'][0]} ms 過刻度 → 放電")]),
    dict(k=4, title="放電與不反應期", g=[-5, 100], speed=0, text=(
        f"{n(s4['sends'][0][0], 1)} ms 時 {s4['sends'][0][2]} 個同時送，{s4['spike_ms'][0]} ms 放電：水位拉回 V<sub>rest</sub>、g 歸零，"
        f"接下來 {P['t_rfc_ms']} ms 是不反應期（灰底），兩條方程式暫停。{n(s4['sends'][1][0], 1)} ms 又送出 {s4['sends'][1][2]} 個，"
        f"{s4['arrive2_ms']} ms 到達時正在不反應期裡：先存在 g（{n(s4['g_stored'])} mV，不衰減、也不推水位）。"
        f"{s4['rfc_end_ms']} ms 不反應期結束，存著的 g 才開始推水位，{s4['spike_ms'][1]} ms 再放電一次。"
        f"右邊軌跡裡放電畫成一根直線，只是記號：模型裡沒有這個尖峰，水位一過刻度就直接拉回 V<sub>rest</sub>。"),
         notes=[dict(ms=s4["sends"][0][0], row="up", dx=-6, dy=0, anchor="end", t=f"同一刻 {s4['sends'][0][2]} 個"),
                dict(ms=s4["sends"][1][0], row="up", dx=6, dy=0, t=f"再送 {s4['sends'][1][2]} 個"),
                dict(ms=s4["spike_ms"][0], row="V", v=-45, dx=-6, dy=-40, anchor="end", t="放電：拉回 V_rest、g 歸零"),
                dict(ms=s4["arrive2_ms"], row="g", v=s4["g_stored"], dx=8, dy=-4, t="不反應期裡到達：先存在 g"),
                dict(ms=s4["rfc_end_ms"], row="V", v=-52, dx=6, dy=18, t=f"不反應期結束（放電後 {P['t_rfc_ms']} ms）"),
                dict(ms=s4["spike_ms"][1], row="V", v=-45, dx=6, dy=-40, t="再放電一次")]),
    dict(k=5, title="抑制", g=[-35, 65], speed=1, text=(
        f"{n(s5['sends'][0][0], 1)} ms 送 {s5['sends'][0][2]} 個興奮輸入，{s5['spike_ms'][0]} ms 放電。"
        f"{n(s5['sends'][1][0], 1)} ms 同樣 {s5['sends'][1][2]} 個興奮，但同時來了 {s5['sends'][2][2]} 個抑制輸入（每個 −{n(W)} mV，"
        f"上游是 GABA 或麩胺酸的神經元）：g 只淨增 {n(s5['g_net_at_60'])} mV，水位最高 {n(s5['max_v_inh'])} mV，沒放電。"
        f"抑制等於把水龍頭往負的方向開、從桶裡抽水。"),
         notes=[dict(ms=s5["sends"][0][0], row="up", dx=6, dy=0, t=f"{s5['sends'][0][2]} 個興奮"),
                dict(ms=s5["spike_ms"][0], row="V", v=-45, dx=6, dy=-16, t="放電"),
                dict(ms=s5["sends"][1][0], row="up", dx=6, dy=0, t=f"{s5['sends'][1][2]} 個興奮 ＋ {s5['sends'][2][2]} 個抑制"),
                dict(ms=s5["max_v_inh_ms"], row="V", v=s5["max_v_inh"], dx=8, dy=-12, t=f"最高 {n(s5['max_v_inh'])} mV，沒放電")]),
    dict(k=6, title="持續輸入 → 放電率", g=[-5, 90], speed=2, text=(
        f"真實的迴路裡，輸入是好幾顆上游神經元在隨機時刻各自放電。拉「上游顆數」：假設每顆上游平均每秒放電 20 次、每次 {n(W)} mV"
        f"（20 次是為了示範挑的）。上游愈多，水位愈常被推過刻度，這顆神經元每秒放電的次數（放電率）就愈高。"
        f"照作者程式各跑 {dr['seconds']} 秒："
        + "、".join(f"{int(r) // 20} 顆 → {n(v, 1)} Hz" for r, v in dr["in_rate_to_out_hz"].items())
        + "。下面的讀數是最近 1 秒的放電次數，會跟著隨機輸入上下跳。"), notes=[]),
    dict(k=7, title="LC10a 的外部刺激", g=[-5, 90], speed=2, text=(
        f"LC10a 的輸入不是來自上游神經元，而是程式直接刺激（第 4 節、圖 4 第 ⑥ 步）：每 0.1 ms 抽一次籤，抽中的機率 ＝ r × 0.1 ms，"
        f"抽中就把水位直接加 {n(kk['kick_mv'])} mV（不經過 g，所以 g 一直是 0），一定過刻度、馬上放電；V 的圖上紫色小箭頭是抽中的時刻。所以輸出的放電率幾乎就等於設定的 r。"
        f"照作者程式各跑 {kk['seconds']} 秒："
        + "、".join(f"r ＝ {r} → {n(v, 1)} Hz" for r, v in kk["rate_to_out_hz"].items())
        + "。注意：程式檢查「過刻度」時不看是不是在不反應期，所以抽中時就算正在不反應期裡，也會馬上再放電一次；"
          "不反應期擋得住的只有經過 g 的輸入（第 ④ 步）。"), notes=[]),
]

data = dict(v0=P["v0"], vrst=P["v_rst"], vth=P["v_th"], av=P["a_v"], dg=P["decay_g"], rfc=P["rfc_steps"], dly=P["dly_steps"],
            kick=P["poisson_kick_mv"], w=W,
            steps=[dict(k=s["k"], g=s["g"], speed=s["speed"], notes=s["notes"],
                        win=S[str(s["k"])]["window_ms"] if str(s["k"]) in S else 200,
                        vinit=S.get(str(s["k"]), {}).get("v_init"),
                        sends=S.get(str(s["k"]), {}).get("sends", []),
                        expect=S.get(str(s["k"]), {}).get("spike_ms")) for s in STEPS])

# ── 版面（viewBox 900 × 530）──────────────────────────────
# 水桶：x 60–220，水位 −60 mV 在桶底 y 470，−40 mV 在桶口 y 140
BX0, BX1, BY0, BY1 = 60, 220, 140, 470
TX0, TX1 = 368, 884                        # 右邊軌跡的橫向範圍
UP0, UP1 = 46, 70                          # 上游那一排
G0, G1 = 110, 202                          # g 的圖
V0Y, V1Y = 234, 436                        # V 的圖（−40 在上、−60 在下）
OUT0, OUT1 = 460, 478                      # 輸出放電那一排
INK, SOFT, FAINT, BORDER = "#1b2733", "#5a6b7b", "#8b98a5", "#e4e8ee"
BLUE, PURPLE, ORANGE, RED, WATER = "#2563eb", "#9333ea", "#ea580c", "#dc2626", "#7cb6f0"


def by(v):
    return BY1 - (v + 60) / 20 * (BY1 - BY0)


def ty(v):
    return V1Y - (v + 60) / 20 * (V1Y - V0Y)


svg = f'''<svg class="enc-svg lif-svg" viewBox="0 0 900 530" role="img" aria-labelledby="lifTitle" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,-apple-system,'Segoe UI','Microsoft JhengHei',sans-serif">
<title id="lifTitle">漏電整合發放示意：左邊水桶的水位是膜電位 V，水龍頭開度是 g，桶底的洞是漏電；右邊是上游輸入、g、V 與輸出放電隨時間的變化</title>
<defs>
  <clipPath id="lifBucket"><rect x="{BX0 + 3}" y="{BY0 - 60}" width="{BX1 - BX0 - 6}" height="{BY1 - BY0 + 57}"/></clipPath>
  <clipPath id="lifTr"><rect x="{TX0}" y="0" width="{TX1 - TX0}" height="530"/></clipPath>
  <marker id="lifArr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ORANGE}"/></marker>
</defs>
<text x="20" y="24" font-size="15" font-weight="700" fill="{INK}">水桶比喻</text>
<!-- 上游與水管：上游放電後訊號沿管子走 {P['t_dly_ms']} ms 才到水龍頭 -->
<circle cx="30" cy="62" r="11" fill="#fff" stroke="{BLUE}" stroke-width="2"/><text x="30" y="66" font-size="11" text-anchor="middle" fill="{BLUE}">興</text>
<circle cx="30" cy="96" r="11" fill="#fff" stroke="{PURPLE}" stroke-width="2"/><text x="30" y="100" font-size="11" text-anchor="middle" fill="{PURPLE}">抑</text>
<path d="M41 62 H70 V78 H150 M41 96 H70 V78" fill="none" stroke="{FAINT}" stroke-width="6" stroke-linejoin="round" stroke-opacity=".45"/>
<text x="74" y="97" font-size="10" fill="{SOFT}">沿管子走 {P['t_dly_ms']} ms</text>
<rect x="148" y="66" width="34" height="24" rx="5" fill="#cbd5e1" stroke="{SOFT}"/>
<rect x="158" y="90" width="14" height="12" fill="#cbd5e1" stroke="{SOFT}"/>
<g class="lif-handle"><rect x="162" y="52" width="6" height="14" fill="{SOFT}"/><rect x="150" y="47" width="30" height="6" rx="3" fill="{SOFT}"/></g>
<g class="lif-travel"></g>
<text class="lif-gtxt" x="190" y="74" font-size="12" fill="{INK}"></text>
<text x="190" y="90" font-size="11" fill="{SOFT}">水龍頭開度 g</text>
<!-- 水 -->
<g clip-path="url(#lifBucket)"><rect class="lif-stream" x="160" y="102" width="0" height="0" fill="{WATER}"/>
<rect class="lif-water" x="{BX0}" y="{BY1}" width="{BX1 - BX0}" height="0" fill="{WATER}" fill-opacity=".85"/>
<g class="lif-suck"></g></g>
<path d="M{BX0} {BY0 - 6} V{BY1} H{(BX0 + BX1) / 2 - 6} M{(BX0 + BX1) / 2 + 6} {BY1} H{BX1} V{BY0 - 6}" fill="none" stroke="{INK}" stroke-width="3" class="lif-wall"/>
<line x1="{BX0}" x2="{BX1 + 4}" y1="{by(P['v_th'])}" y2="{by(P['v_th'])}" stroke="{RED}" stroke-width="2" stroke-dasharray="6 4"/>
<text x="{BX1 + 8}" y="{by(P['v_th']) - 2}" font-size="12" fill="{RED}">刻度 V<tspan font-size="9" dy="3">th</tspan><tspan dy="-3"> {n(P['v_th'])}</tspan></text>
<line x1="{BX0}" x2="{BX1 + 4}" y1="{by(P['v0'])}" y2="{by(P['v0'])}" stroke="{SOFT}" stroke-width="1.5" stroke-dasharray="3 3"/>
<text x="{BX1 + 8}" y="{by(P['v0']) + 4}" font-size="12" fill="{SOFT}">V<tspan font-size="9" dy="3">rest</tspan><tspan dy="-3"> {n(P['v0'])}</tspan></text>
<text x="{BX1 + 8}" y="{BY0 + 4}" font-size="11" fill="{FAINT}">−40</text>
<text x="{BX1 + 8}" y="{BY1 + 4}" font-size="11" fill="{FAINT}">−60 mV</text>
<text class="lif-vtxt" x="{BX0 + 6}" y="{BY1 - 8}" font-size="12" font-weight="600" fill="{INK}"></text>
<g class="lif-drips"></g>
<text x="{(BX0 + BX1) / 2}" y="{BY1 + 46}" font-size="11" text-anchor="middle" fill="{SOFT}">桶底的洞（漏電）：水位往 V<tspan font-size="8" dy="3">rest</tspan><tspan dy="-3"> 拉</tspan></text>
<g class="lif-over" opacity="0"><text x="{(BX0 + BX1) / 2}" y="{BY0 - 24}" font-size="12" text-anchor="middle" fill="{ORANGE}">↑ 加 {n(kk['kick_mv'])} mV，滿出桶口</text></g>
<g class="lif-fire" opacity="0"><text x="{(BX0 + BX1) / 2}" y="{BY0 - 10}" font-size="18" font-weight="800" text-anchor="middle" fill="{ORANGE}">放電！</text>
<line x1="{BX1 + 2}" y1="{BY0 + 50}" x2="{BX1 + 60}" y2="{BY0 + 50}" stroke="{ORANGE}" stroke-width="3" marker-end="url(#lifArr)"/>
<text x="{BX1 + 8}" y="{BY0 + 44}" font-size="11" fill="{ORANGE}">送給下游</text></g>
<g class="lif-rfc" opacity="0"><rect x="{BX0 + 3}" y="{BY0}" width="{BX1 - BX0 - 6}" height="{BY1 - BY0}" fill="#94a3b8" fill-opacity=".35"/>
<text x="{(BX0 + BX1) / 2}" y="{BY0 + 30}" font-size="13" font-weight="700" text-anchor="middle" fill="{INK}">不反應期</text>
<text x="{(BX0 + BX1) / 2}" y="{BY0 + 48}" font-size="11" text-anchor="middle" fill="{INK}">{P['t_rfc_ms']} ms 內兩式暫停</text>
<rect class="lif-rfcbar" x="{BX0 + 30}" y="{BY0 + 56}" width="0" height="5" fill="{INK}"/></g>
<!-- 右邊：軌跡 -->
<line x1="{TX0 - 30}" x2="{TX0 - 30}" y1="20" y2="510" stroke="{BORDER}"/>
<text x="{TX0}" y="{UP0 - 8}" font-size="12" fill="{SOFT}">上游送出的放電（<tspan fill="{BLUE}">↑ 興奮</tspan>、<tspan fill="{PURPLE}">↓ 抑制</tspan>，數字＝同一刻幾個）</text>
<line x1="{TX0}" x2="{TX1}" y1="{(UP0 + UP1) / 2}" y2="{(UP0 + UP1) / 2}" stroke="{BORDER}"/>
<text x="{TX0}" y="{G0 - 8}" font-size="12" fill="{SOFT}">g：水龍頭開度（mV）</text>
<g class="lif-gaxis"></g>
<text x="{TX0}" y="{V0Y - 8}" font-size="12" fill="{SOFT}">V：膜電位＝水位（mV）</text>
<line x1="{TX0}" x2="{TX1}" y1="{ty(P['v_th'])}" y2="{ty(P['v_th'])}" stroke="{RED}" stroke-dasharray="6 4"/>
<line x1="{TX0}" x2="{TX1}" y1="{ty(P['v0'])}" y2="{ty(P['v0'])}" stroke="{SOFT}" stroke-dasharray="3 3"/>
<text x="{TX0 - 4}" y="{ty(P['v_th']) + 4}" font-size="11" text-anchor="end" fill="{RED}">{n(P['v_th'])}</text>
<text x="{TX0 - 4}" y="{ty(P['v0']) + 4}" font-size="11" text-anchor="end" fill="{SOFT}">{n(P['v0'])}</text>
<text x="{TX0 - 4}" y="{V0Y + 4}" font-size="11" text-anchor="end" fill="{FAINT}">−40</text>
<text x="{TX0 - 4}" y="{V1Y + 4}" font-size="11" text-anchor="end" fill="{FAINT}">−60</text>
<rect x="{TX0}" y="{V0Y}" width="{TX1 - TX0}" height="{V1Y - V0Y}" fill="none" stroke="{BORDER}"/>
<text x="{TX0}" y="{OUT0 - 6}" font-size="12" fill="{SOFT}">輸出放電（送給下游）</text>
<line x1="{TX0}" x2="{TX1}" y1="{OUT1}" y2="{OUT1}" stroke="{BORDER}"/>
<g clip-path="url(#lifTr)"><g class="lif-shade"></g><g class="lif-up"></g><path class="lif-g" fill="none" stroke="{BLUE}" stroke-width="1.8"/>
<path class="lif-v" fill="none" stroke="{INK}" stroke-width="1.8"/><g class="lif-spk"></g><g class="lif-out"></g><g class="lif-notes"></g>
<line class="lif-now" y1="{UP0}" y2="{OUT1}" stroke="{ORANGE}" stroke-opacity=".5"/></g>
<g class="lif-taxis"></g>
</svg>'''

ctl = '''<div class="enc-ctl">
  <button type="button" class="lif-prev">← 上一步</button><button type="button" class="lif-next">下一步 →</button>
  <button type="button" class="lif-play">⏸ 暫停</button><button type="button" class="lif-replay">↻ 重播這一步</button>
  <label>速度 <select class="lif-speed"><option value="0">很慢（1 ms 演 0.2 秒）</option><option value="1">慢（1 ms 演 0.05 秒）</option><option value="2">快（1 ms 演 0.01 秒）</option></select></label>
</div>
<div class="enc-ctl">
  自己送輸入：<button type="button" class="lif-add" data-n="1" data-s="1">＋1 興奮</button><button type="button" class="lif-add" data-n="1" data-s="-1">＋1 抑制</button>
  <button type="button" class="lif-add" data-n="''' + str(it["n_min_same_step"]) + '''" data-s="1">＋''' + str(it["n_min_same_step"]) + ''' 興奮（同一刻）</button>
  <label class="lif-nup">上游顆數 <input type="range" min="0" max="200" step="5" value="50"> <b></b></label>
  <label class="lif-rate">設定放電率 r <input type="range" min="0" max="150" step="5" value="100"> <b></b></label>
</div>'''
steps_html = "\n".join(f'    <li data-k="{s["k"]}"><b>{"①②③④⑤⑥⑦"[s["k"] - 1]} {s["title"]}：</b>{s["text"]}</li>' for s in STEPS)

SCRIPT = r'''<script>
(function(){
const DATA=__DATA__;
const box=document.getElementById('p1lif'),Q=s=>box.querySelector(s),svg=Q('.lif-svg');
const TX0=__TX0__,TX1=__TX1__,UP0=__UP0__,UP1=__UP1__,G0=__G0__,G1=__G1__,V0Y=__V0Y__,V1Y=__V1Y__,OUT0=__OUT0__,OUT1=__OUT1__;
const BX0=__BX0__,BX1=__BX1__,BY0=__BY0__,BY1=__BY1__;
const SPEEDS=[1/200,1/50,1/10];                  // 模擬 1 ms 用真實幾 ms
const BLUE='#2563eb',PURPLE='#9333ea',ORANGE='#ea580c',INK='#1b2733',SOFT='#5a6b7b',FAINT='#8b98a5';
const by=v=>BY1-(v+60)/20*(BY1-BY0),ty=v=>V1Y-(Math.max(-60,Math.min(-40,v))+60)/20*(V1Y-V0Y);
let step=1,cfg,t,v,g,rfc,arrive,sends,spikes,kicks,H,playing=true,ended=false,speed=1,acc=0,last=null,nup=50,rate=100,rnd=Math.random;
const fmt=(x,d)=>x.toFixed(d).replace('-','−');
function send(at,w,n){arrive.set(at+DATA.dly,(arrive.get(at+DATA.dly)||0)+w*n);sends.push({t:at,w,n})}
function reset(){
  cfg=DATA.steps[step-1];t=0;g=0;rfc=0;v=cfg.vinit==null?DATA.v0:cfg.vinit;arrive=new Map();sends=[];spikes=[];kicks=[];H={v:[],g:[]};ended=false;acc=0;
  for(const [ms,w,n] of cfg.sends)send(Math.round(ms/0.1),w,n);
}
// 一步 0.1 ms，順序照抄 lif.py 的 _kernel
function tick1(){
  if(step===6&&nup>0){const pr=nup*20*1e-4;if(rnd()<pr)send(t,DATA.w,1)}
  if(arrive.has(t)){const add=arrive.get(t);arrive.delete(t);g+=add}   // 同一步到達的照送出順序加總（與 Python 相同）
  if(rfc<=0){v+=DATA.av*(DATA.v0-v+g);g*=DATA.dg}
  rfc-=1;
  if(step===7&&rate>0&&rnd()<rate*1e-4){v+=DATA.kick;kicks.push(t)}
  if(v>DATA.vth){v=DATA.vrst;g=0;rfc=DATA.rfc;spikes.push(t)}
  H.v.push(v);H.g.push(g);t++;
  if(H.v.length>40000){const cut=20000;H.v.splice(0,cut);H.g.splice(0,cut);H.off=(H.off||0)+cut}
}
const histAt=(arr,i)=>arr[i-(H.off||0)];
function view(){const W=cfg.win*10;const end=Math.max(W,t);return [end-W,end]}
function draw(now){
  const [va,vb]=view(),W=vb-va,X=i=>TX0+(i-va)/W*(TX1-TX0);
  const [gl,gh]=cfg.g,gy=x=>G1-(Math.max(gl,Math.min(gh,x))-gl)/(gh-gl)*(G1-G0);
  // 軸
  let ga=`<line x1="${TX0}" x2="${TX1}" y1="${gy(0)}" y2="${gy(0)}" stroke="#e4e8ee"/><text x="${TX0-4}" y="${gy(0)+4}" font-size="11" text-anchor="end" fill="${FAINT}">0</text>`;
  ga+=`<text x="${TX0-4}" y="${G0+8}" font-size="11" text-anchor="end" fill="${FAINT}">${gh}</text>`;
  if(gy(0)-G1<-22)ga+=`<text x="${TX0-4}" y="${G1}" font-size="11" text-anchor="end" fill="${FAINT}">${fmt(gl,0)}</text>`;
  Q('.lif-gaxis').innerHTML=ga;
  const span=cfg.win,stepT=span<=50?5:span<=120?10:span<=200?20:50;let ta='';
  for(let ms=Math.ceil(va/10/stepT)*stepT;ms<=vb/10+1e-9;ms+=stepT){const x=X(ms*10);ta+=`<line x1="${x}" x2="${x}" y1="${OUT1}" y2="${OUT1+4}" stroke="${FAINT}"/><text x="${x}" y="${OUT1+16}" font-size="11" text-anchor="middle" fill="${FAINT}">${ms}</text>`}
  ta+=`<text x="${TX1}" y="${OUT1+32}" font-size="11" text-anchor="end" fill="${SOFT}">時間（ms）</text>`;
  Q('.lif-taxis').innerHTML=ta;
  // 軌跡：每個像素取一點，g 的跳升用該段最大絕對值保留
  const i0=Math.max(va,H.off||0),i1=t,k=Math.max(1,Math.floor(W/520));let pv='',pg='';
  for(let i=i0;i<i1;i+=k){let gv=histAt(H.g,i);for(let j=i+1;j<Math.min(i+k,i1);j++){const q=histAt(H.g,j);if(Math.abs(q)>Math.abs(gv))gv=q}
    pv+=(pv?'L':'M')+X(i).toFixed(1)+' '+ty(histAt(H.v,i)).toFixed(1);pg+=(pg?'L':'M')+X(i).toFixed(1)+' '+gy(gv).toFixed(1)}
  Q('.lif-v').setAttribute('d',pv);Q('.lif-g').setAttribute('d',pg);
  // 上游、不反應期灰底、放電
  const mid=(UP0+UP1)/2;let up='';const byT=new Map();
  for(const s of sends){if(s.t>t||s.t<va)continue;const key=s.t+(s.w>0?'+':'-');byT.set(key,(byT.get(key)||{t:s.t,w:s.w,n:0}));byT.get(key).n+=s.n}
  for(const s of byT.values()){const x=X(s.t),c=s.w>0?BLUE:PURPLE,y2=s.w>0?UP0:UP1;
    up+=`<line x1="${x}" x2="${x}" y1="${mid}" y2="${y2}" stroke="${c}" stroke-width="2"/>`;
    if(s.n>1)up+=`<text x="${x+3}" y="${s.w>0?UP0+8:UP1}" font-size="10" fill="${c}">${s.n}</text>`}
  Q('.lif-up').innerHTML=up;
  let sh='',sp='',ou='';
  for(const s of spikes){if(s+DATA.rfc<va)continue;const x=X(s);
    sh+=`<rect x="${x}" y="${V0Y}" width="${Math.max(1,X(s+DATA.rfc)-x)}" height="${V1Y-V0Y}" fill="#94a3b8" fill-opacity=".25"/>`;
    sp+=`<line x1="${x}" x2="${x}" y1="${ty(DATA.vth)}" y2="${V0Y}" stroke="${ORANGE}" stroke-width="2"/><circle cx="${x}" cy="${V0Y}" r="3" fill="${ORANGE}"/>`;
    ou+=`<line x1="${x}" x2="${x}" y1="${OUT0+2}" y2="${OUT1}" stroke="${ORANGE}" stroke-width="2"/>`}
  for(const s of kicks){if(s<va)continue;const x=X(s);sp+=`<path d="M${x-3} ${V0Y+12} L${x} ${V0Y+4} L${x+3} ${V0Y+12}" fill="none" stroke="${PURPLE}" stroke-width="1.5"/>`}
  Q('.lif-shade').innerHTML=sh;Q('.lif-spk').innerHTML=sp;Q('.lif-out').innerHTML=ou;
  // 註記
  let no='';
  for(const m of cfg.notes){const i=Math.round(m.ms*10);if(i>t||i<va)continue;const x=X(i);
    let y=m.row==='up'?UP1+12:m.row==='g'?gy(m.v):ty(m.v);
    if(m.vline)no+=`<line x1="${x}" x2="${x}" y1="${V0Y}" y2="${V1Y}" stroke="${ORANGE}" stroke-dasharray="3 3"/>`;
    if(m.row!=='up')no+=`<circle cx="${x}" cy="${y}" r="3.5" fill="none" stroke="${ORANGE}" stroke-width="1.5"/>`;
    const tx=m.row==='up'?x+(m.anchor==='end'?-4:4):x+m.dx;
    no+=`<text x="${tx}" y="${y+m.dy}" font-size="12" font-weight="600" text-anchor="${m.anchor||'start'}" fill="${ORANGE}" paint-order="stroke" stroke="#fff" stroke-width="4">${m.t}</text>`}
  Q('.lif-notes').innerHTML=no;
  const nx=X(t);const nl=Q('.lif-now');nl.setAttribute('x1',nx);nl.setAttribute('x2',nx);
  // 水桶
  const vy=Math.max(BY0-50,by(Math.min(v,-37.5)));const wa=Q('.lif-water');wa.setAttribute('y',vy);wa.setAttribute('height',BY1-vy);
  Q('.lif-vtxt').textContent='水位 V = '+fmt(v,2)+' mV';
  Q('.lif-gtxt').textContent='g = '+fmt(g,2)+' mV';
  const st=Q('.lif-stream'),wdt=Math.min(14,Math.abs(g)*1.2);
  if(g>0.02){st.setAttribute('x',165-wdt/2);st.setAttribute('width',wdt);st.setAttribute('y',102);st.setAttribute('height',Math.max(0,vy-102));st.setAttribute('fill','#7cb6f0')}
  else st.setAttribute('width',0);
  let su='';if(g<-0.02){const n=Math.min(5,1+Math.floor(-g/6));for(let j=0;j<n;j++){const ph=((now/600+j/n)%1);su+=`<text x="${150+j*8%30}" y="${vy-6-ph*40}" font-size="13" fill="${PURPLE}" opacity="${1-ph}">↑</text>`}
    su+=`<text x="${(BX0+BX1)/2}" y="${vy+18}" font-size="11" text-anchor="middle" fill="${PURPLE}">g 是負的：抽水</text>`}
  Q('.lif-suck').innerHTML=su;
  Q('.lif-handle').setAttribute('transform',`rotate(${Math.max(-40,Math.min(40,g*2))} 165 66)`);
  // 訊號沿管子走
  let tr='';for(const s of byT.values()){if(t-s.t>=DATA.dly)continue;const f=(t-s.t)/DATA.dly,y0=s.w>0?62:96;
    const x=f<.3?41+f/.3*29:70+(f-.3)/.7*80,y=f<.3?y0:78;tr+=`<circle cx="${x}" cy="${y}" r="5" fill="${s.w>0?BLUE:PURPLE}"/>`;if(s.n>1)tr+=`<text x="${x}" y="${y-8}" font-size="10" text-anchor="middle" fill="${s.w>0?BLUE:PURPLE}">×${s.n}</text>`}
  Q('.lif-travel').innerHTML=tr;
  // 漏水：水位高於 V_rest 才往下滴，滴的快慢跟離 V_rest 多遠成正比
  let dp='';const gap=v-DATA.v0,cx=(BX0+BX1)/2;
  if(rfc<=0&&gap>0.05){const n=3,sp2=Math.min(1,gap/5);for(let j=0;j<n;j++){const ph=((now/1000*(0.6+2.4*sp2)+j/n)%1);dp+=`<circle cx="${cx}" cy="${BY1+4+ph*26}" r="${2+2*sp2}" fill="#7cb6f0" opacity="${(1-ph)*Math.min(1,0.3+sp2)}"/>`}}
  else if(rfc<=0&&gap<-0.05)dp+=`<text x="${cx}" y="${BY1+22}" font-size="13" text-anchor="middle" fill="#7cb6f0">↑</text>`;
  Q('.lif-drips').innerHTML=dp;
  const lastS=spikes.length?spikes[spikes.length-1]:-1e9,since=t-lastS;
  Q('.lif-fire').setAttribute('opacity',since<=DATA.rfc+30?1:0);
  Q('.lif-rfc').setAttribute('opacity',rfc>0?1:0);
  Q('.lif-rfcbar').setAttribute('width',rfc>0?(BX1-BX0-60)*rfc/DATA.rfc:0);
  const lastK=kicks.length?kicks[kicks.length-1]:-1e9;Q('.lif-over').setAttribute('opacity',t-lastK<=DATA.rfc+30?1:0);
  // 讀數
  let r='t = '+fmt(t/10,1)+' ms　V = '+fmt(v,2)+' mV　g = '+fmt(g,2)+' mV　輸出放電 '+spikes.length+' 次';
  if(step>=6){const recent=spikes.filter(s=>s>t-10000).length;r+=t>=10000?'　最近 1 秒：'+recent+' Hz':'　（跑滿 1 秒才算放電率：還差 '+fmt((10000-t)/10,0)+' ms）'}
  if(ended)r+='　｜ 這一步播完了：按「重播這一步」，或自己送輸入';
  Q('.enc-read').textContent=r;
}
function frame(ts){
  if(last==null)last=ts;const dt=Math.min(100,ts-last);last=ts;
  if(playing&&!ended){acc+=dt*SPEEDS[speed]*10;let k=Math.floor(acc);acc-=k;
    const W=cfg.win*10;
    while(k-->0){if(step<=5&&t>=W&&!manual){ended=true;break}tick1()}}
  draw(ts);requestAnimationFrame(frame);
}
let manual=false;
function render(){
  for(const li of box.querySelectorAll('.enc-steps li')){const k=+li.dataset.k;li.className=k===step?'on':k<step?'done':''}
  Q('.lif-prev').disabled=step===1;Q('.lif-next').disabled=step===7;
  Q('.lif-nup').style.display=step===6?'':'none';Q('.lif-rate').style.display=step===7?'':'none';
}
function go(s){step=s;speed=DATA.steps[s-1].speed;Q('.lif-speed').value=speed;manual=false;reset();playing=true;Q('.lif-play').textContent='⏸ 暫停';render()}
Q('.lif-prev').onclick=()=>{if(step>1)go(step-1)};
Q('.lif-next').onclick=()=>{if(step<7)go(step+1)};
Q('.lif-replay').onclick=()=>go(step);
Q('.lif-play').onclick=()=>{playing=!playing;Q('.lif-play').textContent=playing?'⏸ 暫停':'▶ 播放'};
Q('.lif-speed').onchange=e=>{speed=+e.target.value};
for(const b of box.querySelectorAll('.lif-add'))b.onclick=()=>{send(t,DATA.w*(+b.dataset.s),+b.dataset.n);manual=true;ended=false;playing=true;Q('.lif-play').textContent='⏸ 暫停'};
const nu=Q('.lif-nup input'),ra=Q('.lif-rate input');
const showN=()=>{nup=+nu.value;Q('.lif-nup b').textContent=nup+' 顆（每秒共 '+(nup*20).toLocaleString()+' 個輸入）'};
const showR=()=>{rate=+ra.value;Q('.lif-rate b').textContent=rate+' Hz'};
nu.oninput=showN;ra.oninput=showR;showN();showR();
for(const li of box.querySelectorAll('.enc-steps li'))li.onclick=()=>go(+li.dataset.k);
// 給單獨頁與自我檢查用：box.lif.set({step, speed, seed})；box.lif.run(ms) 直接算完不播
box.lif={get step(){return step},get spikes(){return spikes.map(s=>+(s/10).toFixed(1))},
  set(o){if(o.seed!=null){let a=o.seed>>>0;rnd=()=>{a=a+0x6D2B79F5|0;let x=Math.imul(a^a>>>15,1|a);x=x+Math.imul(x^x>>>7,61|x)^x;return((x^x>>>14)>>>0)/4294967296}}
    if(o.step)go(Math.max(1,Math.min(7,o.step)));if(o.speed!=null){speed=o.speed;Q('.lif-speed').value=speed}if(o.nup!=null){nu.value=o.nup;showN()}if(o.rate!=null){ra.value=o.rate;showR()}if(o.play!=null){playing=!!o.play;Q('.lif-play').textContent=playing?'⏸ 暫停':'▶ 播放'}},
  run(ms){const end=t+Math.round(ms*10);while(t<end)tick1();if(step<=5&&t>=cfg.win*10)ended=true;draw(0)}};
go(1);requestAnimationFrame(frame);
})();
</script>'''
for k, val in dict(TX0=TX0, TX1=TX1, UP0=UP0, UP1=UP1, G0=G0, G1=G1, V0Y=V0Y, V1Y=V1Y, OUT0=OUT0, OUT1=OUT1,
                   BX0=BX0, BX1=BX1, BY0=BY0, BY1=BY1).items():
    SCRIPT = SCRIPT.replace(f"__{k}__", str(val))
frag = (f'<div class="enc lif" id="p1lif">\n<div class="lif-wrap">{svg}</div>\n<div class="enc-read" aria-live="off"></div>\n{ctl}\n'
        f'<ol class="enc-steps">\n{steps_html}\n  </ol>\n</div>\n'
        + SCRIPT.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
page = open(PAGE, encoding="utf-8").read()
new, cnt = re.subn(r"<!-- lif:start -->.*?<!-- lif:end -->", lambda m: "<!-- lif:start -->\n" + frag + "\n<!-- lif:end -->", page, flags=re.S)
assert cnt == 1, "頁面裡找不到 <!-- lif:start --> … <!-- lif:end -->"
open(PAGE, "w", encoding="utf-8").write(new)
print("圖 1（漏電整合發放）已寫入 part1-what.html")

STANDALONE = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>漏電整合發放｜果蠅玩 Doom</title>
<style>
/* PART 1 圖 1 的單獨頁：給簡報嵌入（PowerPoint 網頁增益集）或離線用瀏覽器全螢幕開。由 scripts/make_lif_anim.py 產生，不要手改。
   單一檔案、不依賴其他檔，file:// 也能用。版面照視窗大小縮放，16:9 剛好填滿。
   網址參數：s=1–7 第幾步；speed=0–2 很慢／慢／快；nup=0–200 第 6 步上游顆數；rate=0–150 第 7 步的 r；seed 固定隨機；
   at=毫秒 直接算到那一刻並暫停；d=1 顯示說明；clean=1 只留圖 */
:root{--ink:#1b2733;--soft:#5a6b7b;--faint:#8b98a5;--border:#e4e8ee;--panel:#f7f8fa;--accent:#2563eb;--accent-soft:#eef3fe;--fs:clamp(11px,1.05vw,24px)}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:#fff;color:var(--ink);font-size:var(--fs);line-height:1.6;overflow:hidden;
  font-family:-apple-system,"Segoe UI","Noto Sans TC","Microsoft JhengHei","PingFang TC",Roboto,Helvetica,Arial,sans-serif;
  display:flex;flex-direction:column;gap:.4em;padding:.6em 1em}
#p1lif{display:contents}
.enc-ctl{order:0;display:flex;flex-wrap:wrap;align-items:center;gap:.4em .9em;color:var(--soft)}
.name{font-weight:700;color:var(--ink);margin-right:.3em}
.enc-ctl button,.enc-ctl select{font:inherit;font-size:.95em;padding:.2em .8em;border:1px solid var(--border);border-radius:8px;background:var(--panel);color:var(--ink);cursor:pointer}
.enc-ctl button:disabled{opacity:.4;cursor:default}
.enc-ctl button:hover:not(:disabled){border-color:var(--accent)}
.enc-ctl button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.enc-ctl button[aria-pressed="true"]{background:var(--ink);color:#fff;border-color:var(--ink)}
.enc-ctl label{display:inline-flex;align-items:center;gap:.4em}
.enc-ctl input[type=range]{width:8em}
.right{margin-left:auto;display:flex;gap:.4em}
.lif-wrap{order:1;flex:1 1 0;min-height:0;display:flex}
.lif-svg{width:100%;height:100%;display:block;font-size:16px}
.lif-svg g{transition:opacity .3s}
.enc-read{order:2;margin:0;font-family:Menlo,Consolas,monospace;font-size:.9em;color:var(--ink);background:var(--panel);border-radius:8px;padding:.2em .7em}
.enc-steps{order:3;display:none;margin:0;padding:0;list-style:none;font-size:.95em;max-height:24vh;overflow:auto}
body.showdesc .enc-steps,body.showdesc .figsrc{display:block}
.figsrc{order:4;display:none;margin:0;font-size:.8em;color:var(--faint)}
.enc-steps li{display:none;padding:.2em .7em;border-left:3px solid var(--accent);background:var(--accent-soft)}
.enc-steps li.on{display:block}
body.clean{padding:0}
body.clean .enc-ctl,body.clean .enc-read,body.clean .enc-steps,body.clean .figsrc{display:none!important}
</style>
</head>
<body>
%FRAG%
<p class="figsrc">更新規則照抄 fruitfly-lab 的 flycircuit/lif.py（_kernel）；參數讀 circuit/meta.json，步驟裡的數字在 out/lif_fig.json。說明全文：https://marginli.github.io/bsc-flysimu/part1-what.html#s2</p>
<script>
(function(){
  var box=document.getElementById("p1lif"),q=new URLSearchParams(location.search),ctl=box.querySelector(".enc-ctl");
  ctl.insertAdjacentHTML("afterbegin",'<span class="name">漏電整合發放：一顆神經元怎麼整合輸入、決定放電</span>');
  ctl.insertAdjacentHTML("beforeend",'<span class="right"><button type="button" id="lifDesc" aria-pressed="false">說明</button><button type="button" id="lifFull">全螢幕</button></span>');
  if(q.get("clean")==="1")document.body.classList.add("clean");
  if(q.get("d")==="1")document.body.classList.add("showdesc");
  var o={};
  if(q.get("seed"))o.seed=+q.get("seed");if(q.get("s"))o.step=+q.get("s");
  box.lif.set(o);o={};
  if(q.get("speed"))o.speed=+q.get("speed");if(q.get("nup"))o.nup=+q.get("nup");if(q.get("rate"))o.rate=+q.get("rate");
  box.lif.set(o);
  if(q.get("at")){box.lif.set({play:false});box.lif.run(+q.get("at"))}
  var dBtn=document.getElementById("lifDesc"),fs=document.getElementById("lifFull"),de=document.documentElement;
  dBtn.onclick=function(){dBtn.setAttribute("aria-pressed",document.body.classList.toggle("showdesc"))};
  dBtn.setAttribute("aria-pressed",document.body.classList.contains("showdesc"));
  if(!(document.fullscreenEnabled||document.webkitFullscreenEnabled))fs.style.display="none";
  fs.onclick=function(){if(document.fullscreenElement||document.webkitFullscreenElement)(document.exitFullscreen||document.webkitExitFullscreen).call(document);else(de.requestFullscreen||de.webkitRequestFullscreen).call(de)};
  var Q=function(s){return box.querySelector(s)},next=Q(".lif-next"),prev=Q(".lif-prev");
  document.addEventListener("keydown",function(e){
    if(e.altKey||e.ctrlKey||e.metaKey)return;
    if(e.target.tagName==="INPUT"&&e.target.type==="range"&&(e.key==="ArrowLeft"||e.key==="ArrowRight"))return;
    if(e.target.tagName==="SELECT")return;
    var k=e.key,sp=Q(".lif-speed");
    if(k==="ArrowRight"||k==="PageDown"){e.preventDefault();if(!next.disabled)next.click()}
    else if(k==="ArrowLeft"||k==="PageUp"){e.preventDefault();if(!prev.disabled)prev.click()}
    else if(k==="Home"){e.preventDefault();box.lif.set({step:1})}
    else if(k==="End"){e.preventDefault();box.lif.set({step:7})}
    else if("1234567".indexOf(k)>=0&&k.length===1)box.lif.set({step:+k});
    else if(k===" "||k==="p"||k==="P"){e.preventDefault();Q(".lif-play").click()}
    else if(k==="r"||k==="R")Q(".lif-replay").click();
    else if(k==="e"||k==="E")box.querySelectorAll(".lif-add")[0].click();
    else if(k==="i"||k==="I")box.querySelectorAll(".lif-add")[1].click();
    else if(k==="b"||k==="B")box.querySelectorAll(".lif-add")[2].click();
    else if(k==="s"||k==="S"){sp.value=(+sp.value+1)%3;sp.dispatchEvent(new Event("change"))}
    else if(k==="d"||k==="D")dBtn.click();
    else if(k==="f"||k==="F")fs.click();
  });
})();
</script>
</body>
</html>
"""
open(os.path.join(D, "lif.html"), "w", encoding="utf-8").write(STANDALONE.replace("%FRAG%", frag))
print("單獨頁 lif.html 已寫入")
