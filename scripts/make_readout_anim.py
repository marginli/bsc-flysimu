"""PART 1 第 4 節〈讀出規則〉的圖 5：八群放電率 → 轉向訊號 → 跟門檻比 → 按鍵，七步可逐步看。
數字全部讀 out/readout_fig.json（scripts/readout_fig_data.py：作者 fly_doom.py 的常數、calibration_fly.json 的校準表與閾值、
PART 5 那一局的逐格紀錄）。瀏覽器裡的讀出照抄作者 make_policy() 裡的 act()。
產出：part1-what.html 裡 <!-- readout:start --> … <!-- readout:end --> 之間的片段。圖的文字要改在這裡，不要直接改頁面。
用法：python3 scripts/make_readout_anim.py"""
import json
import os
import re
from decimal import ROUND_HALF_UP, Decimal

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(D, "out/readout_fig.json")))
C, CAL, EP, CR = R["const"], R["cal"], R["episode"], R["cal_rule"]
PAGE = os.path.join(D, "part1-what.html")


def n(x, d=2):
    if isinstance(x, float):
        s = str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
        s = s.rstrip("0").rstrip(".") if "." in s else s
    else:
        s = str(x)
    return s.replace("-", "−")


row = {r["az"]: r for r in R["rows"]}
TT, FT, QT = CAL["turn_th"], CAL["fire_th"], CAL["quiet_th"]
s6a, s6b = EP["seg6"]
act = EP["actions"]
STEPS = [
    dict(k=1, title="讀哪些數：八群的放電率", text=(
        f"遊戲每前進一格（{C['tic_ms']} ms），大腦往前跑 {C['steps_per_tic']} 步。每顆神經元這 {C['steps_per_tic']} 步放電幾次，"
        f"除以 {C['tic_ms']} ms，就是這一格的放電率；同一群取平均（LC10a 左 {R['sizes']['LC10a_L']} 顆、右 {R['sizes']['LC10a_R']} 顆；"
        f"AOTU019、AOTU025、DNa02 每側只有 1 顆，就是那一顆）。單獨一顆在一格裡只放電幾次，所以單算一格的放電率只能是約 "
        f"{n(C['hz_per_spike'], 0)} Hz 的整數倍（放電 4 次 ≈ 140 Hz），一格一格跳得很兇。作者因此再做一次平滑："
        f"新值 ＝ {n(C['alpha_2dp'])} × 上一格的值 ＋ {n(C['one_minus_alpha_2dp'])} × 這一格單算的值"
        f"（{n(C['alpha_2dp'])} ＝ e<sup>−{C['tic_ms']} ÷ {n(C['tau_s_ms'], 0)}</sup>，作者設的平滑時間常數 {C['tau_s']} 秒）。"
        f"長條是平滑後的值，細黑線是這一格單算的值。這裡播的是 PART 5 那一局的開頭 {EP['seg1'][1] + 1} 格："
        f"平滑從 0 開始，長條要好幾格才升上來。讀出規則用的都是平滑後的值。")),
    dict(k=2, title="轉向訊號：四個數加減", text=(
        "轉向訊號 ＝ (DNa02<sub>右</sub> − DNa02<sub>左</sub>) ＋ (AOTU019<sub>右</sub> − AOTU019<sub>左</sub>)，"
        "只用八群裡的四個數（亮的那兩列）；LC10a、AOTU025 不直接進公式。正的表示右邊比較強，負的表示左邊比較強。"
        "從這一步到第 ⑤ 步用的是校準表的數字（假想敵人、刺激最強、20 格平均）：拖「敵人方位」換位置，或按「▶ 播放」掃過 17 個方位。")),
    dict(k=3, title="轉向門檻", text=(
        f"轉向訊號超過 +{n(TT)} 按右轉、低於 −{n(TT)} 按左轉，中間什麼都不按。敵人在 0° 時是 {n(row[0]['steer'])}、"
        f"±5° 時是 {n(row[5]['steer'])}，都在中間，不轉；從 ±10° 起（{n(row[10]['steer'])}、{n(row[-10]['steer'])}）全部超過門檻。")),
    dict(k=4, title="開火：兩側 AOTU019 都夠高", text=(
        f"看兩側 AOTU019 裡<b>較小</b>的那個：超過 {n(FT)} 就按開火。取較小的，等於要求兩側<b>都</b>超過。"
        f"校準表上只有 0° 和 ±5° 符合：敵人在雙眼重疊區，兩眼都看到，兩側 AOTU019 都亮；+10° 時左側只剩 {n(row[10]['AOTU019_L'])} Hz。"
        "轉向和開火各自判斷，同一格可以同時按。")),
    dict(k=5, title="門檻怎麼定：校準曲線", text=(
        f"17 個方位的轉向訊號連成曲線。轉向門檻 ＝ 0° 的絕對值 {n(CR['s0'])} 和 ±10° 較小的絕對值 {n(CR['s_off'])} 的中點："
        f"({n(CR['s0'])} ＋ {n(CR['s_off'])}) ÷ 2 ＝ {n(TT)}；開火門檻 ＝ 0° 時兩側 AOTU019 較小的 {n(CR['aotu019_min_at_0'])} 的一半 ＝ {n(FT)}。"
        "綠點是會開火的方位。校準只做一次，之後玩遊戲時不再改。")),
    dict(k=6, title="沒有敵人：迴路安靜就往右找", text=(
        f"PART 5 那一局的第 {s6a}–{s6b} 格。第 {EP['gone_tic']} 格敵人離開畫面，但平滑讓放電率每格只降到約 {n(C['alpha_2dp'])} 倍，"
        f"八群加總從 {n(EP['sum_at_gone'], 0)} Hz 一格一格往下掉；這段時間照公式判斷，訊號不夠大，什麼都不按。"
        f"第 {EP['first_quiet_tic']} 格加總 {n(EP['sum_at_q0'])} Hz，低於安靜門檻 {n(QT, 0)} Hz（作者定的），從這一格起固定按右轉，"
        f"讓視野轉起來找敵人。從敵人消失到開始找，隔了 {EP['search_delay_tics']} 格，約 {n(EP['search_delay_ms'] / 1000, 1)} 秒。")),
    dict(k=7, title=f"真實的一局：{EP['n']} 格逐格重播", text=(
        f"PART 5 影片那一局（{EP['seconds']} 秒、擊倒 {EP['kills']} 個敵人），每一格都照上面的規則算。"
        f"{EP['n']} 格裡 {act['000']} 格什麼都不按、{act['010']} 格右轉、{act['001']} 格開火、{act['011']} 格同時右轉和開火，"
        f"這一局沒有按過左轉。用紀錄裡的放電率重算一遍，{EP['n']} 格按的鍵<b>全部</b>和遊戲當時一樣（右下角「紀錄」那行）。"
        "拖「第幾格」可以跳到任何一格。")),
]
MODES = {1: ("trace", EP["seg1"]), 2: ("cal", 10), 3: ("cal", 10), 4: ("cal", 0), 5: ("cal", 0), 6: ("trace", EP["seg6"]),
         7: ("trace", [0, EP["n"] - 1])}
data = dict(cal=CAL, rows=R["rows"], tr=R["trace"], raw=R["raw"], alpha=C["alpha"], cr=CR,
            steps=[dict(k=k, mode=m, arg=a, play=(k in (1, 5, 6, 7)), speed=(0 if k in (1, 6) else 1)) for k, (m, a) in MODES.items()])

INK, SOFT, FAINT, BORDER = "#1b2733", "#5a6b7b", "#8b98a5", "#e4e8ee"
BLUE, ORANGE, RED, GREEN, PURPLE = "#2563eb", "#ea580c", "#dc2626", "#16a34a", "#9333ea"
svg = f'''<svg class="enc-svg ro-svg" viewBox="0 0 900 620" role="img" aria-labelledby="roTitle" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,-apple-system,'Segoe UI','Microsoft JhengHei',sans-serif">
<title id="roTitle">讀出規則示意：八群神經元的放電率，算出轉向訊號、跟門檻比，決定按左轉、右轉、開火</title>
<text x="16" y="24" font-size="14" font-weight="700" fill="{INK}">敵人在哪（俯視，正前方朝上）</text>
<g class="ro-view"></g>
<text class="ro-viewtxt" x="126" y="236" font-size="12" text-anchor="middle" fill="{SOFT}"></text>
<line x1="246" x2="246" y1="14" y2="300" stroke="{BORDER}"/>
<text x="262" y="24" font-size="14" font-weight="700" fill="{INK}">八群的放電率（Hz）</text>
<text x="330" y="46" font-size="12" text-anchor="middle" fill="{BLUE}">← 左半腦</text><text x="532" y="46" font-size="12" text-anchor="middle" fill="{ORANGE}">右半腦 →</text>
<g class="ro-bars"></g>
<line x1="616" x2="616" y1="14" y2="300" stroke="{BORDER}"/>
<g class="ro-right"></g>
<line x1="16" x2="884" y1="312" y2="312" stroke="{BORDER}"/>
<g class="ro-meters"></g>
<g class="ro-keys"></g>
</svg>'''

ctl = '''<div class="enc-ctl">
  <button type="button" class="ro-prev">← 上一步</button><button type="button" class="ro-next">下一步 →</button>
  <button type="button" class="ro-play">⏸ 暫停</button>
  <label class="ro-azl">敵人方位 <input type="range" min="0" max="16" step="1" value="10"> <b></b></label>
  <label class="ro-ticl">第幾格 <input type="range" min="0" max="480" step="1" value="0"> <b></b></label>
  <label class="ro-spl">速度 <select class="ro-speed"><option value="0">每秒 2 格</option><option value="1">每秒 6 格</option><option value="2">每秒 35 格（實際速度）</option></select></label>
</div>'''
steps_html = "\n".join(f'    <li data-k="{s["k"]}"><b>{"①②③④⑤⑥⑦"[s["k"] - 1]} {s["title"]}：</b>{s["text"]}</li>' for s in STEPS)

SCRIPT = r'''<script>
(function(){
const DATA=__DATA__;
const box=document.getElementById('p1ro'),Q=s=>box.querySelector(s);
const BLUE='#2563eb',ORANGE='#ea580c',RED='#dc2626',GREEN='#16a34a',PURPLE='#9333ea',INK='#1b2733',SOFT='#5a6b7b',FAINT='#8b98a5',BORDER='#e4e8ee';
const G=['LC10a','AOTU019','AOTU025','DNa02'],TT=DATA.cal.turn_th,FT=DATA.cal.fire_th,QT=DATA.cal.quiet_th;
const fmt=(x,d)=>(Math.round(x*Math.pow(10,d))/Math.pow(10,d)).toFixed(d).replace('-','−');
const sgn=x=>(x>0?'+':'')+fmt(x,2);
let step=1,cfg,azi=10,tic=0,playing=true,speed=0,acc=0,last=null,cur=null;
const SP=[2,6,35];
// 讀出：照抄 fly_doom.py make_policy() 的 act()
function readout(r,hasEnemy){
  const s=(r.DNa02_R-r.DNa02_L)+(r.AOTU019_R-r.AOTU019_L);
  let left=+(s<-TT),right=+(s>TT);const m=Math.min(r.AOTU019_L,r.AOTU019_R),fire=+(m>FT);
  let sum=0;for(const g of G)sum+=r[g+'_L']+r[g+'_R'];
  const quiet=!hasEnemy&&sum<QT;if(quiet){left=0;right=1}
  return {s,m,sum,quiet,left,right,fire,code:''+left+right+fire};
}
function state(){
  if(cfg.mode==='cal'){const row=DATA.rows[azi],r={};for(const g of G){r[g+'_L']=row[g+'_L'];r[g+'_R']=row[g+'_R']}
    return {r,en:[row.az],has:true,rec:null,raw:null,az:row.az}}
  const T=DATA.tr,r={},raw={};for(const g of G)for(const sd of ['_L','_R']){r[g+sd]=T[g+sd][tic];raw[g+sd]=DATA.raw[g+sd][tic]}
  const prev={};for(const g of G)for(const sd of ['_L','_R'])prev[g+sd]=tic>0?T[g+sd][tic-1]:0;
  return {r,raw,prev,en:T.e[tic],has:T.e[tic].length>0,rec:T.a[tic],k:T.k[tic]};
}
const actTxt=c=>{const t=[];if(c[0]==='1')t.push('左轉');if(c[1]==='1')t.push('右轉');if(c[2]==='1')t.push('開火');return t.length?t.join('＋'):'不按'};
// 依步驟決定哪些部分要亮
const FOCUS={1:{bars:1,right:1},2:{bars:1,right:1,steer:1,use:1},3:{steer:1,keys:1,thr:1,use:1,right:1,bars:1},4:{fire:1,keys:1,fthr:1,bars:1,right:1},
  5:{right:1,steer:1,thr:1,keys:1,bars:1,use:1},6:{quiet:1,keys:1,thr:1,steer:1,right:1,bars:1,use:1},7:{bars:1,right:1,steer:1,fire:1,quiet:1,keys:1,thr:1,fthr:1,use:1}};
function view(st){
  const cx=126,cy=200,R=104,P=a=>[cx+R*Math.sin(a*Math.PI/180),cy-R*Math.cos(a*Math.PI/180)];
  let h=`<path d="M${cx-R} ${cy} A${R} ${R} 0 0 1 ${cx+R} ${cy} Z" fill="#f7f8fa" stroke="${BORDER}"/>`;
  const w1=P(-6),w2=P(6);h+=`<path d="M${cx} ${cy} L${w1[0]} ${w1[1]} A${R} ${R} 0 0 1 ${w2[0]} ${w2[1]} Z" fill="${GREEN}" fill-opacity=".18"/>`;
  for(const a of [-90,-45,0,45,90]){const p=P(a),q=[cx+(R+12)*Math.sin(a*Math.PI/180),cy-(R+12)*Math.cos(a*Math.PI/180)];
    h+=`<line x1="${cx}" y1="${cy}" x2="${p[0]}" y2="${p[1]}" stroke="${BORDER}"/><text x="${q[0]}" y="${q[1]+4}" font-size="10" text-anchor="middle" fill="${FAINT}">${a>0?'+':''}${String(a).replace('-','−')}°</text>`}
  h+=`<text x="${cx}" y="${cy-R-22}" font-size="10" text-anchor="middle" fill="${GREEN}">雙眼重疊 ±6°</text>`;
  h+=`<ellipse cx="${cx}" cy="${cy}" rx="11" ry="8" fill="${INK}"/>`;
  for(const a of st.en){const p=[cx+R*0.78*Math.sin(a*Math.PI/180),cy-R*0.78*Math.cos(a*Math.PI/180)];
    h+=`<line x1="${cx}" y1="${cy}" x2="${p[0]}" y2="${p[1]}" stroke="${RED}" stroke-dasharray="3 3"/><circle cx="${p[0]}" cy="${p[1]}" r="8" fill="${RED}"/>`;
    h+=`<text x="${p[0]}" y="${p[1]-12}" font-size="11" font-weight="600" text-anchor="middle" fill="${RED}">${a>0?'+':''}${fmt(a,1).replace('.0','')}°</text>`}
  Q('.ro-view').innerHTML=h;
  Q('.ro-viewtxt').textContent=cfg.mode==='cal'?'校準：假想敵人放在 '+(st.az>0?'+':'')+String(st.az).replace('-','−')+'°':
    (st.en.length?'第 '+tic+' 格（共 '+DATA.tr.a.length+' 格），已擊倒 '+st.k:'第 '+tic+' 格：畫面上沒有敵人');
}
function bars(st,F){
  const C=431,GAP=38,S=140/300,Y=[72,124,176,228];let h='';
  for(let i=0;i<4;i++){const g=G[i],y=Y[i],use=(g==='AOTU019'||g==='DNa02'),dim=F.use&&!use||(step===4&&g!=='AOTU019');
    h+=`<g opacity="${dim?0.3:1}">`;
    h+=`<text x="${C}" y="${y+4}" font-size="12" font-weight="${use&&F.use?700:500}" text-anchor="middle" fill="${INK}">${g}</text>`;
    for(const [sd,dir,col] of [['_L',-1,BLUE],['_R',1,ORANGE]]){const v=cur[g+sd],w=Math.min(300,v)*S,x0=C+dir*GAP;
      h+=`<rect x="${dir<0?x0-w:x0}" y="${y-12}" width="${w}" height="24" rx="3" fill="${col}" fill-opacity=".8"/>`;
      h+=`<line x1="${x0}" x2="${x0+dir*140}" y1="${y+12}" y2="${y+12}" stroke="${BORDER}"/>`;
      const inb=w>110;h+=`<text x="${x0+dir*(inb?w-4:w+4)}" y="${y+4}" font-size="11" text-anchor="${(dir<0)!==inb?'end':'start'}" fill="${inb?'#fff':INK}">${fmt(v,1)}</text>`;
      if(step===1&&st.raw){const rx=x0+dir*Math.min(300,st.raw[g+sd])*S;h+=`<line x1="${rx}" x2="${rx}" y1="${y-17}" y2="${y+17}" stroke="${INK}" stroke-width="2"/>`}
      if(F.fthr&&g==='AOTU019'){const tx=x0+dir*FT*S;h+=`<line x1="${tx}" x2="${tx}" y1="${y-18}" y2="${y+18}" stroke="${RED}" stroke-width="1.5" stroke-dasharray="4 3"/>`;
        if(dir>0)h+=`<text x="${tx}" y="${y-21}" font-size="10" text-anchor="middle" fill="${RED}">${fmt(FT,2)}</text>`}}
    h+='</g>'}
  h+=`<text x="${C}" y="${Y[3]+38}" font-size="10" text-anchor="middle" fill="${FAINT}">長條刻度 0–300 Hz</text>`;
  if(step===1)h+=`<text x="${C}" y="${Y[3]+54}" font-size="11" text-anchor="middle" fill="${INK}">長條＝平滑後的值；細黑線＝這一格單算的值</text>`;
  Q('.ro-bars').innerHTML=h;
}
function right(st,o,F){
  const X=630;let h='';
  if(step===1){const p=st.prev.AOTU019_L,raw=st.raw.AOTU019_L,nw=st.r.AOTU019_L,c=Math.round(raw/35);
    h+=`<text x="${X}" y="24" font-size="14" font-weight="700" fill="${INK}">每一格怎麼算（以左 AOTU019 為例）</text>`;
    const L=[`① 這一格（28.6 ms）放電 ${c} 次`,`② ÷ 28.6 ms → 單算 ${fmt(raw,1)} Hz`,`③ 平滑：0.75 × 上一格 ${fmt(p,1)}`,`　　　＋ 0.25 × ${fmt(raw,1)}`,`　　　＝ ${fmt(nw,1)} Hz（長條）`];
    L.forEach((t,i)=>h+=`<text x="${X}" y="${60+i*26}" font-size="13" fill="${INK}">${t}</text>`);
    h+=`<text x="${X}" y="${60+5*26+6}" font-size="11" fill="${SOFT}">單算的值由紀錄反推，誤差約 ±0.4 Hz</text>`;
  }else if(step===5){
    const x0=X+26,x1=880,y0=40,y1=236,ax=a=>x0+(a+90)/180*(x1-x0),ay=v=>(y0+y1)/2-v/350*((y1-y0)/2);
    h+=`<text x="${X}" y="24" font-size="14" font-weight="700" fill="${INK}">校準曲線：轉向訊號 對 方位</text>`;
    h+=`<rect x="${x0}" y="${y0}" width="${x1-x0}" height="${y1-y0}" fill="none" stroke="${BORDER}"/>`;
    h+=`<line x1="${x0}" x2="${x1}" y1="${ay(0)}" y2="${ay(0)}" stroke="${BORDER}"/>`;
    for(const v of [TT,-TT])h+=`<line x1="${x0}" x2="${x1}" y1="${ay(v)}" y2="${ay(v)}" stroke="${RED}" stroke-dasharray="5 4"/>`;
    h+=`<text x="${x0-3}" y="${ay(TT)+4}" font-size="10" text-anchor="end" fill="${RED}">+${fmt(TT,0)}</text><text x="${x0-3}" y="${ay(-TT)+4}" font-size="10" text-anchor="end" fill="${RED}">−${fmt(TT,0)}</text>`;
    for(const a of [-90,0,90])h+=`<text x="${ax(a)}" y="${y1+14}" font-size="10" text-anchor="middle" fill="${FAINT}">${a>0?'+':''}${String(a).replace('-','−')}°</text>`;
    let d='';DATA.rows.forEach((r,i)=>d+=(i?'L':'M')+ax(r.az).toFixed(1)+' '+ay(r.steer).toFixed(1));
    h+=`<path d="${d}" fill="none" stroke="${INK}" stroke-width="1.6"/>`;
    DATA.rows.forEach((r,i)=>{const f=Math.min(r.AOTU019_L,r.AOTU019_R)>FT;h+=`<circle cx="${ax(r.az)}" cy="${ay(r.steer)}" r="${i===azi?6:3.5}" fill="${f?GREEN:INK}" ${i===azi?`stroke="${ORANGE}" stroke-width="3"`:''}/>`});
    const cr=DATA.cr;h+=`<text x="${X}" y="${y1+36}" font-size="11" fill="${INK}">轉向門檻 ＝ (${fmt(cr.s0,2)} ＋ ${fmt(cr.s_off,2)}) ÷ 2 ＝ ${fmt(TT,2)}</text>`;
    h+=`<text x="${X}" y="${y1+54}" font-size="11" fill="${INK}">開火門檻 ＝ ${fmt(cr.aotu019_min_at_0,2)} ÷ 2 ＝ ${fmt(FT,2)}（綠點會開火）</text>`;
  }else{const r=st.r;
    h+=`<text x="${X}" y="24" font-size="14" font-weight="700" fill="${INK}">讀出的算式</text>`;
    h+=`<text x="${X}" y="56" font-size="13" fill="${INK}">轉向訊號</text>`;
    h+=`<text x="${X}" y="82" font-size="13" fill="${INK}">＝ (DNa02<tspan fill="${ORANGE}">右</tspan> − DNa02<tspan fill="${BLUE}">左</tspan>)</text>`;
    h+=`<text x="${X}" y="104" font-size="13" fill="${INK}">＋ (AOTU019<tspan fill="${ORANGE}">右</tspan> − AOTU019<tspan fill="${BLUE}">左</tspan>)</text>`;
    h+=`<text x="${X}" y="130" font-size="13" fill="${INK}">＝ (${fmt(r.DNa02_R,1)} − ${fmt(r.DNa02_L,1)}) ＋ (${fmt(r.AOTU019_R,1)} − ${fmt(r.AOTU019_L,1)})</text>`;
    h+=`<text x="${X}" y="158" font-size="16" font-weight="700" fill="${INK}">＝ ${sgn(o.s)}</text>`;
    h+=`<g opacity="${F.fire||F.fthr?1:0.35}"><text x="${X}" y="196" font-size="13" fill="${INK}">開火看：較小的 AOTU019</text>`;
    h+=`<text x="${X}" y="218" font-size="13" fill="${INK}">＝ min(${fmt(r.AOTU019_L,1)}, ${fmt(r.AOTU019_R,1)}) ＝ <tspan font-weight="700">${fmt(o.m,1)}</tspan></text></g>`;
    h+=`<g opacity="${F.quiet?1:0.35}"><text x="${X}" y="256" font-size="13" fill="${INK}">八群加總 ＝ <tspan font-weight="700">${fmt(o.sum,1)}</tspan> Hz</text>`;
    h+=`<text x="${X}" y="276" font-size="11" fill="${SOFT}">${st.has?'畫面上有敵人：不看這一項':'畫面上沒有敵人：低於 '+fmt(QT,0)+' 就固定右轉'}</text></g>`;
  }
  Q('.ro-right').innerHTML=h;
}
function meters(st,o,F){
  const M0=40,M1=600;let h='';
  const meter=(y,title,lo,hi,v,zones,thr,on,unit)=>{const X=x=>M0+(Math.max(lo,Math.min(hi,x))-lo)/(hi-lo)*(M1-M0);
    let t=`<g opacity="${on?1:0.3}"><text x="${M0}" y="${y-40}" font-size="13" font-weight="600" fill="${INK}">${title}</text>`;
    for(const z of zones)t+=`<rect x="${X(z[0])}" y="${y-14}" width="${X(z[1])-X(z[0])}" height="28" fill="${z[2]}" fill-opacity=".14"/><text x="${(X(z[0])+X(z[1]))/2}" y="${y+28}" font-size="11" text-anchor="middle" fill="${z[2]}">${z[3]}</text>`;
    t+=`<line x1="${M0}" x2="${M1}" y1="${y}" y2="${y}" stroke="${FAINT}"/>`;
    for(const [tv,lab] of thr)t+=`<line x1="${X(tv)}" x2="${X(tv)}" y1="${y-18}" y2="${y+18}" stroke="${RED}" stroke-width="1.5" stroke-dasharray="4 3"/><text x="${X(tv)}" y="${y-22}" font-size="10" text-anchor="middle" fill="${RED}">${lab}</text>`;
    t+=`<text x="${M0}" y="${y+42}" font-size="10" fill="${FAINT}">${String(lo).replace('-','−')}</text><text x="${M1}" y="${y+42}" font-size="10" text-anchor="end" fill="${FAINT}">${hi}${v>hi?'（超出）':''}</text>`;
    const mx=X(v);t+=`<path d="M${mx-7} ${y-22} L${mx+7} ${y-22} L${mx} ${y-10} Z" fill="${INK}"/><line x1="${mx}" x2="${mx}" y1="${y-10}" y2="${y+14}" stroke="${INK}" stroke-width="2.5"/>`;
    const lr=mx>M1-60;t+=`<text x="${lr?mx-11:mx+11}" y="${y-11}" font-size="12" font-weight="700" text-anchor="${lr?'end':'start'}" fill="${INK}" paint-order="stroke" stroke="#fff" stroke-width="4">${fmt(v,1)}${unit}</text></g>`;return t};
  h+=meter(368,'轉向訊號',-350,350,cur.s,[[-350,-TT,BLUE,'按左轉'],[-TT,TT,SOFT,'不轉'],[TT,350,ORANGE,'按右轉']],F.thr?[[-TT,'−'+fmt(TT,2)],[TT,'+'+fmt(TT,2)]]:[],F.steer,'');
  h+=meter(466,'開火：兩側 AOTU019 較小的那個（Hz）',0,300,cur.m,[[FT,300,RED,'按開火']],[[FT,fmt(FT,2)]],F.fire,'');
  h+=meter(564,'沒有敵人時：八群加總（Hz）',0,60,cur.sum,[[0,QT,ORANGE,'安靜 → 按右轉']],[[QT,fmt(QT,0)]],F.quiet&&!st.has,'');
  Q('.ro-meters').innerHTML=h;
  // 按鍵
  const K=[['← 左轉',o.left,BLUE],['→ 右轉',o.right,ORANGE],['● 開火',o.fire,RED]];let k=`<g opacity="${F.keys?1:0.35}"><text x="640" y="336" font-size="14" font-weight="700" fill="${INK}">這一格按的鍵</text>`;
  K.forEach(([t,on,col],i)=>{const y=350+i*58;k+=`<rect x="640" y="${y}" width="240" height="46" rx="10" fill="${on?col:'#fff'}" stroke="${on?col:BORDER}" stroke-width="2"/><text x="760" y="${y+29}" font-size="16" font-weight="700" text-anchor="middle" fill="${on?'#fff':FAINT}">${t}</text>`});
  let why=o.quiet?'沒有敵人、迴路安靜 → 固定右轉':(o.code==='000'?'轉向、開火都沒過門檻':'');
  k+=`<text x="640" y="534" font-size="12" fill="${SOFT}">${why}</text>`;
  if(st.rec!=null)k+=`<text x="640" y="556" font-size="12" fill="${st.rec===o.code?GREEN:RED}">紀錄：遊戲當時按的是「${actTxt(st.rec)}」${st.rec===o.code?' ✓ 相同':' ✗ 不同'}</text>`;
  Q('.ro-keys').innerHTML=k+'</g>';
  Q('.enc-read').textContent=(cfg.mode==='cal'?'方位 '+(st.az>0?'+':'')+String(st.az).replace('-','−')+'°':'第 '+tic+' 格')+'　轉向訊號 '+sgn(o.s)+'　較小的 AOTU019 '+fmt(o.m,1)+' Hz　八群加總 '+fmt(o.sum,1)+' Hz　→ 按：'+actTxt(o.code);
}
function draw(dt){
  const st=state(),o=readout(st.r,st.has),F=FOCUS[step];
  const tgt=Object.assign({},st.r,{s:o.s,m:o.m,sum:o.sum});
  if(!cur)cur=Object.assign({},tgt);const f=Math.min(1,dt/110);for(const k in tgt)cur[k]+=(tgt[k]-cur[k])*f;
  view(st);bars(st,F);right(st,o,F);meters(st,o,F);
}
function frame(ts){
  if(last==null)last=ts;const dt=Math.min(200,ts-last);last=ts;
  if(playing){acc+=dt;
    if(cfg.mode==='cal'){if(acc>1100){acc=0;azi=(azi+1)%17;syncCtl()}}
    else{const per=1000/SP[speed];while(acc>=per){acc-=per;tic=tic>=cfg.arg[1]?cfg.arg[0]:tic+1;syncCtl()}}}
  draw(dt);requestAnimationFrame(frame);
}
const az=Q('.ro-azl input'),tc=Q('.ro-ticl input');
function syncCtl(){az.value=azi;const a=DATA.rows[azi].az;Q('.ro-azl b').textContent=(a>0?'+':'')+String(a).replace('-','−')+'°';tc.value=tic;Q('.ro-ticl b').textContent=tic}
function render(){
  for(const li of box.querySelectorAll('.enc-steps li')){const k=+li.dataset.k;li.className=k===step?'on':k<step?'done':''}
  Q('.ro-prev').disabled=step===1;Q('.ro-next').disabled=step===7;
  Q('.ro-azl').style.display=cfg.mode==='cal'?'':'none';Q('.ro-ticl').style.display=cfg.mode==='trace'?'':'none';Q('.ro-spl').style.display=cfg.mode==='trace'?'':'none';
  if(cfg.mode==='trace'){tc.min=cfg.arg[0];tc.max=cfg.arg[1]}
  Q('.ro-play').textContent=playing?'⏸ 暫停':'▶ 播放';syncCtl();
}
function go(k){step=k;cfg=DATA.steps[k-1];playing=cfg.play;speed=cfg.speed;Q('.ro-speed').value=speed;acc=0;
  if(cfg.mode==='cal')azi=DATA.rows.findIndex(r=>r.az===cfg.arg);else tic=cfg.arg[0];render()}
Q('.ro-prev').onclick=()=>{if(step>1)go(step-1)};Q('.ro-next').onclick=()=>{if(step<7)go(step+1)};
Q('.ro-play').onclick=()=>{playing=!playing;acc=0;render()};
Q('.ro-speed').onchange=e=>{speed=+e.target.value};
az.oninput=()=>{azi=+az.value;playing=false;render()};tc.oninput=()=>{tic=+tc.value;playing=false;render()};
for(const li of box.querySelectorAll('.enc-steps li'))li.onclick=()=>go(+li.dataset.k);
// 給單獨頁與自我檢查用
box.ro={get step(){return step},check(){let bad=0;for(let i=0;i<DATA.tr.a.length;i++){const r={};for(const g of G)for(const sd of ['_L','_R'])r[g+sd]=DATA.tr[g+sd][i];
    if(readout(r,DATA.tr.e[i].length>0).code!==DATA.tr.a[i])bad++}return bad},
  set(o){if(o.step)go(Math.max(1,Math.min(7,o.step)));if(o.az!=null){const i=DATA.rows.findIndex(r=>r.az===o.az);if(i>=0)azi=i}
    if(o.tic!=null)tic=o.tic;if(o.speed!=null){speed=o.speed;Q('.ro-speed').value=speed}if(o.play!=null)playing=!!o.play;cur=null;render()}};
go(1);requestAnimationFrame(frame);
})();
</script>'''
frag = (f'<div class="enc ro" id="p1ro">\n<div class="lif-wrap">{svg}</div>\n<div class="enc-read" aria-live="off"></div>\n{ctl}\n'
        f'<ol class="enc-steps">\n{steps_html}\n  </ol>\n</div>\n'
        + SCRIPT.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
page = open(PAGE, encoding="utf-8").read()
new, cnt = re.subn(r"<!-- readout:start -->.*?<!-- readout:end -->", lambda m: "<!-- readout:start -->\n" + frag + "\n<!-- readout:end -->", page, flags=re.S)
assert cnt == 1, "頁面裡找不到 <!-- readout:start --> … <!-- readout:end -->"
open(PAGE, "w", encoding="utf-8").write(new)
print("圖 5（讀出規則）已寫入 part1-what.html")
