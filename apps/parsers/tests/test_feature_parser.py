"""FeatureParser 단위 테스트 — 기능정의.md → Screen / Feature."""
from django.test import TestCase

from apps.dashboard.models import Feature, Screen
from apps.parsers.services.feature_parser import FeatureParser
from apps.projects.models import Project

SAMPLE_MD = """
## 2.1 사용자 화면

| Screen ID | 화면명 | URL | 설명 |
|---|---|---|---|
| SCR-PROJ-01 | 프로젝트 목록 | `/` | 등록된 전체 프로젝트 |
| SCR-PROJ-02 | 프로젝트 등록 | `/projects/add/` | 폴더 경로 등록 |

## 3.1 프로젝트 관리

| 기능 ID | 기능명 | 화면 | 상태 | 상세 |
|---|---|---|---|---|
| F-PROJ-01 | 프로젝트 목록 조회 | SCR-PROJ-01 | not_implemented | 카드 표시 |
| F-PROJ-02 | 프로젝트 등록 | SCR-PROJ-02 | implemented | 폼 입력 |
"""


class FeatureParserTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(path="/tmp/p1", name="t")
        self.parser = FeatureParser()

    def test_parse_extracts_screens(self):
        result = self.parser.parse(SAMPLE_MD)
        screens = {s["screen_id"]: s for s in result["screens"]}
        self.assertEqual(set(screens.keys()), {"SCR-PROJ-01", "SCR-PROJ-02"})
        self.assertEqual(screens["SCR-PROJ-01"]["name"], "프로젝트 목록")
        self.assertEqual(screens["SCR-PROJ-01"]["url"], "/")
        self.assertEqual(screens["SCR-PROJ-01"]["category"], "2.1 사용자 화면")

    def test_parse_extracts_features_with_status(self):
        result = self.parser.parse(SAMPLE_MD)
        features = {f["feature_id"]: f for f in result["features"]}
        self.assertEqual(set(features.keys()), {"F-PROJ-01", "F-PROJ-02"})
        self.assertEqual(features["F-PROJ-01"]["screen_id"], "SCR-PROJ-01")
        self.assertEqual(features["F-PROJ-01"]["status"], "not_implemented")
        self.assertEqual(features["F-PROJ-02"]["status"], "implemented")

    def test_save_creates_db_rows(self):
        summary = self.parser.parse_and_save(self.project, SAMPLE_MD)
        self.assertEqual(Screen.objects.filter(project=self.project).count(), 2)
        self.assertEqual(Feature.objects.filter(project=self.project).count(), 2)
        self.assertIn("SCR 2", summary)
        self.assertIn("F 2", summary)

    def test_parse_and_save_replaces_existing(self):
        self.parser.parse_and_save(self.project, SAMPLE_MD)
        replacement = """
| Screen ID | 화면명 | URL |
|---|---|---|
| SCR-X-01 | 화면 X | `/x/` |
"""
        self.parser.parse_and_save(self.project, replacement)
        screens = list(Screen.objects.filter(project=self.project))
        self.assertEqual(len(screens), 1)
        self.assertEqual(screens[0].screen_id, "SCR-X-01")
        self.assertEqual(Feature.objects.filter(project=self.project).count(), 0)

    def test_empty_input_returns_empty_lists(self):
        result = self.parser.parse("")
        self.assertEqual(result["screens"], [])
        self.assertEqual(result["features"], [])

    def test_raw_text_is_preserved(self):
        result = self.parser.parse(SAMPLE_MD)
        self.assertIn("SCR-PROJ-01", result["screens"][0]["raw_text"])
        self.assertIn("F-PROJ-01", result["features"][0]["raw_text"])
