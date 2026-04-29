# harness-dashboard Feature Map

> 기능 ID ↔ 소스 파일:함수 ↔ DB 테이블:필드 매핑.
> 기능변경·신규 시 즉시 갱신한다 (CLAUDE.md §Hooks `feature_map_update` 스킬 자동 트리거).

| 기능 ID | 기능명 | 진입점 (URL) | 뷰 (파일:함수) | 서비스 (파일:함수) | 모델/DB | 템플릿/UI | 외부 API |
|---|---|---|---|---|---|---|---|
| F-PROJ-01 | 프로젝트 목록 조회 | `/` | `apps/dashboard/views.py:project_list` | `apps/projects/services/project_service.py:list_active` | `project` | `dashboard/project_list.html` | — |
| F-PROJ-02 | 프로젝트 등록 | `/projects/add/` | `apps/projects/views.py:project_create` | `apps/projects/services/project_service.py:create_with_initial_sync` | `project`, `sync_log` | `projects/project_form.html` | — |
| F-PROJ-03 | 프로젝트 편집 | `/projects/<id>/edit/` | `apps/projects/views.py:project_update` | `apps/projects/services/project_service.py:update` | `project` | `projects/project_form.html` | — |
| F-PROJ-04 | 프로젝트 삭제(소프트) | `/projects/<id>/delete/` | `apps/projects/views.py:project_delete` | `apps/projects/services/project_service.py:soft_delete` | `project.deleted_at` | `dashboard/project_list.html` (확인 모달) | — |
| F-PROJ-05 | 미갱신 문서 경고 배지 | `/` | `apps/dashboard/views.py:project_list` | `apps/projects/services/project_service.py:get_pending_count` | — (외부 `tmp/pending_updates.json` 파일 읽기) | `dashboard/_project_card.html` | — |
| F-FEAT-01 | 화면 ID 목록 | `/projects/<id>/features/` | `apps/dashboard/views.py:features_tab` | — (직접 ORM) | `screen` | `dashboard/features_tab.html` | — |
| F-FEAT-02 | 기능 ID 목록 | `/projects/<id>/features/` | `apps/dashboard/views.py:features_tab` | — | `feature` | `dashboard/features_tab.html` | — |
| F-FEAT-03 | 앱별 필터 | `/projects/<id>/features/?app=<name>` | `apps/dashboard/views.py:features_tab` | — | `feature`, `app_module` | `dashboard/features_tab.html` | — |
| F-FEAT-04 | 미구현 기능 강조 | `/projects/<id>/features/?status=not_implemented` | `apps/dashboard/views.py:features_tab` | — | `feature.status` | `dashboard/features_tab.html` (Tailwind `text-rose-500`) | — |
| F-PHASE-01 | Phase 목록 | `/projects/<id>/phases/` | `apps/dashboard/views.py:phases_tab` | — | `phase`, `checklist_item` | `dashboard/phases_tab.html` | — |
| F-PHASE-02 | 텍스트 완료율 | `/projects/<id>/phases/` | `apps/dashboard/views.py:phases_tab` | `apps/dashboard/services/phase_service.py:calc_progress` | `phase.done_items / phase.total_items` | `dashboard/phases_tab.html` | — |
| F-PHASE-03 | 현재 Phase 강조 | `/projects/<id>/phases/` | `apps/dashboard/views.py:phases_tab` | — | `phase.status='in_progress'` | `dashboard/phases_tab.html` | — |
| F-PHASE-04 | 체크리스트 항목 | `/projects/<id>/phases/` | `apps/dashboard/views.py:phases_tab` | — | `checklist_item` | `dashboard/phases_tab.html` | — |
| F-STRUCT-01 | 앱 목록 | `/projects/<id>/structure/` | `apps/dashboard/views.py:structure_tab` | — | `app_module` | `dashboard/structure_tab.html` | — |
| F-STRUCT-02 | feature_map 테이블 | `/projects/<id>/structure/` | `apps/dashboard/views.py:structure_tab` | — | `feature_map` | `dashboard/structure_tab.html` | — |
| F-STRUCT-03 | 모델 요약 | `/projects/<id>/structure/` | `apps/dashboard/views.py:structure_tab` | — | `model_info` | `dashboard/structure_tab.html` | — |
| F-IMPR-01 | 개선 항목 목록 | `/projects/<id>/improvements/` | `apps/dashboard/views.py:improvements_tab` | — | `improvement_item` | `dashboard/improvements_tab.html` | — |
| F-IMPR-02 | 우선순위 필터 | `/projects/<id>/improvements/?priority=P0` | `apps/dashboard/views.py:improvements_tab` | — | `improvement_item.priority` | `dashboard/improvements_tab.html` | — |
| F-IMPR-03 | 완료/미완료 필터 | `/projects/<id>/improvements/?done=0` | `apps/dashboard/views.py:improvements_tab` | — | `improvement_item.is_done` | `dashboard/improvements_tab.html` | — |
| F-SYNC-01 | 수동 동기화 | `POST /projects/<id>/sync/` | `apps/sync/views.py:sync_now` | `apps/sync/services/sync_service.py:sync_project` | `sync_log`, 모든 파싱 테이블 | `dashboard/sync_panel.html` (HTMX) | — |
| F-SYNC-02 | mtime 변경 감지 | (내부) | — | `apps/sync/services/sync_service.py:sync_one_file` | `sync_log.file_mtime` | — | — |
| F-SYNC-03 | 동기화 로그 | `/projects/<id>/sync/` | `apps/sync/views.py:sync_log_list` | — | `sync_log` | `dashboard/sync_log.html` | — |

---

## 변경 이력

| 일자 | 변경 |
|---|---|
| 2026-04-29 | 최초 작성. 22개 기능 모두 `not_implemented` 상태. 구현 시 행별로 갱신. |
