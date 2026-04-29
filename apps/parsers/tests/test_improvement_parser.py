"""ImprovementParser 단위 테스트 — uiux개선.md → ImprovementItem / ChecklistItem."""
from django.test import TestCase

from apps.dashboard.models import ChecklistItem, ImprovementItem, Phase
from apps.parsers.services.improvement_parser import ImprovementParser
from apps.projects.models import Project

SAMPLE_MD = """
# UI/UX 개선

## P0 항목

### [P0] 폴더 경로 검증
경로 미존재 시 분기 처리

### ✅ [P0] 빈 화면 안내
완료된 항목

## P1 항목

### [P1] 카드 컴포넌트 정렬

## Phase 체크리스트

### Phase 1 — 데이터 레이어
- ✅ 모델 정의
- [x] 마이그레이션
- [ ] 파서 구현

### Phase 2 — 화면
- [ ] 카드 컴포넌트
- [ ] 폼 검증
"""


class ImprovementParserTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(path="/tmp/p3", name="t")
        self.parser = ImprovementParser()

    def test_parse_extracts_improvements(self):
        result = self.parser.parse(SAMPLE_MD)
        items = result["improvements"]
        self.assertEqual(len(items), 3)
        priorities = [i["priority"] for i in items]
        self.assertEqual(priorities, ["P0", "P0", "P1"])

    def test_parse_marks_done_with_check(self):
        result = self.parser.parse(SAMPLE_MD)
        done = [i for i in result["improvements"] if i["is_done"]]
        self.assertEqual(len(done), 1)
        self.assertEqual(done[0]["title"], "빈 화면 안내")

    def test_parse_extracts_phase_checklist(self):
        result = self.parser.parse(SAMPLE_MD)
        phases = result["phase_items"]
        self.assertEqual(set(phases.keys()), {1, 2})
        self.assertEqual(len(phases[1]["items"]), 3)
        done_count = sum(1 for it in phases[1]["items"] if it["is_done"])
        self.assertEqual(done_count, 2)  # ✅ 모델 정의, [x] 마이그레이션

    def test_save_creates_db_rows(self):
        summary = self.parser.parse_and_save(self.project, SAMPLE_MD)
        self.assertEqual(ImprovementItem.objects.filter(project=self.project).count(), 3)
        self.assertEqual(ChecklistItem.objects.filter(project=self.project).count(), 5)
        self.assertIn("개선 3", summary)
        self.assertIn("체크리스트 5", summary)

    def test_save_creates_phase_stub_with_progress(self):
        self.parser.parse_and_save(self.project, SAMPLE_MD)
        phase1 = Phase.objects.get(project=self.project, phase_num=1)
        self.assertEqual(phase1.total_items, 3)
        self.assertEqual(phase1.done_items, 2)
        self.assertEqual(phase1.status, Phase.Status.IN_PROGRESS)

        phase2 = Phase.objects.get(project=self.project, phase_num=2)
        self.assertEqual(phase2.total_items, 2)
        self.assertEqual(phase2.done_items, 0)
        self.assertEqual(phase2.status, Phase.Status.PENDING)

    def test_phase_completion_status_when_all_done(self):
        md = """
### Phase 9 — 완료된 단계
- ✅ A
- ✅ B
"""
        self.parser.parse_and_save(self.project, md)
        phase = Phase.objects.get(project=self.project, phase_num=9)
        self.assertEqual(phase.status, Phase.Status.DONE)
