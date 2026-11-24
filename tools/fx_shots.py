"""전투 이펙트 연출 스크린샷: 한 동작을 시간순 프레임으로 찍어 한 장(contact sheet)으로 붙인다.
  python3 tools/fx_shots.py . out.png ann,joker,mona 0 8 100 "<찍기 전 실행할 JS>"   (4번째: 스킬 번호 또는 data-a 값, 예: allout)
  DSF=1 이면 1배율로 작게
"""
import asyncio, sys, os, http.server, threading, functools
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw

ROOT, OUT, PARTY, SK = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]
N = int(sys.argv[5]) if len(sys.argv) > 5 else 12
STEP = int(sys.argv[6]) if len(sys.argv) > 6 else 90
PRE = sys.argv[7] if len(sys.argv) > 7 else ''

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
    threading.Thread(target=s.serve_forever, daemon=True).start(); return s

async def main():
    srv = serve(); url = f'http://127.0.0.1:{srv.server_address[1]}/index.html'
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=int(os.environ.get('DSF','2')))
        pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        await pg.goto(url); await pg.wait_for_timeout(600)
        await pg.evaluate("SV.tutOff=true;SV.mute=true;save()")
        await pg.evaluate(f"newRun({PARTY!r})"); await pg.wait_for_timeout(300)
        await pg.evaluate("G.story=null;G.ev=null;G.pick=null;ui.screen='map';startBattle('normal')")
        await pg.wait_for_timeout(1500)
        if PRE: await pg.evaluate(PRE); await pg.wait_for_timeout(200)
        st = await pg.query_selector('.stage'); box = await st.bounding_box()
        clip = {'x': 0, 'y': max(0, box['y'] - 10), 'width': 360, 'height': box['height'] + 20}
        await pg.click(f'[data-a="sk:{SK}"]' if SK.isdigit() else f'[data-a="{SK}"]')
        frames = []
        for i in range(N):
            frames.append(await pg.screenshot(clip=clip))
            await pg.wait_for_timeout(STEP)
        ims = [Image.open(__import__('io').BytesIO(f)) for f in frames]
        w, h = ims[0].size; cols = 4; rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (w * cols, (h + 30) * rows), '#222')
        d = ImageDraw.Draw(sheet)
        for i, im in enumerate(ims):
            x, y = (i % cols) * w, (i // cols) * (h + 30)
            sheet.paste(im, (x, y + 30)); d.text((x + 8, y + 6), f'{i*STEP}ms', fill='white')
        sheet.save(OUT)
        print('errors', errs)
asyncio.run(main())
