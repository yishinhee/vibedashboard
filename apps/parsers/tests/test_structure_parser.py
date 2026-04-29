"""StructureParser 단위 테스트 — 프로그램구조.md → AppModule / ModelInfo."""
from django.test import TestCase

from apps.dashboard.models import AppModule, ModelInfo
from apps.parsers.services.structure_parser import StructureParser
from apps.projects.models import Project

SAMPLE_MD = """
## 1. apps/projects/ — 프로젝트 등록 관리

### 책임
- Project CRUD

### 모델
| 모델 | 테이블 | 주요 필드 |
|---|---|---|
| Project | `project` | `path`, `name`, `deleted_at` |

### 서비스
| 함수 | 파일 | 책임 |
|---|---|---|
| `list_active()` | `services/project_service.py` | 활성 |
| `soft_delete(project)` | `services/project_service.py` | 소프트 |

## 2. apps/dashboard/ — 화면

### 모델
| 모델 | 테이블 |
|---|---|
| Screen | `screen` |
| Feature | `feature` |
"""


class StructureParserTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(path="/tmp/p2", name="t")
        self.parser = StructureParser()

    def test_parse_extracts_apps(self):
        result = self.parser.parse(SAMPLE_MD)
        apps = result["apps"]
        self.assertEqual(set(apps.keys()), {"projects", "dashboard"})
        self.assertIn("프로젝트 등록 관리", apps["projects"]["responsibility"])

    def test_parse_counts_models(self):
        result = self.parser.parse(SAMPLE_MD)
        self.assertEqual(result["apps"]["projects"]["model_count"], 1)
        self.assertEqual(result["apps"]["dashboard"]["model_count"], 2)

    def test_parse_counts_services(self):
        result = self.parser.parse(SAMPLE_MD)
        self.assertEqual(result["apps"]["projects"]["service_count"], 2)
        self.assertEqual(result["apps"]["dashboard"]["service_count"], 0)

    def test_save_creates_db_rows(self):
        summary = self.parser.parse_and_save(self.project, SAMPLE_MD)
        self.assertEqual(AppModule.objects.filter(project=self.project).count(), 2)
        self.assertEqual(ModelInfo.objects.filter(project=self.project).count(), 3)
        self.assertIn("앱 2", summary)
        self.assertIn("모델 3", summary)

    def test_save_persists_table_name_and_fields(self):
        self.parser.parse_and_save(self.project, SAMPLE_MD)
        proj_model = ModelInfo.objects.get(
            project=self.project, app_name="projects", model_name="Project"
        )
        self.assertEqual(proj_model.table_name, "project")
        self.assertIn("path", proj_model.fields)

    def test_empty_input(self):
        result = self.parser.parse("")
        self.assertEqual(result["apps"], {})
