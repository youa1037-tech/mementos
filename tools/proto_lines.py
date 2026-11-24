"""proto/index.html에 시제품용 대사를 넣는다 (개발용)

사용법: python3 tools/proto_lines.py
본 게임 index.html의 SCRIPT 블록(= content/script.xlsx 내용)에서 시제품 파티(PARTY) 대사만 골라
proto/index.html의 /*LINES-BEGIN*/ ... /*LINES-END*/ 사이를 바꾼다. 대사는 고치지 않고 자리만 옮긴다.
"""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), '..')
PARTY = {'joker', 'mona', 'ryuji', 'ann', 'yusuke', 'makoto', 'futaba', 'haru', 'akechi', 'kasumi'}

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
a = src.index('/*SCRIPT-BEGIN*/const SCRIPT=') + len('/*SCRIPT-BEGIN*/const SCRIPT=')
S = json.loads(src[a:src.index(';/*SCRIPT-END*/', a)])


def ok(cs):
    """조건 중 시제품 파티 밖 사람이 걸린 줄은 뺀다 (분위기 같은 수치 조건은 무시)"""
    for c in cs or []:
        if c.get('k') == 'target' and c.get('v') not in PARTY:
            return False
        if c.get('k') == 'party' and not set(c.get('v') or []) <= PARTY:
            return False
    return True


lines = {}
for l in S['lines']:
    if l['who'] in PARTY and ok(l.get('c')):
        tg = next((c['v'] for c in l.get('c') or [] if c.get('k') == 'target'), None)
        lines.setdefault(l['who'], {}).setdefault(l['k'], []).append([l['t'], tg] if tg else l['t'])

pairs = [{'a': p['a'], 'b': p['b'], 'qa': p['qa'], 'qb': p['qb'], 'end': p.get('end')}
         for p in S['pairs'] if p['a'] in PARTY and p['b'] in PARTY and ok(p.get('c'))]
chem = [{'a': c['a'], 'b': c['b'], 'qa': c['qa'], 'qb': c['qb'], 'end': c.get('end')}
        for c in S['chem']['lines'] if c['a'] in PARTY and c['b'] in PARTY]
solo = [{'who': x['who'], 'n': x['n'], 'q': x['q']} for x in S['solo'] if x['who'] in PARTY]
reaper = [x['t'] for x in S['reaper'] if not x.get('who')]

data = {'lines': lines, 'pairs': pairs, 'chem': chem, 'solo': solo, 'reaper': reaper}
p = os.path.join(ROOT, 'proto', 'index.html')
html = open(p, encoding='utf-8').read()
b0 = html.index('/*LINES-BEGIN*/') + len('/*LINES-BEGIN*/')
b1 = html.index('/*LINES-END*/')
html = html[:b0] + 'const LINES=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';' + html[b1:]
open(p, 'w', encoding='utf-8').write(html)
n = sum(len(v) for w in lines.values() for v in w.values())
print(f'기본대사 {n} · 쌍대사 {len(pairs)} · 케미 {len(chem)} · 단독행동 {len(solo)} · 거두는 자 {len(reaper)}')
