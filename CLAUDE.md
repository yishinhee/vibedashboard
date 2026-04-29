# CLAUDE.md — 전역 공통 하네스

> 이 파일은 **모든 프로젝트에 동일하게 적용**되는 전역 설정이다.
> 프로젝트별 규칙은 반드시 `agents.md` 에만 작성한다.

---

## ⚠️ 필수 선행 조건 — 로딩 의무 (절대 준수)

**이 파일을 읽은 직후, 다른 어떤 작업보다 먼저 아래 순서대로 파일을 Read 도구로 읽어야 한다.**

1. `agents.md` — 프로젝트별 규칙
2. `docs/진행순서.md` — 현재 작업 단계 (없으면 건너뛰고, 있으면 §현재 단계 표를 반드시 확인)
3. `codingconventions.md` — 코딩 컨벤션 (존재하는 경우)

규칙:
- 위 파일들을 읽지 않은 상태에서 코드 수정·파일 생성·명령 실행 시작 금지.
- 사용자가 먼저 질문하더라도 로딩 완료 후 응답한다.
- **agents.md가 없으면 작업을 시작하지 않고 사용자에게 생성을 요청한다.**
- `docs/진행순서.md` 가 존재하면 §현재 단계 표를 읽어 어느 단계인지 파악한 뒤 작업한다. 없으면 첫 작업 시 생성 권장.
- `codingconventions.md`는 없으면 건너뛴다. 있으면 반드시 읽는다.
- 운영 서버 작업 시 `production.md` 존재 여부 확인 후 있으면 반드시 먼저 읽는다.

---

## Hooks — 전역 강제 적용

아래 훅은 모든 프로젝트에서 자동 실행된다. 비활성화 금지.

### PostToolUse Hook: `sync_structure.py`

- **트리거**: Write / Edit / MultiEdit 도구 실행 직후
- **동작**: 변경 성격을 3단계로 자동 분류 후 갱신 대상 명시
  - `단순수정` — 템플릿·CSS·JS 변경. 문서 갱신 불필요.
  - `기능변경` — views/services/models 수정. `docs/프로그램구조.md` + `docs/feature_map.md` 갱신 필수.
  - `신규기능` — 새 파일 생성. `docs/기능정의.md` + `docs/프로그램구조.md` + `docs/feature_map.md` + E2E 테스트 갱신 필수.
- **위치**: `.claude/hooks/sync_structure.py`
- **Claude 의무**:
  - 알림 출력 즉시 해당 문서를 갱신한다. 알림 무시 후 다음 작업 진행 금지.
  - 기능변경·신규 시 `tmp/doc_update_required.txt` 에 자동 기록 → `dod_check.py` 가 세션 종료 전 블로킹.

### Stop Hook: `telegram_notify.py`

- **트리거**: 세션 종료 시 자동 실행
- **동작**: `tmp/telegram_pending.txt` 존재 시 Telegram 발송 → 파일 삭제
- **위치**: `.claude/hooks/telegram_notify.py`
- **Claude 의무**: 유의미한 작업(기능 추가·버그 수정·테스트 통과) 완료 시 반드시 아래 형식으로 `tmp/telegram_pending.txt` 에 기록한다.

```
[<scope>] <한 줄 제목>
=== 수정 내용 ===
[백엔드] 파일:라인 - 변경 요지
[프론트엔드] 파일:라인 - 변경 요지
=== 테스트 방법 ===
=== 파일 변경 ===
작성일: YYYY-MM-DD / 작성자: Claude <사용 모델>
```

### Stop Hook: `dod_check.py`

- **트리거**: 세션 종료 시 자동 실행
- **동작**: DoD 미충족 항목 감지 시 경고 출력, `telegram_pending.txt` 자동 보완
- **위치**: `.claude/hooks/dod_check.py`
- **Claude 의무**: 경고 출력 시 해당 항목 완료 후 세션 종료한다.

---

## Skills — 전역 강제 적용

아래 스킬은 해당 조건 감지 시 자동 활성화된다. 별도 지시 없이 실행한다.

### `feature-map-update` 스킬 ★ 핵심

- **위치**: `.claude/skills/feature_map_update/SKILL.md`
- **자동 트리거**:
  - `sync_structure.py` 가 `feature_map.md 갱신 전 다음 작업 금지` 출력 시
  - `tmp/pending_updates.json` 에 `feature_map.md` 미갱신 항목 존재 시
- **동작**: 수정된 소스 파일을 분석해 `docs/feature_map.md` 의 해당 행을 정확한 형식으로 갱신
- **게이트 해제**: 갱신 완료 시 `sync_structure.py` 가 자동으로 pending 항목 클리어

### `new-project-setup` 스킬

- **위치**: `.claude/skills/new_project_setup/SKILL.md`
- **트리거**: "새 프로젝트 세팅", "프로젝트 초기화", "하네스 세팅해줘" 등
- **동작**: 프로젝트 정보 인터뷰 → `agents.md` + `docs/` 3종 + `feature_map.md` 자동 생성

---

## Golden Rules — 전역 불변 규칙

프로젝트에 무관하게 항상 적용된다.

### 🚫 웹 서버 프로세스 구동 절대 금지

사용자가 명시적으로 지시하지 않는 한 웹 서버를 절대 구동하지 않는다.

```
# 사용자 지시 없이 실행 불가
runserver / gunicorn / uvicorn / runserver_plus
```

허용: `test` / `migrate` / `makemigrations` / `pip install` 등 서버 구동이 아닌 명령.

### 🚫 비밀값 하드코딩 금지

SECRET_KEY, DB 비밀번호, API 토큰, 인증 키는 `.env` 에만 저장. 소스·테스트·문서 커밋 금지.

### 🚫 물리 삭제 금지 (소프트 딜리트 프로젝트 한정)

`agents.md` 에 소프트 딜리트 정책이 명시된 경우, `delete()` 직접 호출 금지.

### 🚫 동일 실패 반복 금지

동일 방식 3회 연속 실패 시 같은 시도 반복 금지 — 원인 재분석 후 접근 전환.

### 🚫 중복 스키마 금지

새 모델·필드 추가 전 `docs/프로그램구조.md` 검색 필수.

---

## Definition of Done — 전역 기준

아래 **모두** 만족해야 작업 완료로 간주한다.

- [ ] 관련 단위 테스트 작성 및 통과
- [ ] 서비스 함수 수정·추가 시 대응 테스트 파일 존재
- [ ] `docs/프로그램구조.md` 해당 섹션 갱신
- [ ] `docs/feature_map.md` 기능↔파일:함수↔DB 매핑 갱신 (기능변경·신규)
- [ ] `docs/기능정의.md` SCR-* / F-* ID 등록 (신규 기능)
- [ ] `docs/uiux개선.md` 완료 마커 추가 (해당 항목)
- [ ] **`docs/진행순서.md` §현재 단계 + 해당 단계 체크박스 갱신** (모든 의미있는 작업)
- [ ] Telegram 알림 기록 (`tmp/telegram_pending.txt`)
- [ ] E2E 테스트 작성 (신규 화면·기능)
- [ ] 구현한 기능과 E2E 테스트 결과 (화면캡쳐)를 통해 구현기능을 docs/매뉴얼.html 를 업데이트한다. (없다면 생성한다.)

> 프로젝트별 추가 DoD 항목은 `agents.md` §Definition of Done 에 작성한다.
> `dod_check.py` 가 세션 종료 시 위 항목 중 자동 검증 가능한 항목을 체크한다.

---

## 문서 갱신 규칙 — 전역

| 작업 | 갱신 대상 |
|---|---|
| **모든 단계 시작/완료** | **`docs/진행순서.md` §현재 단계 표 + 해당 단계 행** |
| 모델·뷰·URL·서비스 변경 | `docs/프로그램구조.md` 해당 섹션 |
| 모델·뷰·서비스 변경 | `docs/feature_map.md` 해당 기능 행 |
| 신규 기능·화면 추가 | `docs/기능정의.md` SCR-* / F-* 등록 |
| 신규 기능·화면 추가 | `docs/feature_map.md` 신규 행 추가 |
| 개선 항목 완료 | `docs/uiux개선.md` 완료 마커 |
| 사용자 화면·동작 변경 | `docs/매뉴얼.html` (해당 프로젝트) |

### 진행순서.md 갱신 의무 ★ 핵심

`docs/진행순서.md` 는 **이 프로젝트의 현재 작업 단계**를 추적하는 단일 진실의 원천이다.
세션을 새로 시작하거나 다른 작업자가 인수받았을 때, 이 파일 한 곳만 보면 어느 단계인지 즉시 파악할 수 있어야 한다.

작업 흐름:
1. **작업 시작 시점에 읽기** — 현재 단계 ID 와 해당 단계 체크박스를 확인.
2. **단계 시작 시** — `§현재 단계` 표의 `현재 단계 ID` / `Phase` / `마지막 갱신` / `갱신 사유` 를 갱신.
3. **단계 완료 시** — 해당 행 `상태` 컬럼을 `⬜` → `✅` 로 변경, 다음 단계 ID 로 `§현재 단계` 표 갱신, `§갱신 이력` 에 한 줄 추가.
4. **계획 변경 시** — 새 단계를 표에 추가하거나 기존 단계를 수정. 삭제는 지양(이력 보존).

규칙:
- `docs/진행순서.md` 가 없는 프로젝트는 첫 작업 시 생성한다 (Phase 0 골격은 `agents.md` §Phase 계획 또는 `docs/프로젝트설계.md` 기준).
- 단계 ID 표기법: `S{Phase}.{순번}` (예: `S1.4`).
- 단계 완료 마킹 없이 다음 단계 작업 시작 금지.
- 사용자가 "어디까지 했어?" 라고 물으면 본 파일의 `§현재 단계` 표를 그대로 인용해 답한다 — 추측 금지.

### feature_map.md 갱신 의무

`docs/feature_map.md` 는 **기능↔소스파일:함수↔DB테이블:필드** 의 전체 지도다.
이 파일이 최신 상태여야 1개월 후에도 소스를 전체 탐색하지 않고 즉시 작업 위치를 파악할 수 있다.

- 기능변경·신규 시 반드시 갱신한다.
- 프로젝트 시작 시 `docs/feature_map.template.md` 를 복사해 `docs/feature_map.md` 로 생성한다.
- `dod_check.py` 가 갱신 여부를 세션 종료 전 자동 검사한다.

---

## 위임 선언

아래 항목은 `agents.md` 에서만 정의한다. 이 파일에 작성 금지.

- 프로젝트 개요 / 도메인 설명
- Tech Stack 상세
- DB 접속 정보 형식 / ORM 선택
- 환경변수 목록
- 프로젝트별 Do's / Don'ts
- Git 브랜치 전략 / 커밋 컨벤션
- Context Map (작업 유형별 참조 문서)
- Nested AGENTS Boundaries
- 프로젝트별 추가 DoD 항목
