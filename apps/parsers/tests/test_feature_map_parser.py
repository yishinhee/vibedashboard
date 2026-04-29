"""FeatureMapParser 단위 테스트 — feature_map.md → FeatureMap."""
from django.test import TestCase

from apps.dashboard.models import FeatureMap
from apps.parsers.services.feature_map_parser import FeatureMapParser
from apps.projects.models import Project

SAMPLE_MD = """
# Feature Map

| 기능 ID | 기능명 | 진입점 | 뷰 | 서비스 | 모델/DB | 템플릿 | 외부 API |
|---|---|---|---|---|---|---|---|
| F-PROJ-01 | 프로젝트 목록 조회 | `/` | `views.py:project_list` | `project_service.py:list_active` | `project` | `project_list.html` | — |
| F-PROJ-02 | 프로젝트 등록 | `/projects/add/` | `views.py:project_create` | `project_service.py:create` | `project, sync_log` | `project_form.html` | — |
| F-SYNC-01 | 수동 동기화 | `POST /sync/` | `views.py:sync_now` | `sync_service.py:sync_project` | `sync_log` | `sync_panel.html` | — |
"""


class FeatureMapParserTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(path="/tmp/p5", name="t")
        self.parser = FeatureMapParser()

    def test_parse_extracts_rows(self):
        result = self.parser.parse(SAMPLE_MD)
        ids = [r["feature_id"] for r in result["rows"]]
        self.assertEqual(ids, ["F-PROJ-01", "F-PROJ-02", "F-SYNC-01"])

    def test_parse_extracts_all_columns(self):
        result = self.parser.parse(SAMPLE_MD)
        proj01 = result["rows"][0]
        self.assertEqual(proj01["feature_id"], "F-PROJ-01")
        self.assertEqual(proj01["feature_name"], "프로젝트 목록 조회")
        self.assertEqual(proj01["entry_point"], "/")
        self.assertEqual(proj01["view_handler"], "views.py:project_list")
        self.assertEqual(proj01["service"], "project_service.py:list_active")
        self.assertEqual(proj01["model_db"], "project")
        self.assertEqual(proj01["template_ui"], "project_list.html")

    def test_parse_skips_header_and_separator(self):
        # 헤더(`기능 ID`) 와 구분 행(`|---|`)은 제외
        result = self.parser.parse(SAMPLE_MD)
        self.assertEqual(len(result["rows"]), 3)

    def test_save_creates_db_rows(self):
        summary = self.parser.parse_and_save(self.project, SAMPLE_MD)
        self.assertEqual(FeatureMap.objects.filter(project=self.project).count(), 3)
        self.assertIn("FeatureMap 3", summary)

    def test_parse_and_save_replaces_existing(self):
        self.parser.parse_and_save(self.project, SAMPLE_MD)
        replacement = """
| 기능 ID | 기능명 | 진입점 |
|---|---|---|
| F-X-01 | 새 기능 | `/x/` |
"""
        self.parser.parse_and_save(self.project, replacement)
        rows = list(FeatureMap.objects.filter(project=self.project))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].feature_id, "F-X-01")

    def test_empty_input(self):
        result = self.parser.parse("")
        self.assertEqual(result["rows"], [])
