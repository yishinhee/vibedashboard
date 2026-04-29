# harness-dashboard UI/UX 개선 항목

> P0 ~ P3 우선순위로 분류. 완료 시 `### ✅ [P{n}]` 으로 변경.
> Phase 별 체크리스트는 §10 에서 별도 관리.

---

## P0 — 핵심 가치 차단 (즉시)

### [P0] 등록 폴더 경로 검증 강화
- 폴더 미존재 / `docs/` 없음 / 권한 없음 → 명확한 에러 메시지 (Tailwind alert 컴포넌트)
- 잘못된 경로로 등록 시 사용자가 원인을 즉시 알 수 있어야 함.

### [P0] 동기화 결과 시각적 표시
- 수동 동기화 후 `success / no_change / failed` 별 색상 구분 (`green-500` / `slate-400` / `rose-500`)
- 실패 파일은 detail 메시지를 카드에 노출.

---

## P1 — 사용성 핵심

### [P1] 미갱신 문서 경고 배지
- 등록 프로젝트의 `tmp/pending_updates.json` 존재 시 카드에 빨간 점 + 항목 수.
- 클릭 시 어떤 문서가 미갱신인지 모달로 표시.

### [P1] Phase 완료율 한눈에 보기
- 프로젝트 카드에 `Phase 2 (3/8)` 형태로 현재 Phase + 텍스트 진행도 표시.
- 파이차트는 사용하지 않는다.

### [P1] 마지막 동기화 시각 상대 표기
- "방금", "5분 전", "어제" 형태 (절대 시각은 hover tooltip).

---

## P2 — 개선 (있으면 좋은)

### [P2] 키보드 단축키
- `s` 동기화, `1`~`4` 탭 전환, `/` 검색.

### [P2] 다크 모드
- Tailwind `dark:` variant 활용. 시스템 prefers-color-scheme 기본 적용.

### [P2] 파싱 실패 항목 인라인 보기
- `raw_text` 가 채워진 행을 별도 색상으로 구분 + 클릭 시 원문 펼치기.

---

## P3 — 부가

### [P3] 프로젝트 즐겨찾기
- 자주 보는 프로젝트 상단 고정.

### [P3] CSV 내보내기
- 기능 현황 / 개선 항목 탭에서 현재 필터 결과를 CSV 로 export.

---

## 10. Phase 별 체크리스트

> `improvement_parser.py` 가 본 섹션의 `- ✅` / `- [ ]` 패턴을 ChecklistItem 으로 추출한다.

### Phase 1 — 데이터 레이어
- [ ] Django 프로젝트 초기화 (`config/`, `apps/` 골격)
- [ ] 9개 테이블 마이그레이션 (`project`, `screen`, `feature`, `app_module`, `model_info`, `phase`, `checklist_item`, `improvement_item`, `feature_map`, `sync_log`)
- [ ] `BaseParser` 추상 클래스 + 6개 파서 구현
- [ ] `sync_service.sync_one_file` mtime 비교 로직
- [ ] 파서 6종 단위 테스트 (fixture md 기반)

### Phase 2 — 프로젝트 관리 화면
- [ ] `templates/base.html` Tailwind 레이아웃
- [ ] `dashboard/project_list.html` 카드 컴포넌트
- [ ] `projects/project_form.html` 등록/편집 폼
- [ ] 폴더 경로 검증 메시지 (P0)
- [ ] 소프트 삭제 확인 모달

### Phase 3 — 상세 4개 탭
- [ ] 기능 현황 탭 (SCR-* / F-* 표 + 필터)
- [ ] Phase 진행 탭 (체크리스트 + 텍스트 완료율)
- [ ] 프로그램 구조 탭 (앱·모델·feature_map 표)
- [ ] 개선 항목 탭 (P0~P3 필터)

### Phase 4 — 동기화 고도화
- [ ] HTMX 기반 수동 동기화 버튼
- [ ] 동기화 로그 화면 (SyncLog 시간 역순)
- [ ] `sync_all` 관리 명령어
- [ ] mtime 변경 감지 로직 통합 테스트

### Phase 5 — E2E + 매뉴얼
- [ ] Playwright 또는 Django LiveServerTestCase 기반 E2E
- [ ] 화면 캡처를 `docs/매뉴얼.html` 에 갱신
- [ ] README 사용법 보강

---

## 변경 이력

| 일자 | 변경 |
|---|---|
| 2026-04-29 | 최초 작성. P0 2건 / P1 3건 / P2 3건 / P3 2건. Phase 1~5 체크리스트 골격. |
