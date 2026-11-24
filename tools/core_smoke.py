"""새 코어(index.html) 스모크 검사: 헤드리스 브라우저에서 봇이 판을 끝까지 돈다.
찾는 것: 예외(pageerror), 진행 멈춤(상태가 오래 안 바뀜), 판 길이, 층 도달·결과 분포.
균형을 재는 도구가 아니라 "터지거나 멈추는가"를 보는 도구.

  python3 tools/core_smoke.py [판 수=20] [속도 배율=0.04]
결과: 화면에 요약, docs/smoke.json 에 판별 기록
"""
import asyncio, json, sys, os, time, http.server, threading, functools
from playwright.async_api import async_playwright

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
BUY = os.environ.get("BUY", "1") == "1"  # 0이면 아무것도 사지 않는 봇
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 0.04
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT = r"""
(()=>{
const S=window.setTimeout.bind(window),SP=%SPEED%;
window.setTimeout=(f,ms,...a)=>S(f,Math.max(0,(ms||0)*SP),...a);   /* 연출 대기 줄이기 */
const BUY=%BUY%,B=window.__bot={meta:{},ovf:{},small:{},runs:[],errs:[],stuck:[],cur:null,last:'',lastT:Date.now(),ticks:0};
const q=s=>[...document.querySelectorAll(s)].filter(b=>!b.disabled&&b.offsetParent!==null);
const click=b=>{if(b){b.click();return true}return false};
const any=s=>click(q(s)[Math.floor(Math.random()*q(s).length)]);
function sig(){try{return JSON.stringify([ui.screen,ui.busy,G.fl,G.at,G.risk,G.battle&&G.battle.round,G.battle&&G.battle.foes.map(f=>f.hp),G.party&&G.party.map(m=>[m.hp,m.sp,m.row]),G.items&&G.items.length,G.yen,G.shop&&G.shop.sold.length,!!G.ev,!!G.pick,G.end&&G.end.kind])}catch(e){return 'x'}}
function tick(){B.ticks++;
 const s=sig();if(s!==B.last){B.last=s;B.lastT=Date.now()}
 else if(Date.now()-B.lastT>8000){B.stuck.push({screen:ui.screen,busy:ui.busy,fl:G.fl,round:G.battle&&G.battle.round,btn:q('[data-a]').map(b=>b.dataset.a).slice(0,12)});B.lastT=Date.now();
  /* 멈춤에서 빠져나오기: 처음 화면부터 */ if(B.cur){B.cur.end='STUCK';B.runs.push(B.cur);B.cur=null}try{ui.busy=false;ui.screen='title';G.battle=null;G.ev=null;G.pick=null;render()}catch(e){}return}
 if(click(q('[data-a="tutoff"]')[0]))return;
 const sc=ui.screen;
 {const k=sc+(sc==='hub'?':'+ui.ht:'');if(!B.ovf[k]&&document.documentElement.scrollWidth>innerWidth+1){const w=[...document.querySelectorAll('#app *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,3).map(e=>e.tagName+'.'+e.className);B.ovf[k]=w}
  if(!B.small[k]){const sm=[...document.querySelectorAll('#app *')].filter(e=>e.offsetParent!==null&&e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&parseFloat(getComputedStyle(e).fontSize)<11);B.small[k]=sm.slice(0,4).map(e=>e.tagName+'.'+e.className+' '+getComputedStyle(e).fontSize+' "'+e.textContent.trim().slice(0,14)+'"').concat(sm.length>4?['…'+sm.length]:[])}}
 if(sc==='title'){if(B.cur&&G.end){B.cur.end=G.end.kind;B.runs.push(B.cur);B.cur=null}return click(q('[data-a="go"]')[0])||click(q('[data-a="start"]')[0])}
 if(sc==='hub'&&!BUY){if(ui.ht!=='go')return click(q('[data-a="ht:go"]')[0]);const ps=ui.ps||[];if(ps.length<3)return any('[data-a^="ps:"]');B.cur={t0:Date.now(),party:[...ps],maxFl:0,battles:0,rounds:0,clicks:0,q0:SV.q,yen0:SV.yen};return click(q('[data-a="go"]')[0])}
 if(sc==='hub'){if(ui.ht!=='go'&&B.buy){B.buy=0;const c=q('[data-a^="upg:"],[data-a^="unl:"],[data-a^="bond:"]');if(c.length){const x=c[0];B.meta['buy-'+x.dataset.a.split(':')[0]]=(B.meta['buy-'+x.dataset.a.split(':')[0]]||0)+1;return click(x)}}
  if(ui.ht==='go'&&!B.cur&&Math.random()<.8&&click(q('.nextu.ok')[0])){B.buy=1;return}
  if(ui.ht==='go'&&!B.cur){const w=q('[data-a^="setwarp:"]');if(w.length&&!w[w.length-1].classList.contains('on'))return click(w[w.length-1])}/* 직행이 있으면 가장 깊은 층부터 */
  if(ui.ht!=='go'){if(Math.random()<.5){const c=q('[data-a^="unl:"],[data-a^="upg:"],[data-a^="bond:"],[data-a^="bsee:"],[data-a^="setstart:"],[data-a="setneg"],[data-a="setbet"],[data-a^="setwarp:"],[data-a^="ssave:"],[data-a="tutt"],[data-a^="sv:"]');if(c.length){const b=c[Math.floor(Math.random()*c.length)];B.meta[b.dataset.a.split(':')[0]]=(B.meta[b.dataset.a.split(':')[0]]||0)+1;return click(b)}}return click(q('[data-a="ht:go"]')[0])}
  if(!B.cur&&Math.random()<.25&&!B.hubSeen){B.hubSeen=1;return any('[data-a^="ht:"]')}B.hubSeen=0;
  const ps=ui.ps||[];if(ps.length<3)return any('[data-a^="ps:"]:not(.on)')||any('[data-a^="ps:"]');
  B.cur={t0:Date.now(),party:[...ps],maxFl:0,battles:0,rounds:0,clicks:0,q0:SV.q,yen0:SV.yen};return click(q('[data-a="go"]')[0])}
 if(B.cur){B.cur.clicks++;B.cur.maxFl=Math.max(B.cur.maxFl,G.fl||0)}
 if(sc==='result'){if(B.cur){B.cur.end=G.end&&G.end.kind;B.cur.cleared=!!G.cleared;B.cur.yen=G.end&&G.end.y;B.cur.ms=Date.now()-B.cur.t0;B.cur.rooms=G.stats.rooms;B.cur.battles=G.stats.battles;B.cur.q1=SV.q;B.cur.gates=G.stats.gates||0;B.cur.gain=G.end&&(G.end.y+G.end.bet+G.end.sy);B.cur.spent=0;B.cur.sub=G.end&&G.end.subOk;B.runs.push(B.cur);B.cur=null}
  return click(q('[data-a="hubgo"]')[0])||click(q('[data-a="title"]')[0])||any('[data-a]')}
 if(sc==='story')return click(q('[data-a="storyok"]')[0]);
 if(sc==='battle'){if(Math.random()<.01&&click(q('[data-a="auto"]')[0])){B.meta.auto=(B.meta.auto||0)+1;return}if(ui.busy)return;if(B.cur&&G.battle)B.cur.rounds=Math.max(B.cur.rounds,G.battle.round);
  if(click(q('[data-a="allout"]')[0]))return;
  if(Math.random()<.6&&any('[data-a^="bt:"]'))return;
  const fa=q('[data-a^="sel:"]');if(fa.length&&Math.random()<.3)click(fa[Math.floor(Math.random()*fa.length)]);
  const sk=q('[data-a^="sk:"]'),wk=sk.filter(b=>b.textContent.includes('약점'));
  if(wk.length)return click(wk[0]);if(sk.length&&Math.random()<.9)return click(sk[Math.floor(Math.random()*sk.length)]);
  return any('[data-a^="sw:"]')||any('[data-a^="sk:"]')}
 if(sc==='event'){return any('[data-a^="cb:"]')||any('[data-a^="deal:"]')||any('[data-a^="ev:"]')||any('[data-a]')}
 if(sc==='pick'){if(Math.random()<.1&&click(q('[data-a="reroll"]')[0])){B.meta.reroll=(B.meta.reroll||0)+1;return}return any('[data-a^="take:"]')}
 if(sc==='bench'){if(Math.random()<.5&&any('[data-a^="buy:"]')){B.meta.buy=(B.meta.buy||0)+1;return}if(Math.random()<.3&&click(q('[data-a="shopheal"]')[0])){B.meta.heal=(B.meta.heal||0)+1;return}const bs=q('[data-a^="bsel:"]');if(bs.length>=2&&!G.benchUsed&&Math.random()<.7){click(bs[0]);click(q('[data-a^="bsel:"]')[1]);if(click(q('[data-a="synth"]')[0]))return}return click(q('[data-a="leave"]')[0])}
 const hpr=()=>{const P=G.party||[];return P.reduce((t,m)=>t+Math.max(0,m.hp),0)/Math.max(1,P.reduce((t,m)=>t+m.max,0))};/* 사람처럼: 많이 다치면 귀환 */
 if(sc==='floor'){if(hpr()<.45)return click(q('[data-a="ret"]')[0]);return click(q('[data-a="down"]')[0])||click(q('[data-a="ret"]')[0])}
 if(sc==='map'){if(hpr()<.4&&click(q('[data-a="curry"]')[0])){B.meta.curry=(B.meta.curry||0)+1;return}if(hpr()<.28&&click(q('[data-a="ret"]')[0])){B.meta.retreat=(B.meta.retreat||0)+1;return}if(ui.walk&&Date.now()-ui.walk<1100*SP+30)return;
  const mv=q('[data-a^="mv:"]');if(!mv.length)return any('[data-a="down"]')||any('[data-a="ret"]');
  const fresh=mv.filter(b=>!G.map.done.has(+b.dataset.a.split(':')[1]));
  const boss=mv.filter(b=>G.map.T[+b.dataset.a.split(':')[1]]==='boss');
  const pool=fresh.filter(b=>!boss.includes(b));
  return click((pool.length?pool:fresh.length?fresh:mv)[Math.floor(Math.random()*(pool.length?pool:fresh.length?fresh:mv).length)])}
 return any('[data-a]')}
const ok=()=>typeof ui!=='undefined';
window.addEventListener('error',e=>B.errs.push({m:String(e.message),at:(e.filename||'').split('/').pop()+':'+e.lineno,screen:window.ui&&ui.screen}));
window.addEventListener('unhandledrejection',e=>B.errs.push({m:'promise: '+String(e.reason&&e.reason.stack||e.reason).slice(0,300),screen:window.ui&&ui.screen}));
setInterval(()=>{if(!ok())return;try{tick()}catch(e){B.errs.push({m:'bot: '+e.message})}},25);
})();
"""

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Q, directory=ROOT)
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

async def main():
    srv = serve(); port = srv.server_address[1]
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': int(os.environ.get('W', 360)), 'height': 740})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
        await pg.add_init_script(BOT.replace('%SPEED%', str(SPEED)).replace('%BUY%', 'true' if BUY else 'false'))
        await pg.goto(f'http://127.0.0.1:{port}/index.html')
        t0 = time.time(); last = -1
        while time.time() - t0 < 60 * 25:
            await asyncio.sleep(2)
            st = await pg.evaluate('({n:__bot.runs.length,stuck:__bot.stuck.length,errs:__bot.errs.length,scr:ui.screen})')
            if st['n'] != last:
                last = st['n']; print(f"  {st['n']}/{RUNS}판 · 멈춤 {st['stuck']} · 에러 {st['errs']} · 지금 {st['scr']}", flush=True)
            if st['n'] >= RUNS: break
        R = await pg.evaluate('__bot')
        await b.close()
    srv.shutdown()
    runs = R['runs']
    out = {'runs': runs, 'errors': R['errs'], 'pageerrors': errs, 'stuck': R['stuck']}
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, 'docs', 'smoke-buy.json' if BUY else 'smoke-nobuy.json'), 'w'), ensure_ascii=False, indent=1)
    from collections import Counter
    print('\n== 결과 ==')
    print('판:', len(runs), '· 결과:', dict(Counter(r.get('end') for r in runs)), '· 최고층:', dict(Counter(r.get('maxFl', 0) + 1 for r in runs)))
    ok = [r for r in runs if r.get('ms')]
    if ok:
        print('판당 클릭 평균 %.0f · 전투 평균 %.1f · 방 평균 %.1f' % (sum(r['clicks'] for r in ok) / len(ok), sum(r['battles'] for r in ok) / len(ok), sum(r['rooms'] for r in ok) / len(ok)))
    print('메타·조작 누른 횟수:', R['meta'])
    n=len(runs) or 1
    print('관문 돌파율: B1 %d%% · B2 %d%% · B3 %d%%' % tuple(100*sum(1 for r in runs if (r.get('gates') or 0)>=k)/n for k in (1,2,3)))
    fq=lambda k: next((i+1 for i,r in enumerate(runs) if (r.get('q1') or 0)>=k), None)
    print('의뢰 완료 판: 1 → %s · 2 → %s · 3 → %s' % (fq(1), fq(2), fq(3)))
    print('의뢰 진행(판 순서):', ' '.join(str(r.get('q1','?')) for r in runs))
    g=[r.get('gain') or 0 for r in runs if r.get('gain') is not None]
    if g: print('판당 지갑 수입 평균 ¥%d (최소 ¥%d · 최대 ¥%d) · 서브 의뢰 성공 %d/%d' % (sum(g)/len(g), min(g), max(g), sum(1 for r in runs if r.get('sub')), len(runs)))
    print('가로 넘침 화면:', {k: v for k, v in R['ovf'].items() if v} or '없음')
    print('11px 미만 글씨 화면:'); [print('  ', k, v) for k, v in R['small'].items() if v]
    out['ovf'] = R['ovf']; out['small'] = R['small']; out['meta'] = R['meta']
    json.dump(out, open(os.path.join(ROOT, 'docs', 'smoke-buy.json' if BUY else 'smoke-nobuy.json'), 'w'), ensure_ascii=False, indent=1)
    print('멈춤', len(R['stuck']), '· 에러', len(R['errs']) + len(errs))
    for e in (R['errs'] + [{'m': x} for x in errs])[:12]: print('  !', e)
    for s in R['stuck'][:8]: print('  ⏸', s)

asyncio.run(main())
