# agents.md — harness-dashboard

> 이 파일은 **harness-dashboard 프로젝트에만 적용**되는 규칙이다.
> 전역 규칙(Golden Rules, Hooks, Skills, DoD 기준)은 CLAUDE.md 참조.

---

## 프로젝트 개요

- **목적**: Claude Code 하네스가 적용된 프로젝트들의 docs 문서(기능정의·프로그램구조·uiux개선·feature_map·프로젝트설계)를 자동 파싱해 **여러 프로젝트의 진행 상황을 한 화면에서 관리**하는 웹 대시보드.
- **레포지토리**: https://github.com/yishinhee/vibedashboard.git
- **운영 URL**: 미정 (단일 사용자 로컬 도구로 시작)
- **개발 서버**: `http://127.0.0.1:8000`

> **보안 주의**: GitHub PAT, Telegram Token, Synology Bot Token 등 인증 정보는 절대 이 문서에 작성하지 않는다. `.env` 파일에만 저장한다. (CLAUDE.md §Golden Rules `🚫 비밀값 하드코딩 금지` 참조)

---

## Tech Stack

| 구분 | 선택 |
|---|---|
| Backend | Python 3.12 / Django 5.x |
| Frontend | Django 템플릿 + Tailwind CSS (CDN 또는 django-tailwind) |
| 템플릿 엔진 | Django Templates (HTMX 보조 활용 가능) |
| DB (개발) | SQLite |
| DB (운영) | SQLite (단일 사용자 도구) — 다중 사용자 확장 시 PostgreSQL |
| 캐시 | Django LocMemCache (Redis 미사용) |
| 비동기 작업 | 동기 처리 + Django management command (Celery 미사용) |
| 인증 | 미사용 (단일 사용자 로컬 도구) — 추후 Django session 도입 |
| 파일 저장 | 로컬 파일 시스템 (등록된 프로젝트의 docs/ 디렉토리 직접 read-only 참조) |
| 외부 연동 | Synology Chat Bot (세션 종료 알림), Telegram Bot (선택) |
| 가상환경 | `venv` (디렉토리명 고정) |

---

## 환경변수 (.env 필수 항목)

```
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# DB
DATABASE_URL=sqlite:///db.sqlite3

# 외부 연동 (.env.global 에서 복사)
SYNOLOGY_BASE_URL=
SYNOLOGY_BOT_TOKEN=
SYNOLOGY_BOT_USER_ID=
SYNOLOGY_CHANNEL_ID=

# 선택 사용
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# GitHub (PR 생성·푸시용 — 사용자 별도 관리)
GITHUB_PAT=
```

> 위 값은 절대 소스·문서·커밋에 포함하지 않는다. (CLAUDE.md §Golden Rules 참조)
> `.env` 는 반드시 `.gitignore` 에 등록한다.

---

## 프로젝트 명령어

```bash
# 프로젝트 루트에서 실행 (가상환경 활성화 후)
python manage.py migrate
python manage.py createsuperuser            # 추후 인증 도입 시
python manage.py runserver                  # 사용자 지시 시에만

# 프로젝트별 동기화 (관리 명령어)
python manage.py sync_project <project_id>          # 단일 프로젝트 재파싱
python manage.py sync_all                            # 등록된 전체 프로젝트 재파싱

# Tailwind (django-tailwind 사용 시)
python manage.py tailwind install
python manage.py tailwind start              # 사용자 지시 시에만 (watcher)
python manage.py tailwind build              # 정적 파일 빌드

# 테스트
python manage.py test apps.<app_name>
python manage.py test                       # 전체

# 의존성
pip install -r requirements.txt
pip freeze > requirements.txt               # 의존성 추가 시
```

---

## 아키텍처 개요

### 디렉토리 구조

```
harness_dashboard/                  # 프로젝트 루트 (= 작업 디렉토리)
├── CLAUDE.md                       # 전역 하네스 규칙
├── agents.md                       # 이 파일
├── manage.py
├── requirements.txt
├── .env                            # 비밀값 (gitignore)
├── .env.global                     # 공통 환경변수 (참조용)
├── config/                         # Django settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── projects/                   # 프로젝트 등록 관리
│   │   ├── models.py               # Project
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services/
│   │   │   └── project_service.py
│   │   └── tests/
│   ├── parsers/                    # docs/*.md 파싱 서비스
│   │   ├── services/
│   │   │   ├── base_parser.py
│   │   │   ├── feature_parser.py
│   │   │   ├── structure_parser.py
│   │   │   ├── improvement_parser.py
│   │   │   ├── design_parser.py
│   │   │   └── feature_map_parser.py
│   │   └── tests/
│   ├── dashboard/                  # 대시보드 화면 (목록 + 4개 탭)
│   │   ├── models.py               # Screen, Feature, AppModule, Phase, ImprovementItem, ChecklistItem, FeatureMap
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── templates/dashboard/
│   │   └── tests/
│   └── sync/                       # 동기화 오케스트레이션
│       ├── models.py               # SyncLog
│       ├── services/
│       │   └── sync_service.py
│       ├── management/commands/
│       │   ├── sync_project.py
│       │   └── sync_all.py
│       └── tests/
├── static/                         # Tailwind 빌드 산출물 + 정적 파일
│   └── css/
├── templates/                      # 공통 base.html
│   └── base.html
├── tests/                          # 통합/E2E 테스트
└── docs/
    ├── raw/                        # 테스트용 샘플 raw md (옵션)
    ├── 기능정의.md
    ├── 프로그램구조.md
    ├── uiux개선.md
    ├── 프로젝트설계.md
    ├── feature_map.md
    └── 매뉴얼.html
```

### 앱 책임 분리

| 앱 | 경로 | 책임 |
|---|---|---|
| projects | `apps/projects/` | Project 등록/편집/삭제(소프트), 폴더 경로 검증 |
| parsers | `apps/parsers/` | docs/*.md 파일별 파서 서비스. 파싱 실패 시 raw_text 보존 |
| dashboard | `apps/dashboard/` | 화면 렌더링: 프로젝트 목록 + 4개 상세 탭(기능/Phase/구조/개선) |
| sync | `apps/sync/` | 파싱 오케스트레이션, mtime 기반 변경 감지, SyncLog 기록 |

### 핵심 아키텍처 패턴

- **서비스 레이어**: 뷰는 HTTP 처리만, 비즈니스 로직(파싱·동기화)은 `apps/{app}/services/*.py` 로 분리.
- **파싱 레이어 분리**: 원본 md 형식이 프로젝트마다 달라도 파서 모듈만 수정하면 됨. `BaseParser` 추상 클래스 → 파일 유형별 구현체.
- **raw_text 보존**: 모든 파싱 산출물 모델은 `raw_text` 필드를 가진다. 파싱 실패 시 원문 복구 가능.
- **mtime 기반 변경 감지**: `SyncLog.file_mtime` 비교로 불필요한 재파싱 방지.
- **Read-only 외부 폴더 참조**: 등록된 프로젝트의 docs 폴더는 읽기 전용. 절대 쓰지 않는다.

---

## Golden Rules — 프로젝트 추가 규칙

> 전역 불변 규칙은 CLAUDE.md §Golden Rules 참조.

### 절대 금지 (Immutable)

- **등록된 외부 프로젝트 폴더에 쓰기 금지** — `Project.path` 가 가리키는 폴더는 read-only 참조만. `os.remove`, `shutil.move`, `open(..., 'w')` 등 일체 금지.
- **Project 물리 삭제 금지** — `deleted_at` 컬럼 set 처리(소프트 딜리트). 관련 파싱 데이터 삭제는 cascade 로 명시 처리.
- **Bootstrap·기타 CSS 프레임워크 사용 금지** — 스타일은 Tailwind 만 사용.
- **억지 통계 추가 금지** — 코드 라인 수, 커밋 횟수, "생산성 점수" 류 지표는 절대 추가하지 않는다 (기능정의서 §1.3 참조).
- **파이차트·도넛차트로 단일 완료율 표시 금지** — 텍스트 `5/8 완료` 형태로 충분.

### Do's

- 비즈니스 로직은 `apps/{app}/services/*.py` 에만 작성. 뷰는 직렬화·폼 처리만.
- 파싱 실패는 예외 throw 가 아니라 `raw_text` 에 원문 저장 + `SyncLog.result='failed'` + `detail` 에 사유.
- 새 파서 추가 시 `BaseParser` 를 상속하고 `apps/parsers/tests/` 에 fixture 기반 단위 테스트 추가.
- 모든 화면은 `templates/base.html` 을 extends 하여 일관된 레이아웃 유지.
- 프로젝트 카드·탭 UI 는 Tailwind utility class 만 사용. 커스텀 CSS 는 `static/css/custom.css` 에 한정.

### Don'ts

- Redis, Celery, Channels 등 비동기·메시지 브로커 도입 금지 (단일 사용자 도구).
- jQuery·Bootstrap·Chart.js 류 무거운 외부 라이브러리 추가 금지. 가벼운 표시는 HTMX 또는 Alpine.js 까지만 허용.
- `Project.delete()` 직접 호출 금지 — 매니저 메서드 또는 service 함수 통해 소프트 딜리트.
- 파싱 결과를 메모리에 캐시하지 말고 매번 DB 조회. (Redis 미사용)

---

## Definition of Done — 프로젝트 추가 기준

> 전역 DoD는 CLAUDE.md §Definition of Done 참조.

- [ ] 새 파서 추가 시 fixture(샘플 md) 기반 단위 테스트 통과
- [ ] 새 화면·탭 추가 시 Tailwind 클래스만 사용 확인 (`grep -r 'class=".*btn-' templates/` 비어 있어야 함)
- [ ] SCR-* / F-* 신규 시 `docs/기능정의.md` 표 갱신 + `docs/feature_map.md` 행 추가
- [ ] 파싱 결과 모델에 `raw_text` 필드 누락 여부 확인
- [ ] `sync_service` 호출 후 `SyncLog` 행이 정확히 N건(파일 수만큼) 기록되는지 통합 테스트로 검증
- [ ] 등록된 외부 프로젝트 폴더에 쓰기 시도가 없는지 코드 리뷰 시 확인

---

## Git 전략

- **Branch 전략**
  - `main` — 배포 가능 상태만
  - `develop` — 통합 브랜치
  - `feature/<phase>-<num>-<slug>` (예: `feature/p1-01-project-model`)

- **Commit 메시지**: `<type>(<scope>): <subject>`
  - type: `feat` / `fix` / `refactor` / `docs` / `test` / `chore`
  - scope: `projects` / `parsers` / `dashboard` / `sync` / `docs` / `infra`

- **gitignore 필수**: `.env` / `db.sqlite3` / `staticfiles/` / `venv/` / `__pycache__/` / `*.pyc` / `.pytest_cache/` / `tmp/`

---

## 규약

- **네이밍**:
  - 테이블명: `snake_case` (예: `app_module`, `improvement_item`)
  - URL name: `<app>:<view>` 형식 (예: `dashboard:project_list`)
  - 템플릿 파일: `<app>/<view_name>.html` (예: `dashboard/project_list.html`)
- **날짜 형식**: `YYYY-MM-DD`
- **문서 언어**: `docs/` 하위 `.md` 파일은 한국어
- **Tailwind 클래스 정렬**: layout → spacing → sizing → typography → color → state 순으로 작성
- **모델 필드 순서**: PK → FK → 식별자(코드) → 본문 → 상태 플래그 → 타임스탬프 → soft-delete

---

## Context Map

작업 유형별 참조 문서:

- **[진행 순서](./docs/진행순서.md)** ★ — **현재 작업 단계** 단일 진실의 원천. 세션 시작 시 가장 먼저 확인.
- **[기능 ID 매핑](./docs/기능정의.md)** — 신규 화면·기능 설계, SCR-* / F-* 조회·등록
- **[UI/UX 개선](./docs/uiux개선.md)** — P0~P3 개선 항목 선정·구현 체크
- **[구조 명세](./docs/프로그램구조.md)** — 모델·뷰·URL·서비스 위치 조회·갱신
- **[기능 매핑](./docs/feature_map.md)** — 기능↔파일:함수↔DB 테이블 매핑 갱신
- **[구현 로드맵](./docs/프로젝트설계.md)** — Phase 일정·마일스톤·리스크
- **[사용자 매뉴얼](./docs/매뉴얼.html)** — 화면 캡처 + 사용 흐름 (E2E 통과 후 갱신)

---

## Nested AGENTS Boundaries

앱별 상세 규칙 파일 (Phase 진입 시 생성):

- **[projects](./apps/projects/AGENTS.md)** — 프로젝트 등록·검증·소프트딜리트
- **[parsers](./apps/parsers/AGENTS.md)** — md 파싱 규칙 추가·수정 가이드
- **[dashboard](./apps/dashboard/AGENTS.md)** — 화면 추가, Tailwind 컴포넌트 패턴
- **[sync](./apps/sync/AGENTS.md)** — 동기화 오케스트레이션, mtime 비교 규칙

---

## Change Log

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| 1.0 | 2026-04-29 | 최초 작성 — Django 5.x + Tailwind, Redis/Celery 미사용 결정. 외부 프로젝트 폴더 read-only 원칙 명시. |
