"""
대시보드 모델 — 외부 프로젝트 docs/*.md 파싱 산출물 8종.
공통: project FK + raw_text 보존 (agents.md §파싱 정책).
"""
from django.db import models


# ============================================================
# 기능정의.md 파싱 → Screen, Feature
# ============================================================
class Screen(models.Model):
    """SCR-* 화면 ID."""

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="screens",
    )
    screen_id = models.CharField(max_length=50, verbose_name="화면 ID")
    category = models.CharField(max_length=200, blank=True, verbose_name="카테고리")
    name = models.CharField(max_length=300, blank=True, verbose_name="화면명")
    url = models.CharField(max_length=300, blank=True, verbose_name="URL")
    raw_text = models.TextField(blank=True, verbose_name="원문")

    class Meta:
        db_table = "screen"
        unique_together = [("project", "screen_id")]
        verbose_name = "화면"
        verbose_name_plural = "화면"

    def __str__(self):
        return f"{self.screen_id} {self.name}"


class Feature(models.Model):
    """F-* 기능 ID."""

    class Status(models.TextChoices):
        IMPLEMENTED = "implemented", "구현 완료"
        NOT_IMPLEMENTED = "not_implemented", "미구현"
        UNKNOWN = "unknown", "미상"

    class Priority(models.TextChoices):
        P0 = "P0", "P0"
        P1 = "P1", "P1"
        P2 = "P2", "P2"
        P3 = "P3", "P3"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="features",
    )
    screen_id = models.CharField(max_length=50, blank=True, verbose_name="연결 SCR")
    feature_id = models.CharField(max_length=50, verbose_name="기능 ID")
    name = models.CharField(max_length=300, blank=True, verbose_name="기능명")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNKNOWN,
    )
    priority = models.CharField(max_length=4, choices=Priority.choices, blank=True)
    raw_text = models.TextField(blank=True)

    class Meta:
        db_table = "feature"
        unique_together = [("project", "feature_id")]
        indexes = [
            models.Index(fields=["project", "status"], name="idx_feature_status"),
        ]
        verbose_name = "기능"
        verbose_name_plural = "기능"

    def __str__(self):
        return f"{self.feature_id} {self.name}"


# ============================================================
# 프로그램구조.md 파싱 → AppModule, ModelInfo
# ============================================================
class AppModule(models.Model):
    """앱 모듈."""

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="app_modules",
    )
    app_name = models.CharField(max_length=100, verbose_name="앱명")
    responsibility = models.TextField(blank=True, verbose_name="책임")
    model_count = models.IntegerField(default=0)
    service_count = models.IntegerField(default=0)
    raw_text = models.TextField(blank=True)

    class Meta:
        db_table = "app_module"
        unique_together = [("project", "app_name")]
        verbose_name = "앱 모듈"
        verbose_name_plural = "앱 모듈"

    def __str__(self):
        return self.app_name


class ModelInfo(models.Model):
    """모델 정보."""

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="model_infos",
    )
    app_name = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100)
    table_name = models.CharField(max_length=100, blank=True)
    fields = models.TextField(blank=True, verbose_name="필드 JSON")
    raw_text = models.TextField(blank=True)

    class Meta:
        db_table = "model_info"
        unique_together = [("project", "app_name", "model_name")]
        verbose_name = "모델 정보"
        verbose_name_plural = "모델 정보"

    def __str__(self):
        return f"{self.app_name}.{self.model_name}".strip(".")


# ============================================================
# 프로젝트설계.md 파싱 → Phase
# uiux개선.md 파싱 → ChecklistItem (Phase 종속)
# ============================================================
class Phase(models.Model):
    """Phase 정보."""

    class Status(models.TextChoices):
        DONE = "done", "완료"
        IN_PROGRESS = "in_progress", "진행 중"
        PENDING = "pending", "대기"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="phases",
    )
    phase_num = models.IntegerField(verbose_name="Phase 번호")
    name = models.CharField(max_length=200, blank=True, verbose_name="Phase명")
    goal = models.TextField(blank=True, verbose_name="목표")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_items = models.IntegerField(default=0)
    done_items = models.IntegerField(default=0)

    class Meta:
        db_table = "phase"
        unique_together = [("project", "phase_num")]
        ordering = ["phase_num"]
        verbose_name = "Phase"
        verbose_name_plural = "Phase"

    def __str__(self):
        return f"Phase {self.phase_num} {self.name}".rstrip()

    @property
    def completion_text(self) -> str:
        """`5/8 완료` 형식 (agents.md §Don'ts: 파이차트 금지)."""
        return f"{self.done_items}/{self.total_items} 완료"


class ChecklistItem(models.Model):
    """Phase 체크리스트 항목."""

    class Priority(models.TextChoices):
        P0 = "P0", "P0"
        P1 = "P1", "P1"
        P2 = "P2", "P2"
        P3 = "P3", "P3"

    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    priority = models.CharField(max_length=4, choices=Priority.choices, blank=True)
    content = models.TextField(verbose_name="내용")
    is_done = models.BooleanField(default=False)
    raw_text = models.TextField(blank=True)

    class Meta:
        db_table = "checklist_item"
        indexes = [
            models.Index(fields=["phase", "is_done"], name="idx_checklist_phase"),
        ]
        verbose_name = "체크리스트 항목"
        verbose_name_plural = "체크리스트 항목"

    def __str__(self):
        marker = "x" if self.is_done else " "
        return f"[{marker}] {self.content[:60]}"


# ============================================================
# uiux개선.md 파싱 → ImprovementItem
# ============================================================
class ImprovementItem(models.Model):
    """P0~P3 개선 항목."""

    class Priority(models.TextChoices):
        P0 = "P0", "P0"
        P1 = "P1", "P1"
        P2 = "P2", "P2"
        P3 = "P3", "P3"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="improvement_items",
    )
    priority = models.CharField(max_length=4, choices=Priority.choices)
    title = models.CharField(max_length=300, verbose_name="제목")
    description = models.TextField(blank=True)
    phase_target = models.CharField(max_length=50, blank=True, verbose_name="구현 예정 Phase")
    is_done = models.BooleanField(default=False)
    raw_text = models.TextField(blank=True)

    class Meta:
        db_table = "improvement_item"
        indexes = [
            models.Index(
                fields=["project", "priority", "is_done"],
                name="idx_improvement_priority",
            ),
        ]
        verbose_name = "개선 항목"
        verbose_name_plural = "개선 항목"

    def __str__(self):
        return f"[{self.priority}] {self.title}"


# ============================================================
# feature_map.md 파싱 → FeatureMap
# ============================================================
class FeatureMap(models.Model):
    """기능↔파일↔DB 매핑."""

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="feature_maps",
    )
    feature_id = models.CharField(max_length=50, blank=True)
    feature_name = models.CharField(max_length=300, blank=True)
    entry_point = models.CharField(max_length=500, blank=True, verbose_name="진입점")
    view_handler = models.CharField(max_length=500, blank=True, verbose_name="뷰 핸들러")
    service = models.CharField(max_length=500, blank=True)
    model_db = models.CharField(max_length=500, blank=True, verbose_name="모델/DB")
    template_ui = models.CharField(max_length=500, blank=True)
    external_api = models.CharField(max_length=500, blank=True, verbose_name="외부 API")
    raw_text = models.TextField(blank=True)

    class Meta:
        db_table = "feature_map"
        indexes = [
            models.Index(fields=["project"], name="idx_featuremap_project"),
        ]
        verbose_name = "기능 매핑"
        verbose_name_plural = "기능 매핑"

    def __str__(self):
        return f"{self.feature_id} {self.feature_name}".strip()
