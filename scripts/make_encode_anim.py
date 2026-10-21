"""PART 1 第 4 節〈輸入編碼〉的圖 3：遊戲畫面 → 方位角 → 哪一眼 → 哪幾顆 LC10a → 多強 → 隨機放電，六步可逐步看、可拖。
數字全部讀 out/encode_fig.json（scripts/encode_fig_data.py 從作者 fly_doom.py 抓的常數與 234 顆 LC10a 的偏好位置）；
瀏覽器裡的算法照抄作者的 enemies() 與 stim_rates()。
產出：part1-what.html 裡 <!-- encode:start --> … <!-- encode:end --> 之間的片段。圖的文字要改在這裡，不要直接改頁面。
用法：python3 scripts/make_encode_anim.py"""
import json
import math
import os
import re

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = json.load(open(os.path.join(D, "out/encode_fig.json")))
C = E["const"]
PAGE = os.path.join(D, "part1-what.html")

# ── 版面（viewBox 900 × 622）──────────────────────────────
SX, SY, K = 30, 62, 1.15                       # 遊戲畫面左上角與放大倍數（320×240 → 368×276）
SW, SH = C["screen_w"] * K, C["screen_h"] * K
FX, FY, FR = 668, 330, 178                     # 果蠅俯視圖：圓心與半徑
MID, SPAN, GAP = 450, 372, 8                   # LC10a 帶：正前方在 MID，外圍在 MID ± (GAP + SPAN)
CURVE_BASE, CURVE_H = 478, 48                  # 調諧曲線的基線與滿格高度
DOT_Y, DOT_R, DOT_D = 540, 2.7, 6.2            # LC10a 點的中線、半徑、最小間距


def dot_x(side, p):
    return MID - GAP - p * SPAN if side == "L" else MID + GAP + p * SPAN


def swarm():
    """偏好位置相同的有幾十顆（0、0.5、1），用二維蜂群排開：x 盡量不動，y 往上下擠。"""
    placed, out = [], {"L": [], "R": []}
    cand = sorted(((dx, dy) for dx in range(-21, 22, 3) for dy in range(-48, 49, 3)), key=lambda t: 2.5 * t[0] ** 2 + t[1] ** 2)
    items = sorted(((dot_x(s, p), s, i) for s in "LR" for i, p in enumerate(E["pref_ecc"][s])), key=lambda t: t[0])
    pos = {}
    for x, s, i in items:
        for dx, dy in cand:
            nx, ny = x + dx, DOT_Y + dy
            if all((nx - a) ** 2 + (ny - b) ** 2 >= DOT_D ** 2 for a, b in placed if abs(nx - a) < DOT_D):
                break
        placed.append((nx, ny))
        pos[(s, i)] = (round(nx, 1), round(ny, 1))
    for s in "LR":
        out[s] = [pos[(s, i)] for i in range(len(E["pref_ecc"][s]))]
    return out


DOTS = swarm()
INK, SOFT, FAINT, BORDER = "#1b2733", "#5a6b7b", "#8b98a5", "#e4e8ee"
BLUE, AMBER, PURPLE, YEL = "#2563eb", "#d97706", "#9333ea", "#facc15"


def arc_pt(az, r=FR):
    a = math.radians(az)
    return FX + r * math.sin(a), FY - r * math.cos(a)


def wedge(a0, a1, r=FR):
    x0, y0 = arc_pt(a0, r)
    x1, y1 = arc_pt(a1, r)
    large = 1 if a1 - a0 > 180 else 0
    return f"M{FX},{FY} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z"


B = C["BINO"]
S = []
S.append('<svg class="enc-svg" viewBox="0 0 900 622" role="img" aria-labelledby="encTitle" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,-apple-system,\'Segoe UI\',\'Microsoft JhengHei\',sans-serif">')
S.append('<title id="encTitle">輸入編碼示意：遊戲回報敵人方框的位置與大小，換成方位角，決定刺激哪一眼、哪幾顆 LC10a、多強，最後變成隨機放電</title>')
S.append(f'<text id="encHead" x="24" y="32" font-size="17" font-weight="700" fill="{INK}"></text>')

# A：遊戲畫面
S.append('<g id="encA">')
S.append(f'<text x="{SX}" y="{SY - 10}" font-size="13" font-weight="700" fill="{SOFT}">遊戲畫面（{C["screen_w"]}×{C["screen_h"]} 像素，橫向 90°）</text>')
S.append(f'<rect x="{SX}" y="{SY}" width="{SW:.0f}" height="{SH / 2:.0f}" fill="#3b4048"/>')
S.append(f'<rect x="{SX}" y="{SY + SH / 2:.0f}" width="{SW:.0f}" height="{SH / 2:.0f}" fill="#6b5b47"/>')
S.append(f'<line x1="{SX + SW / 2:.1f}" y1="{SY}" x2="{SX + SW / 2:.1f}" y2="{SY + SH:.0f}" stroke="#fff" stroke-opacity=".35" stroke-dasharray="4 4"/>')
S.append('<g id="encMon"></g><g id="encMon2"></g>')
S.append(f'<rect x="{SX}" y="{SY}" width="{SW:.0f}" height="{SH:.0f}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
S.append('</g>')

# A 下方：三把尺
ax_y = SY + SH + 16
S.append('<g id="encAx" font-size="11" fill="' + SOFT + '">')
rows = [("像素", ["0", str(C["screen_center"]), str(C["screen_w"])]),
        ("Doom 角度", [f"−{C['HALF_FOV_DOOM']:.0f}°", "0°", f"+{C['HALF_FOV_DOOM']:.0f}°"]),
        ("果蠅方位角", ["−90°", "0°", "+90°"])]
for j, (name, labs) in enumerate(rows):
    y = ax_y + j * 17
    bold = ' font-weight="700" id="encAxFly"' if j == 2 else ""
    S.append(f'<text x="{SX + SW + 6:.0f}" y="{y + 4}"{bold}>{name}</text>')
    for k, lab in enumerate(labs):
        anchor = ["start", "middle", "end"][k]
        hi = f' font-weight="700" fill="{INK}"' if j == 2 else ""
        S.append(f'<text x="{SX + k * SW / 2:.1f}" y="{y + 4}" text-anchor="{anchor}"{hi}>{lab}</text>')
S.append(f'<path id="encMark" d="M0,0 L5,8 L-5,8 Z" fill="{INK}"/>')
S.append('</g>')

# B：果蠅俯視
S.append('<g id="encB">')
S.append(f'<text x="{FX}" y="{SY - 10}" text-anchor="middle" font-size="13" font-weight="700" fill="{SOFT}">果蠅的視野（從上往下看，頭朝上）</text>')
S.append(f'<path id="encEyeL" d="{wedge(-90, 0)}" fill="{BLUE}" fill-opacity=".06" stroke="{BORDER}"/>')
S.append(f'<path id="encEyeR" d="{wedge(0, 90)}" fill="{AMBER}" fill-opacity=".06" stroke="{BORDER}"/>')
S.append(f'<path id="encBino" d="{wedge(-B, B)}" fill="{PURPLE}" fill-opacity=".10"/>')
for az in (-90, -45, 0, 45, 90):
    x, y = arc_pt(az, FR + 14)
    S.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="{"end" if az < 0 else "start" if az > 0 else "middle"}" font-size="11" fill="{SOFT}">{"+" if az > 0 else "−" if az < 0 else ""}{abs(az)}°</text>')
S.append(f'<text x="{FX - 92}" y="{FY - 40}" text-anchor="middle" font-size="13" font-weight="700" fill="{BLUE}">左眼</text>')
S.append(f'<text x="{FX + 92}" y="{FY - 40}" text-anchor="middle" font-size="13" font-weight="700" fill="{AMBER}">右眼</text>')
bx, by = arc_pt(0, FR + 30)
S.append(f'<text id="encBinoLab" x="{bx:.1f}" y="{by + 2:.1f}" text-anchor="middle" font-size="11" fill="{PURPLE}">兩眼都看到 ±{B:.0f}°</text>')
S.append(f'<line id="encRay2" x1="{FX}" y1="{FY}" x2="{FX}" y2="{FY - FR}" stroke="{FAINT}" stroke-width="2" stroke-dasharray="5 4" visibility="hidden"/>')
S.append(f'<line id="encRay" x1="{FX}" y1="{FY}" x2="{FX}" y2="{FY - FR}" stroke="{INK}" stroke-width="2.5"/>')
S.append(f'<circle id="encRayDot" cx="{FX}" cy="{FY - FR}" r="6" fill="#8b3a2b"/>')
S.append(f'<ellipse cx="{FX}" cy="{FY + 2}" rx="9" ry="15" fill="{INK}"/><circle cx="{FX}" cy="{FY - 15}" r="6" fill="{INK}"/>')
S.append(f'<text id="encAzTxt" x="{FX}" y="{FY + 34}" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}"></text>')
S.append('</g>')

# C：LC10a 帶
S.append('<g id="encC">')
S.append(f'<text x="24" y="{CURVE_BASE - CURVE_H - 14}" font-size="13" font-weight="700" fill="{SOFT}">234 顆 LC10a，依作者指定的「偏好位置」排開（不是真的視野位置）</text>')
S.append(f'<line x1="{dot_x("L", 1) - 6:.0f}" y1="{CURVE_BASE}" x2="{dot_x("R", 1) + 6:.0f}" y2="{CURVE_BASE}" stroke="{BORDER}"/>')
S.append(f'<line x1="{MID}" y1="{CURVE_BASE - CURVE_H - 4}" x2="{MID}" y2="{DOT_Y + 56}" stroke="{FAINT}" stroke-dasharray="3 3"/>')
S.append(f'<path id="encCurveL" d="" fill="{BLUE}" fill-opacity=".14" stroke="{BLUE}" stroke-width="1.5"/>')
S.append(f'<path id="encCurveR" d="" fill="{AMBER}" fill-opacity=".14" stroke="{AMBER}" stroke-width="1.5"/>')
S.append(f'<text id="encCurveLab" x="0" y="0" font-size="12" font-weight="700" fill="{INK}" text-anchor="end"></text>')
S.append('<g id="encDots">')
for s in "LR":
    for i, (x, y) in enumerate(DOTS[s]):
        S.append(f'<circle cx="{x}" cy="{y}" r="{DOT_R}"/>')
S.append('</g>')
ly = DOT_Y + 70
S.append(f'<text x="{dot_x("L", 1):.0f}" y="{ly}" font-size="11" fill="{SOFT}">← 外圍</text>')
S.append(f'<text x="{MID}" y="{ly}" text-anchor="middle" font-size="11" fill="{SOFT}">正前方</text>')
S.append(f'<text x="{dot_x("R", 1):.0f}" y="{ly}" text-anchor="end" font-size="11" fill="{SOFT}">外圍 →</text>')
S.append(f'<text x="{(dot_x("L", 0.5)):.0f}" y="{ly}" text-anchor="middle" font-size="12" font-weight="700" fill="{BLUE}">左眼 {E["pref_summary"]["L"]["n"]} 顆</text>')
S.append(f'<text x="{(dot_x("R", 0.5)):.0f}" y="{ly}" text-anchor="middle" font-size="12" font-weight="700" fill="{AMBER}">右眼 {E["pref_summary"]["R"]["n"]} 顆</text>')
S.append('</g>')
S.append('</svg>')
svg = "\n".join(S)

STEPS = [
    ("① 遊戲回報方框", "ViZDoom 不給模型看像素，而是回報畫面上每個物件的<b>方框</b>（標籤）：左緣、寬、高，單位是像素。程式只取敵人方框的<b>橫向中心</b>與<b>高度</b>。"),
    ("② 換成方位角", f"橫向中心從 0 到 {C['screen_w']} 像素，對到 Doom 的 −{C['HALF_FOV_DOOM']:.0f}° 到 +{C['HALF_FOV_DOOM']:.0f}°，再乘 {C['FLY_SCALE']:.0f}，攤成果蠅的 −90° 到 +90°。"),
    ("③ 哪一眼", f"方位角是正的刺激右眼的 LC10a，負的刺激左眼；在正前方 ±{B:.0f}° 以內兩眼都刺激。另一眼的 LC10a 完全不刺激。"),
    ("④ 哪幾顆", f"每顆 LC10a 有一個作者指定的偏好位置（下排的橫軸）。敵人方位愈接近它的偏好位置，刺激愈強，像一座鐘形的山：差 0 是滿格，差 {C['SIGMA']} 剩 61%，差 0.5 剩 25%。"),
    ("⑤ 多強", f"強度 ＝ {C['strength_base']} ＋ 方框高度 ÷ {C['strength_div']}，最多 1。敵人愈近、方框愈高，整座山愈高；高 {E['height_full']} 像素以上就是滿格（最強那顆每秒 {C['MAX_RATE']:.0f} 次）。"),
    ("⑥ 隨機放電", f"山的高度只是「平均每秒放電幾次」。每 {C['dt_ms']} ms 依這個機率擲一次骰子決定放不放電，所以放電時刻每次都不同。畫面上放慢 {E['display']['slow']} 倍播放。"),
]
steps_html = "\n".join(f'    <li data-k="{k + 1}"><b>{t}</b>：{d}</li>' for k, (t, d) in enumerate(STEPS))

data = {"C": C, "pref": E["pref_ecc"], "dots": DOTS, "slowMs": E["display"]["model_ms_per_frame"], "frameMs": E["display"]["frame_ms"],
        "geo": {"SX": SX, "SY": SY, "K": K, "SW": SW, "SH": SH, "FX": FX, "FY": FY, "FR": FR, "MID": MID, "SPAN": SPAN, "GAP": GAP,
                "CB": CURVE_BASE, "CH": CURVE_H, "AXY": ax_y + 2 * 17 - 10, "R": DOT_R},
        "heads": [t for t, _ in STEPS]}

SCRIPT = r"""<script>
(()=>{
const D=__DATA__,C=D.C,G=D.geo,$=s=>document.querySelector('#p1enc '+s),NS="http://www.w3.org/2000/svg";
const box=document.getElementById('p1enc');if(!box)return;
const dots=[...$('#encDots').children],side=dots.map((_,i)=>i<D.pref.L.length?'L':'R'),pref=[...D.pref.L,...D.pref.R];
const flash=new Float32Array(dots.length);
let step=1,cx=232,h=26,two=false,walk=false,t0=null,acc=0,last=0,reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
// 照抄作者 enemies()：方位角與強度
const az=c=>Math.max(-90,Math.min(90,(c-C.screen_center)/C.screen_center*C.HALF_FOV_DOOM*C.FLY_SCALE));
const strength=hh=>Math.min(1,C.strength_base+hh/C.strength_div);
const targets=()=>{const t=[[az(cx),strength(h),cx,h]];if(two)t.push([az(70),strength(14),70,14]);return t};
// 照抄作者 stim_rates()：多個敵人疊加，每顆最多 MAX_RATE
function rates(){
  const r=new Float32Array(dots.length);
  for(const [a,st] of targets()){
    const ecc=Math.min(Math.abs(a)/90,1),sides=Math.abs(a)<C.BINO?['L','R']:(a>0?['R']:['L']);
    for(let i=0;i<dots.length;i++)if(sides.includes(side[i])){
      const tune=Math.exp(-((pref[i]-ecc)**2)/(2*C.SIGMA**2));r[i]=Math.min(C.MAX_RATE,r[i]+C.MAX_RATE*st*tune)}
  }
  return r;
}
function monster(g,c,hh,main){
  g.innerHTML='';const k=G.K,w=Math.round(hh*0.6),x=G.SX+c*k,feet=Math.min(G.SY+G.SH-6,G.SY+G.SH/2+hh*k*0.9),top=feet-hh*k;
  const add=(t,a)=>{const e=document.createElementNS(NS,t);for(const n in a)e.setAttribute(n,a[n]);g.appendChild(e);return e};
  add('rect',{x:x-w*k*0.42,y:top+hh*k*0.3,width:w*k*0.84,height:hh*k*0.7,rx:hh*k*0.12,fill:main?'#8b3a2b':'#6d3a30'});
  add('circle',{cx:x,cy:top+hh*k*0.18,r:hh*k*0.17,fill:main?'#8b3a2b':'#6d3a30'});
  add('circle',{cx:x-hh*k*0.06,cy:top+hh*k*0.16,r:Math.max(1,hh*k*0.035),fill:'#fde047'});
  add('circle',{cx:x+hh*k*0.06,cy:top+hh*k*0.16,r:Math.max(1,hh*k*0.035),fill:'#fde047'});
  if(step>=1){
    add('rect',{x:x-w*k/2,y:top,width:w*k,height:hh*k,fill:'none',stroke:'#facc15','stroke-width':1.6,'stroke-dasharray':'4 3'});
    const lab=add('text',{x:x,y:top-6,'text-anchor':'middle','font-size':11,'font-weight':700,fill:'#facc15'});
    lab.textContent=main?`中心 ${c} px・高 ${hh} px`:`第二個敵人`;
    if(x-w*k/2<G.SX+60)lab.setAttribute('text-anchor','start'),lab.setAttribute('x',G.SX+4);
    if(x+w*k/2>G.SX+G.SW-60)lab.setAttribute('text-anchor','end'),lab.setAttribute('x',G.SX+G.SW-4);
  }
}
const sx=(s,p)=>s==='L'?G.MID-G.GAP-p*G.SPAN:G.MID+G.GAP+p*G.SPAN;
function curve(s,list){
  if(!list.length)return'';let d='';
  for(let j=0;j<=60;j++){const p=j/60;let v=0;for(const [ecc,st] of list)v+=C.MAX_RATE*st*Math.exp(-((p-ecc)**2)/(2*C.SIGMA**2));v=Math.min(C.MAX_RATE,v);
    d+=(j?'L':'M')+sx(s,p).toFixed(1)+','+(G.CB-v/C.MAX_RATE*G.CH).toFixed(1)}
  return d+`L${sx(s,1).toFixed(1)},${G.CB}L${sx(s,0).toFixed(1)},${G.CB}Z`;
}
let R=new Float32Array(dots.length);
function render(){
  const T=targets(),a=T[0][0],st=T[0][1];
  $('#encHead').textContent=`第 ${step} 步　`+D.heads[step-1].slice(2);
  monster($('#encMon'),cx,h,true);two?monster($('#encMon2'),70,14,false):$('#encMon2').innerHTML='';
  // 尺上的記號與俯視圖的射線
  $('#encMark').setAttribute('transform',`translate(${G.SX+cx*G.K},${G.SY+G.SH+1})`);
  const ray=(id,dot,aa)=>{const r=Math.PI*aa/180,x=G.FX+G.FR*Math.sin(r),y=G.FY-G.FR*Math.cos(r);const L=$(id);L.setAttribute('x2',x);L.setAttribute('y2',y);if(dot){$(dot).setAttribute('cx',x);$(dot).setAttribute('cy',y)}};
  ray('#encRay','#encRayDot',a);
  $('#encRay2').setAttribute('visibility',two&&step>=2?'visible':'hidden');ray('#encRay2',null,az(70));
  $('#encAzTxt').textContent=`方位角 ${a>0?'+':a<0?'−':''}${Math.abs(a).toFixed(1)}°`;
  const sidesOf=aa=>Math.abs(aa)<C.BINO?['L','R']:(aa>0?['R']:['L']),on=new Set(T.flatMap(t=>sidesOf(t[0])));
  $('#encEyeL').setAttribute('fill-opacity',step>=3&&on.has('L')?.28:.06);
  $('#encEyeR').setAttribute('fill-opacity',step>=3&&on.has('R')?.28:.06);
  $('#encBino').setAttribute('fill-opacity',step>=3&&Math.abs(a)<C.BINO?.45:.10);
  // 鐘形的山：④ 起顯示；⑤ 起高度乘上強度（④ 先固定用滿格看形狀）
  const k4=step===4;const by={L:[],R:[]};
  for(const [aa,s2] of T)for(const sd of sidesOf(aa))by[sd].push([Math.min(Math.abs(aa)/90,1),k4?1:s2]);
  for(const sd of ['L','R'])$('#encCurve'+sd).setAttribute('d',step>=4?curve(sd,by[sd]):'');
  const lab=$('#encCurveLab');
  if(step>=4){const sd=sidesOf(a)[sidesOf(a).length-1],ecc=Math.min(Math.abs(a)/90,1),pk=Math.min(C.MAX_RATE,C.MAX_RATE*(k4?1:st));
    lab.setAttribute('x',876);lab.setAttribute('y',G.CB-G.CH-14);
    lab.textContent=k4?'鐘形曲線的形狀（還沒乘強度）':`山頂 ${pk.toFixed(0)} 次／秒（強度 ${st.toFixed(2)}）`}else lab.textContent='';
  R=rates();
  paintDots();
  for(const li of box.querySelectorAll('.enc-steps li'))li.classList.toggle('on',+li.dataset.k===step),li.classList.toggle('done',+li.dataset.k<step);
  const op=(id,v)=>$(id).style.opacity=v;
  op('#encB',step>=2?1:.15);op('#encAx',step>=2?1:.15);op('#encC',step>=3?1:.15);
  box.querySelector('.enc-prev').disabled=step===1;box.querySelector('.enc-next').disabled=step===6;
  const ro=box.querySelector('.enc-read');
  ro.textContent=`中心 ${cx} px → 方位角 ${a>0?'+':a<0?'−':''}${Math.abs(a).toFixed(1)}° → `+
    (Math.abs(a)<C.BINO?'兩眼':a>0?'右眼':'左眼')+` → 強度 ${st.toFixed(2)} → 最強那顆 ${Math.max(...R).toFixed(0)} 次／秒`+(two?'（含第二個敵人）':'');
}
function paintDots(){
  for(let i=0;i<dots.length;i++){
    const c=side[i]==='L'?'#2563eb':'#d97706',d=dots[i];let v=step>=4?R[i]/C.MAX_RATE:0;
    if(step===4){/* ④ 只看形狀：除掉強度 */const st=strength(h);v=Math.min(1,v/st)}
    const lit=step>=3&&R[i]>0;
    if(step>=6&&flash[i]>0){d.setAttribute('fill','#111827');d.setAttribute('r',G.R+2.2*flash[i]);d.setAttribute('fill-opacity',1);continue}
    d.setAttribute('r',G.R);
    if(step===3){d.setAttribute('fill',lit?c:'#cbd5e1');d.setAttribute('fill-opacity',lit?.75:1);continue}
    d.setAttribute('fill',v>0.02?c:'#cbd5e1');d.setAttribute('fill-opacity',v>0.02?0.2+0.8*v:1);
  }
}
function tick(now){
  if(t0===null)t0=now,last=now;const dt=now-last;last=now;
  if(walk&&!reduce){const t=(now-t0)/1000;cx=Math.round(160+148*Math.sin(t*0.45));h=Math.round(22+18*Math.sin(t*0.27+1));syncSliders();render()}
  if(step>=6){acc+=dt;
    while(acc>=D.frameMs){acc-=D.frameMs;
      for(let i=0;i<dots.length;i++){flash[i]=Math.max(0,flash[i]-0.5);const pr=1-Math.exp(-R[i]*D.slowMs/1000);if(Math.random()<pr)flash[i]=1}}
    paintDots()}
  requestAnimationFrame(tick);
}
function syncSliders(){box.querySelector('.enc-cx').value=cx;box.querySelector('.enc-h').value=h}
box.querySelector('.enc-prev').onclick=()=>{if(step>1){step--;flash.fill(0);render()}};
box.querySelector('.enc-next').onclick=()=>{if(step<6){step++;render()}};
box.querySelector('.enc-cx').oninput=e=>{cx=+e.target.value;walk=false;wb.textContent='▶ 讓敵人走動';render()};
box.querySelector('.enc-h').oninput=e=>{h=+e.target.value;walk=false;wb.textContent='▶ 讓敵人走動';render()};
const wb=box.querySelector('.enc-walk');wb.onclick=()=>{walk=!walk;wb.textContent=walk?'⏸ 停住':'▶ 讓敵人走動'};
box.querySelector('.enc-two').onchange=e=>{two=e.target.checked;render()};
for(const li of box.querySelectorAll('.enc-steps li'))li.onclick=()=>{step=+li.dataset.k;render()};
syncSliders();render();requestAnimationFrame(tick);
})();
</script>"""

ctl = f'''<div class="enc" id="p1enc">
{svg}
  <div class="enc-ctl">
    <button class="enc-prev" type="button">◀ 上一步</button>
    <button class="enc-next" type="button">下一步 ▶</button>
    <button class="enc-walk" type="button">▶ 讓敵人走動</button>
    <label>敵人位置 <input class="enc-cx" type="range" min="0" max="{C['screen_w']}" step="1"></label>
    <label>敵人大小 <input class="enc-h" type="range" min="{C['min_height']}" max="70" step="1"></label>
    <label><input class="enc-two" type="checkbox"> 加第二個敵人</label>
  </div>
  <p class="enc-read" aria-live="polite"></p>
  <ol class="enc-steps">
{steps_html}
  </ol>
</div>'''
frag = ctl + "\n" + SCRIPT.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))

page = open(PAGE, encoding="utf-8").read()
new = re.sub(r"(<!-- encode:start -->\n).*?(<!-- encode:end -->)", lambda m: m.group(1) + frag + "\n" + m.group(2), page, flags=re.S)
assert new != page or frag in page, "找不到 <!-- encode:start --> 標記"
open(PAGE, "w", encoding="utf-8").write(new)
print("圖 3 已寫入 part1-what.html")
