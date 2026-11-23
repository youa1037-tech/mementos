"""1단계 UI 검사: 지휘 창 표시 · 키 2 부추김 · 자동 정지 토글 · 작전 방침 삭제 · 백업 버튼 · 초기화 (개발용)
사용법: python3 -I tools/ui_check.py
"""
import os
import tempfile,sys,time
from playwright.sync_api import sync_playwright
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','index.html'),encoding='utf-8').read()
MARK="render();\n}\n</script>"
src=src.replace(MARK,"window.__g={get run(){return run},get S(){return S},get ui(){return ui},step,newRun,render,save,choose,get tq(){return tq},tutRun,cmdOk};\n"+MARK)
tmp=tempfile.NamedTemporaryFile('w',suffix='.html',delete=False,encoding='utf-8',dir='/tmp');tmp.write(src);tmp.close()
ok=True
def ck(n,c,i=''):
  global ok;ok&=bool(c);print('PASS' if c else 'FAIL',n,i)
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('**/fonts.*/**',lambda r:r.abort());pg.goto('file://'+tmp.name);pg.evaluate('localStorage.clear()');pg.reload();time.sleep(.5)
  # 지휘 창 열릴 때까지 진행
  r=pg.evaluate("""()=>{const g=window.__g,S=g.S;S.tut=true;S.hintsOff=true;S.tips=['start','choose','tag','event'];S.tutorialStep=['T-1','T-2','T-3','T-4','T-5','T-6','T-7','T-8'];
   for(let t=0;t<40;t++){g.newRun(['ryuji','haru','mona']);g.ui.screen='explore';const R=g.run;R.manual=true;let k=0;
    while(R.phase!=='done'&&!R.cmd&&k++<800){if(R.phase==='event'){g.choose(R.ev.choices.findIndex(x=>!x.dis));continue}
     if(R.phase==='choose'){g.render();const bs=[...document.querySelectorAll('#app button[data-act^="move:"]:not(:disabled)')];if(!bs.length)break;bs[Math.floor(Math.random()*bs.length)].click();continue}g.step()}
    if(R.cmd){R.manual=false;g.render();return {ok:true,t,id:R.cmd.id,n:R.nudge}}}return {ok:false,qn:g.run.qn,nudge:g.run.nudge,tq:!!g.tq,tut:g.tutRun(),cmdOk:g.cmdOk(),ph:g.run.phase,turn:g.run.turn}}""")
  ck('command window opens',r.get('ok'),r)
  pg.evaluate("window.__g.render()");time.sleep(.3)
  ck('cmdwin rendered',pg.locator('.cmdwin').count()==1)
  pg.screenshot(path='/tmp/cmd.png')
  pg.keyboard.press('2');time.sleep(.3)
  r2=pg.evaluate("()=>({n:window.__g.run.nudge,cmd:!!window.__g.run.cmd,last:window.__g.run.log.slice(-3).map(b=>(b.text||b.n||'')+' '+(b.res||''))})")
  ck('key 2 = boost uses one command',r2['n']==r['n']-1 and not r2['cmd'],r2)
  # 설정 토글
  pg.evaluate("()=>{const g=window.__g;g.run.phase='done';g.ui.screen='party';g.ui.pMore=true;g.render()}");time.sleep(.2)
  t=pg.locator('button[data-act="cmdstop"]');ck('auto-stop toggle visible',t.count()==1)
  if t.count():t.click();time.sleep(.1)
  ck('toggle sets S.cmdStop',pg.evaluate("window.__g.S.cmdStop===true"))
  ck('no ORDERS chips',pg.locator('[data-act^="pol:"]').count()==0)
  # 초기화 버그
  pg.evaluate("()=>{localStorage.setItem('todays-mementos-run','{\"x\":1}');const g=window.__g;g.ui.screen='shop';g.render()}");time.sleep(.2)
  ck('backup/load buttons',pg.locator('[data-act="backup"]').count()==1 and pg.locator('[data-act="restore"]').count()==1)
  pg.click('[data-act="reset"]');pg.click('[data-act="reset"]');time.sleep(.2)
  ck('reset clears run save',pg.evaluate("localStorage.getItem('todays-mementos-run')")is None)
  ck('no page errors',not errs,errs[:3])
  b.close()
print('ALL OK' if ok else 'SOME FAIL')
