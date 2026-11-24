# TODAY'S MEMENTOS! · 오늘도 메멘토스!

《페르소나 5 더 로열》 괴도단 10인 중 3명을 골라 메멘토스 깊은 곳으로 내려가는 웹 브라우저용 초경량 로그라이크입니다.

- 목표: 괴도 채널 의뢰 셋(B1 검표원 → B2 분실물 보관소의 주인 → B3 최심부의 거두는 자)을 해내 지지율 100%.
- 환승 노선도: 이웃 역만 보입니다. 한 역마다 경계도 +1, 16이 되면 거두는 자가 쫓아옵니다.
- 3열 턴제 전투: 약점을 찌르면 DOWN + 1 MORE, 바톤 터치, 전원 DOWN이면 총공격. 속성 9종. 영수증 대미지와 타격 연출.
- 템 조합: 스위칭 · 약점 · 왜곡(HP가 낮을수록 강해짐) 세 갈래, 가방 칸 제한 없음. 대가가 붙은 '왜곡된 인지' 템, 벨벳 룸 출장소에서 구입 · 합성.
- 판 밖의 엔: 모나 버스 개조(더 깊은 선로) · 템 해금 · 유대(바톤을 주고받은 두 사람의 장면과 보너스).
- 대사 580줄과 쌍대사·케미 대사가 전투와 행군 중 말풍선으로 나옵니다.

## 플레이

`index.html` 하나로 동작하는 정적 페이지입니다(그림은 `img/`, 글꼴은 `fonts/`). 진행도는 브라우저의 LocalStorage에만 저장됩니다.
예전 관찰형 버전은 `legacy.html`로 그대로 남아 있습니다.

## 파일

- `index.html` — 게임 전체 (새 코어). 설계와 수치는 `docs/core-proto.md`
- `legacy.html` — 예전 관찰형 버전 (기능 동결)
- `DESIGN.md` — 색·글꼴·컴포넌트·모션 규칙
- `content/script.xlsx` — 대사·스크립트 시트 원본
- `tools/import_script.py` — 시트를 게임 데이터로 바꿔 `index.html`의 SCRIPT 블록에 넣는 도구. 결과 보고는 `docs/script-import.md`
- `tools/item_icons.py` — 템·진화 템·부정 기물 16×16 도트 아이콘(`img/items/`)을 글자 격자로 그려 만드는 도구. 직접 그린 PNG로 같은 이름 덮어써도 됨
- `tools/core_smoke.py` · `tools/core_scenarios.py` — 새 코어 자동 플레이 · 기능 확인 도구(결과는 `docs/verify.md`)
- `tools/sim.py` 등 — 예전 버전(`legacy.html`)용 개발 도구

## 안내

비상업 · 비공식 팬 게임입니다. 《페르소나 5》 및 등장인물의 권리는 ATLUS / SEGA에 있으며, 공식 게임의 일러스트·음악·UI 리소스는 사용하지 않았습니다.

배경음악:
- 대기 화면 — "Vibing Over Venus" Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0 (https://creativecommons.org/licenses/by/4.0/)
- 탐사 — "Hopstep Battle" PeriTune (https://peritune.com)
- 심층(버려진 플랫폼 단계) — "Deep Sea" PeriTune (https://peritune.com)

제작: [@nyamaker](https://x.com/nyamaker)
