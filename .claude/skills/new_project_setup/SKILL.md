---
name: new-project-setup
version: 1.0.0
description: 새 프로젝트 시작 시 agents.md 작성 + docs 3종 + feature_map.md 자동 초기화
---

# New Project Setup Skill

## 활성화 조건

다음 표현이 포함된 요청 시 자동 실행:
- "새 프로젝트 세팅", "프로젝트 초기화", "하네스 세팅해줘"
- "agents.md 만들어줘", "docs 초기화"

---

## 실행 절차

### Step 1 — 프로젝트 정보 수집 (인터뷰)

아래 항목을 사용자에게 순서대로 확인한다. 한 번에 전부 묻지 않고 **그룹별로** 묻는다.

**그룹 A — 기본 정보**
```
1. 프로젝트명 (영문 slug, 예: inidk-django)
2. 프로젝트 목적 (한 줄)
3. GitHub 레포지토리 URL
```

**그룹 B — 기술 스택**
```
4. Backend 프레임워크 (Django / FastAPI / Express / etc.)
5. Frontend 방식 (Django 템플릿 / React / Vue / etc.)
6. DB (개발): SQLite / PostgreSQL / MySQL
7. DB (운영): PostgreSQL / MySQL / 기타
8. 외부 연동 서비스 (있으면 나열)
```

**그룹 C — 운영 규칙**
```
9. 소프트 딜리트 사용 여부 (Y/N)
10. 다국어 지원 여부 (Y/N, 지원 시 언어 목록)
11. Telegram 알림 사용 여부 (Y/N)
```

### Step 2 — agents.md 생성

`agents.template.md` 를 기반으로 수집한 정보를 채워 `agents.md` 를 생성한다.

- `[대괄호]` 항목 전부 실제 값으로 교체
- 소프트 딜리트 Y → Golden Rules 에 물리 삭제 금지 규칙 추가
- 다국어 Y → 규약 섹션에 lang_cd 처리 규칙 추가
- Telegram N → DoD 에서 Telegram 항목 제거

### Step 3 — docs/ 초기 문서 3종 생성

#### `docs/기능정의.md`

```markdown
# 기능정의.md — [프로젝트명]

> SCR-* : 화면 ID / F-* : 기능 ID
> 신규 기능 추가 시 이 파일에 먼저 ID 를 등록한 후 코드를 작성한다.

## 화면·기능 ID 규칙
- Screen ID: SCR-{MENU}-NN (예: SCR-BRD-01)
- Feature ID: F-{MENU}-NN  (예: F-BRD-01)
- 마지막 등록 번호: SCR-000-00 / F-000-00  ← 작업마다 갱신

## 기능 목록

| 기능 ID | 화면 ID | 기능명 | 권한 | 상태 |
|---|---|---|---|---|
| F-000-00 | SCR-000-00 | [예시 기능] | 전체 | 미구현 |

## 권한 매트릭스

| 기능 | 비로그인 | 일반사용자 | 관리자 |
|---|---|---|---|
| [기능명] | - | ✅ | ✅ |
```

#### `docs/프로그램구조.md`

```markdown
# 프로그램구조.md — [프로젝트명]

> 이 파일은 코드 수정 시 sync_structure.py 훅에 의해 갱신이 강제된다.
> 마지막 갱신: YYYY-MM-DD

## 앱 구조

[앱별 섹션 — 모델/뷰/URL/서비스/템플릿 명세]

## 모델 명세

| 앱 | 모델 | 테이블명 | 주요 필드 |
|---|---|---|---|

## URL 명세

| 앱 | URL name | path | View |
|---|---|---|---|

## 서비스 함수 명세

| 앱 | 파일 | 함수명 | 역할 |
|---|---|---|---|
```

#### `docs/feature_map.md`

`docs/feature_map.template.md` 를 복사하여 프로젝트명·날짜를 채운다.

### Step 4 — 체크리스트 출력

생성 완료 후 아래 체크리스트를 출력한다.

```
✅ 프로젝트 초기 세팅 완료
─────────────────────────────────────
생성된 파일:
  □ agents.md
  □ docs/기능정의.md
  □ docs/프로그램구조.md
  □ docs/feature_map.md

다음 할 일:
  □ .env 파일 생성 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
  □ docs/기능정의.md 에 첫 번째 기능 F-* ID 등록
  □ git init + 첫 커밋
  □ develop 브랜치 생성
─────────────────────────────────────
```

---

## 주의사항

- `docs/` 디렉토리가 없으면 생성한다.
- `tmp/` 디렉토리가 없으면 생성하고 `.gitignore` 에 추가한다.
- 기존 `agents.md` 가 있으면 덮어쓰기 전 사용자에게 확인한다.
