"""DesignParser 단위 테스트 — 프로젝트설계.md → Phase."""
from django.test import TestCase

from apps.dashboard.models import Phase
from apps.parsers.services.design_parser import DesignParser
from apps.projects.models import Project

SAMPLE_MD = """
# 프로젝트 설계

## Phase 1 — 데이터 레이어 (완료)
SQLite 스키마 작성, 파서 5종 구현

## Phase 2 — 프로젝트 관리 화면 (진행 중)
F-PROJ-01~05 구현

## Phase 3 — 상세 4개 탭
F-FEAT / F-PHASE / F-STRUCT / F-IMPR
"""


class DesignParserTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(path="/tmp/p4", name="t")
        self.parser = DesignParser()

    def test_parse_extracts_phase_headings(self):
        result = self.parser.parse(SAMPLE_MD)
        self.assertEqual(set(result["phases"].keys()), {1, 2, 3})

    def test_parse_detects_status(self):
        result = self.parser.parse(SAMPLE_MD)
        self.assertEqual(result["phases"][1]["status"], Phase.Status.DONE)
        self.assertEqual(result["phases"][2]["status"], Phase.Status.IN_PROGRESS)
        self.assertEqual(result["phases"][3]["status"], Phase.Status.PENDING)

    def test_parse_extracts_goal(self):
        result = self.parser.parse(SAMPLE_MD)
        self.assertIn("SQLite", result["phases"][1]["goal"])
        self.assertIn("F-PROJ-01", result["phases"][2]["goal"])

    def test_save_creates_db_rows(self):
        summary = self.parser.parse_and_save(self.project, SAMPLE_MD)
        self.assertEqual(Phase.objects.filter(project=self.project).count(), 3)
        self.assertIn("Phase 3", summary)

    def test_save_updates_existing_phase(self):
        # improvement_parser 가 만든 stub 처럼 빈 Phase 생성
        Phase.objects.create(project=self.project, phase_num=1, name="stub")

        self.parser.parse_and_save(self.project, SAMPLE_MD)
        phase = Phase.objects.get(project=self.project, phase_num=1)
        self.assertNotEqual(phase.name, "stub")  # update_or_create 가 갱신
        self.assertEqual(phase.status, Phase.Status.DONE)

    def test_empty_input(self):
        result = self.parser.parse("")
        self.assertEqual(result["phases"], {})
