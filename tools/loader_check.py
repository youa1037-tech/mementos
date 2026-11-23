"""로딩 화면 검사: 구글 폰트가 막힘/느림/무응답일 때, 본 스크립트가 죽었을 때 로딩 화면이 제때 걷히는지 (개발용)
사용법: python3 -I tools/loader_check.py
"""
import time,os,sys
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));P='file://'+ROOT+'/index.html'
JS="""()=>{const l=document.getElementById('loader');return l?(l.classList.contains('out')?'out':'on'):'gone'}"""
def run(name,mode,reduced=False,breakjs=False):
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},reduced_motion='reduce' if reduced else 'no-preference')
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    def fonts(r):
      if mode=='fail':r.abort()
      elif mode=='hang':pass
      else:time.sleep(mode);r.fulfill(status=200,content_type='text/css',body='/*x*/')
    pg.route('**/fonts.googleapis.com/**',fonts);pg.route('**/fonts.gstatic.com/**',lambda r:r.abort())
    if breakjs:pg.route('**/index.html',lambda r:r.fulfill(body=open(ROOT+'/index.html',encoding='utf-8').read().replace('const TYPES={','throw 0;const TYPES={',1),content_type='text/html'))
    t0=time.time();pg.goto(P,wait_until='commit')
    pg.wait_for_selector('#loader',state='attached',timeout=5000)
    first=pg.evaluate(JS);t_out=None;seen=[]
    while time.time()-t0<7:
      st=pg.evaluate(JS)
      if st!='on' and t_out is None:t_out=round(time.time()-t0,2)
      if st=='gone':break
      time.sleep(.05)
    app=pg.evaluate("document.getElementById('app').children.length")
    print(f"{name:28s} first={first} hidden_at={t_out}s final={pg.evaluate(JS)} app_rendered={app>0} errs={len(errs)}")
    b.close()
run('fonts blocked','fail')
run('fonts slow 1.2s',1.2)
run('fonts hang (timeout)','hang')
run('reduced motion, blocked','fail',reduced=True)
run('main script crashes','fail',breakjs=True)
