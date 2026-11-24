"""새 코어 기능별 확인 (core_smoke.py가 못 누르는 흐름)
  1 이어하기: 판 도중 새로고침 → CONTINUE → 같은 층·위치·템으로 돌아오나
  2 기록 슬롯: 저장 → 지갑 바꿈 → 불러오기 → 되돌아오나
  3 거두는 자: 경계도를 최대 직전으로 두고 한 칸 → 거두는 자 전투가 열리나, RETURN NOW로 나가지나
  4 전투 중 새로고침: 이어하기가 지도에서 다시 시작하나 (전투 중엔 저장 안 함)
  python3 tools/core_scenarios.py
"""
import asyncio, os, http.server, threading, functools, json
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
    threading.Thread(target=s.serve_forever, daemon=True).start(); return s

FAST = "(()=>{const S=window.setTimeout.bind(window);window.setTimeout=(f,ms,...a)=>S(f,(ms||0)*.05,...a)})()"
RES = []
def ok(name, cond, note=''):
    RES.append((name, bool(cond), note)); print(('  ✔ ' if cond else '  ✘ ') + name + (f' — {note}' if note else ''))

async def start_run(pg):
    await pg.evaluate("SV.tutOff=true;save();ui.screen='hub';ui.ht='go';ui.ps=null;render()")
    await pg.evaluate("newRun(['ryuji','joker','mona'])")
    await pg.wait_for_timeout(200)

async def walk_to_fresh(pg, n=3):
    """싸움 없는 이동이 되도록 방 종류와 무관하게 이웃으로 n칸 (전투가 열리면 이긴 걸로 정리)"""
    for _ in range(n):
        await pg.evaluate("""(()=>{if(G.battle){for(const f of G.battle.foes)f.hp=0;checkWin()}if(G.ev){G.ev=null}if(G.pick){G.pick=null}G.story=null;ui.screen='map';ui.busy=false;render();
          const nb=G.map.adj(G.at).filter(i=>G.map.T[i]!=='boss');move(nb[0])})()""")
        await pg.wait_for_timeout(250)
    await pg.evaluate("""(()=>{if(G.battle){for(const f of G.battle.foes)f.hp=0;checkWin()}G.ev=null;G.pick=null;G.story=null;ui.busy=false;ui.screen='map';render();runSave()})()""")
    await pg.wait_for_timeout(200)

async def main():
    srv = serve(); url = f'http://127.0.0.1:{srv.server_address[1]}/index.html'
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width': 360, 'height': 740})
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        await pg.add_init_script(FAST); await pg.goto(url); await pg.wait_for_timeout(500)

        print('1 이어하기')
        await start_run(pg); await walk_to_fresh(pg, 3)
        before = await pg.evaluate("JSON.stringify({fl:G.fl,at:G.at,risk:G.risk,items:G.items,hp:G.party.map(m=>m.hp),yen:G.yen})")
        saved = await pg.evaluate("!!localStorage.getItem('mm-run')"); ok('지도에서 판이 자동 저장된다', saved)
        await pg.reload(); await pg.wait_for_timeout(500)
        has = await pg.evaluate("!!document.querySelector('[data-a=\"cont\"]')"); ok('새로고침 뒤 처음 화면에 CONTINUE', has)
        if has:
            await pg.click('[data-a="cont"]'); await pg.wait_for_timeout(300)
            after = await pg.evaluate("JSON.stringify({fl:G.fl,at:G.at,risk:G.risk,items:G.items,hp:G.party.map(m=>m.hp),yen:G.yen})")
            ok('이어하기로 같은 상태(층·위치·위험도·템·HP·엔)', before == after, '' if before == after else f'{before} → {after}')
            scr = await pg.evaluate("ui.screen"); ok('이어하기 뒤 지도 화면', scr == 'map', scr)

        print('4 전투 중 새로고침')
        await pg.evaluate("startBattle('normal')"); await pg.wait_for_timeout(200)
        await pg.reload(); await pg.wait_for_timeout(500)
        has = await pg.evaluate("!!document.querySelector('[data-a=\"cont\"]')"); ok('전투 중 새로고침해도 CONTINUE가 남는다', has)
        if has:
            await pg.click('[data-a="cont"]'); await pg.wait_for_timeout(300)
            scr = await pg.evaluate("ui.screen"); ok('전투 중 새로고침 → 지도에서 다시', scr == 'map', scr)

        print('2 기록 슬롯')
        await pg.evaluate("SV.yen=12345;save();ui.screen='hub';ui.ht='rec';render()"); await pg.wait_for_timeout(200)
        btn = await pg.query_selector('[data-a="ssave:0"]'); ok('기록 탭에 슬롯 저장 버튼', btn)
        if btn:
            await btn.click(); await pg.evaluate("SV.yen=1;save();render()"); await pg.wait_for_timeout(100)
            lb = await pg.query_selector('[data-a="sload:0"]'); ok('저장한 슬롯에 불러오기 버튼', lb)
            if lb:
                await lb.click(); await pg.wait_for_timeout(200)
                y = await pg.evaluate("SV.yen"); ok('불러오면 지갑이 저장 때로', y == 12345, f'¥{y}')
                await pg.reload(); await pg.wait_for_timeout(400)
                y2 = await pg.evaluate("SV.yen"); ok('불러온 기록이 새로고침 뒤에도 유지', y2 == 12345, f'¥{y2}')

        print('3 거두는 자')
        await start_run(pg)
        await pg.evaluate("G.risk=RISK_MAX-1;render()")
        await pg.evaluate("(()=>{const nb=G.map.adj(G.at).filter(i=>G.map.T[i]!=='boss');move(nb[0])})()"); await pg.wait_for_timeout(400)
        k = await pg.evaluate("G.battle&&G.battle.kind"); ok('경계도 최대에서 거두는 자 전투', k == 'reaper', str(k))
        r = await pg.query_selector('[data-a="ret"]'); ok('거두는 자 전투에 RETURN NOW', r)
        if r:
            await r.click(); await pg.wait_for_timeout(300)
            scr = await pg.evaluate("ui.screen+':'+(G.end&&G.end.kind)"); ok('RETURN NOW → 결과 화면', scr.startswith('result'), scr)

        ok('페이지 에러 없음', not errs, ' | '.join(errs[:3]))
        await b.close()
    srv.shutdown()
    json.dump([{'name': n, 'ok': o, 'note': t} for n, o, t in RES], open(os.path.join(ROOT, 'docs', 'scenarios.json'), 'w'), ensure_ascii=False, indent=1)

asyncio.run(main())
