"""오늘도 메멘토스! 밸런스 시뮬레이터 (개발용, 게임에는 포함되지 않음)

사용법: python3 tools/sim.py [index.html 경로] [판 수]
필요: pip install playwright && python3 -m playwright install chromium

index.html을 임시로 복사해 내부 함수를 window.__g로 노출한 뒤,
헤드리스 크롬에서 전략 3가지로 자동 플레이하고 지표를 출력합니다.
- greedy-first : 매 턴 가장 깊은 구역, 선택지는 항상 첫 번째 (아무 생각 없는 플레이)
- greedy-best  : 매 턴 가장 깊은 구역, 선택지는 미리 정한 선호 순서
- cautious     : 위험도 7 이상이면 승강장으로 물러나 위험도를 낮추고, 누군가 HP 40 이하·전투불능이면 귀환
"""
import json, os, statistics as st, sys, tempfile, collections
from playwright.sync_api import sync_playwright

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'index.html')
N = int(sys.argv[2]) if len(sys.argv) > 2 else 300
MARK = "render();\n}\n</script>"
HOOK = ("window.__g={get run(){return run},get S(){return S},set S(v){S=v},step,move,choose,newRun,ZONES,canEnter,endRun,SCRIPT,"
        "get ui(){return ui}};\n" + MARK)

JS = r"""
(a)=>{const g=window.__g,out=[];
const IDS=['joker','mona','ryuji','ann','yusuke','makoto','futaba','haru','akechi','kasumi'];
const PREF=[/특수/,/기책/,/들어간다/,/버스로/,/조사를/,/열어 본다/,/100엔/,/마셔/,/모나에게/,/같이 넘는다/,/중재/,/스킬|SP|와이어|로그만|추리/];
for(let k=0;k<a.n;k++){
 g.S=Object.assign(g.S,JSON.parse(JSON.stringify(a.state)));g.S.tips=['start','choose','tag','event'];g.S.tut=true;
 const ids=[...IDS].sort(()=>Math.random()-.5).slice(0,3);g.S.today=g.SCRIPT.days.length?g.SCRIPT.days[Math.floor(Math.random()*g.SCRIPT.days.length)].id:null;g.S.lastChains=[];
 g.newRun(ids);const r=g.run;r.manual=true;let guard=0,ch=0;const ev=[];
 while(r.phase!=='done'&&guard++<3000){
  if(r.phase==='choose'){
   const al=r.party.filter(m=>m.hp>0);
   if(a.strat==='cautious'&&(al.length<3||Math.min(...al.map(m=>m.hp))<=40)){g.endRun('retreat');break}
   const opts=[r.zone,...g.ZONES[r.zone].links].filter(g.canEnter);
   const order=a.strat==='cautious'&&r.heat>=7?['gate','pass','lost','plat']:['plat','lost','pass','gate'];
   g.move(order.find(o=>opts.includes(o)));continue}
  if(r.phase==='event'){ch++;const c=r.ev.choices;ev.push(r.ev.title);let i=c.findIndex(x=>!x.dis);
   if(a.strat!=='greedy-first')for(const p of PREF){const j=c.findIndex(x=>!x.dis&&p.test(x.label));if(j>=0){i=j;break}}
   g.choose(i);continue}
  g.step()}
 const x=g.ui.res;out.push({inc:x.inc,st:x.st,reason:x.reason,ch,ev,wipe:/긴급/.test(x.reason),ret:/자발/.test(x.reason),hidden:r.hidden,chainEnd:r.chains.some(x=>x.done),chainStart:r.chains.length,tags:r.tags.length,pairs:r.pairs.length,day:r.day&&r.day.id})}
return out}
"""

BASE = {"yen": 0, "props": [], "bus": 1, "pick": 0, "smoke": 1, "curry": 1,
        "codex": {"combos": [], "events": [], "hidden": [], "reports": 0, "best": 0}}
FULL = dict(BASE, props=["game", "tea", "easel", "cushion", "dart"], bus=4, pick=3)

def main():
    src = open(SRC, encoding='utf-8').read()
    assert src.count(MARK) == 1, 'index.html 끝부분 구조가 바뀌어 훅을 넣을 수 없습니다'
    tmp = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8')
    tmp.write(src.replace(MARK, HOOK)); tmp.close()
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.route('**/fonts.*/**', lambda r: r.abort())
        pg.goto('file://' + tmp.name)
        for label, state in [('기본', BASE), ('풀업', FULL)]:
            for strat in ['greedy-first', 'greedy-best', 'cautious']:
                res = pg.evaluate(JS, {"n": N, "state": state, "strat": strat})
                inc = [x['inc'] for x in res]; evc = collections.Counter(e for x in res for e in x['ev'])
                rows.append(dict(state=label, strat=strat, n=N, inc_mean=round(st.mean(inc)), inc_median=st.median(inc),
                                 wipe=round(sum(x['wipe'] for x in res) / N * 100, 1),
                                 retreat=round(sum(x['ret'] for x in res) / N * 100, 1),
                                 star5=round(sum(x['st'] == 5 for x in res) / N * 100, 1),
                                 choices=round(st.mean(x['ch'] for x in res), 2),
                                 quarrel=round(sum('의견 충돌' in x['ev'] for x in res) / N * 100, 1),
                                 hidden=round(sum(x['hidden'] for x in res) / N * 100, 1),
                                 chain_end=round(sum(x['chainEnd'] for x in res) / N * 100, 1),
                                 tags=round(st.mean(x['tags'] for x in res), 1),
                                 pairs=round(st.mean(x['pairs'] for x in res), 1)))
        b.close()
    os.unlink(tmp.name)
    hdr = ['state', 'strat', 'n', 'inc_mean', 'wipe', 'retreat', 'star5', 'choices', 'quarrel', 'chain_end', 'tags', 'pairs', 'hidden']
    print('| ' + ' | '.join(hdr) + ' |'); print('|' + '---|' * len(hdr))
    for r in rows: print('| ' + ' | '.join(str(r[h]) for h in hdr) + ' |')

if __name__ == '__main__':
    main()
