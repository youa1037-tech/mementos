"""index.html 안의 도트 데이터(ART)로 아틀라스 PNG와 메타데이터 JSON을 만든다.
sprite-atlas 계약: 영역 ID, 원본 크기, 위치, 기준점(pivot), 차지 칸(footprint), 레이어.
사용법: python3 tools/build_atlas.py  → docs/art/atlas.png, atlas.json, room.png
"""
import base64, json, os, tempfile
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(__file__), '..')
MARK = "render();\n}\n</script>"
JS = r"""()=>{const pad=2,ids=Object.keys(SPRB);let x=pad,h=0;const frames={};
for(const id of ids){const b=SPRB[id],f=FU[id];frames[id]={x,y:pad,w:b.w,h:b.h,layer:f.layer,footprint:[f.w,f.h],
 pivot:f.layer==='floor'?[b.w/2,b.h]:[b.w/2,b.h/2],flip:'horizontal mirror at runtime'};x+=b.w+pad;h=Math.max(h,b.h)}
const c=document.createElement('canvas');c.width=x;c.height=h+pad*2;const g=c.getContext('2d');
for(const id of ids)g.drawImage(sprC(id,0),frames[id].x,frames[id].y);
const r=document.createElement('canvas');r.width=ART.W;r.height=ART.H;r.getContext('2d').drawImage(bake(ART.roomBase(),0),0,0);
return {atlas:c.toDataURL(),room:r.toDataURL(),meta:{version:1,cell:ART.TILE,palette:ART.PAL,room:{w:ART.W,h:ART.H,cols:ART.RW,rows:ART.RH,wall_rows:ART.WALL},frames}}}"""
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
assert src.count(MARK) == 1
tmp = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8')
tmp.write(src.replace(MARK, "window.__atlas=" + JS + ";\n" + MARK)); tmp.close()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.route('**/fonts.*/**', lambda r: r.abort())
    pg.goto('file://' + tmp.name); out = pg.evaluate('window.__atlas()'); b.close()
os.unlink(tmp.name)
d = os.path.join(ROOT, 'docs', 'art'); os.makedirs(d, exist_ok=True)
for k in ['atlas', 'room']:
    open(os.path.join(d, k + '.png'), 'wb').write(base64.b64decode(out[k].split(',')[1]))
json.dump(out['meta'], open(os.path.join(d, 'atlas.json'), 'w'), ensure_ascii=False, indent=1)
print('ok', len(out['meta']['frames']), 'frames')
