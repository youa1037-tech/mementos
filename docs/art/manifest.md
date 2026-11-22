# 스프라이트 매니페스트 · 다락방

open-game-art-skills의 `sprite-catalog` 형식입니다. 필요한 그림의 목록과 상태를 적는 계획표이고, 실제 영역 좌표는 `atlas.json`에 있습니다.

- 가족(family): prop(소품), tileset(방 배경)
- 셀 크기: 16px 타일 기준, 스프라이트는 칸보다 위로 솟을 수 있음
- 출처·권리: 전부 이 저장소에서 코드로 그린 오리지널. 외부 에셋 없음
- 상태: approved = 게임에 들어갔고 390px 화면에서 확인함

| ID | 이름 | 가족 | 레이어 | 칸(가로×세로) | 스프라이트 px | 가격 | 효과 | 상태 |
|---|---|---|---|---|---|---|---|---|
| room | 다락방 배경 | tileset | base | 11×8 | 176×128 | - | - | approved |
| sofa | 벨벳 소파 | prop | floor | 2×1 | 34×24 | 시작 소품 | 장식 | approved |
| plant | 화분 | prop | floor | 1×1 | 18×26 | 시작 소품 | 장식 | approved |
| rug | 붉은 러그 | prop | rug | 3×2 | 48×30 | ¥1,500 | 장식 | approved |
| lamp | 스탠드 조명 | prop | floor | 1×1 | 16×36 | ¥1,200 | 장식 | approved |
| poster | 별 포스터 | prop | wall | 1×1 | 16×20 | ¥800 | 장식 | approved |
| game | 레트로 게임기 | prop | floor | 1×1 | 18×26 | ¥3,000 | 분위기 +15 | approved |
| tea | 커피·홍차 세트 | prop | floor | 1×1 | 18×22 | ¥3,500 | SP +10% | approved |
| easel | 화구·이젤 세트 | prop | floor | 1×1 | 18×32 | ¥3,000 | 단서 발견율 | approved |
| cushion | 고양이 방석·참치캔 | prop | floor | 1×1 | 20×14 | ¥2,500 | 보물 +6% | approved |
| dart | 다트 보드 | prop | wall | 1×1 | 16×16 | ¥4,000 | 교류 성공률 | approved |

## 배치 규칙

- floor끼리, wall끼리는 겹칠 수 없음. rug는 floor 밑에 깔릴 수 있음
- 벽 칸은 11×2. 둥근 창과 지붕 경사 자리는 막힘
- 효과는 소품을 **가지고 있으면** 적용(창고에 넣어도 유지). 배치는 꾸미기 전용

## 다음 후보 (missing)

벽지·바닥 교체 세트, 책장, 침대, 벽시계, 카페 1층 방
