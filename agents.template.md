# agents.md — [프로젝트명]

> 이 파일은 **이 프로젝트에만 적용**되는 규칙이다.
> 전역 규칙(Golden Rules, Hooks, Skills, DoD 기준)은 CLAUDE.md 참조.

---

## 프로젝트 개요

- **목적**: [프로젝트 목적 한 줄 요약]
- **레포지토리**: [GitHub URL]
- **운영 URL**: [서비스 URL]
- **개발 서버**: `http://127.0.0.1:8000`

---

## Tech Stack

| 구분 | 선택 |
|---|---|
| Backend | [예: Python 3.12 / Django 5.x] |
| Frontend | [예: Django 템플릿 / React / Vue] |
| DB (개발) | [예: SQLite] |
| DB (운영) | [예: PostgreSQL 15 / MySQL 8] |
| 캐시 | [예: Redis / LocMemCache] |
| 인증 | [예: Django session / JWT] |
| 파일 저장 | [예: 로컬 FileField / S3] |
| 리치텍스트 | [예: Quill + bleach sanitize] |
| 외부 연동 | [예: NICE API / Telegram Bot] |
| 가상환경 | `venv` (디렉토리명 고정) |

---

## 환경변수 (.env 필수 항목)

```
# DB
DATABASE_URL=

# 보안
SECRET_KEY=

# 외부 연동 (프로젝트별 추가)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

> 위 값은 절대 소스·문서·커밋에 포함하지 않는다. (CLAUDE.md §Golden Rules 참조)

---

## 프로젝트 명령어

```bash
# 프로젝트 루트에서 실행
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/seed.json
python manage.py runserver          # 사용자 지시 시에만

# 테스트
python manage.py test apps.<app_name>

# 의존성
pip install -r requirements.txt
```

---

## 아키텍처 개요

### 디렉토리 구조

```
[프로젝트루트]/
├── CLAUDE.md
├── agents.md
├── [메인앱]/
│   ├── manage.py
│   ├── config/         # settings (base/dev/prod)
│   └── apps/
│       └── [앱명]/
└── docs/
```

### 앱 책임 분리

| 앱 | 경로 | 책임 |
|---|---|---|
| [앱명] | `apps/[앱명]/` | [책임 설명] |

### 핵심 아키텍처 패턴

- **서비스 레이어**: 뷰는 HTTP 처리만, 비즈니스 로직은 `apps/{app}/services/` 로 분리
- [프로젝트별 패턴 추가]

---

## Golden Rules — 프로젝트 추가 규칙

> 전역 불변 규칙은 CLAUDE.md §Golden Rules 참조. 여기에는 이 프로젝트에만 적용되는 규칙만 작성.

### 절대 금지 (Immutable)

- [예: rtrack API에 GET 외 메서드 전달 금지]
- [예: Post.objects.delete() 금지 — del_yn='Y' 처리만]
- [프로젝트별 추가]

### Do's

- [예: 비즈니스 로직은 apps/{app}/services/*.py 에만 작성]
- [프로젝트별 추가]

### Don'ts

- [예: Bootstrap 계열 클래스 사용 금지]
- [프로젝트별 추가]

---

## Definition of Done — 프로젝트 추가 기준

> 전역 DoD는 CLAUDE.md §Definition of Done 참조. 여기에는 추가 항목만 작성.

- [ ] [예: rtrack 연동 기능은 mock/fixture로 단위 테스트 검증]
- [ ] [예: 한국어/영어 UI 라벨·에러 메시지 일관성 유지]
- [ ] [프로젝트별 추가]

---

## Git 전략

- **Branch 전략**
  - `main` — 배포 가능 상태만
  - `develop` — 통합 브랜치
  - `feature/<phase>-<num>-<slug>` (예: `feature/p1-01-board-common`)

- **Commit 메시지**: `<type>(<scope>): <subject>`
  - type: `feat` / `fix` / `refactor` / `docs` / `test` / `chore`

- **gitignore 필수**: `.env` / `db.sqlite3` / `staticfiles/` / `venv/`

---

## 규약

- **네이밍**: [예: 테이블명 snake_case, URL name `앱:뷰` 형식]
- **날짜 형식**: `YYYY-MM-DD`
- **문서 언어**: `docs/` 하위 `.md` 파일은 한국어
- [프로젝트별 규약 추가]

---

## Context Map

작업 유형별 참조 문서:

- **[기능 ID 매핑](./docs/기능정의.md)** — 신규 화면·기능 설계, SCR-* / F-* 조회·등록
- **[UI/UX 개선](./docs/uiux개선.md)** — P0~P3 개선 항목 선정·구현 체크
- **[구조 명세](./docs/프로그램구조.md)** — 모델·뷰·URL·서비스 위치 조회·갱신
- **[구현 로드맵](./docs/프로젝트설계.md)** — Phase 일정·마일스톤·리스크
- [프로젝트별 문서 추가]

---

## Nested AGENTS Boundaries

앱별 상세 규칙 파일 (Phase 진입 시 생성):

- **[앱명](./apps/[앱명]/AGENTS.md)** — [담당 도메인 한 줄 설명]
- [프로젝트별 앱 추가]

---

## Change Log

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| 1.0 | YYYY-MM-DD | 최초 작성 |
