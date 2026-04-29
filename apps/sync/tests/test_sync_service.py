"""sync_service 통합 테스트 — 임시 docs/ 디렉토리 기반 시나리오 검증."""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

from django.test import TestCase

from apps.dashboard.models import Feature, FeatureMap, Phase, Screen
from apps.projects.models import Project
from apps.sync.models import SyncLog
from apps.sync.services.sync_service import sync_one_file, sync_project

# ============================================================
# 미니 fixture md — 5개 파일에 대응
# ============================================================
FIX_FEATURE = """
## 2.1 화면

| Screen ID | 화면명 | URL | 설명 |
|---|---|---|---|
| SCR-T-01 | 테스트 화면 | `/t/` | 설명 |

## 3.1 기능

| 기능 ID | 기능명 | 화면 | 상태 | 상세 |
|---|---|---|---|---|
| F-T-01 | 테스트 기능 | SCR-T-01 | implemented | 본문 |
"""

FIX_STRUCTURE = """
## 1. apps/test_app/ — 테스트 앱

### 모델
| 모델 | 테이블 | 주요 필드 |
|---|---|---|
| TestModel | `test_model` | name |
"""

FIX_IMPROVEMENT = """
### [P0] 테스트 개선
설명

### Phase 1 — 데이터
- ✅ 모델 작성
- [ ] 테스트
"""

FIX_DESIGN = """
## Phase 1 — 데이터 (완료)
스키마 작성

## Phase 2 — 화면
F-PROJ-01 등 구현
"""

FIX_FEATURE_MAP = """
| 기능 ID | 기능명 | 진입점 |
|---|---|---|
| F-T-01 | 테스트 기능 | `/t/` |
"""

FIXTURES = {
    "기능정의.md": FIX_FEATURE,
    "프로그램구조.md": FIX_STRUCTURE,
    "uiux개선.md": FIX_IMPROVEMENT,
    "프로젝트설계.md": FIX_DESIGN,
    "feature_map.md": FIX_FEATURE_MAP,
}


class SyncServiceIntegrationTests(TestCase):
    """sync_service.sync_one_file / sync_project 시나리오 검증."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="harness_sync_")
        docs = Path(self.tmpdir) / "docs"
        docs.mkdir()
        for fn, content in FIXTURES.items():
            (docs / fn).write_text(content, encoding="utf-8")
        self.project = Project.objects.create(path=self.tmpdir, name="integration")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_first_sync_all_success(self):
        results = sync_project(self.project)
        self.assertEqual(len(results), 5)
        self.assertEqual(set(results.values()), {"success"})
        self.assertEqual(
            SyncLog.objects.filter(project=self.project, result="success").count(), 5
        )

    def test_second_sync_all_no_change(self):
        sync_project(self.project)
        results = sync_project(self.project)
        self.assertEqual(set(results.values()), {"no_change"})
        self.assertEqual(
            SyncLog.objects.filter(project=self.project, result="no_change").count(), 5
        )

    def test_modifying_one_file_only_resyncs_that_file(self):
        sync_project(self.project)
        target = Path(self.tmpdir) / "docs" / "기능정의.md"
        target.write_text(FIX_FEATURE + "\n", encoding="utf-8")
        future = time.time() + 10  # mtime 을 미래로 강제 이동
        os.utime(target, (future, future))

        results = sync_project(self.project)
        self.assertEqual(results["기능정의.md"], "success")
        for fn in ("프로그램구조.md", "uiux개선.md", "프로젝트설계.md", "feature_map.md"):
            self.assertEqual(results[fn], "no_change")

    def test_missing_file_returns_failed(self):
        result = sync_one_file(self.project, "nonexistent.md")
        self.assertEqual(result, "failed")
        log = SyncLog.objects.filter(
            project=self.project, file_name="nonexistent.md"
        ).latest("synced_at")
        self.assertEqual(log.result, "failed")
        self.assertIn("not found", log.detail)

    def test_unregistered_filename_returns_failed(self):
        unknown = Path(self.tmpdir) / "docs" / "random.md"
        unknown.write_text("# random", encoding="utf-8")
        result = sync_one_file(self.project, "random.md")
        self.assertEqual(result, "failed")
        log = SyncLog.objects.filter(
            project=self.project, file_name="random.md"
        ).latest("synced_at")
        self.assertEqual(log.detail, "no parser registered")

    def test_last_synced_at_updated_on_sync_project(self):
        self.assertIsNone(self.project.last_synced_at)
        sync_project(self.project)
        self.project.refresh_from_db()
        self.assertIsNotNone(self.project.last_synced_at)

    def test_first_sync_persists_parsed_rows(self):
        sync_project(self.project)
        self.assertEqual(Screen.objects.filter(project=self.project).count(), 1)
        self.assertEqual(Feature.objects.filter(project=self.project).count(), 1)
        self.assertEqual(FeatureMap.objects.filter(project=self.project).count(), 1)
        self.assertGreaterEqual(Phase.objects.filter(project=self.project).count(), 1)

    def test_failed_file_does_not_block_others(self):
        (Path(self.tmpdir) / "docs" / "프로그램구조.md").unlink()
        results = sync_project(self.project)
        self.assertEqual(results["프로그램구조.md"], "failed")
        success_count = sum(1 for r in results.values() if r == "success")
        self.assertEqual(success_count, 4)
