---
name: feature-map-update
version: 1.0.0
description: sync_structure.py 게이트 해제를 위한 feature_map.md 정밀 갱신 스킬
---

# Feature Map Update Skill

## 활성화 조건

다음 중 하나라도 해당되면 이 스킬을 즉시 실행한다. 별도 지시 불필요.

1. `sync_structure.py` 가 `feature_map.md 갱신 전 다음 작업 금지` 출력 시
2. `tmp/pending_updates.json` 에 `feature_map.md` 미갱신 항목 존재 시
3. 사용자가 "기능 매핑 갱신", "feature map 업데이트" 등을 요청 시

---

## 실행 절차

### Step 1 — 갱신 대상 파악

```bash
# pending_updates.json 에서 갱신 대상 확인
cat tmp/pending_updates.json
```

항목별로 `type` (feature/new) 과 `source_file` 을 확인한다.

### Step 2 — 수정된 소스 파일 분석

대상 파일을 Read 도구로 읽어 다음을 추출한다.

| 추출 항목 | 추출 방법 |
|---|---|
| **기능 ID** | `docs/기능정의.md` 에서 해당 기능의 F-* ID 확인 |
| **기능명** | 함수·클래스의 docstring 또는 주석에서 추출 |
| **진입점** | `urls.py` 에서 해당 view 의 URL path 확인 |
| **View/Handler** | 수정된 파일의 클래스·함수명 (`파일경로:클래스.메서드`) |
| **Service** | view 에서 호출하는 service 함수 (`파일경로:함수명`) |
| **Model/DB** | import 된 모델명 + 실제 사용 필드 (`테이블명 (필드1, 필드2)`) |
| **Template/UI** | `render()` 또는 `template_name` 에서 경로 추출 |
| **외부 연동** | 외부 API 호출 여부 확인 |

**분석 순서**: 수정 파일 → urls.py → services/ → models.py → templates/

### Step 3 — feature_map.md 갱신

`docs/feature_map.md` 를 Read 도구로 읽은 후:

#### 기능변경 (type: feature) 인 경우
해당 기능 ID 행을 찾아 변경된 컬럼만 업데이트한다.

```
변경 전: | F-BRD-01 | 게시글 목록 | GET /boards/ | views.py:BoardListView | ... |
변경 후: | F-BRD-01 | 게시글 목록 | GET /boards/ | views.py:BoardListView | board_service.py:get_list_v2() | ... |
```

#### 신규기능 (type: new) 인 경우
**기능 매핑 테이블** 에 새 행을 추가한다.

```markdown
| F-XXX-NN | [기능명] | [진입점] | [View:함수] | [Service:함수] | [테이블 (필드)] | [템플릿] | [외부연동] |
```

동시에 **DB 테이블 역참조** 와 **파일 역참조** 섹션도 갱신한다.

### Step 4 — 갱신 완료 확인

feature_map.md 저장 후 sync_structure.py 가 자동으로 게이트 해제 메시지를 출력한다.

```
[sync] ✅ feature_map.md 갱신 확인 — N개 항목 클리어
```

이 메시지가 나오면 다음 작업으로 진행한다.
나오지 않으면 파일 저장이 제대로 됐는지 확인한다.

---

## 갱신 품질 기준

| 항목 | 기준 |
|---|---|
| 기능 ID | `docs/기능정의.md` 의 F-* ID 와 일치 |
| 파일경로 | 프로젝트 루트 기준 상대경로 (`apps/boards/views.py`) |
| 함수명 | 실제 코드의 함수·클래스명 그대로 |
| DB 필드 | 실제 사용하는 필드만 기재 (전체 필드 나열 금지) |
| 외부 연동 | 없으면 `-` 로 표기 |

---

## 주의사항

- 행을 추가할 때 기존 행의 정렬(컬럼 너비)을 유지한다.
- 기능 ID 는 임의로 생성하지 않는다. 반드시 `docs/기능정의.md` 에서 확인 후 기재.
- 아직 기능정의.md 에 등록되지 않은 신규 기능이면 기능정의.md 먼저 등록 후 feature_map.md 갱신.
