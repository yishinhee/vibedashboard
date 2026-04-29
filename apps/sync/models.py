"""
SyncLog — 동기화 이력.
sync_service.sync_one_file 이 파일별로 1행씩 기록한다.
"""
from django.db import models


class SyncLog(models.Model):
    """파일별 동기화 결과 1행."""

    class Result(models.TextChoices):
        SUCCESS = "success", "성공"
        FAILED = "failed", "실패"
        NO_CHANGE = "no_change", "변경 없음"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="sync_logs",
    )
    file_name = models.CharField(max_length=200, blank=True, verbose_name="파일명")
    file_mtime = models.DateTimeField(null=True, blank=True, verbose_name="파일 mtime")
    changed = models.BooleanField(default=False, verbose_name="변경 여부")
    result = models.CharField(max_length=20, choices=Result.choices, blank=True)
    detail = models.TextField(blank=True, verbose_name="요약/오류")
    synced_at = models.DateTimeField(auto_now_add=True, verbose_name="동기화 시각")

    class Meta:
        db_table = "sync_log"
        ordering = ["-synced_at"]
        indexes = [
            models.Index(
                fields=["project", "-synced_at"],
                name="idx_synclog_project_time",
            ),
        ]
        verbose_name = "동기화 로그"
        verbose_name_plural = "동기화 로그"

    def __str__(self):
        return f"[{self.synced_at:%Y-%m-%d %H:%M}] {self.file_name} {self.result}"
