"""
Project 모델 — 등록된 외부 프로젝트.
agents.md §아키텍처: 외부 폴더 read-only 참조.
agents.md §Don'ts: 물리 삭제 금지 → soft delete (deleted_at).
"""
from django.db import models
from django.utils import timezone


class ActiveProjectManager(models.Manager):
    """deleted_at 이 null 인 프로젝트만 반환."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Project(models.Model):
    # 식별자 (path 가 unique 비즈니스 키)
    path = models.CharField(max_length=500, unique=True, verbose_name="절대 경로")

    # 본문
    name = models.CharField(max_length=200, verbose_name="프로젝트명")
    description = models.TextField(blank=True, verbose_name="설명")

    # 상태
    last_synced_at = models.DateTimeField(null=True, blank=True, verbose_name="마지막 동기화")

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 소프트 딜리트
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active = ActiveProjectManager()

    class Meta:
        db_table = "project"
        ordering = ["-updated_at"]
        verbose_name = "프로젝트"
        verbose_name_plural = "프로젝트"
        indexes = [
            models.Index(
                fields=["deleted_at"],
                name="idx_project_active",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    def soft_delete(self):
        """deleted_at 만 set. 자식 row cascade 는 service 에서 처리."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
