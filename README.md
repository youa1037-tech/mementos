# TODAY'S MEMENTOS! · 오늘도 메멘토스!

《페르소나 5 더 로열》 괴도단 10인 중 3명을 골라 메멘토스 깊은 곳으로 내려가는 웹 브라우저용 초경량 로그라이크입니다.

- 4×4 방 미니맵: 이웃 방만 보입니다. 한 칸마다 위험도 +1, 10이 되면 거두는 자가 옵니다.
- 3열 턴제 전투: 약점을 찌르면 DOWN + 1 MORE, 바톤 터치, 전원 DOWN이면 총공격. 속성 9종.
- 6칸 템 조합: 스위칭 · 스트레스 폭주 · 약점 연쇄 세 갈래, 작업대에서 진화 템으로 합성. 부정 기물을 떠안으면 대박 보상.
- 스트레스: 100이 되면 붕괴(제멋대로) 또는 각성. 판을 넘어 남습니다.
- 3층 구조: 층 보스를 잡을 때마다 르블랑 귀환 vs 하강.
- 르블랑: 번 엔으로 템 풀 해금 · 리롤 · 카레 · 스트레스 케어 · 판 세팅.
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
- `tools/sim.py` 등 — 예전 버전(`legacy.html`)용 개발 도구

## 안내

비상업 · 비공식 팬 게임입니다. 《페르소나 5》 및 등장인물의 권리는 ATLUS / SEGA에 있으며, 공식 게임의 일러스트·음악·UI 리소스는 사용하지 않았습니다.

배경음악:
- 대기 화면 — "Vibing Over Venus" Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0 (https://creativecommons.org/licenses/by/4.0/)
- 탐사 — "Hopstep Battle" PeriTune (https://peritune.com)
- 심층(버려진 플랫폼 단계) — "Deep Sea" PeriTune (https://peritune.com)

제작: [@nyamaker](https://x.com/nyamaker)
