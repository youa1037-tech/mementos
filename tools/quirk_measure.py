"""구조 개편 측정: 여러 판을 자동으로 돌려 성격 사고·지휘 창·큰 사건·자동 처리 횟수와 판 수입을 잰다 (개발용)
사용법: python3 -I tools/quirk_measure.py legacy.html 100 rand|leave
첫 판(#0)은 튜토리얼을 건너뛴 탓에 편성 화면으로 빠질 수 있음 — 무시
"""
import tempfile,json,sys,os
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();N=int(sys.argv[2]);MODE=sys.argv[3]
MARK="render();\n}\n</script>"
HOOK="window.__g={get run(){return run},get S(){return S},get ui(){return ui},step,move,choose,newRun,render,resolveQuirk:typeof resolveQuirk!=='undefined'?resolveQuirk:null,CHARS};\n"+MARK
tmp=tempfile.NamedTemporaryFile('w',suffix='.html',delete=False,encoding='utf-8',dir='/tmp');tmp.write(src.replace(MARK,HOOK));tmp.close()
JS="""([N,MODE])=>{const g=window.__g,ids=g.CHARS.map(c=>c.id),out=[];
 const pickParty=i=>{const a=[...ids];for(let k=a.length-1;k>0;k--){const j=Math.floor(Math.random()*(k+1));[a[k],a[j]]=[a[j],a[k]]}return a.slice(0,3)};
 for(let n=0;n<N;n++){const S=g.S;S.tut=true;S.hintsOff=true;S.tips=['start','choose','tag','event'];S.yen=0;S.smoke=1;S.curry=0;
  g.newRun(pickParty(n));g.ui.screen='explore';const r=g.run;r.manual=true;const st={ev:0,relic:0,cmd:0,mv:0,qk:0,err:''};let k=0;
  try{while(g.run&&g.run.phase!=='done'&&k++<3000){const R=g.run;
   if(R.cmd){st.cmd++;const m=MODE==='leave'?'leave':['stop','boost','tag','leave'][Math.floor(Math.random()*4)];g.resolveQuirk(m);continue}
   if(R.phase==='event'){if(R.evId==='relic')st.relic++;else st.ev++;const i=R.ev.choices.findIndex(x=>!x.dis);g.choose(i);continue}
   if(R.phase==='choose'){st.mv++;g.render();const b=[...document.querySelectorAll('#app button[data-act^="move:"]:not(:disabled)')];if(!b.length){st.err='nomove:#'+n+':t'+R.turn+':'+R.zone+':'+[...document.querySelectorAll('#app [data-act]')].map(x=>x.dataset.act).filter(a=>!/^(pause|speed|manual|mute|curry|retreat|next|ff)/.test(a)).slice(0,8).join(',');break}b[Math.floor(Math.random()*b.length)].click();continue}
   const n0=R.log.length,q0=R.q.length;g.step();if(g.run&&g.run.phase==='running'&&!g.run.cmd&&g.run.log.length===n0&&g.run.q.length===q0){st.err='stuck:q='+q0+':hold='+!!g.run.hold+':'+(g.run.log.slice(-2).map(b=>(b.text||b.n||'').slice(0,40)).join('|'));break}}}catch(e){st.err=String(e).slice(0,120)}
  const R=g.run;st.qk=R?(R.qn||0):-1;st.yen=R?R.yen:0;st.turn=R?R.turn:0;st.auto=R?R.log.filter(b=>/^\\[성격대로\\]/.test(b.n||'')).length:0;st.ph=R?R.phase:'none';out.push(st)}
 return out}"""
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:150]))
  pg.route('**/fonts.*/**',lambda r:r.abort())
  pg.goto('file://'+tmp.name);pg.evaluate('localStorage.clear()');pg.reload()
  res=pg.evaluate(JS,[N,MODE]);b.close()
avg=lambda k:sum(x[k] for x in res)/len(res)
print(f"runs={len(res)} done={sum(x['ph']=='done' for x in res)} errs={len([x for x in res if x['err']])} pageerr={len(errs)}")
for k in ['qk','cmd','ev','relic','auto','mv','yen']:print(f"  {k:6s} avg={avg(k):.2f}")
import collections;print('  qk dist',sorted(collections.Counter(x['qk'] for x in res).items()));print('  big-ev dist',sorted(collections.Counter(x['ev'] for x in res).items()))
import collections as C;print('  errs',C.Counter(x['err'].split(':')[0] for x in res if x['err']));[print('   ',e) for e in list(dict.fromkeys(x['err'] for x in res if x['err']))[:6]];print('  pageerrs',errs[:3])
