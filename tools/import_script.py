"""대사·스크립트 시트(xlsx)를 게임 데이터로 바꿔 index.html에 넣는다.

사용법: python3 tools/import_script.py [content/script.xlsx] [--only-done]
  --only-done  상태가 '완료'·'게임 반영'인 줄만 넣음 (기본: 빈 줄 빼고 전부)

- 조건·효과 표기를 구조화된 데이터로 바꾸고, 모르는 표기는 끝에 보고한다.
- 사건·사건선택지·후일담의 '게임 반영' 줄은 코드에 이미 있는 것이라 건너뛴다.
- 기본대사·단독행동은 시트가 원본이다('게임 반영' 줄도 그대로 씀).
- 밸런스 조정(BALANCE)은 시트 숫자 위에 덮어쓴다. 바뀐 내용은 docs/script-import.md에 남는다.
"""
import json, os, re, sys

SEP = re.compile(r'\s+·\s*|\s*·\s+')  # ' · '로 나눔. '커피·홍차'처럼 붙은 가운뎃점은 이름의 일부
from openpyxl import load_workbook

ROOT = os.path.join(os.path.dirname(__file__), '..')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
ONLY_DONE = '--only-done' in sys.argv
SRC = args[0] if args else os.path.join(ROOT, 'content', 'script.xlsx')

CH = {'조커': 'joker', '모르가나': 'mona', '류지': 'ryuji', '안': 'ann', '유스케': 'yusuke', '마코토': 'makoto',
      '후타바': 'futaba', '하루': 'haru', '아케치': 'akechi', '카스미': 'kasumi'}
ZONE = {'승강장': 'gate', '통로': 'pass', '보관실': 'lost', '플랫폼': 'plat'}
SIT = {'발견': 'find', '잡담': 'chat', '대답': 'reply', '회복·지원': 'support', '감싸기': 'protect', '피격': 'hurt',
       '승리': 'win', '함정 감지': 'trap', '보물': 'treasure', '섀도 조우': 'enemy', '말다툼': 'argue', '기책': 'gambit',
       '귀환 인사': 'back'}
RESULT = {'완주': 'complete', '귀환': 'retreat', '전멸': 'forced', '히든': 'hidden'}
PROP = {'레트로 게임기': 'game', '커피·홍차 세트': 'tea', '화구·이젤 세트': 'easel', '고양이 방석': 'cushion', '다트 보드': 'dart'}
STAGE = {'발견': 'find', '전개': 'grow', '결말': 'end', '후일담': 'after', '놓쳤을 때': 'miss'}
CLUE = '단서: 지도에 없는 선로'

# 시트 숫자 위에 덮어쓰는 밸런스 조정 (이유는 docs/script-import.md)
BALANCE = {
    ('E-001', 'title'): {'title': '노골적인 보물상자'},
    ('E-001', 'B'): {'ok_fx': 'SP-15 · 보물+1 · 태그:완벽한 추리 · MVP+3', 'sub': 'SP -15 · 안전하지만 보물 1개'},
    ('E-004', 'B'): {'ok_fx': 'SP-15 · 엔+400~600 · MVP+3', 'sub': 'SP -15 · 무피해, 보상은 적음'},
    ('E-008', 'B'): {'p': 0.85, 'ok_fx': 'SP-14 · 보물+1 · 엔+500 · MVP+2', 'sub': 'SP -14 · 안전하지만 보물 1개'},
    ('E-009', 'A'): {'ok_fx': '보물+2 · 엔+800~1100 · 태그:심야 열차 탑승 · MVP+3'},
    ('E-013', 'B'): {'ok_fx': 'SP-15 · 보물+1 · 엔+500 · MVP+2', 'sub': 'SP -15 · 확실하지만 보물 1개'},
    ('E-017', 'B'): {'p': 0.85, 'ok_fx': 'SP-10 · 엔+400 · 보물+1 · MVP+2'},
    ('E-019', 'B'): {'ok_fx': 'SP-10 · 보물+1 · MVP+2', 'sub': 'SP -10 · 안전하게 상자 하나'},
    ('E-020', 'A'): {'ok_fx': '보물+2 · 엔+900~1200 · 분위기+8 · MVP+3'},
    ('E-020', 'B'): {'ok_fx': '엔+400 · MVP+2', 'sub': '안전하지만 엔만'},
    ('C-003', 'end'): {'fx': '엔+900 · 보물+2 · MVP+3'},
    ('C-005', 'end'): {'fx': '보물+2 · 엔+800 · 분위기+8'},
    ('C-006', 'end'): {'fx': '보물+2 · 엔+800 · SP+15'},
}

# 대실패 해프닝(단독행동) 피해 조정: 위험도 배율이 붙으면 깊은 구역에서 전멸 원인이 됨 (docs/balance.md sitcom-v3)
SOLO_BALANCE = {
    '조커': 'HP-6 · 사고+3 · 태그:대실패(본인) · 분위기+4',
    '모르가나': 'HP-6 · 사고+3 · 태그:대실패(본인) · 분위기+3',
    '류지': 'HP-4(전원) · 사고+3 · 태그:대실패(본인) · 분위기-4',
    '안': 'HP-4(전원) · 사고+3 · 태그:대실패(본인) · 태그:도발',
    '유스케': 'HP-6 · SP-6 · 사고+3 · 태그:대실패(본인) · 분위기+3',
    '아케치': 'HP-6 · 사고+3 · 태그:대실패(본인) · 분위기-3',
    '카스미': 'HP-5 · 사고+3 · 태그:대실패(본인) · 분위기+5',
}

# 튜토리얼 '하이라이트 대상' 이름 → 화면 요소 (CSS 선택자)
HL = {
    '3인 파티 슬롯': '.slots', '잠금 멤버 카드': '.cards', 'START': '[data-act="start"]',
    '말풍선': '.party', '행동 로그': '.logbox', 'HP 막대': '.party', '분위기': '#moodtag',
    '배속': '[data-act="speed"]', '일시정지': '[data-act="pause"]', '구역 이동 지도': '.map',
    '통로': '[data-act="move:pass"]', '보관실': '[data-act="move:lost"]', '구역': '.node.opt',
    '사건 팝업창': '.evt', '사건 선택지': '.evt .ch', '충돌 선택지': '.evt .ch',
    '활성 상태 태그': '.ptags, .tile .mt', 'RISK 표시': '#risktag', 'RISK': '#risktag', 'RETURN NOW': '[data-act="cashout"]',
    '보고서 카드': '.report', '후일담': '.after', '수익 정산': '.report dl', '르블랑': '[data-act="go:shop"]',
    '르블랑 가기': '[data-act="go:shop"]', '오늘의 메멘토스 배너': '.today', '캐릭터 선택 그리드': '.cards',
    '사슬 배지': '.logbox', '도감': '[data-act="go:codex"]', '모나 버스 튜닝': '[data-act="bus"]',
}
GO = {'탭': 'tap', '선택': 'choice', '버튼 누름': 'act', '구역 클릭': 'act', '선택지 클릭': 'act',
      '선택 후 행동': 'choice', '선택 후 버튼': 'choice', '탭 (T-8 직행)': 'tap'}

unknown = []


def s(v):
    return '' if v is None else str(v).strip()


def name_id(v, where):
    v = s(v)
    if not v:
        return None
    v = re.sub(r'\s*\(.*\)$', '', v)
    if v not in CH:
        unknown.append(f'{where}: 캐릭터 "{v}"')
        return None
    return CH[v]


def conds(text, where):
    out = []
    for tok in [t.strip() for t in SEP.split(s(text)) if t.strip()]:
        m = re.fullmatch(r'분위기\s*(\d+)\s*(이상|미만)', tok)
        if m:
            out.append({'k': 'mood', 'op': '>=' if m[2] == '이상' else '<', 'v': int(m[1])}); continue
        m = re.fullmatch(r'턴\s*(\d+)\s*이상', tok)
        if m:
            out.append({'k': 'turn', 'v': int(m[1])}); continue
        if tok.startswith('구역:') or tok in ZONE:
            z = tok.split(':', 1)[-1].strip()
            if z not in ZONE:
                unknown.append(f'{where}: 구역 "{z}"'); continue
            if tok in ZONE and out and out[-1]['k'] == 'zone':
                out[-1]['v'].append(ZONE[z])
            else:
                out.append({'k': 'zone', 'v': [ZONE[z]]})
            continue
        if tok == '단서':
            out.append({'k': 'tag', 'v': CLUE}); continue
        if tok.startswith('태그:'):
            m = re.fullmatch(r'(.+?)\(본인\)', tok[3:].strip())
            out.append({'k': 'tag', 'v': m[1].strip(), 'w': 'self'} if m else {'k': 'tag', 'v': tok[3:].strip()}); continue
        if tok.startswith('파티:'):
            ids = [name_id(x, where) for x in tok[3:].split('+')]
            out.append({'k': 'party', 'v': [i for i in ids if i]}); continue
        m = re.fullmatch(r'대상이\s*(\S+?)일\s*때', tok)
        if m:
            out.append({'k': 'target', 'v': name_id(m[1], where)}); continue
        if tok.startswith('소품:'):
            p = tok[3:].strip()
            pid = next((v for k, v in PROP.items() if p == k or k.startswith(p) or p.startswith(k)), None)
            if not pid:
                unknown.append(f'{where}: 소품 "{p}"'); continue
            out.append({'k': 'prop', 'v': pid}); continue
        if tok.startswith('결과:'):
            r = tok[3:].strip()
            if r not in RESULT:
                unknown.append(f'{where}: 결과 "{r}"'); continue
            out.append({'k': 'result', 'v': RESULT[r]}); continue
        if tok in ('없음', '-'):
            continue
        unknown.append(f'{where}: 조건 "{tok}"')
        out.append({'k': 'never', 'v': tok})
    return out


def effects(text, where):
    out = []
    toks = [t.strip() for t in SEP.split(s(text)) if t.strip()]
    group = any('(전원)' in t for t in toks)
    for tok in toks:
        m = re.fullmatch(r'엔\s*([+-])\s*(\d+)(?:\s*~\s*(\d+))?', tok)
        if m:
            a = int(m[2]); b = int(m[3] or m[2]); sg = 1 if m[1] == '+' else -1
            out.append({'k': 'yen', 'a': sg * a, 'b': sg * b}); continue
        m = re.fullmatch(r'보물\s*\+\s*(\d+)', tok)
        if m:
            out.append({'k': 'tre', 'v': int(m[1])}); continue
        m = re.fullmatch(r'(분위기|HP|SP|MVP|사고)\s*([+-]\d+)(\(전원\))?', tok)
        if m:
            k = {'분위기': 'mood', 'HP': 'hp', 'SP': 'sp', 'MVP': 'mvp', '사고': 'mis'}[m[1]]
            v = int(m[2]); all_ = bool(m[3]) or (k == 'sp' and v > 0 and group)
            out.append({'k': k, 'v': v, 'all': all_}); continue
        if tok == '단서':
            out.append({'k': 'tag', 'v': CLUE, 'own': False}); continue
        m = re.fullmatch(r'태그\s*제거\s*:\s*(.+)', tok)
        if m:
            out.append({'k': 'untag', 'v': m[1].strip()}); continue
        m = re.fullmatch(r'태그\s*:\s*(.+?)(\(본인\))?', tok)
        if m:
            out.append({'k': 'tag', 'v': m[1].strip(), 'own': bool(m[2])}); continue
        unknown.append(f'{where}: 효과 "{tok}"')
    return out


def own_tags(out):
    """'본인' 태그(효과에서 늘 '(본인)'으로만 붙는 태그, 예: 대실패)는 누가 가졌는지까지 본다.
    - 기본대사 '태그:X'      → 말하는 사람이 아닌 다른 누군가가 X를 가졌을 때 (동료 반응)
    - 기본대사 '태그:X(본인)' → 말하는 사람이 X를 가졌을 때
    - 쌍대사 '태그:X'        → 캐릭터 A가 X를 가졌을 때
    - 후일담 '태그:X' + 첫 줄 필요 캐릭터 → 그 캐릭터가 X를 가졌을 때
    """
    fx = [f for x in out['solo'] for f in x['fx']] + [f for x in out['pairs'] for f in x['fx']]
    fx += [f for e in out['events'] for c in e['choices'] for f in c['ok']['fx'] + (c.get('ng') or {}).get('fx', [])]
    fx += [f for c in out['chains'] for st in c['steps'].values() for f in st['fx']]
    given = {}
    for f in fx:
        if f['k'] == 'tag':
            given.setdefault(f['v'], set()).add(bool(f.get('own')))
    own = {v for v, s_ in given.items() if s_ == {True}}
    def mark(cs, w):
        for c in cs:
            if c['k'] == 'tag' and c['v'] in own and 'w' not in c:
                c['w'] = w
    for l in out['lines']:
        mark(l['c'], 'other')
    for p in out['pairs']:
        mark(p['c'], 'a')
    for a in out['afters']:
        if a['lines'] and a['lines'][0]['need']:
            mark(a['c'], a['lines'][0]['need'])
    return own


def tutorial(wb):
    """튜토리얼 탭 → {단계 ID: [대사 줄]}. 탭이 없으면 index.html에 있던 것을 그대로 둔다."""
    if '튜토리얼' not in wb.sheetnames:
        try:
            html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
            old = json.loads(html[html.index('/*SCRIPT-BEGIN*/') + 29:html.index(';/*SCRIPT-END*/')])
            unknown.append('튜토리얼 탭이 없어 지난번 튜토리얼 대사를 그대로 씀')
            return old.get('tut', {})
        except Exception:
            unknown.append('튜토리얼 탭이 없음'); return {}
    out = {}
    for d in rows(wb['튜토리얼']):
        sid = s(d['단계 ID']); w = f"튜토리얼 {sid}-{s(d['순서'])}"
        if not sid or not s(d['대사']):
            unknown.append(f'{w}: 단계 ID나 대사가 빈 칸'); continue
        who = name_id(s(d['화자']).split(',')[0], w)
        hl = []
        for nm in [x.strip() for x in SEP.split(s(d['하이라이트 대상'])) if x.strip()]:
            k = re.sub(r'\s*버튼$', '', nm)
            sel = HL.get(nm) or HL.get(k)
            if sel:
                hl.append(sel)
            else:
                unknown.append(f'{w}: 하이라이트 대상 "{nm}"')
        go = GO.get(s(d['넘어가는 조건']))
        if not go:
            unknown.append(f"{w}: 넘어가는 조건 \"{s(d['넘어가는 조건'])}\" → 탭으로 처리"); go = 'tap'
        ch = [x.strip() for x in SEP.split(s(d.get('조커 대답 선택지'))) if x.strip()][:2]
        if go == 'choice' and len(ch) < 2:
            unknown.append(f'{w}: 선택인데 조커 대답이 두 개가 아님 → 탭으로 처리'); go = 'tap'
        if go == 'act' and not hl:
            unknown.append(f'{w}: 눌러야 넘어가는데 하이라이트 대상이 없음 → 탭으로 처리'); go = 'tap'
        o = s(d['순서']); o = o[:-2] if o.endswith('.0') else o
        out.setdefault(sid, []).append({'o': o, 'who': who, 't': s(d['대사']), 'hl': hl, 'ch': ch if go == 'choice' else [], 'go': go})
    return out


TRIG = {'A가 B를 감쌈': '감싸기', 'A의 대실패': '대실패', '의견 충돌': '충돌', '함께 승리': '승리', 'A가 B를 회복': '회복', '쌍대사': '쌍대사'}
RELS = ['의기투합', '티격태격', '냉전', '뜻밖의 신뢰']
RSTAGE = {'경고 1 (위험도 9)': 'warn1', '경고 2 (위험도 10)': 'warn2', '출현 (위험도 10~)': 'appear', '도망침': 'escape', '붙잡힘': 'caught',
          '경고 1 (위험도 10)': 'warn1', '경고 2 (위험도 11)': 'warn2', '출현 (위험도 12)': 'appear'}  # 아래 셋은 예전 표기
CUTS = ['대실패', '감싸기', '긴급 구출·전멸', '조합 이벤트', '사슬 결말', '거두는 자 탈출', '케미 반전', '유물 대박', '히든', '평범한 날']


def any_id(v, w):
    return '*' if s(v) == '아무나' else name_id(v, w)


def new_tabs(wb, out):
    """케미 대사·케미 변화·혼잣말·거두는 자·결정적 1컷·인지 유물. 탭이 없으면 빈 목록(게임은 기본 문구를 씀)."""
    tab = lambda n: rows(wb[n]) if n in wb.sheetnames else []
    lines, shifts = [], []
    for d in tab('케미 대사'):
        w = f"케미 대사 {d['_row']}행"; a = name_id(d['캐릭터 A'], w); b = name_id(d['캐릭터 B'], w); r = s(d['관계'])
        if r not in RELS:
            unknown.append(f'{w}: 관계 "{r}"'); continue
        if not (a and b and s(d['A 대사']) and s(d['B 대사'])):
            unknown.append(f'{w}: 캐릭터나 대사가 빈 칸'); continue
        end = s(d.get('마무리 대사(선택)')); endo = None
        if end:
            m = re.match(r'(\S+?)\s*:\s*(.+)', end)
            endo = {'who': name_id(m[1], w), 'q': m[2].strip()} if m else {'who': a, 'q': end}
        lines.append({'a': a, 'b': b, 'rel': r, 'qa': s(d['A 대사']), 'qb': s(d['B 대사']), 'end': endo})
    for d in tab('케미 변화'):
        w = f"케미 변화 {d['_row']}행"; a = any_id(d['캐릭터 A'], w); b = any_id(d['캐릭터 B'], w)
        tr = TRIG.get(s(d['계기'])); r = s(d['바뀐 관계'])
        if not (a and b and tr and r in RELS):
            unknown.append(f'{w}: 캐릭터·계기·바뀐 관계 확인'); continue
        shifts.append({'a': a, 'b': b, 'trig': tr, 'rel': r, 'n': s(d['서술']), 'qa': s(d['A 대사']), 'qb': s(d['B 대사'])})
    out['chem'] = {'lines': lines, 'shifts': shifts}
    out['idle'] = []
    for d in tab('혼잣말'):
        w = f"혼잣말 {d['_row']}행"; who = name_id(d['캐릭터'], w)
        if who and s(d['혼잣말']):
            out['idle'].append({'who': who, 'n': s(d.get('딴짓 서술(선택)')), 'q': s(d['혼잣말']), 'c': conds(d.get('조건(선택)'), w)})
    out['reaper'] = []
    for d in tab('거두는 자'):
        w = f"거두는 자 {d['_row']}행"; st = RSTAGE.get(s(d['단계']))
        if not st or not s(d['내용']):
            unknown.append(f'{w}: 단계나 내용 확인'); continue
        out['reaper'].append({'st': st, 'who': name_id(d.get('화자(없으면 서술)'), w), 't': s(d['내용'])})
    out['cuts'] = []
    for d in tab('결정적 1컷'):
        w = f"결정적 1컷 {d['_row']}행"; k = s(d['장면'])
        if k not in CUTS or not s(d['헤드라인']):
            unknown.append(f'{w}: 장면이나 헤드라인 확인'); continue
        out['cuts'].append({'k': k, 't': s(d['헤드라인'])})
    out['relics'] = []
    for d in tab('인지 유물'):
        w = f"인지 유물 {s(d['ID'])}"; rid = s(d['ID'])
        if not re.fullmatch(r'R-(0[1-9]|1[0-3])', rid):
            if s(d['이름']) or not s(d['효과(말로)']).startswith('('):
                unknown.append(f'{w}: 새 유물 아이디어 — 효과 구현이 필요해요: {s(d["효과(말로)"])}')
            continue
        out['relics'].append({'id': rid, 'name': s(d['이름']), 'en': s(d['영문 이름']), 'desc': s(d['설명 한 줄'])})


def prob(v):
    v = s(v)
    if not v:
        return 1.0
    if v.endswith('%'):
        return float(v[:-1]) / 100
    f = float(v)
    return f / 100 if f > 1 else f


def turns(v):
    m = re.fullmatch(r'(\d+)\s*~\s*(\d+)', s(v))
    return [int(m[1]), int(m[2])] if m else None


def rows(ws):
    hdr = [s(c) for c in next(ws.iter_rows(max_row=1, values_only=True))]
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(c is not None and s(c) for c in r):
            continue
        d = dict(zip(hdr, r))
        st = s(d.get('상태'))
        if ONLY_DONE and st not in ('완료', '게임 반영'):
            continue
        d['_row'] = i
        yield d


def main():
    wb = load_workbook(SRC, data_only=True)
    out = {'lines': [], 'solo': [], 'pairs': [], 'events': [], 'chains': [], 'days': [], 'afters': []}
    seen = set()
    for d in rows(wb['기본대사']):
        w = f"기본대사 {d['_row']}행"
        who = name_id(d['캐릭터'], w); k = SIT.get(s(d['상황'])); t = s(d['대사'])
        if not (who and k and t):
            unknown.append(f'{w}: 캐릭터·상황·대사 중 빈 칸'); continue
        if (who, k, t) in seen:
            unknown.append(f'{w}: 같은 대사가 이미 있어 건너뜀 "{t}"'); continue
        seen.add((who, k, t))
        out['lines'].append({'who': who, 'k': k, 't': t, 'c': conds(d.get('조건(선택)'), w)})
    for d in rows(wb['단독행동']):
        w = f"단독행동 {d['_row']}행"
        who = name_id(d['캐릭터'], w)
        if who:
            fx = d['효과']
            if '대실패(본인)' in s(fx) and s(d['캐릭터']) in SOLO_BALANCE:
                fx = SOLO_BALANCE[s(d['캐릭터'])]
            out['solo'].append({'who': who, 'n': s(d['서술']), 'q': s(d['대사']), 'fx': effects(fx, w)})
    for d in rows(wb['쌍대사']):
        w = f"쌍대사 {s(d['ID'])}"
        a = name_id(d['캐릭터 A'], w); b = name_id(d['캐릭터 B'], w)
        end = s(d.get('마무리 대사(선택)'))
        endo = None
        if end:
            m = re.match(r'(\S+?)\s*:\s*(.+)', end)
            endo = {'who': name_id(m[1], w), 'q': m[2].strip()} if m else {'who': a, 'q': end}
        if a and b:
            out['pairs'].append({'id': s(d['ID']), 'a': a, 'b': b, 'c': conds(d['조건'], w), 'qa': s(d['A 대사']),
                                 'qb': s(d['B 대사']), 'end': endo, 'fx': effects(d['결과 효과'], w)})
    ch = {}
    for d in rows(wb['사건선택지']):
        if s(d['상태']) == '게임 반영':
            continue
        eid = s(d['사건 ID']); key = s(d['선택지']); w = f'사건선택지 {eid}-{key}'
        bal = BALANCE.get((eid, key), {})
        c = {'key': key, 'label': s(d['버튼 문구']), 'sub': bal.get('sub', s(d['설명'])), 'p': bal.get('p', prob(d['성공 확률'])),
             'ok': {'n': s(d['성공 서술']), 'q': s(d['성공 대사']), 'fx': effects(bal.get('ok_fx', d['성공 효과']), w)}}
        if s(d['실패 서술']) or s(d['실패 효과']):
            c['ng'] = {'n': s(d['실패 서술']), 'q': s(d['실패 대사']), 'fx': effects(d['실패 효과'], w)}
        ch.setdefault(eid, []).append(c)
    for d in rows(wb['사건']):
        if s(d['상태']) == '게임 반영':
            continue
        eid = s(d['사건 ID']); w = f'사건 {eid}'
        zones = [ZONE[z.strip()] for z in SEP.split(s(d['구역'])) if z.strip() in ZONE]
        if not ch.get(eid):
            unknown.append(f'{w}: 선택지가 없음'); continue
        out['events'].append({'id': eid, 'title': BALANCE.get((eid, 'title'), {}).get('title', s(d['제목'])), 'en': s(d['영문 제목']), 'zones': zones,
                              'min': int(float(s(d['최소 턴']) or 1)), 'c': conds(d['필요 조건'], w), 'intro': s(d['도입 서술']),
                              'who': name_id(d['화자'], w), 'q': s(d['화자 대사']), 'choices': ch[eid]})
    chains = {}
    for d in rows(wb['사슬']):
        cid = s(d['사슬 ID']); st = STAGE.get(s(d['단계'])); w = f'사슬 {cid} {s(d["단계"])}'
        if not st:
            unknown.append(f'{w}: 단계'); continue
        c = chains.setdefault(cid, {'id': cid, 'name': cid, 'steps': {}})
        m = re.search(r'사슬 이름:\s*([^·]+)', s(d['메모']))
        if m:
            c['name'] = m[1].strip()
        tag = s(d['붙는 태그'])
        tagfx = effects(tag, w) if tag else []
        bal = BALANCE.get((cid, st), {})
        c['steps'][st] = {'turn': turns(d['턴']), 'c': [x for x in conds(d['조건'], w) if x['k'] != 'result'],
                          'n': s(d['서술']), 'who': name_id(d['화자'], w), 'q': s(d['대사']),
                          'fx': tagfx + effects(bal.get('fx', d['효과']), w)}
    for c in chains.values():
        miss = [x for x in ('find', 'grow', 'end') if x not in c['steps']]
        if miss:
            unknown.append(f"사슬 {c['id']}: 단계 빠짐 {miss}")
        out['chains'].append(c)
    for d in rows(wb['오늘의메멘토스']):
        w = f"오늘의메멘토스 {s(d['ID'])}"
        line = s(d['출발 대사(화자: 대사)']); m = re.match(r'(\S+?)\s*:\s*(.+)', line)
        out['days'].append({'id': s(d['ID']), 'name': s(d['이름']), 'en': s(d['영문 이름']), 'intro': s(d['출발 안내문']),
                            'rule': s(d['규칙(말로)']), 'who': name_id(m[1], w) if m else None, 'q': m[2].strip() if m else line})
    cur = None
    for d in rows(wb['후일담']):
        if s(d['상태']) == '게임 반영':
            continue
        w = f"후일담 {d['_row']}행"; order = int(float(s(d['순서']) or 1)); cond = s(d['조건'])
        if cur is None or order == 1 or cond != cur['raw']:
            cur = {'raw': cond, 'c': conds(cond, w), 'lines': []}; out['afters'].append(cur)
        cur['lines'].append({'need': name_id(d['필요 캐릭터'], w), 'who': name_id(d['화자(없으면 서술)'], w), 't': s(d['내용'])})
    for a in out['afters']:
        a.pop('raw')
    own_tags(out)
    out['tut'] = tutorial(wb)
    new_tabs(wb, out)

    blob = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    p = os.path.join(ROOT, 'index.html'); html = open(p, encoding='utf-8').read()
    A, B = '/*SCRIPT-BEGIN*/', '/*SCRIPT-END*/'
    assert html.count(A) == 1 and html.count(B) == 1, 'index.html에 SCRIPT 표시가 없음'
    i, j = html.index(A) + len(A), html.index(B)
    html = html[:i] + 'const SCRIPT=' + blob + ';' + html[j:]
    open(p, 'w', encoding='utf-8').write(html)
    counts = {k: len(v) for k, v in out.items()}
    rep = ['# 시트 반영 보고서', '', f'원본: `{os.path.relpath(SRC, ROOT)}` · 모드: {"완료만" if ONLY_DONE else "전부"}', '',
           '| 항목 | 개수 |', '|---|---|'] + [f'| {k} | {v} |' for k, v in counts.items()] + [
           '', '## 시트 숫자 위에 덮어쓴 밸런스 조정', '',
           '안전한 선택지가 위험한 선택지보다 늘 이득이던 곳과, 보상이 너무 큰 곳을 고쳤어요. 시트도 같이 고쳐 두면 다음 반영 때 이 표가 필요 없어져요.', '',
           '| 대상 | 바뀐 값 |', '|---|---|'] + [f'| {k[0]} {k[1]} | ' + ' / '.join(f'{kk}: {vv}' for kk, vv in v.items()) + ' |' for k, v in BALANCE.items()] + [
           f'| 단독행동 {k} 대실패 | 효과: {v} |' for k, v in SOLO_BALANCE.items()] + [
           '', '대실패처럼 늘 (본인)으로 붙는 태그는 누가 가졌는지까지 봅니다. 기본대사의 그냥 `태그:대실패`는 말하는 사람이 아닌 동료가 실패했을 때, `태그:대실패(본인)`은 본인이 실패했을 때 나옵니다. 쌍대사는 캐릭터 A가 실패했을 때, 후일담은 첫 줄의 필요 캐릭터가 실패했을 때 나옵니다.'] + [
           '', '## 읽지 못했거나 건너뛴 표기', ''] + ([f'- {u}' for u in unknown] or ['없음'])
    open(os.path.join(ROOT, 'docs', 'script-import.md'), 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
    print(counts); print('unknown', len(unknown)); [print(' ', u) for u in unknown]


if __name__ == '__main__':
    main()
