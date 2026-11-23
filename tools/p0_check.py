"""P0 회귀 검사: 리뷰에서 나온 신뢰 버그와 선택의 값(무리수 손실·정석 보너스·기세)이 유지되는지 확인 (개발용)

사용법: python3 tools/p0_check.py [index.html 경로]
크롬 경로를 지정하려면 CHROME=/usr/bin/google-chrome
"""
import tempfile,json,sys,os
from playwright.sync_api import sync_playwright
src=open(sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),'..','index.html'),encoding='utf-8').read()
MARK="render();\n}\n</script>"
assert src.count(MARK)==1
HOOK="window.__g={get run(){return run},set run(v){run=v},get S(){return S},get ui(){return ui},step,move,choose,newRun,endRun,useCurry,saveRun,resumeRun,relicOffer,pickCut,EVENTS,render,SCRIPT,typeof_payout:typeof payout,hp,momShift,spillAmt,save};\n"+MARK
tmp=tempfile.NamedTemporaryFile('w',suffix='.html',delete=False,encoding='utf-8',dir='/tmp');tmp.write(src.replace(MARK,HOOK));tmp.close()
ok=True
def check(name,cond,info=''):
  global ok;ok&=bool(cond);print(('PASS' if cond else 'FAIL'),name,info)
TOCHOOSE="""()=>{const g=window.__g;g.S.tut=true;g.S.tips=['start','choose','tag','event'];g.newRun(['joker','haru','ryuji']);const r=g.run;r.manual=true;let k=0;
 while(r.phase!=='choose'&&k++<500){if(r.phase==='event'){g.choose(r.ev.choices.findIndex(x=>!x.dis));continue}g.step()}return r.phase}"""
with sync_playwright() as p:
  b=p.chromium.launch(**({'executable_path':os.environ['CHROME']} if os.environ.get('CHROME') else {}));pg=b.new_page()
  errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('**/fonts.*/**',lambda r:r.abort())
  pg.goto('file://'+tmp.name);pg.evaluate('localStorage.clear()');pg.reload()
  # 1a 역 선택 화면에서 카레 → 이어하기: HP 100 · 카레 0
  check('choose phase reached',pg.evaluate(TOCHOOSE)=='choose')
  pg.evaluate("()=>{const g=window.__g,h=g.run.party.find(m=>m.id==='haru');g.run.party.forEach(m=>m.hp=100);h.hp=90;g.S.curry=1;g.saveRun();g.useCurry()}")
  pg.reload();r=pg.evaluate("()=>{const g=window.__g;g.resumeRun();return {hp:g.run.party.find(m=>m.id==='haru').hp,curry:g.S.curry}}")
  check('curry at choose then continue',r=={'hp':100,'curry':0},r)
  pg.reload();r=pg.evaluate("()=>{const g=window.__g;g.resumeRun();return {hp:g.run.party.find(m=>m.id==='haru').hp,curry:g.S.curry}}")
  check('second continue no double use',r=={'hp':100,'curry':0},r)
  # 1b 턴 중간에 카레 → 이어하기: 체크포인트로 함께 되감김 (HP 90 · 카레 1)
  pg.evaluate("()=>{const g=window.__g,h=g.run.party.find(m=>m.id==='haru');h.hp=90;g.S.curry=1;g.saveRun();const cur=g.run.map.st[g.run.at];g.move(cur.id);g.useCurry()}")
  mid=pg.evaluate("()=>({ph:window.__g.run.phase,c:window.__g.S.curry})")
  pg.reload();r=pg.evaluate("()=>{const g=window.__g;g.resumeRun();return {hp:g.run.party.find(m=>m.id==='haru').hp,curry:g.S.curry}}")
  check('curry mid-turn rewinds with run',r=={'hp':90,'curry':1},{'mid':mid,'after':r})
  # 3 귀환 예상액 = 정산
  r=pg.evaluate("""()=>{const g=window.__g,r=g.run;r.yen=1704;r.tval=0;r.heat=4;r.phase='choose';g.render();const t=document.querySelector('.cash p').innerText;g.endRun('retreat');return {t,inc:g.ui.res.inc}}""")
  import re as _re
  est=int(_re.search(r'¥([\d,]+)',r['t']).group(1).replace(',',''))
  check('cashout estimate matches report',est==r['inc'] and '위험 수당 ¥68' in r['t'],{'est':est,'inc':r['inc']})
  # 4 막차 승차권
  r=pg.evaluate("""()=>{const g=window.__g;let five=0,seven=0;for(let i=0;i<400;i++){g.newRun(['joker','mona','ann']);g.run.manual=true;g.run.maxT=i%2?5:7;g.run.relics=[];const o=g.relicOffer();o[1].fn();const x=g.run.ev.choices.map(c=>c.label).join();if(x.includes('막차'))i%2?five++:seven++}return {five,seven}}""")
  check('R-13 never offered in 5-turn run',r['five']==0 and r['seven']>0,r)
  # 5 결정적 1컷
  r=pg.evaluate("""()=>{const g=window.__g,bad=[];for(let i=0;i<300;i++){g.newRun(['joker','mona','ann']);const r=g.run;r.moments=i%3?[]:[{k:'케미 반전',score:50,v:{}}];const c=g.pickCut(r,5000);if(/\\{|(^|[\\s:])\\(|\\(\\)/.test(c.t))bad.push(c.t)}return bad.slice(0,3)}""")
  check('cut lines have no empty names',not r,r)
  # 6 사건 대표 대사
  r=pg.evaluate("""()=>{const g=window.__g;g.newRun(['joker','ann','ryuji']);const e=g.EVENTS.find(x=>x.id==='E-012');const out=[];for(let i=0;i<20;i++){const d=e.make();out.push([d.who,d.q])}return out}""")
  check('stand-in speaker omits generic find quote',all(w is None and q is None for w,q in r),r[:2])
  # 7 결정적 1컷: 쓰러지기 직전까지 몰린 판은 '평범한 날'이 아니다
  r=pg.evaluate("""()=>{const g=window.__g;g.newRun(['joker','mona','ann']);const r=g.run;r.moments=[];const m=r.party[1];g.hp(m,-(m.hp-15));return g.pickCut(r,4000)}""")
  check('close call becomes 구사일생 cut',r['k']=='구사일생' and '모르가나' in r['t'],r)
  # 8 선택의 값: 무리수 손실과 정석 보너스가 선택지에 숫자로 보인다
  r=pg.evaluate("""()=>{const g=window.__g;g.newRun(['joker','mona','ann']);const r=g.run;r.yen=3000;r.heat=5;const e=g.EVENTS.find(x=>x.id==='E-008').make();
   return {a:e.choices[0].sub,b:e.choices[1].sub,c:e.choices[2].sub,spill:g.spillAmt()}}""")
  check('gamble shows yen at risk',r['spill']==660 and '실패\u00a0시\u00a0-\u2060¥660' in r['a'],r)
  check('steady choice shows bonus',('정석\u00a0보너스' in r['b']) and ('정석' not in r['a']) and ('-¥' not in r['c']),r)
  # 9 기세: 한 칸당 탐색 수확 ±15%, HUD에 FLOW 표시
  r=pg.evaluate("""()=>{const g=window.__g;g.S.codex.reports=5;g.newRun(['joker','mona','ann']);g.run.mom=0;g.momShift(1);g.momShift(1);g.momShift(5);g.ui.screen='explore';g.render();return {mom:g.run.mom,hud:(document.querySelector('#flowtag')||{}).innerText||''}}""")
  check('momentum clamps and shows in HUD',r['mom']==3 and 'FLOW ▲3' in r['hud'],r)
  # 10 쉬는 시간: 고른 두 사람의 관계·HP·기세·도감
  r=pg.evaluate("""()=>{const g=window.__g;g.newRun(['joker','mona','ann']);const r=g.run;r.mom=0;r.party.forEach(m=>m.hp=50);const e=g.EVENTS.find(x=>x.id==='break').make();
   const out=e.choices[0].go();const f=out[out.length-1];if(f.fn)f.fn();const k=['joker','mona'].sort().join('+');
   return {n:e.choices.length,mom:r.mom,hp:r.party[0].hp,rel:(r.rel||{})[k]||null,cx:(g.S.codex.breaks||[]).includes(k),again:e.choices.length}}""")
  check('break scene bonds a pair',r['mom']==1 and r['hp']==60 and r['rel']=='의기투합' and r['cx'] and r['n']==4,r)
  # 11 영구 관계·기억·컨디션·소원 (docs/persistence.md)
  r=pg.evaluate("""()=>{const g=window.__g,S=g.S;S.tut=true;S.bonds={'akechi+joker':{aff:85,last:'냉전'}};S.mems={ryuji:[{id:'MEM_SAVED',t:'ann',ttl:1}]};S.cond={ryuji:{streak:3,rest:0},ann:{streak:0,rest:2}};S.wish={ryuji:{step:2,prog:0}};S.codex.cards=[];
   g.newRun(['joker','akechi','mona']);const a={rel:g.run.rel['akechi+joker'],mood:g.run.mood};
   g.newRun(['ryuji','ann','mona']);const r=g.run;const b={c1:r.cond.ryuji,c2:r.cond.ann};r.reaper=true;r.relSeen={'ann+ryuji':['의기투합']};r.rel={'ann+ryuji':'의기투합'};g.endRun('retreat');
   const x=g.ui.res;return {...a,...b,mem:(S.mems.ryuji||[]).map(m=>m.id),aff:S.bonds['ann+ryuji'].aff,streak:S.cond.ryuji.streak,rest:S.cond.akechi?S.cond.akechi.rest:null,card:S.codex.cards,wish:S.wish.ryuji,after:x.after.some(l=>/라멘|류지/.test((l.q||l.n||''))),log:x.pz.wish.find(w=>w.id==='ryuji')}}""")
  check('bond carries last state and Lv3 mood',r['rel']=='냉전' and r['mood']>=68,r)
  check('condition from streak/rest',r['c1']=='tired' and r['c2']=='fresh',r)
  check('memory ttl expires and new ones land',('MEM_SAVED' not in r['mem']) and ('MEM_REAPER' in r['mem']) and r['aff']==10,r)
  check('wish completes → ending card',r['card']==['ryuji'] and r['wish']['step']==3 and r['log'].get('card'),r)
  check('no page errors',not errs,errs[:3])
  b.close()
print('ALL OK' if ok else 'SOME FAILED');sys.exit(0 if ok else 1)
